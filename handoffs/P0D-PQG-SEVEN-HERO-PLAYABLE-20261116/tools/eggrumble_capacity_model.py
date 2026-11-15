"""EGGRUMBLE engineering *planning* model; coefficients are assumptions, not Roblox measurements.

Usage: python -m unittest discover -s ../tests -p "test_v3_*.py"
       python tools/eggrumble_capacity_model.py
"""
from dataclasses import dataclass
from math import floor

# Budget is a game-specific planning cap; Roblox does NOT promise these coefficients.
MODEL_SCRIPT_BUDGET_MS = 10.0
BASELINE_MS = 2.0
HUMAN_SCRIPT_MS = 0.16
BOT_AI_SCRIPT_MS = 0.28
CASTLE_SCRIPT_MS = 0.035
LIGHTWEIGHT_NEUTRAL_SCRIPT_MS = 0.012
ROBLOX_DOCUMENTED_SERVER_MAX_USERS = 200  # platform configuration ceiling, NOT this game's target
MATCH_SECONDS = 900

@dataclass(frozen=True)
class Estimate:
    human: int
    bots: int
    active_neutrals: int
    script_ms: float
    headroom_ms: float
    within_assumed_budget: bool

def model(human: int, bots: int, neutrals: int) -> Estimate:
    assert 0 <= human <= ROBLOX_DOCUMENTED_SERVER_MAX_USERS
    assert 0 <= bots <= 32
    assert 0 <= neutrals <= 10000
    heroes = human + bots
    assert 2 <= heroes <= ROBLOX_DOCUMENTED_SERVER_MAX_USERS
    total = (BASELINE_MS + human*HUMAN_SCRIPT_MS + bots*BOT_AI_SCRIPT_MS +
             heroes*CASTLE_SCRIPT_MS + neutrals*LIGHTWEIGHT_NEUTRAL_SCRIPT_MS)
    return Estimate(human, bots, neutrals, round(total, 3),
                    round(MODEL_SCRIPT_BUDGET_MS-total, 3), total <= MODEL_SCRIPT_BUDGET_MS)

def kills_per_second(kills: int, seconds: int = MATCH_SECONDS) -> float:
    assert kills >= 0 and seconds > 0
    return kills / seconds

def max_mean_neutral_lifetime(live_neutrals: int, kills: int, seconds: int = MATCH_SECONDS) -> float:
    """Upper bound of mean lifespan assuming perfect replenishment at all times."""
    assert live_neutrals > 0
    if kills == 0: return float("inf")
    return live_neutrals / kills_per_second(kills, seconds)

def scenarios():
    return [
        ("first release 12H + 4AI", model(12,4,240)),
        ("first release 16H", model(16,0,240)),
        ("stretch 20H + 4AI", model(20,4,220)),
        ("stretch 24H", model(24,0,240)),
        ("heavy 28H + 4AI", model(28,4,160)),
        ("heavy 32H", model(32,0,160)),
    ]

if __name__ == "__main__":
    print("ASSUMED game-script per-tick budget:", MODEL_SCRIPT_BUDGET_MS, "ms, not measured")
    for label,s in scenarios():
        print(f"{label:24} humans={s.human:2} bots={s.bots:2} neutrals={s.active_neutrals:3}"
              f" script={s.script_ms:5.2f}ms reserve={s.headroom_ms:+5.2f}ms"
              f" model_pass={s.within_assumed_budget}")
    print("10k individual KOs/15min:", round(kills_per_second(10000),3), "kills/s")
    print("30k total KOs/15min:", round(kills_per_second(30000),3), "kills/s")
    print("240-active for 30k:",round(max_mean_neutral_lifetime(240,30000),2),
          "seconds mean lifetime; zero spare capacity")
