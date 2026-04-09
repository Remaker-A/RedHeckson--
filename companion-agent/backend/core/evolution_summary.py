"""Generate user-friendly summaries for personality evolution events.

Combines digest signals, LLM reasons, event statistics, and parameter
deltas into natural-language text suitable for the footprint timeline.
"""

from __future__ import annotations

from typing import Optional

_DELTA_PHRASES: dict[str, tuple[str, str]] = {
    "night_owl_index":      ("蓬蓬开始习惯晚睡了",       "蓬蓬作息变早了"),
    "anxiety_sensitivity":  ("蓬蓬变得更能感知你的情绪了", "蓬蓬没那么紧张了"),
    "quietness":            ("蓬蓬更喜欢安静地待着了",     "蓬蓬话变多了"),
    "playfulness":          ("蓬蓬说话更爱开玩笑了",       "蓬蓬变得沉稳了些"),
    "attachment_level":     ("蓬蓬变得更粘人了",           "蓬蓬更独立了"),
}

_STAGE_ZH = {
    "stranger": "陌生",
    "acquaintance": "熟悉中",
    "friend": "朋友",
}


def _clean_prefix(text: str) -> str:
    """Strip technical prefixes like 'conversation_digest:', 'LLM analysis' etc."""
    for prefix in ("conversation_digest:", "conversation_digest：", "LLM analysis", "rule-based periodic update"):
        if text.startswith(prefix):
            text = text[len(prefix):]
    return text.strip()


def _deltas_to_phrases(
    current_snapshot: Optional[dict],
    prev_snapshot: Optional[dict],
) -> list[str]:
    """Turn param delta into human phrases using the mapping table."""
    if not current_snapshot:
        return []
    phrases: list[str] = []
    for key, (inc_phrase, dec_phrase) in _DELTA_PHRASES.items():
        after = current_snapshot.get(key)
        if after is None:
            continue
        before = float(prev_snapshot.get(key, 0)) if prev_snapshot else 0.0
        delta = float(after) - before
        if abs(delta) < 0.005:
            continue
        phrases.append(inc_phrase if delta > 0 else dec_phrase)
    return phrases


def build_evolution_summary(
    *,
    params_snapshot: Optional[dict] = None,
    prev_snapshot: Optional[dict] = None,
    digest_result: Optional[dict] = None,
    llm_reason: Optional[str] = None,
    events_summary: Optional[str] = None,
    event_type: str = "personality",
) -> tuple[str, str]:
    """Return (summary_zh, context_hint) for an evolution log entry.

    Parameters
    ----------
    params_snapshot : current personality params after change
    prev_snapshot   : personality params before change (for delta computation)
    digest_result   : full LLM digest dict (relationship / personality_adjustment / user_snapshot)
    llm_reason      : reason string from LLM personality update
    events_summary  : text summary of recent state events
    event_type      : "dialogue_digest" | "rhythm_llm" | "rhythm_rule" | ...
    """
    summary_parts: list[str] = []
    hint_parts: list[str] = []

    if digest_result:
        _build_from_digest(digest_result, summary_parts, hint_parts)

    if llm_reason and not digest_result:
        cleaned = _clean_prefix(llm_reason)
        if cleaned:
            summary_parts.append(cleaned)

    if events_summary and not digest_result:
        hint_parts.append(_humanize_events_summary(events_summary))

    delta_phrases = _deltas_to_phrases(params_snapshot, prev_snapshot)

    if not summary_parts and delta_phrases:
        summary_parts.extend(delta_phrases)
    elif delta_phrases and not any(p in "".join(summary_parts) for p in delta_phrases):
        remaining = [p for p in delta_phrases if p not in "".join(summary_parts)]
        if remaining:
            summary_parts.append("，".join(remaining))

    summary_zh = "，".join(summary_parts) if summary_parts else "蓬蓬悄悄发生了一点变化"
    context_hint = "；".join(hint_parts) if hint_parts else ""

    if len(summary_zh) > 80:
        summary_zh = summary_zh[:78] + "…"
    if len(context_hint) > 200:
        context_hint = context_hint[:198] + "…"

    return summary_zh, context_hint


