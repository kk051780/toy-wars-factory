#!/usr/bin/env python3
"""Generate a genuine executable Luau test using the exact tracked source.
The production source is inserted unmodified except the terminal module return.
Standalone luau-cli has no Roblox engine; tests pure Rules.select only.
"""
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src" / "S1First90ClassicWaypointRules.luau"
EXPECTED_END = "return Rules"
HEADER = SOURCE.read_text(encoding="utf8")
assert HEADER.rstrip().endswith(EXPECTED_END), "refuse unexpected module footer"
body = HEADER.rstrip()[:-len(EXPECTED_END)] + "\n"

TESTS = r'''
local selectTarget = Rules.select
local n = 0
local function check(label, actual, expected)
    n += 1
    if actual ~= expected then
        error("FIRST90_NATIVE_CASE_FAIL: " .. label
            .. " expected=" .. tostring(expected) .. " actual=" .. tostring(actual))
    end
end
local function target(label, actual, kind, x, y, z)
    check(label .. ".kind", actual and actual.kind, kind)
    if kind == "EGG" or kind == "HOME" then
        check(label .. ".x", actual.x, x)
        check(label .. ".y", actual.y, y)
        check(label .. ".z", actual.z, z)
    end
end
local function base()
    return {
        phase = "ACTIVE", team = "RED", alive = true, serial = 1,
        elapsedSeconds = 10, carryingEgg = false, ownEggHome = true,
        enemyEggFree = true, enemyPromptEnabled = true,
        enemyEggVisible = true, enemyEgg = {x = 88, y = 3, z = 0},
        ownScorePad = {x = -90, y = 3, z = 0},
    }
end
local s = base()
target("basic RED egg", selectTarget(s), "EGG", 88, 3, 0)
s.team = "BLUE"
target("basic BLUE egg", selectTarget(s), "EGG", 88, 3, 0)
s = base()
s.carryingEgg = true
target("own scorepad", selectTarget(s), "HOME", -90, 3, 0)
s.ownEggHome = false
target("own egg stolen safe RECOVER", selectTarget(s), "RECOVER")
local r = selectTarget(s)
check("RECOVER has no x", r.x, nil)
check("RECOVER has no y", r.y, nil)
check("RECOVER has no z", r.z, nil)
s = base()
s.elapsedSeconds = 0
target("time lower bound", selectTarget(s), "EGG", 88, 3, 0)
s.elapsedSeconds = 89.999
target("time upper interior", selectTarget(s), "EGG", 88, 3, 0)
s.elapsedSeconds = 90
check("time 90 stop", selectTarget(s), nil)
s.elapsedSeconds = 91
check("time 91 stop", selectTarget(s), nil)
s.elapsedSeconds = -1
check("time negative", selectTarget(s), nil)
s.elapsedSeconds = 0/0
check("time NaN", selectTarget(s), nil)
s.elapsedSeconds = math.huge
check("time infinite", selectTarget(s), nil)

for _, phase in ipairs({"LOBBY", "COUNTDOWN", "RESULTS", "INVALID"}) do
    s = base()
    s.phase = phase
    check("phase " .. phase, selectTarget(s), nil)
end
s = base()
s.phase = nil
check("phase nil", selectTarget(s), nil)
s = base()
s.alive = false
check("dead", selectTarget(s), nil)
s.alive = nil
check("alive unknown", selectTarget(s), nil)
s = base()
s.team = "NONE"
check("no team", selectTarget(s), nil)
s.team = ""
check("empty team", selectTarget(s), nil)
s = base()
s.serial = 0
check("zero round", selectTarget(s), nil)
s.serial = -1
check("negative round", selectTarget(s), nil)
s.serial = 1.5
check("fraction round", selectTarget(s), nil)
s.serial = 0/0
check("nan round", selectTarget(s), nil)
s.serial = math.huge
check("infinite round", selectTarget(s), nil)
s = base()
s.enemyEggFree = false
check("egg stolen", selectTarget(s), nil)
s.enemyEggFree = nil
check("egg ownership unknown", selectTarget(s), nil)
s = base()
s.enemyPromptEnabled = false
check("prompt disabled", selectTarget(s), nil)
s.enemyPromptEnabled = nil
check("prompt unknown", selectTarget(s), nil)
s = base()
s.enemyEggVisible = false
check("egg not visible", selectTarget(s), nil)
s.enemyEggVisible = nil
check("egg visibility unknown", selectTarget(s), nil)
s = base()
s.carryingEgg = nil
check("carrier state unknown", selectTarget(s), nil)
s.carryingEgg = "RED"
check("carrier invalid string", selectTarget(s), nil)
s = base()
s.carryingEgg = true
s.ownEggHome = nil
check("score eligibility unknown", selectTarget(s), nil)
s.ownEggHome = true
s.ownScorePad = {x = 1000, y = 3, z = 0}
check("score pad out of bounds", selectTarget(s), nil)
s.ownScorePad = nil
check("score pad unavailable", selectTarget(s), nil)
s = base()
s.enemyEgg = nil
check("enemy egg no point", selectTarget(s), nil)
s.enemyEgg = {}
check("enemy egg no axes", selectTarget(s), nil)
s.enemyEgg = {x = 201, y = 3, z = 0}
check("enemy egg x out", selectTarget(s), nil)
s.enemyEgg = {x = 3, y = -51, z = 0}
check("enemy egg y out", selectTarget(s), nil)
s.enemyEgg = {x = 3, y = 3, z = 121}
check("enemy egg z out", selectTarget(s), nil)
s.enemyEgg = {x = 0/0, y = 3, z = 0}
check("enemy egg NaN", selectTarget(s), nil)
s.enemyEgg = {x = "0", y = 3, z = 0}
check("enemy egg wrong type", selectTarget(s), nil)
check("nil snapshot", selectTarget(nil), nil)
check("string snapshot", selectTarget("bad"), nil)
check("number snapshot", selectTarget(13), nil)

assert(n >= 60, "native coverage floor: " .. tostring(n))
print("P0D_S1_FIRST90_CLASSIC_NATIVE_" .. tostring(n) .. "_ASSERTIONS_PASS")
'''

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", required=True, type=Path)
    args = parser.parse_args()
    args.write.parent.mkdir(parents=True, exist_ok=True)
    args.write.write_text(body + TESTS, encoding="utf8")
    print("WROTE_NATIVE_LUAU", args.write)

if __name__ == "__main__":
    main()
