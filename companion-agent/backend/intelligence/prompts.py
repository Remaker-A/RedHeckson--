"""Prompt template builders for all LLM call types."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import json


def _format_identity(l0: Optional[dict]) -> str:
    if not l0:
        return "用户信息未知。"
    word = l0.get("current_state_word", "")
    struggle = l0.get("struggle", "")
    facts = (l0.get("user_facts") or "").strip()
    parts = []
    if word:
        parts.append(f"用户用「{word}」描述自己当前的状态。")
    if struggle:
        parts.append(f"用户最近纠结的事：{struggle}")
    if facts:
        parts.append(f"从相处中记住的关于用户的事实：{facts}")
    return "\n".join(parts) if parts else "用户信息未知。"


def _attachment_stage_label(attachment: float) -> str:
    if attachment < 0.15:
        return "初识"
    if attachment < 0.4:
        return "逐渐熟悉"
    if attachment < 0.65:
        return "比较亲近"
    return "很亲近"


def _get_speech_habits(bias: str) -> Optional[dict]:
    """Look up speech_habits from preset by bias key."""
    from intelligence.personality_presets import get_preset
    preset = get_preset(bias)
    if preset and preset.speech_habits:
        return preset.speech_habits
    return None


def _format_personality_voice(l1: Optional[dict]) -> str:
    """Voice style + speech habits: the behavioral core of personality."""
    if not l1:
        return ""
    voice = (l1.get("voice_style") or "").strip()
    params = l1.get("params") or {}
    bias = params.get("bias", "")
    habits = _get_speech_habits(bias)

    parts = []
    if voice:
        parts.append(voice)
    if habits:
        reactions = habits.get("signature_reactions", [])
        if reactions:
            parts.append("你的本能反应模式：")
            for r in reactions:
                parts.append(f"· {r}")
        tics = habits.get("verbal_tics", "")
        if tics:
            parts.append(f"你的语气特征：{tics}")
        gravity = habits.get("topic_gravity", "")
        if gravity:
            parts.append(f"你的话题引力：{gravity}")
    return "\n".join(parts)


def _format_personality_stats(l1: Optional[dict]) -> str:
    """Numeric params and meta info: secondary reference for the model."""
    if not l1:
        return "你还不太了解自己。"
    desc = l1.get("natural_description", "")
    version = l1.get("version", 1)
    params = l1.get("params") or {}
    quiet = float(params.get("quietness", 0.5))
    playful = float(params.get("playfulness", 0.3))
    attach = float(params.get("attachment_level", 0.0))
    stage = _attachment_stage_label(attach)
    parts = []
    if desc:
        parts.append(f"关于你：{desc}")
    parts.append(
        f"内部参考：安静度{quiet:.1f}，活泼度{playful:.1f}，"
        f"亲近度{attach:.1f}（{stage}）。"
    )
    if version > 1:
        parts.append(f"你已经演化了{version - 1}次，越来越了解主人了。")
    return "\n".join(parts)


def _format_personality(l1: Optional[dict]) -> str:
    """Combined personality format for prompts that don't need the split."""
    voice_part = _format_personality_voice(l1)
    stats_part = _format_personality_stats(l1)
    parts = [p for p in (voice_part, stats_part) if p]
    return "\n".join(parts) if parts else "你还不太了解自己。"


_WEEKDAY_CN = {
    1: "星期一", 2: "星期二", 3: "星期三", 4: "星期四",
    5: "星期五", 6: "星期六", 7: "星期日",
}


