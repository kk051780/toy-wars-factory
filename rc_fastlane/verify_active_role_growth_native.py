"""Exercise the exact #219 clock and selected Game/Horde on a deterministic Native scene."""

import argparse
from pathlib import Path

from apply_active_role_growth import GAME, GROWTH, HUD, PACKAGE, TIME
from verify_active_undead_native import render, section


def make(dist):
    src = dist / "src"
    game = (src / GAME).read_text(encoding="utf-8")
    growth = (src / GROWTH).read_text(encoding="utf-8")
    time = (src / TIME).read_text(encoding="utf-8")
    source = render(dist, game, True, False)
    end = "\nif true then\n    local guard=addNeutral"
    assert source.count(end) == 1
    source = source.split(end, 1)[0]
    init = 'local Time = require(script.Parent:WaitForChild("TimePremiumRules"))'
    assert growth.count(init) == 1
    growth = growth.replace(init, "local Time=(function()\n" + time + "\nend)()", 1)
    getter = "    function p:SetAttribute(key,value) self.attrs[key]=value end"
    assert source.count(getter) == 1
    source = source.replace(getter, getter + "\n    function p:GetAttribute(key) return self.attrs[key] end", 1)
    flags = "local ServerStorage={GetAttribute=function() return enabled end}"
    assert source.count(flags) == 1
    source = source.replace(flags, """local growthFlag=true
local ServerStorage={GetAttribute=function(_,attribute)
    if attribute=="P0D_RC_ENABLE_MATCH_ROLE_GROWTH" then return growthFlag end
    return enabled
end}""", 1)
    anchor = "local function sevenJobStrike("
    mounted = ("SevenJobs.Growth=(function()\n" + growth + "\nend)()\n"
               "SevenJobs.GrowthStates={}\n"
               + section(game, "function SevenJobs.growthEnabled(", "-- ONLY Server Game confirms objective events."))
    assert source.count(anchor) == 1
    source = source.replace(anchor, mounted + anchor, 1)
    scope = section(game, "    local growth=SevenJobs.activeGrowth(player)\n    local halfMoonSelected", "    return {")
    fields = section(game, "        roleHalfMoon =", "        jobStudioPvE")
    display = section((src / HUD).read_text(encoding="utf-8"),
                      "    local halfMoon=s.roleHalfMoon", "    trapButton.Visible")
    views = ("\nlocal function growthSnapshot(player)\n    local now=serverNow()\n" + scope
             + "    return {\n" + fields + "    }\nend\n"
             + "local jobCast={Visible=true}\nlocal jobSkillName={WARRIOR='重撃'}\n"
             + "local function growthHud(s)\n    local picked='WARRIOR'\n"
               "    local jobCd=s.jobCooldown\n    local currentNetBound=false\n"
             + display + "end\n")
    return (source + views + (PACKAGE / "native_cases.luau").read_text(encoding="utf-8")).encode("utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.write_bytes(make(args.dist))
