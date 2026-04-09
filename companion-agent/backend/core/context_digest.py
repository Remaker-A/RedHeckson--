"""Conversation-driven relationship digest: chat history → LLM signals → L1/L0 updates."""

from __future__ import annotations

import logging
from datetime import datetime

from api.ws import ws_manager
from storage.file_store import file_store
from storage.models import (
    ChatDigestState,
    ChatHistoryEntry,
    EvolutionLogEntry,
    Personality,
    Rhythm,
    Soul,
    SoulEvolutionEntry,
)

logger = logging.getLogger(__name__)

CHAT_HISTORY_FILE = "chat_history.jsonl"
DIGEST_STATE_FILE = "chat_digest_state.json"
MAX_BATCH_ENTRIES = 80


def _format_pending_messages(entries: list[ChatHistoryEntry]) -> str:
    lines: list[str] = []
    for e in entries:
        label = "用户" if e.role == "user" else "陪伴"
        lines.append(f"[{label}] {e.content}")
    return "\n".join(lines)


def _clamp_delta(raw) -> float:
    try:
        x = float(raw)
    except (TypeError, ValueError):
        return 0.0
    return max(-0.1, min(0.1, x))


class RelationshipDigester:
    async def run_digest(self, *, manual: bool = False) -> dict:
        """
        manual=True：至少 2 条待处理消息即可整理（方便 Demo）；自动调度为 4 条。
        成功消费一批对话后 notify_scheduler=True，由调用方执行 scheduler.mark_digested()。
        """
        min_pending = 2 if manual else 4
        checkpoint = file_store.load(DIGEST_STATE_FILE, ChatDigestState)
        if not checkpoint:
            checkpoint = ChatDigestState()

        all_entries = file_store.read_jsonl(CHAT_HISTORY_FILE, ChatHistoryEntry)
        total = len(all_entries)
        if checkpoint.processed_lines > total:
            checkpoint.processed_lines = 0

        pending = all_entries[checkpoint.processed_lines :]
        if len(pending) < min_pending:
            return {
                "ok": True,
                "skipped": True,
                "reason": f"待整理消息不足 {min_pending} 条（当前新增 {len(pending)} 条）",
                "notify_scheduler": False,
            }

        batch = pending[:MAX_BATCH_ENTRIES]

        personality = file_store.load("personality.json", Personality)
        if not personality:
            return {
                "ok": False,
                "error": "personality.json 不存在",
                "notify_scheduler": False,
            }

        from intelligence.llm_adapter import llm_adapter

        if not llm_adapter.available:
            return {
                "ok": False,
                "error": "LLM 未配置",
                "notify_scheduler": False,
            }

        messages_text = _format_pending_messages(batch)
        current_params = personality.params.model_dump(mode="json")
        result = await llm_adapter.digest_conversation(messages_text, current_params)
        if not result:
            return {
                "ok": False,
                "error": "模型未返回可解析的 JSON",
                "notify_scheduler": False,
            }

        rhythm = file_store.load("rhythm.json", Rhythm)
        soul = file_store.load("soul.json", Soul)

        personality_changed = self._apply_personality_deltas(personality, rhythm, result)
        soul_changed = False
        if soul:
            soul_changed = self._merge_user_snapshot(soul, result.get("user_snapshot") or {})

        if personality_changed:
            try:
                personality.natural_description = await llm_adapter.generate_natural_description(
                    personality.model_dump(mode="json")
                )
            except Exception as e:
                logger.warning("Natural description refresh failed: %s", e)
            personality.updated_at = datetime.now()
            file_store.save("personality.json", personality)
            await ws_manager.broadcast(
                "personality_update",
                {
                    "version": personality.version,
                    "params": personality.params.model_dump(),
                    "natural_description": personality.natural_description,
                    "voice_style": personality.voice_style,
                },
            )

        if soul_changed and soul:
            file_store.save("soul.json", soul)
            await ws_manager.broadcast("soul_update", {"soul": soul.model_dump(mode="json")})

        checkpoint.processed_lines += len(batch)
        file_store.save(DIGEST_STATE_FILE, checkpoint)

        return {
            "ok": True,
            "skipped": False,
            "notify_scheduler": True,
            "personality_changed": personality_changed,
            "soul_changed": soul_changed,
            "processed_batch": len(batch),
            "digest": result,
        }

    def _apply_personality_deltas(
        self, personality: Personality, rhythm: Rhythm | None, result: dict
    ) -> bool:
        p = personality.params
        changed = False
        pa = result.get("personality_adjustment") or {}
        rel = result.get("relationship") or {}

        for field, key in [
            ("night_owl_index", "night_owl_delta"),
            ("anxiety_sensitivity", "anxiety_delta"),
            ("quietness", "quietness_delta"),
            ("playfulness", "playfulness_delta"),
        ]:
            d = _clamp_delta(pa.get(key, 0))
            if abs(d) < 1e-6:
                continue
            old = getattr(p, field)
            new_v = max(0.0, min(1.0, round(old + d, 3)))
            if abs(new_v - old) > 1e-6:
                setattr(p, field, new_v)
                changed = True

        attach_delta = _clamp_delta(pa.get("attachment_delta", 0)) + _clamp_delta(
            rel.get("closeness_delta", 0)
        )
        attach_delta = max(-0.1, min(0.1, attach_delta))
        if abs(attach_delta) > 1e-6:
            old = p.attachment_level
            new_v = max(0.0, min(1.0, round(old + attach_delta, 3)))
            if abs(new_v - old) > 1e-6:
                p.attachment_level = new_v
                changed = True

        if changed:
            from core.evolution_summary import build_evolution_summary

            personality.version += 1
            reason = (pa.get("reason") or "").strip() or (rel.get("signals") or "").strip()
            if len(reason) > 200:
                reason = reason[:200] + "…"
            snap = dict(personality.params.model_dump(mode="json"))
            summary_zh, context_hint = build_evolution_summary(
                params_snapshot=snap,
                prev_snapshot=None,
                digest_result=result,
                event_type="dialogue_digest",
            )
            personality.evolution_log.append(
                EvolutionLogEntry(
                    day=rhythm.days_together if rhythm else 0,
                    change=(
                        f"digest: owl={p.night_owl_index}, anx={p.anxiety_sensitivity}, "
                        f"quiet={p.quietness}, play={p.playfulness}, attach={p.attachment_level}"
                    ),
                    reason=reason or "对话整理",
                    timestamp=datetime.now(),
                    personality_version=personality.version,
                    event_type="dialogue_digest",
                    params_snapshot=snap,
                    summary_zh=summary_zh,
                    context_hint=context_hint,
                )
            )
        return changed

    def _merge_user_snapshot(self, soul: Soul, snap: dict) -> bool:
        changed = False
        now = datetime.now()

        w = snap.get("current_state_word")
        if isinstance(w, str) and w.strip() and w.strip() != soul.current_state_word:
            old = soul.current_state_word
            soul.current_state_word = w.strip()
            soul.evolution_log.append(SoulEvolutionEntry(
                timestamp=now, field="current_state_word",
                old_value=old, new_value=w.strip(),
            ))
            changed = True

        s = snap.get("struggle")
        if isinstance(s, str) and s.strip() and s.strip() != soul.struggle:
            old = soul.struggle
            soul.struggle = s.strip()
            soul.evolution_log.append(SoulEvolutionEntry(
                timestamp=now, field="struggle",
                old_value=old, new_value=s.strip(),
            ))
            changed = True

        facts = snap.get("facts")
        if isinstance(facts, str) and facts.strip():
            f = facts.strip()
            existing = (soul.user_facts or "").strip()
            if not existing:
                soul.user_facts = f
                soul.evolution_log.append(SoulEvolutionEntry(
                    timestamp=now, field="user_facts",
                    old_value="", new_value=f,
                ))
                changed = True
            elif f not in existing:
                old = existing
                soul.user_facts = f"{existing}；{f}"
                soul.evolution_log.append(SoulEvolutionEntry(
                    timestamp=now, field="user_facts",
                    old_value=old, new_value=soul.user_facts,
                ))
                changed = True
        return changed


relationship_digester = RelationshipDigester()
