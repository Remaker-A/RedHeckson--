"""Scheduler for periodic tasks: personality evolution triggers, daily rhythm updates."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from config import settings

logger = logging.getLogger(__name__)


class Scheduler:
    def __init__(self):
        self._event_count_since_update = 0
        self._last_evo_time: datetime = datetime.now()
        self._chat_msg_count_since_digest = 0
        self._last_digest_time: datetime = datetime.now()
        self._running = False
        self._task = None

    def record_event(self):
        self._event_count_since_update += 1

    def should_evolve(self) -> bool:
        if self._event_count_since_update >= settings.evo_event_threshold:
            return True
        hours_since = (datetime.now() - self._last_evo_time).total_seconds() / 3600
        if hours_since >= settings.evo_time_threshold_hours:
            return True
        return False

    def mark_evolved(self):
        self._event_count_since_update = 0
        self._last_evo_time = datetime.now()

    def record_chat_message(self):
        self._chat_msg_count_since_digest += 1

    def should_digest(self) -> bool:
        if self._chat_msg_count_since_digest >= settings.digest_msg_threshold:
            return True
        hours = (datetime.now() - self._last_digest_time).total_seconds() / 3600
        return hours >= settings.digest_time_threshold_hours and self._chat_msg_count_since_digest > 0

    def mark_digested(self):
        self._chat_msg_count_since_digest = 0
        self._last_digest_time = datetime.now()

    async def start(self):
        self._running = True
        self._task = asyncio.create_task(self._loop())

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()

    async def _loop(self):
        while self._running:
            await asyncio.sleep(60)
            if self.should_digest():
                try:
                    from core.context_digest import relationship_digester

                    out = await relationship_digester.run_digest()
                    if out.get("notify_scheduler"):
                        self.mark_digested()
                except Exception as e:
                    logger.warning(f"Digest error: {e}")
            if self.should_evolve():
                try:
                    from core.personality import personality_engine
                    await personality_engine.maybe_evolve()
                    self.mark_evolved()
                except Exception as e:
                    logger.warning(f"Evolution error: {e}")


scheduler = Scheduler()