def _build_from_digest(
    result: dict,
    summary_parts: list[str],
    hint_parts: list[str],
) -> None:
    """Extract user-friendly text from a conversation digest result."""
    rel = result.get("relationship") or {}
    adj = result.get("personality_adjustment") or {}
    snap = result.get("user_snapshot") or {}

    signals = (rel.get("signals") or "").strip()
    stage = rel.get("stage", "")
    adj_reason = _clean_prefix((adj.get("reason") or "").strip())
    closeness = float(rel.get("closeness_delta", 0))

    if signals:
        summary_parts.append(signals)
    elif adj_reason:
        summary_parts.append(adj_reason)

    if abs(closeness) > 0.005:
        if closeness > 0:
            summary_parts.append("蓬蓬感觉你们更熟了一点")
        else:
            summary_parts.append("蓬蓬觉得你有些疏远")

    facts = (snap.get("facts") or "").strip()
    if facts:
        summary_parts.append(f"蓬蓬记住了：{facts}")

    if signals:
        hint_parts.append(signals)
    if adj_reason and adj_reason != signals:
        hint_parts.append(adj_reason)
    if stage and stage in _STAGE_ZH:
        hint_parts.append(f"当前关系阶段：{_STAGE_ZH[stage]}")

    state_word = (snap.get("current_state_word") or "").strip()
    struggle = (snap.get("struggle") or "").strip()
    if state_word:
        hint_parts.append(f"用户当前状态：{state_word}")
    if struggle:
        hint_parts.append(f"用户的心事：{struggle}")


def _humanize_events_summary(raw: str) -> str:
    """Turn event summary stats into friendlier language."""
    if not raw or raw == "最近没有事件记录。":
        return ""
    lines = raw.strip().split("\n")
    parts: list[str] = []
    for line in lines:
        line = line.strip()
        if "deep_night" in line:
            parts.append("蓬蓬注意到你有几次深夜还在桌前")
        elif "companion" in line:
            parts.append("蓬蓬出来陪了你好几次")
        elif "focus" in line:
            parts.append("你有几段专注时间")
        elif line.startswith("最近") and "事件" in line:
            continue
        elif "idle" in line:
            continue
        elif line:
            parts.append(line)
    return "；".join(parts) if parts else raw


def generate_fallback_summary(
    params_snapshot: Optional[dict],
    prev_snapshot: Optional[dict],
    reason: Optional[str] = None,
    change: Optional[str] = None,
) -> str:
    """Generate a summary from snapshots / reason / change (for legacy data without summary_zh)."""
    phrases = _deltas_to_phrases(params_snapshot, prev_snapshot)
    if phrases:
        return "，".join(phrases)

    if reason:
        cleaned = humanize_legacy_reason(reason)
        if cleaned:
            return cleaned

    return "蓬蓬悄悄发生了一点变化"


def humanize_legacy_reason(raw: str) -> str:
    """Convert a legacy reason string into a short user-friendly summary.

    Takes only the first meaningful segment so it stays concise.
    """
    text = _clean_prefix(raw)
    if not text:
        return ""

    text = _strip_param_jargon(text)
    text = text.strip("；; ，,")
    if not text or len(text) < 4:
        return ""

    segments = _re.split(r"[；;]", text)
    short = segments[0].strip("，, ")
    if not short or len(short) < 4:
        short = text
    if len(short) > 60:
        short = short[:58] + "…"
    return short


def humanize_legacy_context(raw: str) -> str:
    """Clean a legacy reason for use as context_hint (expanded detail)."""
    text = _clean_prefix(raw)
    text = _strip_param_jargon(text)
    text = text.strip("；; ，,")
    return text


import re as _re

_JARGON_PATTERNS = [
    _re.compile(r"playfulness\s*可?微增"),
    _re.compile(r"closeness_delta\s*已反映此变化"),
    _re.compile(r"其他参数暂无明显变化依据"),
    _re.compile(r"亲近度微增"),
    _re.compile(r"[a-z_]+_delta\S*"),
    _re.compile(r"\b(owl|anx|quiet|play|attach)\s*=\s*[\d.]+"),
    _re.compile(r"(LLM|digest|rule)\s*:\s*"),
]

_JARGON_REPLACEMENTS = {
    "playfulness可微增": "蓬蓬说话更爱开玩笑了",
    "亲近度微增": "蓬蓬感觉你们更熟了一点",
}


def _strip_param_jargon(text: str) -> str:
    """Remove or replace parameter-level jargon from text."""
    for old, new in _JARGON_REPLACEMENTS.items():
        text = text.replace(old, new)

    for pat in _JARGON_PATTERNS:
        text = pat.sub("", text)

    text = _re.sub(r"[；;，,]{2,}", "；", text)
    text = _re.sub(r"\s+", " ", text)
    text = _re.sub(r"[，,；;但、]\s*$", "", text)
    return text.strip("；; ，, ")
