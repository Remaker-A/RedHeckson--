"""Note (纸条) API - it writes thoughts from its perspective."""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException

from storage.file_store import file_store
from storage.models import Note, Personality

router = APIRouter(prefix="/api/notes", tags=["notes"])


@router.get("")
async def list_notes():
    notes = file_store.load_json_list("notes.json", Note)
    return [n.model_dump(mode="json") for n in notes]


@router.get("/latest")
async def get_latest_note():
    notes = file_store.load_json_list("notes.json", Note)
    if not notes:
        raise HTTPException(status_code=404, detail="No notes yet.")
    return notes[-1].model_dump(mode="json")


@router.post("/generate")
async def generate_note():
    """Trigger note generation via LLM with context, or fallback."""
    from core.context import context_manager
    from intelligence.llm_adapter import llm_adapter

    ctx = context_manager.for_note()
    content = await llm_adapter.generate_note(ctx)

    p = file_store.load("personality.json", Personality)
    note = Note(
        id=str(uuid.uuid4())[:8],
        content=content,
        created_at=datetime.now(),
        personality_version=p.version if p else 1,
    )

    notes = file_store.load_json_list("notes.json", Note)
    notes.append(note)
    file_store.save_json_list("notes.json", notes)

    return note.model_dump(mode="json")
