"""Soul creation and retrieval API."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException

from intelligence.personality_presets import get_preset
from storage.file_store import file_store
from storage.models import (
    BiasType,
    Personality,
    PersonalityParams,
    Soul,
    SoulCreateRequest,
)

router = APIRouter(prefix="/api/soul", tags=["soul"])


def _build_personality_params(bias: BiasType) -> PersonalityParams:
    params = PersonalityParams(bias=bias)
    if bias == BiasType.CUSTOM:
        return params
    preset = get_preset(bias.value)
    if not preset:
        return params
    for key, val in preset.default_params.items():
        if hasattr(params, key):
            setattr(params, key, val)
    return params


def _resolve_voice_style(req: SoulCreateRequest) -> str:
    if req.bias == BiasType.CUSTOM:
        text = (req.custom_voice_style or "").strip()
        if not text:
            raise HTTPException(
                status_code=400,
                detail="选择「自定义」时请填写 custom_voice_style（描述说话风格）。",
            )
        return text
    if req.custom_voice_style and req.custom_voice_style.strip():
        return req.custom_voice_style.strip()
    preset = get_preset(req.bias.value)
    if preset:
        return preset.voice_style
    return ""


def _initial_description(bias: BiasType) -> str:
    if bias == BiasType.CUSTOM:
        return "它刚刚来到这里，还在认识你。主人为你写下了专属的说话方式。"
    preset = get_preset(bias.value)
    if preset:
        return f"它刚刚来到这里，还在认识你。{preset.short_desc}"
    legacy = {
        BiasType.DECISIVE: "它刚刚来到这里，还在认识你。它的性格偏果断，喜欢干脆利落。",
        BiasType.ADVENTUROUS: "它刚刚来到这里，还在认识你。它的性格偏冒险，对新事物充满好奇。",
        BiasType.SLOW_DOWN: "它刚刚来到这里，还在认识你。它的性格偏沉稳，喜欢慢慢来。",
    }
    return legacy.get(bias, "它刚刚来到这里，还在认识你。")


@router.post("")
async def create_soul(req: SoulCreateRequest):
    if file_store.exists("soul.json"):
        raise HTTPException(status_code=409, detail="Soul already exists. Delete soul.json to recreate.")

    voice_style = _resolve_voice_style(req)
    params = _build_personality_params(req.bias)

    soul = Soul(
        created_at=datetime.now(),
        current_state_word=req.current_state_word,
        struggle=req.struggle,
        bias=req.bias,
        opening_response="你来了。",
    )
    file_store.save("soul.json", soul)

    personality = Personality(
        version=1,
        updated_at=datetime.now(),
        params=params,
        natural_description=_initial_description(req.bias),
        voice_style=voice_style,
        evolution_log=[],
    )
    file_store.save("personality.json", personality)

    return {"ok": True, "soul": soul.model_dump(mode="json")}


@router.get("")
async def get_soul():
    soul = file_store.load("soul.json", Soul)
    if not soul:
        raise HTTPException(status_code=404, detail="Soul not created yet.")
    return soul.model_dump(mode="json")


@router.delete("")
async def reset_soul():
    """Dev-only: delete soul and all related data to start fresh."""
    import os

    data_dir = file_store.data_dir
    for fname in [
        "soul.json",
        "personality.json",
        "rhythm.json",
        "events.jsonl",
        "notes.json",
        "messages.jsonl",
        "chat_history.jsonl",
        "chat_digest_state.json",
    ]:
        path = data_dir / fname
        if path.exists():
            os.remove(path)
    return {"ok": True, "message": "Soul and all data reset."}
