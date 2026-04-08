"""On-demand companion line and multi-turn chat (dev / manual testing)."""

from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from storage.file_store import file_store
from storage.models import ChatHistoryEntry, ChatRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/companion", tags=["companion"])


@router.post("/speak")
async def companion_speak():
    """Generate one short line from current context (same path as state-change say_line)."""
    from core.context import context_manager
    from intelligence.llm_adapter import llm_adapter

    if not llm_adapter.available:
        return {"ok": False, "say_line": None, "error": "LLM 未配置（检查 SILICONFLOW_API_KEY 等）"}
    ctx = context_manager.for_say_one_line()
    line = await llm_adapter.generate_say_one_line(ctx)
    return {"ok": True, "say_line": line}


@router.post("/chat")
async def companion_chat(req: ChatRequest):
    """Multi-turn chat; optional history as alternating user/assistant messages."""
    from core.context import context_manager
    from intelligence.llm_adapter import llm_adapter

    if not req.message.strip():
        return {"ok": False, "reply": None, "error": "message 不能为空"}
    if not llm_adapter.available:
        return {"ok": False, "reply": None, "error": "LLM 未配置（检查 SILICONFLOW_API_KEY 等）"}

    ctx = context_manager.for_chat()
    hist = [t.model_dump() for t in req.history]
    try:
        reply = await llm_adapter.generate_chat_reply(ctx, hist, req.message)
    except Exception as e:
        return {"ok": False, "reply": None, "error": str(e)}
    if not reply:
        return {"ok": False, "reply": None, "error": "模型未返回有效内容"}

    try:
        from core.scheduler import scheduler

        file_store.append_jsonl(
            "chat_history.jsonl",
            ChatHistoryEntry(role="user", content=req.message.strip(), timestamp=datetime.now()),
        )
        file_store.append_jsonl(
            "chat_history.jsonl",
            ChatHistoryEntry(role="assistant", content=reply.strip(), timestamp=datetime.now()),
        )
        scheduler.record_chat_message()
    except Exception as e:
        logger.warning("chat_history append failed: %s", e)

    return {"ok": True, "reply": reply}


@router.post("/digest")
async def companion_digest():
    """手动触发对话整理（关系信号 → 性格 / L0 更新），用于演示与调试。"""
    from core.context_digest import relationship_digester
    from core.scheduler import scheduler
    from intelligence.llm_adapter import llm_adapter

    if not llm_adapter.available:
        return {"ok": False, "error": "LLM 未配置（检查 SILICONFLOW_API_KEY 等）"}
    out = await relationship_digester.run_digest(manual=True)
    if out.get("notify_scheduler"):
        scheduler.mark_digested()
    return out


@router.get("/context-markdown", response_class=PlainTextResponse)
async def companion_context_markdown():
    """导出 L0–L3 多级上下文为 Markdown（写入 soul.md 等）。"""
    from core.context import context_manager
    from intelligence.prompts import format_context_markdown_snapshot

    ctx = context_manager.for_chat()
    return format_context_markdown_snapshot(ctx)
