"""Hardware simulation layer - replaces real sensors with API-triggered events."""

from __future__ import annotations

import logging
from datetime import datetime

from core.state_machine import state_machine

logger = logging.getLogger(__name__)


class HardwareSimulator:
    """Provides methods to simulate hardware events for development and demo."""

    async def person_arrive(self, distance_cm: float = 150.0):
        await state_machine.person_arrive(distance_cm)
        return state_machine.get_status()

    async def person_sit(self, distance_cm: float = 50.0):
        await state_machine.person_sit(distance_cm)
        return state_machine.get_status()

    async def person_leave(self):
        await state_machine.person_leave()
        return state_machine.get_status()

    def set_distance(self, distance_cm: float):
        state_machine.ctx.distance_cm = distance_cm
        return state_machine.get_status()

    def set_time(self, hour: int, minute: int = 0):
        state_machine.set_simulated_time(hour, minute)
        return {
            "simulated_time": f"{hour:02d}:{minute:02d}",
            "is_night": state_machine.is_night(),
            "time_period": state_machine.time_period(),
        }

    async def fast_forward(self, days: int = 7, late_night_ratio: float = 0.3, focus_ratio: float = 0.4) -> dict:
        """Generate mock historical data for demo personality evolution."""
        from storage.file_store import file_store
        from storage.models import DayRecord, Rhythm, RhythmPatterns

        records = []
        for i in range(days):
            is_late = (i / days) < late_night_ratio or i % 3 == 0
            records.append(DayRecord(
                date=f"2026-04-{max(1, 8 - days + i):02d}",
                first_arrive=f"0{9 + i % 2}:{15 + i * 5 % 60:02d}",
                last_leave=f"{22 + (1 if is_late else 0)}:{30 + i * 7 % 30:02d}",
                total_minutes=360 + i * 20,
                late_night=is_late,
                focus_sessions=int(focus_ratio * 5) + i % 2,
                state_switches=8 + i * 2,
            ))

        late_days = sum(1 for r in records if r.late_night)
        rhythm = Rhythm(
            updated_at=datetime.now().strftime("%Y-%m-%d"),
            days_together=days,
            recent_7_days=records[-7:],
            patterns=RhythmPatterns(
                avg_arrive="09:30",
                avg_leave="23:00" if late_night_ratio > 0.3 else "22:00",
                late_night_ratio=late_days / max(len(records), 1),
                regularity_score=0.4 + 0.05 * days,
            ),
        )
        file_store.save("rhythm.json", rhythm)

        # Trigger personality evolution with the new rhythm data
        try:
            from core.personality import personality_engine
            await personality_engine.maybe_evolve()
        except Exception as e:
            logger.warning(f"fast_forward evolution error: {e}")

        personality = None
        try:
            from storage.models import Personality
            personality = file_store.load("personality.json", Personality)
        except Exception:
            pass

        return {
            "days_generated": days,
            "records": len(records),
            "late_night_ratio": rhythm.patterns.late_night_ratio,
            "regularity_score": rhythm.patterns.regularity_score,
            "personality": personality.model_dump(mode="json") if personality else None,
        }


hardware_sim = HardwareSimulator()
