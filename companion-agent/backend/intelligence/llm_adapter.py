"""LLM adapter - unified OpenAI-compatible interface for multiple cloud providers."""

from __future__ import annotations

import json
import logging
import re
from typing import Optional

import httpx

from config import settings
from intelligence.corpus import pick_line
from intelligence.prompts import (
    build_chat_system_prompt,
    build_note_prompt,
    build_personality_update_prompt,
    build_relationship_digest_prompt,
    build_say_one_line_prompt,
)

logger = logging.getLogger(__name__)

_DIGEST_DELTA_CAP = 0.1


def _clamp_digest_delta(v) -> float:
    try:
        x = float(v)
    except (TypeError, ValueError):
        return 0.0
    if x > _DIGEST_DELTA_CAP:
        return _DIGEST_DELTA_CAP
    if x < -_DIGEST_DELTA_CAP:
        return -_DIGEST_DELTA_CAP
    return x


def _balanced_json_object(s: str) -> Optional[str]:
    """First top-level {...} by brace depth, respecting JSON string escapes."""
    start = s.find("{")
    if start < 0:
        return None
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(s)):
        c = s[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
            continue
        if c == '"':
            in_str = True
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return s[start : i + 1]
    return None


def _lenient_json_dict(blob: str) -> Optional[dict]:
    """Try json.loads; then strip trailing commas before } or ]."""
    blob = blob.strip()
    try:
        out = json.loads(blob)
        return out if isinstance(out, dict) else None
    except json.JSONDecodeError:
        pass
    try:
        fixed = re.sub(r",\s*}", "}", blob)
        fixed = re.sub(r",\s*]", "]", fixed)
        out = json.loads(fixed)
        return out if isinstance(out, dict) else None
    except json.JSONDecodeError:
        return None


def _extract_json_object_string(raw: str) -> Optional[str]:
    """Pull a single JSON object from model text; handles ```json ... ``` fences."""
    s = (raw or "").strip()
    if not s:
        return None
    if "```" in s:
        best: Optional[str] = None
        for seg in s.split("```"):
            seg = seg.strip()
            if not seg:
                continue
            low = seg.lower()
            if low.startswith("json"):
                seg = seg[4:].lstrip()
            cand = _balanced_json_object(seg)
            if cand and (best is None or len(cand) > len(best)):
                best = cand
        if best is not None:
            return best
    return _balanced_json_object(s)


class LLMAdapter:
    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def provider_config(self) -> dict:
        return settings.llm_providers.get(settings.llm_provider, {})

    @property
    def available(self) -> bool:
        cfg = self.provider_config
        return bool(cfg.get("api_key") and cfg.get("base_url"))

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def _chat_completion(
        self,
        system_prompt: str,
        user_content: str = "",
        max_tokens: int = 200,
        temperature: float = 0.8,
        request_timeout: float = 30.0,
    ) -> str:
        cfg = self.provider_config
        if not self.available:
            raise RuntimeError("LLM provider not configured")

        messages = [{"role": "system", "content": system_prompt}]
        if user_content:
            messages.append({"role": "user", "content": user_content})

        payload = {
            "model": cfg["model"],
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        client = self._get_client()
        resp = await client.post(
            f"{cfg['base_url']}/chat/completions",
            json=payload,
            headers={
                "Authorization": f"Bearer {cfg['api_key']}",
                "Content-Type": "application/json",
            },
            timeout=request_timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        msg = data["choices"][0]["message"]
        content = msg.get("content")
        if content is None and isinstance(msg.get("reasoning_content"), str):
            content = msg["reasoning_content"]
        return (str(content) if content is not None else "").strip()

    async def _chat_completion_messages(
        self,
        messages: list[dict],
        max_tokens: int = 800,
        temperature: float = 0.75,
    ) -> str:
        cfg = self.provider_config
        if not self.available:
            raise RuntimeError("LLM provider not configured")
        payload = {
            "model": cfg["model"],
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        client = self._get_client()
        resp = await client.post(
            f"{cfg['base_url']}/chat/completions",
            json=payload,
            headers={
                "Authorization": f"Bearer {cfg['api_key']}",
                "Content-Type": "application/json",
            },
            timeout=120.0,
        )
        resp.raise_for_status()
        data = resp.json()
        msg = data["choices"][0]["message"]
        content = msg.get("content")
        if content is None:
            return ""
        return str(content).strip()

    async def generate_chat_reply(
        self,
        context: dict,
        history: list[dict],
        user_message: str,
    ) -> str:
        system_prompt = build_chat_system_prompt(context)
        messages: list[dict] = [{"role": "system", "content": system_prompt}]
        for turn in history[-24:]:
            role = turn.get("role")
            text = (turn.get("content") or "").strip()
            if role not in ("user", "assistant") or not text:
                continue
            messages.append({"role": role, "content": text})
        messages.append({"role": "user", "content": user_message.strip()})
        return await self._chat_completion_messages(
            messages, max_tokens=1024, temperature=0.82
        )

    async def generate_say_one_line(self, context: dict) -> str:
        """Generate a short companion line (<=15 chars)."""
        try:
            if not self.available:
                raise RuntimeError("no provider")

            system_prompt = build_say_one_line_prompt(context)
            result = await self._chat_completion(
                system_prompt=system_prompt,
                max_tokens=60,
                temperature=0.85,
            )
            result = result.strip().strip('"').strip("'").strip('"').strip('"')
            if len(result) > 20:
                result = result[:15]
            return result

        except Exception as e:
            logger.warning(f"LLM say_one_line failed, using corpus fallback: {e}")
            state = context.get("L3", {}).get("state", "companion")
            time_period = context.get("L3", {}).get("time_period", "afternoon")
            return pick_line(state, time_period)

    async def generate_note(self, context: Optional[dict] = None) -> str:
        """Generate a note (50-100 chars) from its perspective."""
        try:
            if not self.available:
                raise RuntimeError("no provider")

            if context is None:
                from core.context import context_manager
                context = context_manager.for_note()

            system_prompt = build_note_prompt(context)
            result = await self._chat_completion(
                system_prompt=system_prompt,
                max_tokens=200,
                temperature=0.8,
            )
            return result.strip().strip('"').strip("'")

        except Exception as e:
            logger.warning(f"LLM note generation failed: {e}")
            return "有时候不做选择，也是一种选择。站在这里看着窗外，觉得不管怎样，天总会亮的。"

    async def generate_personality_update(self, context: dict, events_summary: str) -> Optional[dict]:
        """Ask LLM to suggest personality parameter deltas."""
        try:
            if not self.available:
                raise RuntimeError("no provider")

            system_prompt = build_personality_update_prompt(context, events_summary)
            result = await self._chat_completion(
                system_prompt=system_prompt,
                user_content="请分析并返回JSON",
                max_tokens=200,
                temperature=0.3,
            )
            start = result.find("{")
            end = result.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(result[start:end])
            return None

        except Exception as e:
            logger.warning(f"LLM personality update failed: {e}")
            return None

    async def digest_conversation(
        self, history_text: str, current_personality: dict
    ) -> Optional[dict]:
        """LLM extracts relationship + personality deltas + user snapshot from chat."""
        try:
            if not self.available:
                raise RuntimeError("no provider")
            system_prompt = build_relationship_digest_prompt(
                history_text, current_personality
            )
            result = await self._chat_completion(
                system_prompt=system_prompt,
                user_content="请只输出 JSON。",
                max_tokens=1024,
                temperature=0.3,
                request_timeout=120.0,
            )
            if not result:
                logger.warning("digest: empty model content")
                return None
            blob = _extract_json_object_string(result)
            if not blob:
                logger.warning(
                    "digest: no JSON object in model output (preview): %s",
                    (result or "")[:500],
                )
                return None
            try:
                data = json.loads(blob)
            except json.JSONDecodeError:
                data = _lenient_json_dict(blob)
            if not data:
                logger.warning(
                    "digest: JSON parse failed (preview): %s",
                    (result or "")[:500],
                )
                return None
            rel = data.get("relationship") or {}
            if isinstance(rel, dict) and "closeness_delta" in rel:
                rel["closeness_delta"] = _clamp_digest_delta(rel.get("closeness_delta"))
            adj = data.get("personality_adjustment")
            if isinstance(adj, dict):
                for key in (
                    "quietness_delta",
                    "playfulness_delta",
                    "night_owl_delta",
                    "anxiety_delta",
                    "attachment_delta",
                ):
                    if key in adj:
                        adj[key] = _clamp_digest_delta(adj.get(key))
            snap = data.get("user_snapshot")
            if not isinstance(snap, dict):
                data["user_snapshot"] = {
                    "current_state_word": "",
                    "struggle": "",
                    "facts": "",
                }
            return data
        except Exception as e:
            logger.warning(f"LLM conversation digest failed: {e}")
            return None

    async def generate_natural_description(self, personality_data: dict) -> str:
        """Use LLM to generate a natural language personality description."""
        try:
            if not self.available:
                raise RuntimeError("no provider")

            params = personality_data.get("params", {})
            system = (
                "你是一个帐篷里的存在的旁白者。根据以下性格参数，"
                "用一句简短的中文描述这个存在的性格特点。"
                "不超过50字，语气温暖自然。\n\n"
                f"性格偏向: {params.get('bias', 'decisive')}\n"
                f"夜猫子指数: {params.get('night_owl_index', 0)}\n"
                f"焦虑敏感度: {params.get('anxiety_sensitivity', 0)}\n"
                f"安静度: {params.get('quietness', 0.5)}\n"
                f"活泼幽默度: {params.get('playfulness', 0.3)}\n"
                f"依恋程度: {params.get('attachment_level', 0)}"
            )
            return await self._chat_completion(system, max_tokens=80, temperature=0.7)

        except Exception:
            return self._rule_based_description(personality_data)

    def _rule_based_description(self, personality_data: dict) -> str:
        params = personality_data.get("params", {})
        parts = []
        bias_names = {
            "decisive": "果断",
            "adventurous": "冒险",
            "slow_down": "沉稳",
            "warm_humor": "温暖幽默",
            "night_owl": "夜猫子",
            "bookish": "爱想事情",
            "custom": "独特",
        }
        parts.append(f"它的性格偏{bias_names.get(params.get('bias', 'decisive'), '果断')}")
        if params.get("night_owl_index", 0) > 0.5:
            parts.append("习惯了晚睡")
        if params.get("anxiety_sensitivity", 0) > 0.4:
            parts.append("会在你焦虑时安静一会儿")
        if params.get("attachment_level", 0) > 0.4:
            parts.append("开始认得你回来的时间了")
        if params.get("quietness", 0.5) > 0.6:
            parts.append("更喜欢安静地陪着")
        if params.get("playfulness", 0.3) > 0.55:
            parts.append("说话时会带点轻松的玩笑")
        return "，".join(parts) + "。"

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()


llm_adapter = LLMAdapter()
