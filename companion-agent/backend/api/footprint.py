"""Footprint timeline API: aggregated personality + soul evolution history."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter

from core.evolution_summary import generate_fallback_summary, humanize_legacy_context
from storage.file_store import file_store
from storage.models import EvolutionLogEntry, Personality, Soul, SoulEvolutionEntry

router = APIRouter(prefix="/api/footprint", tags=["footprint"])

PARAM_LABELS = {
    "night_owl_index": "夜猫子",
    "anxiety_sensitivity": "敏感度",
    "quietness": "安静",
    "playfulness": "活泼",
    "attachment_level": "依赖",
}

EVENT_TYPE_LABELS = {
    "digest": "对话整理",
    "personality": "节奏演化",
    "rule": "规则演化",
    "soul": "灵魂更新",
}

SOUL_FIELD_LABELS = {
    "current_state_word": "状态词",
    "struggle": "心事",
    "user_facts": "记忆",
}


def _compute_param_deltas(
    current_snapshot: dict | None,
    prev_snapshot: dict | None,
) -> list[dict]:
    if not current_snapshot:
        return []
    deltas: list[dict] = []
    for key, label in PARAM_LABELS.items():
        after = current_snapshot.get(key)
        if after is None:
            continue
        after = float(after)
        before = float(prev_snapshot.get(key, 0)) if prev_snapshot else 0.0
        delta = round(after - before, 4)
        if abs(delta) < 1e-6 and prev_snapshot:
            continue
        deltas.append({
            "key": key,
            "label": label,
            "delta": round(delta, 3),
            "before": round(before, 3),
            "after": round(after, 3),
        })
    return deltas


def _build_personality_event(
    entry: EvolutionLogEntry,
    index: int,
    prev_snapshot: dict | None,
    version: int,
) -> dict:
    event_type = entry.event_type or "personality"
    summary = entry.summary_zh or generate_fallback_summary(
        entry.params_snapshot, prev_snapshot,
        reason=entry.reason, change=entry.change,
    )
    context_hint = entry.context_hint or humanize_legacy_context(entry.reason or "")
    return {
        "id": f"p-{index}",
        "kind": "personality",
        "timestamp": entry.timestamp.isoformat(),
        "event_type": event_type,
        "label_zh": EVENT_TYPE_LABELS.get(event_type, event_type),
        "day": entry.day,
        "personality_version": version,
        "change": entry.change,
        "reason": entry.reason,
        "params_snapshot": entry.params_snapshot,
        "param_deltas": _compute_param_deltas(entry.params_snapshot, prev_snapshot),
        "summary": summary,
        "context_hint": context_hint,
    }


def _build_soul_event(entry: SoulEvolutionEntry, index: int) -> dict:
    field_label = SOUL_FIELD_LABELS.get(entry.field, entry.field)
    if entry.old_value and entry.new_value:
        summary = f"{field_label}：{entry.old_value} → {entry.new_value}"
    elif entry.new_value:
        summary = f"{field_label}：{entry.new_value}"
    else:
        summary = field_label
    return {
        "id": f"s-{index}",
        "kind": "soul",
        "timestamp": entry.timestamp.isoformat(),
        "event_type": "soul",
        "label_zh": "灵魂更新",
        "personality_version": None,
        "change": None,
        "reason": None,
        "params_snapshot": None,
        "param_deltas": [],
        "soul_field": entry.field,
        "soul_field_label": field_label,
        "old_value": entry.old_value,
        "new_value": entry.new_value,
        "summary": summary,
        "context_hint": "",
    }


@router.get("/timeline")
async def get_timeline():
    personality = file_store.load("personality.json", Personality)
    soul = file_store.load("soul.json", Soul)

    events: list[dict] = []
    trend_series: list[dict] = []

    if personality:
        prev_snap: dict | None = None
        for i, entry in enumerate(personality.evolution_log):
            ev = _build_personality_event(entry, i, prev_snap, personality.version)
            events.append(ev)
            if entry.params_snapshot:
                trend_series.append({
                    "timestamp": entry.timestamp.isoformat(),
                    "personality_version": personality.version,
                    "params": entry.params_snapshot,
                })
                prev_snap = entry.params_snapshot

    if soul:
        for i, entry in enumerate(soul.evolution_log):
            events.append(_build_soul_event(entry, i))

    events.sort(key=lambda e: e["timestamp"], reverse=True)

    overview = None
    if soul or personality:
        days_together = 1
        if soul:
            days_together = max(1, (datetime.now() - soul.created_at).days + 1)
        params = {}
        if personality:
            params = personality.params.model_dump(mode="json")
        overview = {
            "soul_created_at": soul.created_at.isoformat() if soul else "",
            "days_together": days_together,
            "personality_version": personality.version if personality else 0,
            "current_state_word": soul.current_state_word if soul else "",
            "struggle": soul.struggle if soul else "",
            "user_facts": soul.user_facts if soul else "",
            "params": params,
        }

    return {
        "overview": overview,
        "events": events,
        "trend_series": trend_series,
    }
