"""Room scene API - maps personality + rhythm to visual scene."""

from __future__ import annotations

from fastapi import APIRouter

from core.state_machine import state_machine
from storage.file_store import file_store
from storage.models import CompanionState, Personality, Rhythm, RoomScene

router = APIRouter(prefix="/api/room", tags=["room"])


@router.get("")
async def get_room():
    scene = _compute_scene()
    return {
        "scene": scene.value,
        "details": _scene_details(scene),
    }


def _compute_scene() -> RoomScene:
    sm = state_machine
    personality = file_store.load("personality.json", Personality)
    rhythm = file_store.load("rhythm.json", Rhythm)

    if sm.ctx.current_state == CompanionState.DEEP_NIGHT:
        return RoomScene.NIGHT

    if rhythm and rhythm.days_together >= 3:
        today = rhythm.recent_7_days[-1] if rhythm.recent_7_days else None
        if not today or today.total_minutes == 0:
            if rhythm.days_together > 3:
                return RoomScene.DUSTY

    if personality:
        p = personality.params
        if p.anxiety_sensitivity > 0.5:
            return RoomScene.MESSY
        if p.attachment_level > 0.3 and (rhythm and rhythm.patterns.regularity_score > 0.5):
            return RoomScene.TIDY

    if rhythm and rhythm.days_together <= 1:
        return RoomScene.RECOVERING

    return RoomScene.TIDY


def _scene_details(scene: RoomScene) -> dict:
    details = {
        RoomScene.TIDY: {
            "description": "帐篷内整洁明亮，小物件摆放整齐，灯光温暖",
            "light": "warm",
            "items": ["book", "plant"],
            "creature_state": "reading",
        },
        RoomScene.MESSY: {
            "description": "帐篷内东西堆在一起，灯光偏暗",
            "light": "dim",
            "items": ["papers", "cup"],
            "creature_state": "restless",
        },
        RoomScene.NIGHT: {
            "description": "帐篷里也亮着灯，桌上多了一杯咖啡",
            "light": "warm_low",
            "items": ["coffee", "lamp"],
            "creature_state": "awake_late",
        },
        RoomScene.DUSTY: {
            "description": "帐篷里落了灰，灯几乎灭了，它缩在角落发呆",
            "light": "almost_off",
            "items": [],
            "creature_state": "lonely",
        },
        RoomScene.RECOVERING: {
            "description": "灯慢慢亮起来，它抬头看你",
            "light": "warming_up",
            "items": ["new_item"],
            "creature_state": "waking",
        },
    }
    return details.get(scene, details[RoomScene.TIDY])
