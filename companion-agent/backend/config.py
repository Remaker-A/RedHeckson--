from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv(Path(__file__).parent / ".env")


class Settings(BaseSettings):
    app_name: str = "Companion Agent"
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True

    # Paths
    data_dir: Path = Path(__file__).parent / "data"
    corpus_dir: Path = Path(__file__).parent / "data" / "corpus"

    # LLM
    llm_provider: str = "siliconflow"
    llm_providers: dict = {
        "siliconflow": {
            "base_url": os.getenv(
                "SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1"
            ).rstrip("/"),
            "api_key": os.getenv("SILICONFLOW_API_KEY", ""),
            "model": os.getenv(
                "SILICONFLOW_MODEL", "Pro/MiniMaxAI/MiniMax-M2.5"
            ),
        },
        "deepseek": {
            "base_url": "https://api.deepseek.com/v1",
            "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
            "model": "deepseek-chat",
        },
        "openai": {
            "base_url": "https://api.openai.com/v1",
            "api_key": os.getenv("OPENAI_API_KEY", ""),
            "model": "gpt-4o-mini",
        },
    }

    # State machine
    passerby_cooldown_sec: float = 5.0
    companion_distance_cm: float = 80.0
    companion_hold_sec: float = 3.0
    leaving_buffer_sec: float = 10.0
    night_start_hour: int = 22
    night_end_hour: int = 6
    auto_focus_minutes: int = 90

    # Personality evolution triggers
    evo_event_threshold: int = 20
    evo_time_threshold_hours: float = 6.0

    # Conversation digest (relationship / personality from chat)
    digest_msg_threshold: int = 20
    digest_time_threshold_hours: float = 12.0

    model_config = {"env_prefix": "COMPANION_"}


settings = Settings()
settings.data_dir.mkdir(parents=True, exist_ok=True)
settings.corpus_dir.mkdir(parents=True, exist_ok=True)
