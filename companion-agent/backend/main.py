"""FastAPI entry point for the Companion Agent backend."""

from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

sys.path.insert(0, str(Path(__file__).parent))

from api import companion, desktop, focus, footprint, message, note, personality, room, simulate, soul, status
from api.ws import ws_manager
from core.scheduler import scheduler
from core.state_machine import state_machine
from storage.models import StateEvent


@asynccontextmanager
async def lifespan(app: FastAPI):
    state_machine.on_state_change(_on_state_change)
    await scheduler.start()
    yield
    await scheduler.stop()
    from intelligence.llm_adapter import llm_adapter
    await llm_adapter.close()


app = FastAPI(title="Companion Agent", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(soul.router)
app.include_router(personality.router)
app.include_router(companion.router)
app.include_router(status.router)
app.include_router(room.router)
app.include_router(note.router)
app.include_router(focus.router)
app.include_router(message.router)
app.include_router(simulate.router)
app.include_router(desktop.router)
app.include_router(footprint.router)


async def _on_state_change(event: StateEvent):
    from core.context import context_manager
    from core.scheduler import scheduler as sched
    from intelligence.llm_adapter import llm_adapter
    from storage.file_store import file_store

    file_store.append_jsonl("events.jsonl", event)
    sched.record_event()

    say_line = None
    if event.to_state.value in ("companion", "deep_night", "leaving"):
        try:
            ctx = context_manager.for_say_one_line()
            say_line = await llm_adapter.generate_say_one_line(ctx)
        except Exception:
            say_line = "嗯。"

    await ws_manager.broadcast("state_change", {
        "from": event.from_state.value,
        "to": event.to_state.value,
        "status": state_machine.get_status(),
        "say_line": say_line,
    })


@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Client heartbeat / future commands
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


@app.get("/")
async def root():
    return {
        "name": "Companion Agent Backend",
        "version": "0.1.0",
        "status": state_machine.get_status(),
        "ws_clients": ws_manager.count,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
