"""Focus mode (Pomodoro) API."""

from __future__ import annotations

from fastapi import APIRouter

from core.state_machine import state_machine
from storage.models import FocusStartRequest

router = APIRouter(prefix="/api/focus", tags=["focus"])


@router.post("/start")
async def start_focus(req: FocusStartRequest):
    await state_machine.start_focus(req.duration_minutes)
    return state_machine.get_status()


@router.post("/stop")
async def stop_focus():
    await state_machine.stop_focus()
    return state_machine.get_status()


@router.get("")
async def get_focus():
    return {
        "active": state_machine.focus.active,
        "duration_minutes": state_machine.focus.duration_minutes,
        "started_at": state_machine.focus.started_at.isoformat() if state_machine.focus.started_at else None,
    }
