"""Generate executable native Luau policy tests, no Roblox API emulation."""
from pathlib import Path
DIR = Path(__file__).resolve().parent
policy = (DIR / "EGGRUMBLE_BossCreditPolicy.luau").read_text()
cases = r'''
local P = (function()
__SOURCE__
end)()
local function check(a, b, expect)
    local actual = P.shouldReset(a,b)
    assert(actual == expect, tostring(a).." -> "..tostring(b).." expected "..tostring(expect).." got "..tostring(actual))
end
check(nil, "TEAM", true)
check(nil, "BATTLE_ROYALE", true)
check("TEAM", nil, true)
check("BATTLE_ROYALE", nil, true)
check("TEAM", "BATTLE_ROYALE", true)
check("BATTLE_ROYALE", "TEAM", true)
check("TEAM", "TEAM", false)
check("BATTLE_ROYALE", "BATTLE_ROYALE", false)
check(nil, nil, false)
check("INVALID", "TEAM", false)
check("TEAM", "INVALID", false)
check("INVALID", nil, false)
check(nil, "INVALID", false)
print("BOSS_CREDIT_BOUNDARY_POLICY: 13/13 NATIVE LUAU PASS")
'''
import sys
out = Path(sys.argv[1])
out.write_text(cases.replace("__SOURCE__", policy))
print(out)
