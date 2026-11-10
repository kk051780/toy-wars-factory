"""Exact offline semantic reference for the v39 Luau session-only module.

This does NOT establish authenticity of a match; caller MUST use server-owned data.
"""
from dataclasses import dataclass, field
from math import isfinite
from typing import Any

JOBS = frozenset({"WARRIOR", "NINJA", "TRAPPER", "ZOMBIE_MASTER", "BEAST_TAMER", "MAGE", "BUILDER"})
STAGES = frozenset({"S1", "S2", "S3", "S4"})
MAX_ROUNDS = 512


def _int(v: Any, lo: int, hi: int) -> bool:
    return type(v) is int and lo <= v <= hi


def _num(v: Any) -> bool:
    return type(v) in (int, float) and isfinite(v)


def _match_id(v: Any) -> bool:
    return type(v) is str and 4 <= len(v) <= 128 and v == v.strip()


@dataclass(frozen=True)
class State:
    owner: int
    stamps: int = 0
    finalized: dict[str, int] = field(default_factory=dict)
    session_only: bool = True


def new_state(owner: int) -> State:
    if not _int(owner, 1, 9007199254740991):
        raise ValueError("INVALID_OWNER")
    return State(owner)


def valid_evidence(ev: Any, owner: int) -> bool:
    if type(ev) is not dict or ev.get("kind") != "SERVER_FINALIZED_ROUND":
        return False
    if not _match_id(ev.get("matchId")) or ev.get("userId") != owner or type(ev.get("userId")) is not int:
        return False
    if type(ev.get("stageId")) is not str or type(ev.get("jobId")) is not str:
        return False
    if ev.get("stageId") not in STAGES or ev.get("jobId") not in JOBS:
        return False
    if ev.get("completed") is not True or type(ev.get("won")) is not bool or type(ev.get("contributed")) is not bool:
        return False
    if not _num(ev.get("roundSeconds")) or not _num(ev.get("activeSeconds")):
        return False
    if not 1 <= ev["roundSeconds"] <= 7200 or not 0 <= ev["activeSeconds"] <= ev["roundSeconds"]:
        return False
    return _int(ev.get("meaningfulServerActions"), 0, 2048)


def _receipt(status: str, awarded: int = 0, unlocks: tuple[str, ...] = ()) -> dict:
    return {"status": status, "awarded": awarded, "unlocks": unlocks}


def apply(state: State, ev: Any) -> tuple[State, dict]:
    if not (isinstance(state, State) and _int(state.owner, 1, 9007199254740991)
            and _int(state.stamps, 0, 1024) and state.session_only is True
            and len(state.finalized) <= MAX_ROUNDS
            and all(_match_id(k) and _int(v, 0, 2) for k, v in state.finalized.items())
            and sum(state.finalized.values()) == state.stamps):
        return state, _receipt("INVALID_STATE")
    if not valid_evidence(ev, state.owner):
        return state, _receipt("INVALID_EVIDENCE")
    if ev["matchId"] in state.finalized:
        return state, _receipt("DUPLICATE_FINALIZATION")
    if len(state.finalized) >= MAX_ROUNDS:
        return state, _receipt("LEDGER_FULL")
    needed = min(15, max(1, ev["roundSeconds"] * .3))
    eligible = ev["activeSeconds"] >= needed and ev["meaningfulServerActions"] > 0
    awarded = 1 + int(ev["won"] or ev["contributed"]) if eligible else 0
    if state.stamps + awarded > 1024:
        return state, _receipt("STAMP_CAP_REACHED")
    ledger = dict(state.finalized)
    ledger[ev["matchId"]] = awarded
    result = State(state.owner, state.stamps + awarded, ledger)
    unlocked = []
    if state.stamps < 3 <= result.stamps:
        unlocked.append("FREE_EGG_BANNER")
    if state.stamps < 6 <= result.stamps:
        unlocked.append("FREE_TRAP_TRAIL")
    return result, _receipt("AWARDED_SESSION_ONLY" if eligible else "INELIGIBLE_FINALIZED", awarded, tuple(unlocked))


def view(state: State) -> dict:
    next_at = 3 if state.stamps < 3 else 6 if state.stamps < 6 else None
    unlocked = []
    if state.stamps >= 3:
        unlocked.append("FREE_EGG_BANNER")
    if state.stamps >= 6:
        unlocked.append("FREE_TRAP_TRAIL")
    return {"stamps": state.stamps, "nextRewardAt": next_at,
            "toNextReward": next_at - state.stamps if next_at else 0,
            "unlockedCosmetics": unlocked, "sessionOnly": True, "saved": False}


def sample(match: str = "match-001", **overrides: Any) -> dict:
    ev = dict(kind="SERVER_FINALIZED_ROUND", matchId=match, userId=123456, stageId="S1",
              jobId="TRAPPER", completed=True, won=False, contributed=False,
              roundSeconds=60, activeSeconds=30, meaningfulServerActions=2)
    ev.update(overrides)
    return ev
