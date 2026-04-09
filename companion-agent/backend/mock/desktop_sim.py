"""Simulated desktop context scenarios — replaces the real Mac app for testing."""

from __future__ import annotations

import logging
import random
from datetime import datetime

from storage.file_store import file_store
from storage.models import AppUsageRecord, DesktopContext, DesktopSnapshot

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pre-baked scenario templates
# ---------------------------------------------------------------------------

SCENARIOS: dict[str, dict] = {
    "deep_focus_coding": {
        "label": "深度编码",
        "snapshot": DesktopSnapshot(
            frontmost_app="Xcode",
            frontmost_category="coding",
            window_title_hint="在 Xcode 中编辑 SwiftUI 视图",
            activity_summary="用户在 IDE 中编写 SwiftUI 代码，预览窗口打开着",
            hourly_usage=[
                AppUsageRecord(app_name="Xcode", bundle_id="com.apple.dt.Xcode",
                               duration_minutes=48.0, category="coding"),
                AppUsageRecord(app_name="iTerm2", bundle_id="com.googlecode.iterm2",
                               duration_minutes=7.0, category="terminal"),
                AppUsageRecord(app_name="Safari", bundle_id="com.apple.Safari",
                               duration_minutes=5.0, category="browser"),
            ],
            app_switch_count_last_hour=6,
            screen_time_today_minutes=180,
        ),
        "work_pattern": "deep_focus",
    },

    "distracted_browsing": {
        "label": "分心刷网页",
        "snapshot": DesktopSnapshot(
            frontmost_app="Safari",
            frontmost_category="browser",
            window_title_hint="在浏览器中刷社交媒体",
            activity_summary="用户在浏览器中浏览社交媒体和视频网站",
            hourly_usage=[
                AppUsageRecord(app_name="Safari", bundle_id="com.apple.Safari",
                               duration_minutes=28.0, category="browser"),
                AppUsageRecord(app_name="微信", bundle_id="com.tencent.xinWeChat",
                               duration_minutes=15.0, category="communication"),
                AppUsageRecord(app_name="Spotify", bundle_id="com.spotify.client",
                               duration_minutes=12.0, category="media"),
                AppUsageRecord(app_name="Xcode", bundle_id="com.apple.dt.Xcode",
                               duration_minutes=5.0, category="coding"),
            ],
            app_switch_count_last_hour=32,
            screen_time_today_minutes=260,
        ),
        "work_pattern": "multitasking",
    },

    "in_meeting": {
        "label": "会议中",
        "snapshot": DesktopSnapshot(
            frontmost_app="Zoom",
            frontmost_category="meeting",
            window_title_hint="会议中",
            activity_summary="用户正在视频会议中",
            hourly_usage=[
                AppUsageRecord(app_name="Zoom", bundle_id="us.zoom.xos",
                               duration_minutes=45.0, category="meeting"),
                AppUsageRecord(app_name="备忘录", bundle_id="com.apple.Notes",
                               duration_minutes=10.0, category="office"),
                AppUsageRecord(app_name="Safari", bundle_id="com.apple.Safari",
                               duration_minutes=5.0, category="browser"),
            ],
            app_switch_count_last_hour=4,
            screen_time_today_minutes=200,
        ),
        "work_pattern": "meeting",
    },

    "writing_doc": {
        "label": "写文档",
        "snapshot": DesktopSnapshot(
            frontmost_app="Notion",
            frontmost_category="office",
            window_title_hint="在 Notion 中编辑文档",
            activity_summary="用户在文档编辑器中撰写项目方案",
            hourly_usage=[
                AppUsageRecord(app_name="Notion", bundle_id="com.notion.Notion",
                               duration_minutes=35.0, category="office"),
                AppUsageRecord(app_name="Safari", bundle_id="com.apple.Safari",
                               duration_minutes=15.0, category="browser"),
                AppUsageRecord(app_name="微信", bundle_id="com.tencent.xinWeChat",
                               duration_minutes=5.0, category="communication"),
            ],
            app_switch_count_last_hour=10,
            screen_time_today_minutes=150,
        ),
        "work_pattern": "general",
    },

    "late_night_grind": {
        "label": "深夜赶工",
        "snapshot": DesktopSnapshot(
            frontmost_app="VSCode",
            frontmost_category="coding",
            window_title_hint="在 VSCode 中编辑 Python 文件",
            activity_summary="用户深夜仍在代码编辑器中工作",
            hourly_usage=[
                AppUsageRecord(app_name="VSCode", bundle_id="com.microsoft.VSCode",
                               duration_minutes=50.0, category="coding"),
                AppUsageRecord(app_name="iTerm2", bundle_id="com.googlecode.iterm2",
                               duration_minutes=8.0, category="terminal"),
                AppUsageRecord(app_name="Spotify", bundle_id="com.spotify.client",
                               duration_minutes=55.0, category="media"),
            ],
            app_switch_count_last_hour=5,
            screen_time_today_minutes=420,
        ),
        "work_pattern": "deep_focus",
    },

    "design_review": {
        "label": "设计评审",
        "snapshot": DesktopSnapshot(
            frontmost_app="Figma",
            frontmost_category="design",
            window_title_hint="在 Figma 中查看设计稿",
            activity_summary="用户在设计工具中查看和标注 UI 设计稿",
            hourly_usage=[
                AppUsageRecord(app_name="Figma", bundle_id="com.figma.Desktop",
                               duration_minutes=30.0, category="design"),
                AppUsageRecord(app_name="Slack", bundle_id="com.tinyspeck.slackmacgap",
                               duration_minutes=12.0, category="communication"),
                AppUsageRecord(app_name="Safari", bundle_id="com.apple.Safari",
                               duration_minutes=8.0, category="browser"),
            ],
            app_switch_count_last_hour=14,
            screen_time_today_minutes=190,
        ),
        "work_pattern": "general",
    },

    "idle": {
        "label": "离开电脑",
        "snapshot": DesktopSnapshot(
            frontmost_app="Finder",
            frontmost_category="other",
            window_title_hint="",
            activity_summary="",
            hourly_usage=[],
            app_switch_count_last_hour=0,
            screen_time_today_minutes=90,
        ),
        "work_pattern": "general",
    },
}

