#!/usr/bin/env python3
"""Generate a real native Luau runtime test from the published EXACT source."""
from pathlib import Path
import argparse
import hashlib

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src/FocusTrainingScheduler.luau"
SOURCE_BLOB = "a00caf954aacfca03c92a75b0165c1bafd4de8fd"


def git_blob(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def build() -> str:
    source_bytes = SRC.read_bytes()
    assert git_blob(source_bytes) == SOURCE_BLOB, "unexpected source revision"
    source = source_bytes.decode("utf-8").rstrip()
    assert source.endswith("return Scheduler"), "source must end with return Scheduler"
    return source[: -len("return Scheduler")] + r"""
local assertions = 0
local function check(condition, label)
    assertions += 1
    if not condition then error("assert #" .. tostring(assertions) .. " " .. label) end
end
local function sumByMode(chunks, mode)
    local total = 0
    for _, chunk in ipairs(chunks) do
        if chunk.mode == mode then total += chunk.seconds end
    end
    return total
end
local T = 1700000000
local base = Scheduler.newState(42, T, {})
check(base.userId == 42, "id")
check(base.focusedSeconds == 0, "initial focus")
check(Scheduler.getStatus(base, false).mode == "RANDOM", "initial mode")
for index, skill in ipairs(Scheduler.DISCIPLINES) do
    local state = Scheduler.selectSkill(base, skill)
    check(Scheduler.getStatus(state, false).skill == skill, "selected " .. tostring(index))
end
local state = Scheduler.selectSkill(base, "BEAST")
local updated, chunks = Scheduler.settle(state, T + 60, true, 2, false)
check(#chunks == 1 and chunks[1].skill == "BEAST", "focus segment")
check(chunks[1].bonusBps == 15000, "friend bonus 2")
check(updated.focusedSeconds == 60, "focus seconds")
check(#Scheduler.settle(updated, T + 60, true, 2, false) == 2, "placeholder") -- overwritten below
""" .replace('check(#Scheduler.settle(updated, T + 60, true, 2, false) == 2, "placeholder") -- overwritten below',r"""
local unchanged, noChunks = Scheduler.settle(updated, T + 60, true, 2, false)
check(#noChunks == 0 and unchanged.focusedSeconds == 60, "same tick does not duplicate")
local clockRollback, noRollbackReward = Scheduler.settle(updated, T - 1, true, 2, false)
check(#noRollbackReward == 0 and clockRollback.focusedSeconds == 60, "clock rollback")
local s = Scheduler.selectSkill(base, "WEAPON")
local focusTotal = 0
local randomTotal = 0
local t = T
for n = 1, 31 do
    local segments
    s, segments = Scheduler.settle(s, t + 60, true, 0, false)
    focusTotal += sumByMode(segments, "FOCUS")
    randomTotal += sumByMode(segments, "RANDOM")
    t += 60
end
check(focusTotal == 1800, "30m cap")
check(randomTotal == 60, "automatic random continues")
check(s.focusedSeconds == 1800, "free budget capped")
check(Scheduler.getStatus(s, false).mode == "RANDOM", "random after cap")
local selectedAtCap = Scheduler.selectSkill(s, "MAGIC")
check(Scheduler.getStatus(selectedAtCap, false).mode == "RANDOM", "changing focus cannot bypass cap")
local noTraining, noPassive = Scheduler.settle(s, t + 60, false, 0, false)
check(#noPassive == 0 and noTraining.focusedSeconds == 1800, "paused no XP")
local longGapState, longGapChunks = Scheduler.settle(s, t + 600, true, 0, false)
check(sumByMode(longGapChunks, "RANDOM") == 120, "catchup caps at 120s")
check(longGapState.lastTick == t + 600, "lastTick catches up")
local friend0, friend0Seg = Scheduler.settle(Scheduler.selectSkill(base, "MAGIC"), T + 60, true, 0, false)
local friend5, friend5Seg = Scheduler.settle(Scheduler.selectSkill(base, "MAGIC"), T + 60, true, 5, false)
check(friend0Seg[1].bonusBps == 10000, "no friend normal XP")
check(friend5Seg[1].bonusBps == 20000, "friend cap x2")
local premium, premiumChunks = Scheduler.settle(Scheduler.selectSkill(base, "BEAST"), T + 60, true, 4, true)
check(premiumChunks[1].mode == "FOCUS" and premium.focusedSeconds == 0, "premium model only, no free quota consumption")
check(premiumChunks[1].bonusBps == 20000, "premium does not stack extra bonus")
local bagState = Scheduler.newState(42, T, {})
local collected = {}
local tt = T
for n = 1, 6 do
    local nextState, sample = Scheduler.settle(bagState, tt + 60, true, 0, false)
    local skill = sample[1].skill
    collected[skill] = true
    bagState = nextState
    tt += 60
    -- fill the remaining 9 minutes
    for m = 1, 9 do
        bagState = Scheduler.settle(bagState, tt + 60, true, 0, false)
        tt += 60
    end
end
local numUnique = 0
for _ in pairs(collected) do numUnique += 1 end
check(numUnique == 6, "shuffled bag covers six")
check(bagState.randomCycle == 1 and bagState.randomPosition == 1, "random cycle increments")
local beforeMidnight = (math.floor((T + 9 * 3600) / 86400) + 1) * 86400 - 9 * 3600
local midnightState = Scheduler.newState(42, beforeMidnight - 30, {})
midnightState = Scheduler.selectSkill(midnightState, "BEAST")
midnightState.focusedSeconds = 1785
local nextDay, spans = Scheduler.settle(midnightState, beforeMidnight + 30, true, 0, false)
check(sumByMode(spans, "FOCUS") == 45 and sumByMode(spans, "RANDOM") == 15, "midnight split")
check(nextDay.focusedSeconds == 30, "daily free focus reset")
local snap = Scheduler.snapshot(nextDay)
check(snap.version == 1 and snap.focusedSeconds == 30, "snapshot")
local rejoined = Scheduler.newState(42, beforeMidnight + 5 * 3600, snap)
check(rejoined.lastTick == beforeMidnight + 5 * 3600, "rejoin no offline earnings")
local rejoined2, reward = Scheduler.settle(rejoined, rejoined.lastTick, true, 0, false)
check(#reward == 0, "rejoin zero elapsed")
check(rejoined2.focusedSeconds == 30, "rejoin preserved quota")
local cleared = Scheduler.clearSelection(Scheduler.selectSkill(base, "ZOMBIE"))
check(Scheduler.getStatus(cleared, false).mode == "RANDOM", "clear skill")
print("P0D_V4_FOCUS_NATIVE_" .. tostring(assertions) .. "_ASSERTIONS_PASS")
""")
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", required=True)
    args = parser.parse_args()
    Path(args.write).write_text(build(), encoding="utf-8")
    print("NATIVE_TEST_GENERATED_SOURCE_BLOB", SOURCE_BLOB)
