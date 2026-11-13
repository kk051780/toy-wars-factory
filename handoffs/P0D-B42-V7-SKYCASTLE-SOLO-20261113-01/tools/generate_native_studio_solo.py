#!/usr/bin/env python3
"""Actually execute unchanged, committed StudioSoloPreviewRules source in pinned Luau CLI."""
from pathlib import Path
import argparse

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src/StudioSoloPreviewRules.luau"
code = SRC.read_text(encoding="utf8")
assert code.rstrip().endswith("return Solo"), "refuse source drift"
header = code.rstrip()[:-len("return Solo")]
tests = r'''
local n = 0
local function eq(name, actual, expected)
    n += 1
    if actual ~= expected then
        error("P0D_SOLO_CASE_FAIL:" .. name .. " got=" .. tostring(actual)
            .. " expected=" .. tostring(expected))
    end
end
local can = Solo.canStart
local winner = Solo.emptyWinner
eq("public single red cannot start", can(false, 1, 1, 0, 2), false)
eq("public single blue cannot start", can(false, 1, 0, 1, 2), false)
eq("public zero cannot start", can(false, 0, 0, 0, 2), false)
eq("public two opposing teams", can(false, 2, 1, 1, 2), true)
eq("public three red plus blue", can(false, 3, 2, 1, 2), true)
eq("public two same team cannot start", can(false, 2, 2, 0, 2), false)
eq("public three same team cannot start", can(false, 3, 3, 0, 2), false)
eq("public zero empty blue", can(false, 0, 0, 0, 2), false)
eq("Studio solo RED can start", can(true, 1, 1, 0, 2), true)
eq("Studio solo BLUE can start", can(true, 1, 0, 1, 2), true)
eq("Studio solo no joined team fails", can(true, 1, 0, 0, 2), false)
eq("Studio solo wrong roster fails", can(true, 1, 1, 1, 2), false)
eq("Studio solo no players fails", can(true, 0, 0, 0, 2), false)
eq("Studio 2-client regular opposing teams", can(true, 2, 1, 1, 2), true)
eq("Studio 2-client same team blocked", can(true, 2, 2, 0, 2), false)
eq("Studio 3-client same team blocked", can(true, 3, 3, 0, 2), false)
eq("public BLUE absent loses", winner(false, 1, 1, 0), "RED")
eq("public RED absent loses", winner(false, 1, 0, 1), "BLUE")
eq("public empty red BLUE wins", winner(false, 0, 0, 0), "BLUE")
eq("public two valid no winner", winner(false, 2, 1, 1), nil)
eq("Studio solo RED never auto-win", winner(true, 1, 1, 0), nil)
eq("Studio solo BLUE never auto-win", winner(true, 1, 0, 1), nil)
eq("Studio 2-client no winner", winner(true, 2, 1, 1), nil)
eq("Studio 2-client BLUE empty ends round", winner(true, 2, 2, 0), "RED")
eq("Studio 2-client RED empty ends round", winner(true, 2, 0, 2), "BLUE")
eq("Studio 0-player public rule", winner(true, 0, 0, 0), "BLUE")
eq("Studio invalid 1 counted but 2 team players", winner(true, 1, 1, 1), nil)
eq("Public min 3 with only 2 players", can(false, 2, 1, 1, 3), false)
eq("Studio min3 2 players not bypass", can(true, 2, 1, 1, 3), false)
eq("Studio min3 one-client still permitted", can(true, 1, 1, 0, 3), true)
assert(n >= 30)
print("P0D_S1_STUDIO_SOLO_NATIVE_" .. tostring(n) .. "_ASSERTIONS_PASS")
'''

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", required=True, type=Path)
    args = parser.parse_args()
    args.write.parent.mkdir(parents=True, exist_ok=True)
    args.write.write_text(header + tests, encoding="utf8")
    print("WROTE_SOLO_NATIVE_LUAU", args.write)

if __name__ == "__main__":
    main()
