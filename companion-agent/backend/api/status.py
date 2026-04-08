"""Status query API."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException

from core.state_machine import state_machine
from intelligence.personality_presets import get_all_presets, get_preset
from storage.file_store import file_store
from storage.models import BiasType, Personality, PersonalityUpdateRequest, Soul

router = APIRouter(prefix="/api", tags=["status"])


@router.get("/status")
async def get_status():
    return state_machine.get_status()


@router.get("/personality/presets")
async def list_personality_presets():
    return {"presets": get_all_presets()}


@router.get("/personality")
async def get_personality():
    p = file_store.load("personality.json", Personality)
    if not p:
        return {"error": "Personality not initialized. Create soul first."}
    return p.model_dump(mode="json")


@router.patch("/personality")
async def patch_personality(req: PersonalityUpdateRequest):
    p = file_store.load("personality.json", Personality)
    if not p:
        raise HTTPException(status_code=404, detail="Personality not initialized. Create soul first.")
    soul = file_store.load("soul.json", Soul)
    if not soul:
        raise HTTPException(status_code=404, detail="Soul not found.")

    if req.bias is not None:
        soul.bias = req.bias
        p.params.bias = req.bias
        if req.voice_style is not None:
            p.voice_style = req.voice_style.strip()
        elif req.bias == BiasType.CUSTOM:
            pass
        else:
            preset = get_preset(req.bias.value)
            p.voice_style = preset.voice_style if preset else ""
    elif req.voice_style is not None:
        p.voice_style = req.voice_style.strip()

    p.updated_at = datetime.now()
    file_store.save("personality.json", p)
    file_store.save("soul.json", soul)
    return {"ok": True, "personality": p.model_dump(mode="json")}