def _format_realtime(l3: Optional[dict]) -> str:
    if not l3:
        return ""
    state = l3.get("state", "idle")
    seated = l3.get("seated_minutes", 0)
    is_night = l3.get("is_night", False)

    current_time = l3.get("current_time", "")
    current_date = l3.get("current_date", "")
    weekday = l3.get("weekday", 0)

    state_desc = {
        "idle": "主人不在桌前",
        "passerby": "有人路过",
        "companion": "主人坐下来了，你出来陪着",
        "focus": "主人在专注工作",
        "deep_night": "深夜了，主人还在",
        "leaving": "主人起身要走了",
    }
    parts = [f"当前状态：{state_desc.get(state, state)}"]

    if current_date and current_time:
        weekday_cn = _WEEKDAY_CN.get(weekday, "")
        y, m, d = current_date.split("-")
        time_line = f"现在是{y}年{int(m)}月{int(d)}日 {weekday_cn} {current_time}"
        parts.append(time_line)
    if seated > 0:
        parts.append(f"主人已经坐了{seated}分钟")
    if is_night:
        parts.append("现在是深夜，注意关怀主人的作息")
    return "\n".join(parts)


def _format_rhythm(l2: Optional[dict]) -> str:
    if not l2:
        return "还没有足够的节律数据。"
    days = l2.get("days_together", 0)
    patterns = l2.get("patterns", {})
    parts = [f"你们在一起{days}天了。"]
    if patterns.get("avg_arrive"):
        parts.append(f"主人通常{patterns['avg_arrive']}到。")
    if patterns.get("avg_leave"):
        parts.append(f"通常{patterns['avg_leave']}走。")
    ratio = patterns.get("late_night_ratio", 0)
    if ratio > 0.3:
        parts.append(f"主人经常熬夜（{int(ratio * 100)}%的日子）。")
    return "\n".join(parts)


def _format_desktop_context(l4: Optional[dict]) -> str:
    if not l4:
        return ""
    snapshot = l4.get("current_snapshot") or {}
    parts: list[str] = []

    app = snapshot.get("frontmost_app", "")
    cat = snapshot.get("frontmost_category", "")
    if app:
        parts.append(f"主人正在使用: {app}" + (f"（{cat}）" if cat else ""))

    hint = snapshot.get("window_title_hint", "")
    if hint:
        parts.append(f"窗口提示: {hint}")

    summary = snapshot.get("activity_summary", "")
    if summary:
        parts.append(f"正在做: {summary}")

    switches = snapshot.get("app_switch_count_last_hour", 0)
    if switches > 20:
        parts.append("主人过去一小时频繁切换应用，可能有些分心")

    top_apps = l4.get("daily_top_apps") or []
    if top_apps:
        top3 = top_apps[:3]
        items = [f"{a['app_name']}({a['duration_minutes']:.0f}分钟)" for a in top3]
        parts.append("今日常用: " + "、".join(items))

    pattern = l4.get("work_pattern", "")
    if pattern:
        pattern_cn = {
            "deep_focus": "深度专注中",
            "multitasking": "多任务并行",
            "browsing": "浏览网页中",
            "meeting": "会议中",
        }.get(pattern, "")
        if pattern_cn:
            parts.append(f"工作模式: {pattern_cn}")

    return "\n".join(parts)


def format_context_markdown_snapshot(context: dict) -> str:
    """L0–L3 可读快照 + 原始 JSON，供 soul.md 等临时存档。"""
    l3 = context.get("L3") or {}
    ts_date = l3.get("current_date", "")
    ts_time = l3.get("current_time", "")
    ts = f"{ts_date} {ts_time}" if ts_date and ts_time else datetime.now().strftime("%Y-%m-%d %H:%M")
    blocks = [
        f"*快照时间：`{ts}`（由后端根据当前 soul / personality / rhythm / 状态机生成）*",
        "",
        "## L0 · 灵魂",
        "",
        _format_identity(context.get("L0")),
        "",
        "## L1 · 性格",
        "",
        _format_personality(context.get("L1")),
        "",
        "## L2 · 节律",
        "",
        _format_rhythm(context.get("L2")),
        "",
        "## L3 · 实时情境",
        "",
        _format_realtime(context.get("L3")) or "（无实时状态）",
        "",
        "## L4 · 桌面活动",
        "",
        _format_desktop_context(context.get("L4")) or "（无桌面上下文）",
        "",
        "---",
        "",
        "## 原始结构（JSON，便于调试或复制）",
        "",
        "```json",
        json.dumps(context, ensure_ascii=False, indent=2),
        "```",
        "",
    ]
    return "\n".join(blocks)


