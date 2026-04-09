"""Desktop context API — receives context snapshots from the Mac companion app."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter

from storage.file_store import file_store
from storage.models import (
    AppUsageRecord,
    DesktopContext,
    DesktopHeartbeatRequest,
    DesktopSnapshot,
    DesktopSnapshotRequest,
)

router = APIRouter(prefix="/api/desktop", tags=["desktop"])


def _load_context() -> DesktopContext:
    ctx = file_store.load("desktop_context.json", DesktopContext)
    return ctx or DesktopContext()


def _save_context(ctx: DesktopContext) -> None:
    ctx.updated_at = datetime.now()
    file_store.save("desktop_context.json", ctx)


@router.post("/heartbeat")
async def desktop_heartbeat(req: DesktopHeartbeatRequest):
    """Lightweight call from the Mac app on every foreground-app switch."""
    ctx = _load_context()
    ctx.current_snapshot.frontmost_app = req.frontmost_app
    ctx.current_snapshot.frontmost_category = req.frontmost_category
    ctx.current_snapshot.timestamp = datetime.now()
    _save_context(ctx)
    return {"ok": True}


@router.post("/snapshot")
async def desktop_snapshot(req: DesktopSnapshotRequest):
    """Full snapshot pushed every ~5 minutes from the Mac app."""
    ctx = _load_context()

    snapshot = DesktopSnapshot(
        timestamp=datetime.now(),
        frontmost_app=req.frontmost_app,
        frontmost_category=req.frontmost_category,
        window_title_hint=req.window_title_hint,
        activity_summary=req.activity_summary,
        hourly_usage=req.hourly_usage,
        app_switch_count_last_hour=req.app_switch_count_last_hour,
        screen_time_today_minutes=req.screen_time_today_minutes,
    )
    ctx.current_snapshot = snapshot

    if req.hourly_usage:
        merged: dict[str, AppUsageRecord] = {}
        for existing in ctx.daily_top_apps:
            merged[existing.bundle_id] = existing
        for record in req.hourly_usage:
            if record.bundle_id in merged:
                merged[record.bundle_id].duration_minutes += record.duration_minutes
            else:
                merged[record.bundle_id] = record.model_copy()
        ctx.daily_top_apps = sorted(
            merged.values(), key=lambda r: r.duration_minutes, reverse=True
        )[:10]

    total_minutes = sum(r.duration_minutes for r in ctx.daily_top_apps)
    ctx.avg_daily_screen_time_minutes = int(total_minutes)
    ctx.work_pattern = _infer_work_pattern(snapshot)

    _save_context(ctx)
    return {"ok": True, "work_pattern": ctx.work_pattern}


@router.get("/context")
async def get_desktop_context():
    """Return the current desktop context (for frontend / debug)."""
    ctx = _load_context()
    return ctx.model_dump(mode="json")


@router.get("/summary")
async def get_desktop_summary():
    """一次请求返回桌面上下文：结构化数据 + 给页面展示/陪伴用的可读摘要（与 LLM 使用的 L4 格式一致）。"""
    from intelligence.prompts import _format_desktop_context

    ctx = _load_context()
    data = ctx.model_dump(mode="json")
    snap = data.get("current_snapshot") or {}
    has_desktop = bool(
        (snap.get("frontmost_app") or "").strip()
        or (snap.get("activity_summary") or "").strip()
        or (snap.get("window_title_hint") or "").strip()
        or (data.get("daily_top_apps") or [])
    )
    formatted = _format_desktop_context(data) if has_desktop else ""
    pattern = data.get("work_pattern") or ""
    pattern_zh = {
        "deep_focus": "深度专注中",
        "multitasking": "多任务并行",
        "browsing": "浏览网页中",
        "meeting": "会议中",
        "general": "一般使用",
    }.get(pattern, pattern or "未知")

    return {
        "ok": True,
        "has_desktop": has_desktop,
        "context": data,
        "formatted": formatted,
        "work_pattern": pattern,
        "work_pattern_label_zh": pattern_zh,
    }


def _infer_work_pattern(snapshot: DesktopSnapshot) -> str:
    cat = snapshot.frontmost_category
    switches = snapshot.app_switch_count_last_hour

    if cat in ("meeting",):
        return "meeting"
    if switches > 25:
        return "multitasking"
    if cat in ("coding", "terminal"):
        return "deep_focus"
    if cat in ("browser",):
        return "browsing"
    return "general"
