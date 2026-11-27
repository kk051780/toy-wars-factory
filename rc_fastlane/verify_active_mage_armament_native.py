"""Exercise the selected Game, Horde, and Mage weapon in the established Native scene."""
import argparse
from pathlib import Path

from apply_active_mage_armament import ARMAMENT, GAME, HORDE, PACKAGE
from verify_active_undead_native import PACKAGE as SCENE_PACKAGE, section


def make(dist):
    def body(route):
        return (dist / "src" / route).read_text(encoding="utf-8")

    game = body(GAME)
    horde = body(HORDE)
    base = (SCENE_PACKAGE / "native.luau").read_text(encoding="utf-8")
    template = base[:base.index("local function sevenJobFlash()")]
    replacements = {
        "__ACTIVE_COMBAT_RULES__": body("server/MusouCombatRules.luau"),
        "__ACTIVE_REAL_HORDE_HIT__": section(horde, "type MageCastSweep=", "function Horde:tick("),
        "__ACTIVE_S1_RULES__": body("server/S1Rules.luau"),
        "__ACTIVE_SEVEN_JOBS_RULES__": body("server/SevenJobsRules.luau"),
        "__ORIGINAL_UNDEAD_SQUAD__": "return {clear=function() end}",
        "local CFrame={": "local frameMT={__mul=function(a,b) return {Position=a.Position+b.Position} end}\nlocal CFrame={",
        "new=function(p) return {Position=p} end,": """new=function(x,y,z)
        return setmetatable({Position=if type(x)=="number" then Vector3.new(x,y,z) else x},frameMT)
    end,""",
        'local Enum={PartType={Block="Block",Ball="Ball"}': 'local Enum={PartType={Block="Block",Ball="Ball",Cylinder="Cylinder"}',
        'Material={SmoothPlastic="SmoothPlastic"}': 'Material={SmoothPlastic="SmoothPlastic",Metal="Metal",Neon="Neon"}',
        "    function item:Destroy() self.Parent=nil end": """    function item:Destroy() self.Parent=nil end
    function item:GetChildren()
        local children={}
        for _,candidate in ipairs(made) do
            if candidate.Parent==self then table.insert(children,candidate) end
        end
        return children
    end
    function item:FindFirstChild(name)
        for _,child in ipairs(self:GetChildren()) do
            if child.Name==name then return child end
        end
    end""",
        '    if name=="Players" then return Players end': '''    if name=="Players" then return Players end
    if name=="Debris" then
        return {AddItem=function(_,item,seconds) task.delay(seconds,function() item:Destroy() end) end}
    end''',
        "    function p:SetAttribute(key,value) self.attrs[key]=value end":
            "    function p:SetAttribute(key,value) self.attrs[key]=value end\n    function p:GetAttribute(key) return self.attrs[key] end",
        "local ServerStorage={GetAttribute=function() return enabled end}": """local mageFlag=true
local ServerStorage={GetAttribute=function(_,key)
    if key=="P0D_RC_ENABLE_ACTIVE_MAGE_M1" then return mageFlag end
    return enabled
end}""",
    }
    for marker, value in replacements.items():
        assert template.count(marker) == 1, marker
        template = template.replace(marker, value, 1)
    ownership = section(game, "function SevenJobs.mageArmamentSelected(", "function SevenJobs.growthEnabled(")
    attack = section(game, "local function applyAttack(", "-- H1 RAIDER wind:")
    choose = section(game, "local function selectSevenJob(", "local function sevenJobFlash(")
    tick = section(game, "local function tickRound()", "-- Match growth samples")
    mount = section(tick, "            if sevenJobs[player]", "            local state=dojoStates[player]")
    fixture = (PACKAGE / "native_cases.luau").read_text(encoding="utf-8")
    for marker, source in (("__CONFIG__", body("shared/Config.luau")), ("__ARMAMENT__", body(ARMAMENT)),
                           ("__GAME_MAGE_OWNERSHIP__", ownership), ("__GAME_ATTACK__", attack),
                           ("__GAME_MAGE_TICK__", mount),
                           ("__GAME_PICK__", choose)):
        assert fixture.count(marker) == 1, marker
        fixture = fixture.replace(marker, source, 1)
    return (template + fixture).encode("utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.write_bytes(make(args.dist))