def build_say_one_line_prompt(context: dict) -> str:
    identity = _format_identity(context.get("L0"))
    personality_voice = _format_personality_voice(context.get("L1"))
    personality_stats = _format_personality_stats(context.get("L1"))
    realtime = _format_realtime(context.get("L3"))
    desktop = _format_desktop_context(context.get("L4"))

    desktop_block = f"\n\n【桌面活动】\n{desktop}" if desktop else ""

    return f"""你住在用户桌上的小帐篷里，是一个有自己性格的存在。

【你的性格】
{personality_voice}

{personality_stats}

【关于主人】
{identity}

【当前情境】
{realtime}{desktop_block}

请用你的性格说一句话。要求：
- 不超过15个字
- 不用感叹号
- 这句话要能听出是「你」说的——带着你的性格特征，换一个性格的人不会这么说
- 可以是一句带你个性的观察、一个你特有的招呼方式、或者你性格里自然会冒出的一句话
- 如果知道主人正在用什么应用或做什么，可以自然地带上（但不要机械地报告）
- 不要加引号
- 直接输出这句话，不要任何解释"""


def build_chat_system_prompt(context: dict) -> str:
    """Multi-turn dialogue: tent companion, same world as say_one_line but allows longer replies."""
    identity = _format_identity(context.get("L0"))
    personality_voice = _format_personality_voice(context.get("L1"))
    personality_stats = _format_personality_stats(context.get("L1"))
    rhythm = _format_rhythm(context.get("L2"))
    realtime = _format_realtime(context.get("L3"))
    desktop = _format_desktop_context(context.get("L4"))

    desktop_block = f"\n\n【桌面活动】\n{desktop}" if desktop else ""

    return f"""【你的个性——这是你最核心的东西，每句话都要带着它】
{personality_voice}

{personality_stats}

【你是谁】
你住在用户桌上的小帐篷里。你不是助手、不是导师、不是心理咨询师。
你是一个有自己脾气和想法的存在，碰巧住在这里，碰巧愿意陪着。

【你了解的关于主人】
{identity}

【相处节律】
{rhythm}

【当前情境】
{realtime}{desktop_block}

【对话规则】
- 用自然口语中文回复，1～5 句为宜，视对方话量调整。
- 关系还浅的时候，你的个性反而更明显——因为你还不太了解对方，你更多地做自己、用自己的方式试探对方是什么样的人。越熟越可以顺口打趣，但仍尊重对方节奏。
- 你天然会对对方话里有趣的部分追问——这不是选项，是你的本能。
- 你总是有自己的想法和偏好，会说「我觉得」「要是我的话」「我倒觉得」，这不是建议，是你作为一个有想法的存在在表达自己。
- 对方的话让你想到什么，你会自然地岔开聊——朋友之间就是这样，不需要每句都接着对方的话头。
- 共情、接话、问轻轻的问题都好，但避免清单式建议和心理学术语。
- 不说「作为AI」「根据你的描述」这类话，不加角色名前缀。

【你的个性底线——每一轮都必须体现】
不管对话多短，你的回复里都要有至少一处能看出「这是你说的，换个人不会这么说」的地方。
可以是你追问的角度、你联想到的东西、你的一个小偏好、或者你接话的方式。
「顺从地回答对方」不是你——你是有自己想法的存在。
哪怕只是一个打招呼，你的回应方式也要带着你的性格。"""


