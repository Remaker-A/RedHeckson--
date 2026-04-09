"""Pydantic data models for all persistent and runtime data structures."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ---------- Enums ----------

class CompanionState(str, Enum):
    IDLE = "idle"
    PASSERBY = "passerby"
    COMPANION = "companion"
    FOCUS = "focus"
    DEEP_NIGHT = "deep_night"
    LEAVING = "leaving"


class BiasType(str, Enum):
    DECISIVE = "decisive"
    ADVENTUROUS = "adventurous"
    SLOW_DOWN = "slow_down"
    WARM_HUMOR = "warm_humor"
    NIGHT_OWL = "night_owl"
    BOOKISH = "bookish"
    CUSTOM = "custom"


class RoomScene(str, Enum):
    TIDY = "tidy"
    MESSY = "messy"
    NIGHT = "night"
    DUSTY = "dusty"
    RECOVERING = "recovering"


# ---------- L0 Soul ----------

class SoulEvolutionEntry(BaseModel):
    """对话 digest 合并 user_snapshot 时的单字段变更记录。"""

    timestamp: datetime = Field(default_factory=datetime.now)
    field: str = ""  # "current_state_word" | "struggle" | "user_facts"
    old_value: str = ""
    new_value: str = ""


class Soul(BaseModel):
    created_at: datetime = Field(default_factory=datetime.now)
    current_state_word: str = ""
    struggle: str = ""
    user_facts: str = ""
    bias: BiasType = BiasType.DECISIVE
    opening_response: str = "你来了。"
    evolution_log: list[SoulEvolutionEntry] = Field(default_factory=list)


# ---------- L1 Personality ----------

class PersonalityParams(BaseModel):
    bias: BiasType = BiasType.DECISIVE
    night_owl_index: float = 0.0
    anxiety_sensitivity: float = 0.0
    quietness: float = 0.5
    playfulness: float = 0.3
    attachment_level: float = 0.0


class EvolutionLogEntry(BaseModel):
    day: int = 0
    change: str = ""
    reason: str = ""
    timestamp: datetime = Field(default_factory=datetime.now)
    event_type: str = "personality"  # "personality" | "digest" | "rule"
    params_snapshot: Optional[dict] = None
    summary_zh: str = ""
    context_hint: str = ""


class Personality(BaseModel):
    version: int = 1
    updated_at: datetime = Field(default_factory=datetime.now)
    params: PersonalityParams = Field(default_factory=PersonalityParams)
    natural_description: str = "它刚刚来到这里，还在认识你。"
    voice_style: str = ""
    evolution_log: list[EvolutionLogEntry] = Field(default_factory=list)


# ---------- L2 Rhythm ----------

class DayRecord(BaseModel):
    date: str = ""
    first_arrive: str = ""
    last_leave: str = ""
    total_minutes: int = 0
    late_night: bool = False
    focus_sessions: int = 0
    state_switches: int = 0


class RhythmPatterns(BaseModel):
    avg_arrive: str = "09:00"
    avg_leave: str = "22:00"
    late_night_ratio: float = 0.0
    regularity_score: float = 0.5


class Rhythm(BaseModel):
    updated_at: str = ""
    days_together: int = 0
    recent_7_days: list[DayRecord] = Field(default_factory=list)
    patterns: RhythmPatterns = Field(default_factory=RhythmPatterns)


# ---------- L3 Realtime (in-memory) ----------

class RealtimeContext(BaseModel):
    current_state: CompanionState = CompanionState.IDLE
    state_since: datetime = Field(default_factory=datetime.now)
    seated_minutes: int = 0
    distance_cm: float = 999.0
    time_period: str = "morning"
    today_total_minutes: int = 0
    is_night: bool = False


# ---------- L4 Desktop Context ----------

class AppUsageRecord(BaseModel):
    app_name: str = ""
    bundle_id: str = ""
    duration_minutes: float = 0.0
    category: str = "other"


class DesktopSnapshot(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    frontmost_app: str = ""
    frontmost_category: str = ""
    window_title_hint: str = ""
    activity_summary: str = ""
    hourly_usage: list[AppUsageRecord] = Field(default_factory=list)
    app_switch_count_last_hour: int = 0
    screen_time_today_minutes: int = 0


class DesktopContext(BaseModel):
    updated_at: datetime = Field(default_factory=datetime.now)
    current_snapshot: DesktopSnapshot = Field(default_factory=DesktopSnapshot)
    daily_top_apps: list[AppUsageRecord] = Field(default_factory=list)
    avg_daily_screen_time_minutes: int = 0
    work_pattern: str = ""


# ---------- Events ----------

class StateEvent(BaseModel):
    type: str = "state_change"
    from_state: CompanionState = CompanionState.IDLE
    to_state: CompanionState = CompanionState.IDLE
    distance_cm: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.now)


# ---------- Notes ----------

class Note(BaseModel):
    id: str = ""
    content: str = ""
    created_at: datetime = Field(default_factory=datetime.now)
    personality_version: int = 1


# ---------- Messages ----------

class UserMessage(BaseModel):
    content: str = ""
    mood: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)


# ---------- Focus ----------

class FocusSession(BaseModel):
    active: bool = False
    started_at: Optional[datetime] = None
    duration_minutes: int = 25
    elapsed_minutes: int = 0


# ---------- Room ----------

class RoomState(BaseModel):
    scene: RoomScene = RoomScene.TIDY
    details: dict = Field(default_factory=dict)


# ---------- API request/response ----------

class SoulCreateRequest(BaseModel):
    current_state_word: str
    struggle: str
    bias: BiasType
    custom_voice_style: Optional[str] = None


class SimDistanceRequest(BaseModel):
    distance_cm: float


class SimTimeRequest(BaseModel):
    hour: int
    minute: int = 0


class SimFastForwardRequest(BaseModel):
    days: int = 7
    late_night_ratio: float = 0.3
    focus_ratio: float = 0.4


class FocusStartRequest(BaseModel):
    duration_minutes: int = 25


class MessageRequest(BaseModel):
    content: str = ""
    mood: Optional[str] = None


class MoodRequest(BaseModel):
    mood: str


class PersonalityUpdateRequest(BaseModel):
    bias: Optional[BiasType] = None
    voice_style: Optional[str] = None


class ChatTurn(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatHistoryEntry(BaseModel):
    role: str  # "user" | "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)


class ChatDigestState(BaseModel):
    """How many lines of chat_history.jsonl have been fed to relationship digest."""

    processed_lines: int = 0


class ChatRequest(BaseModel):
    message: str
    history: list[ChatTurn] = Field(default_factory=list)


class SimInjectChatRequest(BaseModel):
    scenarios: list[str] = Field(default_factory=lambda: ["all"])
    reset_digest: bool = True
    clear_history: bool = False


class SimDigestTestRequest(BaseModel):
    scenarios: list[str] = Field(default_factory=lambda: ["all"])
    clear_history: bool = True


class DesktopHeartbeatRequest(BaseModel):
    frontmost_app: str
    frontmost_category: str = "other"
    bundle_id: str = ""


class DesktopSnapshotRequest(BaseModel):
    frontmost_app: str = ""
    frontmost_category: str = ""
    window_title_hint: str = ""
    activity_summary: str = ""
    hourly_usage: list[AppUsageRecord] = Field(default_factory=list)
    app_switch_count_last_hour: int = 0
    screen_time_today_minutes: int = 0


class SimDesktopScenarioRequest(BaseModel):
    scenario: str = "deep_focus_coding"


class WSMessage(BaseModel):
    type: str
    data: dict = Field(default_factory=dict)