ALL_SCENARIO_NAMES = list(SCENARIOS.keys())


class DesktopSimulator:
    """Inject simulated desktop context for development and demo."""

    def get_scenario_names(self) -> list[str]:
        return list(ALL_SCENARIO_NAMES)

    def get_scenarios_info(self) -> list[dict]:
        return [
            {"name": name, "label": s["label"], "work_pattern": s["work_pattern"]}
            for name, s in SCENARIOS.items()
        ]

    def apply_scenario(self, scenario_name: str) -> dict:
        """Write a pre-baked scenario into desktop_context.json."""
        scene = SCENARIOS.get(scenario_name)
        if not scene:
            return {"ok": False, "error": f"unknown scenario: {scenario_name}",
                    "available": ALL_SCENARIO_NAMES}

        snapshot: DesktopSnapshot = scene["snapshot"].model_copy()
        snapshot.timestamp = datetime.now()

        ctx = DesktopContext(
            updated_at=datetime.now(),
            current_snapshot=snapshot,
            daily_top_apps=sorted(
                snapshot.hourly_usage, key=lambda r: r.duration_minutes, reverse=True
            ),
            avg_daily_screen_time_minutes=snapshot.screen_time_today_minutes,
            work_pattern=scene["work_pattern"],
        )
        file_store.save("desktop_context.json", ctx)

        return {
            "ok": True,
            "scenario": scenario_name,
            "label": scene["label"],
            "frontmost_app": snapshot.frontmost_app,
            "work_pattern": scene["work_pattern"],
        }

    def apply_random(self) -> dict:
        """Pick a random scenario (excluding idle) and apply it."""
        candidates = [n for n in ALL_SCENARIO_NAMES if n != "idle"]
        return self.apply_scenario(random.choice(candidates))

    def clear(self) -> dict:
        """Remove desktop_context.json entirely."""
        file_store.delete("desktop_context.json")
        return {"ok": True, "action": "cleared"}

    def cycle(self, steps: list[str] | None = None) -> list[dict]:
        """Apply multiple scenarios in sequence, returning results for each."""
        names = steps or ALL_SCENARIO_NAMES
        results = []
        for name in names:
            results.append(self.apply_scenario(name))
        return results


desktop_simulator = DesktopSimulator()