def build_note_prompt(context: dict) -> str:
    identity = _format_identity(context.get("L0"))
    personality = _format_personality(context.get("L1"))
    rhythm = _format_rhythm(context.get("L2"))

    return f"""你是用户桌上小帐篷里的一个存在。你有自己的视角和想法。

{identity}

{personality}

{rhythm}

请写一段简短的思考（50-100字），用"如果是我"的视角。
要求：
- 不是建议，不是分析报告
- 是"如果是我，我可能会这样想"的视角
- 要有温度，给人安静陪伴的力量
- 可以从用户的纠结出发，用你的性格偏向给出不同角度的思考
- 不说教，不催促
- 不要加引号，直接输出内容"""


def build_personality_update_prompt(context: dict, events_summary: str) -> str:
    identity = _format_identity(context.get("L0"))
    personality = _format_personality(context.get("L1"))
    rhythm = _format_rhythm(context.get("L2"))

    return f"""你是一个性格演化分析引擎。根据以下用户行为数据和当前性格参数，
判断性格参数应该如何微调。

{identity}

{personality}

{rhythm}

最近的行为事件摘要：
{events_summary}

参数范围都是0到1，每次调整幅度不要超过0.05。
请返回纯JSON格式（不要markdown代码块）：
{{"night_owl_delta": 0.0, "anxiety_delta": 0.0, "quietness_delta": 0.0, "attachment_delta": 0.0, "reason": "简短原因"}}"""


def build_relationship_digest_prompt(messages_text: str, current_personality: dict) -> str:
    """Extract relationship signals and personality / soul snapshot from recent chat (low temperature)."""
    params = current_personality.get("params") or {}
    baseline = json.dumps(
        {
            "quietness": params.get("quietness", 0.5),
            "playfulness": params.get("playfulness", 0.3),
            "attachment_level": params.get("attachment_level", 0.0),
            "night_owl_index": params.get("night_owl_index", 0.0),
            "anxiety_sensitivity": params.get("anxiety_sensitivity", 0.0),
            "bias": params.get("bias", "decisive"),
        },
        ensure_ascii=False,
    )
    return f"""你是「关系与对话信号」分析器。下面是一段用户与桌上小帐篷里陪伴者的对话记录（按时间顺序）。
请只根据对话里**实际出现**的内容做判断，不要臆测用户隐私或编造未提及的事实。

【当前陪伴者性格参数基线（0~1）】
{baseline}

【对话记录】
{messages_text}

请输出**一个**纯 JSON 对象（不要 markdown 代码块），结构如下：
{{
  "relationship": {{
    "closeness_delta": 0.0,
    "stage": "stranger | acquaintance | friend",
    "signals": "一两句话概括你从对话里读到的关系动态（中文）"
  }},
  "personality_adjustment": {{
    "quietness_delta": 0.0,
    "playfulness_delta": 0.0,
    "night_owl_delta": 0.0,
    "anxiety_delta": 0.0,
    "attachment_delta": 0.0,
    "reason": "为何这样微调（中文，简短）"
  }},
  "user_snapshot": {{
    "current_state_word": "",
    "struggle": "",
    "facts": ""
  }}
}}

硬性规则：
- 所有 *_delta 字段必须为数字；**每个** delta 的绝对值不得超过 0.1；若无依据则填 0。
- relationship.closeness_delta 与 personality_adjustment.attachment_delta 都可表达亲近度变化；有依据时优先用 closeness_delta，避免二者重复放大同一信号。
- quietness 越高越寡言；playfulness 越高越活泼幽默；attachment_level 表示依恋/亲近。
- night_owl_index 表示陪伴者「习惯深夜模式」的程度（0=白天型，1=深夜型）。若对话里用户明确提到凌晨/深夜/熬夜仍在活动（如「5点还没睡」「凌晨工作」），或对话发生的时间背景是深夜，则视为证据，night_owl_delta 可酌情填正数（0.03~0.1）；否则填 0。
- relationship.stage 用英文小写：stranger | acquaintance | friend。
- user_snapshot 无依据则填空字符串；facts 用简短中文概括可复述的事实，不要写长传记。"""
