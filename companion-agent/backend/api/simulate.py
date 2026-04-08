"""Hardware & chat simulation control API for development and demo."""

from __future__ import annotations

import logging

from fastapi import APIRouter

from mock.hardware_sim import hardware_sim
from storage.models import (
    SimDigestTestRequest,
    SimDistanceRequest,
    SimFastForwardRequest,
    SimInjectChatRequest,
    SimTimeRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sim", tags=["simulate"])


@router.post("/person-arrive")
async def sim_person_arrive():
    return await hardware_sim.person_arrive()


@router.post("/person-sit")
async def sim_person_sit():
    return await hardware_sim.person_sit()


@router.post("/person-leave")
async def sim_person_leave():
    return await hardware_sim.person_leave()


@router.post("/set-distance")
async def sim_set_distance(req: SimDistanceRequest):
    return hardware_sim.set_distance(req.distance_cm)


@router.post("/set-time")
async def sim_set_time(req: SimTimeRequest):
    return hardware_sim.set_time(req.hour, req.minute)


@router.post("/fast-forward")
async def sim_fast_forward(req: SimFastForwardRequest):
    return await hardware_sim.fast_forward(req.days, req.late_night_ratio, req.focus_ratio)


# ── Chat simulation endpoints ──


@router.get("/chat-scenarios")
async def list_chat_scenarios():
    """List available simulated chat scenarios."""
    from mock.chat_sim import chat_simulator
    return {"scenarios": chat_simulator.get_scenario_names()}


@router.post("/inject-chat")
async def sim_inject_chat(req: SimInjectChatRequest):
    """Inject simulated chat history for digest testing."""
    from mock.chat_sim import chat_simulator
    result = chat_simulator.inject(
        scenarios=req.scenarios,
        reset_digest=req.reset_digest,
        clear_history=req.clear_history,
    )
    return result


@router.post("/run-digest-test")
async def sim_run_digest_test(req: SimDigestTestRequest):
    """Inject chat data then run digest in a loop until all data is consumed.

    Returns before/after personality comparison and per-round digest results.
    """
    from mock.chat_sim import chat_simulator
    from core.context_digest import relationship_digester
    from storage.file_store import file_store
    from storage.models import Personality

    personality_before = None
    p = file_store.load("personality.json", Personality)
    if p:
        personality_before = p.params.model_dump(mode="json")

    inject_result = chat_simulator.inject(
        scenarios=req.scenarios,
        reset_digest=True,
        clear_history=req.clear_history,
    )
    if not inject_result.get("ok"):
        return {"ok": False, "error": "inject failed", "detail": inject_result}

    rounds: list[dict] = []
    max_rounds = 10
    consecutive_failures = 0
    for i in range(max_rounds):
        out = await relationship_digester.run_digest(manual=True)
        rounds.append(out)
        if out.get("skipped"):
            break
        if not out.get("ok"):
            consecutive_failures += 1
            if consecutive_failures >= 3:
                logger.warning("run-digest-test: 3 consecutive failures, stopping")
                break
        else:
            consecutive_failures = 0

    personality_after = None
    evolution_log = []
    p = file_store.load("personality.json", Personality)
    if p:
        personality_after = p.params.model_dump(mode="json")
        evolution_log = [e.model_dump(mode="json") for e in p.evolution_log]

    return {
        "ok": True,
        "inject": inject_result,
        "digest_rounds": len([r for r in rounds if not r.get("skipped")]),
        "rounds": rounds,
        "personality_before": personality_before,
        "personality_after": personality_after,
        "evolution_log": evolution_log,
    }
