"""Personality presets list and user edits (voice / bias)."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException

from api.ws import ws_manager
from intelligence.personality_presets import get_all_presets, get_preset
from storage.file_store import file_store
from storage.models import BiasType, Personality, PersonalityUpdateRequest, Soul

router = APIRouter(prefix="/api/personality", tags=["personality"])


@router.get("/presets")
async def list_personality_presets():
    return {"presets": get_all_presets()}


@router.patch("")
async def patch_personality(req: PersonalityUpdateRequest):
    p = file_store.load("personality.json", Personality)
    if not p:
        raise HTTPException(status_code=404, detail="Personality not initialized. Create soul first.")

    soul = file_store.load("soul.json", Soul)

    if req.bias is not None:
        p.params.bias = req.bias
        if soul:
            soul.bias = req.bias
            file_store.save("soul.json", soul)

    if req.voice_style is not None:
        p.voice_style = req.voice_style.strip()
    elif req.bias is not None:
        preset = get_preset(req.bias.value) if req.bias != BiasType.CUSTOM else None
        if preset and preset.voice_style:
            p.voice_style = preset.voice_style
        elif req.bias == BiasType.CUSTOM and not (p.voice_style or "").strip():
            p.voice_style = (
                "你有自己的说话方式：温和、真诚，像身边的朋友。"
                "不刻意搞笑也不说教，顺着对方的话说下去就好。"
            )

    p.updated_at = datetime.now()
    file_store.save("personality.json", p)

    await ws_manager.broadcast("personality_update", {
        "version": p.version,
        "params": p.params.model_dump(),
        "natural_description": p.natural_description,
        "voice_style": p.voice_style,
    })

    return p.model_dump(mode="json")
