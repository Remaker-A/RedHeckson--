"""Tiered context manager: assembles L0-L3 context for LLM calls."""

from __future__ import annotations

from typing import Optional

from core.state_machine import state_machine
from storage.file_store import file_store
from storage.models import Personality, Rhythm, Soul


class ContextManager:
    def get_l0(self) -> Optional[dict]:
        soul = file_store.load("soul.json", Soul)
        if not soul:
            return None
        return soul.model_dump(mode="json")

    def get_l1(self) -> Optional[dict]:
        p = file_store.load("personality.json", Personality)
        if not p:
            return None
        return p.model_dump(mode="json")

    def get_l2(self) -> Optional[dict]:
        r = file_store.load("rhythm.json", Rhythm)
        if not r:
            return None
        return r.model_dump(mode="json")

    def get_l3(self) -> dict:
        return state_machine.get_status()

    def assemble(self, levels: list[int]) -> dict:
        ctx: dict = {}
        getters = {0: self.get_l0, 1: self.get_l1, 2: self.get_l2, 3: self.get_l3}
        for lv in levels:
            getter = getters.get(lv)
            if getter:
                data = getter()
                if data:
                    ctx[f"L{lv}"] = data
        return ctx

    def for_say_one_line(self) -> dict:
        return self.assemble([0, 1, 3])

    def for_chat(self) -> dict:
        return self.assemble([0, 1, 2, 3])

    def for_note(self) -> dict:
        return self.assemble([0, 1, 2])

    def for_personality_update(self) -> dict:
        return self.assemble([0, 1, 2])

    def for_room(self) -> dict:
        return self.assemble([1, 2])


context_manager = ContextManager()
