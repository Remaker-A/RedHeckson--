"""User message and mood API."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter

from storage.file_store import file_store
from storage.models import MessageRequest, MoodRequest, UserMessage

router = APIRouter(prefix="/api", tags=["message"])


@router.post("/message")
async def leave_message(req: MessageRequest):
    msg = UserMessage(content=req.content, mood=req.mood, created_at=datetime.now())
    file_store.append_jsonl("messages.jsonl", msg)
    return {"ok": True}


@router.post("/mood")
async def mark_mood(req: MoodRequest):
    msg = UserMessage(content="", mood=req.mood, created_at=datetime.now())
    file_store.append_jsonl("messages.jsonl", msg)
    return {"ok": True, "mood": req.mood}
