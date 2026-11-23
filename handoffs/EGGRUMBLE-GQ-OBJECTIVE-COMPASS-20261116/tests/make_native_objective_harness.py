#!/usr/bin/env python3
"""Headless native Luau test of the ORIGINAL optional compass objective picker.
Compiles and *executes* the identical source functions: no duplicate routing logic.
This is not Roblox Studio/Android physics evidence.
"""
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "EGGRUMBLE_ObjectiveCompass.client.luau"
PRELUDE = r'''
local mt={}
local function vec(x,z,y)
 return setmetatable({X=x,Y=y or 0,Z=z or 0},mt)
end
mt.__sub=function(a,b)return vec(a.X-b.X,a.Z-b.Z,a.Y-b.Y)end
mt.__index=function(a,k)
 if k=="Magnitude" then return math.sqrt(a.X*a.X+a.Z*a.Z+a.Y*a.Y) end
 return rawget(mt,k)
end
local function part(name,x,z)
 return {Name=name,Position=vec(x,z),CanQuery=true,Transparency=0,
  IsA=function(_,typ)return typ=="BasePart"end}
end
local function model(name,parts)
 local m={Name=name,parts=parts or {}}
 function m:IsA(typ)return typ=="Model"end
 function m:FindFirstChild(k,_recurse)return self.parts[k]end
 function m:FindFirstChildWhichIsA(typ,_recurse)
  for _,p in pairs(self.parts) do if p.IsA and p:IsA(typ) then return p end end
  return nil
 end
 return m
end
local function folder(children)
 return {GetChildren=function() return children end}
end
local floor=part("TacticalBattlefield",0,0)
local own=model("Castle_owner",{EggVault=part("EggVault",-50,0),
 OwnEggDeposit=part("OwnEggDeposit",-55,5)})
local ally=model("Castle_ally",{EggVault=part("EggVault",-70,0)})
local enemy=model("Castle_enemy",{EggVault=part("EggVault",60,0)})
local farEnemy=model("Castle_far_enemy",{EggVault=part("EggVault",160,0)})
-- Color3 values in Studio compare by RGB components.
local Color3={fromRGB=function(r,g,b) return r*65536+g*256+b end}
local function setStatus(castle,status,alive)
 local core=part("StandardCore",0,0)
 core.Color=if alive then Color3.fromRGB(172,166,147) else Color3.fromRGB(59,54,55)
 local label={Text=castle.Name.."\n"..status}
 local board={FindFirstChildOfClass=function(_,kind) return if kind=="TextLabel" then label else nil end}
 function core:FindFirstChildOfClass(kind) return if kind=="BillboardGui" then board else nil end
 castle.parts.StandardCore=core
end
for _,castle in ipairs({own,ally,enemy,farEnemy}) do setStatus(castle,"卵×3 / HP1000",true) end
local arena={}
local castleList={own,ally,enemy,farEnemy}
local extras={TacticalBattlefield=floor}
function arena:FindFirstChild(name,_recurse)return extras[name]end
function arena:GetChildren()return castleList end
local at=vec(-40,0)
'''
SUITE=r'''
local cases=0
local function check(condition,label)
 cases+=1
 assert(condition,label)
end
-- TEAM must guide to the first opposite-side vault, never an ally.
local target,label=pickObjective("TEAM",arena,own,at,false)
check(target==enemy.parts.EggVault,"TEAM incorrectly marks ally / distant vault")
check(string.find(label,"敵城",1,true)~=nil,"TEAM missing raid objective label")
check(not isEnemy("TEAM",own,ally,arena),"TEAM ally mistaken as enemy")
check(isEnemy("TEAM",own,enemy,arena),"TEAM enemy missed")
check(not isEnemy("TEAM",own,own,arena),"own castle mistaken for target")
-- BATTLE ROYALE: other castle is a target even on the same physical side.
target,label=pickObjective("BATTLE_ROYALE",arena,own,at,false)
check(target==ally.parts.EggVault,"BR should target closest other owner")
-- No authoritative state exists on client; manual return must beat loot/boss.
local supply=part("ITEM_1_HEAL",-41,0)
extras.EGGRUMBLE_FieldItems=folder({supply})
local giantCore=part("WeakCore",-42,0)
extras.NEUTRAL_BOSS_STONE_GIANT=model("NEUTRAL_BOSS_STONE_GIANT",{WeakCore=giantCore})
target,label=pickObjective("TEAM",arena,own,at,true)
check(target==own.parts.OwnEggDeposit,"manual return lost to item/boss")
check(string.find(label,"手動",1,true)~=nil,"must disclose manual, not fake cargo")
-- Default still prioritizes nearby meaningful pickups.
target,label=pickObjective("TEAM",arena,own,at,false)
check(target==supply and string.find(label,"物資",1,true)~=nil,"near item missing")
extras.EGGRUMBLE_FieldItems=folder({part("ITEM_1_HEAL",100,0)})
target,label=pickObjective("TEAM",arena,own,at,false)
check(target==giantCore and string.find(label,"巨人",1,true)~=nil,"near giant missing")
-- Far boss and far item may not block valid enemy-raid navigation.
giantCore.Position=vec(250,0)
target,label=pickObjective("TEAM",arena,own,at,false)
check(target==enemy.parts.EggVault,"far giant overriding real enemy")
-- A closer empty, fallen or incompletely replicated castle must not mask a valid enemy.
setStatus(enemy,"HP180 / 卵0",true)
check(pickObjective("TEAM",arena,own,at,false)==farEnemy.parts.EggVault,"empty vault")
setStatus(enemy,"HP180 / 卵3",false)
check(pickObjective("TEAM",arena,own,at,false)==farEnemy.parts.EggVault,"fallen castle with stale stock")
setStatus(enemy,"HP180 / 卵3x",true)
check(pickObjective("TEAM",arena,own,at,false)==farEnemy.parts.EggVault,"unreadable stock")
enemy.parts.StandardCore=nil
check(pickObjective("TEAM",arena,own,at,false)==farEnemy.parts.EggVault,"waiting for replication")
setStatus(farEnemy,"HP0 / 卵0",false)
check(pickObjective("TEAM",arena,own,at,false)==own.parts.OwnEggDeposit,"all enemy vaults unavailable")
setStatus(enemy,"HP0 / 卵12",true)
check(pickObjective("TEAM",arena,own,at,false)==enemy.parts.EggVault,"live fractional HP and restocked vault")
-- With no enemy, fallback is the own deposit, never invented cargo.
local originalList=castleList
castleList={own}
target,label=pickObjective("TEAM",arena,own,at,false)
check(target==own.parts.OwnEggDeposit,"no-enemy fallback lost own castle")
-- Manual selected but deposit temporarily missing => no fake marker.
local storedDeposit=own.parts.OwnEggDeposit
own.parts.OwnEggDeposit=nil
target,label=pickObjective("TEAM",arena,own,at,true)
check(target==nil and string.find(label,"手動",1,true)~=nil,
 "missing deposit must not produce fake world marker")
own.parts.OwnEggDeposit=storedDeposit
-- Missing centerline must fail closed, not misidentify teammate as enemy.
extras.TacticalBattlefield=nil
check(not isEnemy("TEAM",own,enemy,arena),"missing field marks false enemy")
-- Input source remains in our optional client; no server/castle/egg mutation.
print("GQ_REAL_OBJECTIVE_PICKER_NATIVE_PASS cases="..cases)
'''

def build(out: Path) -> None:
    source = CLIENT.read_text(encoding="utf-8")
    begin = source.index("local function isEnemy(")
    end = source.index("local function directionTo(", begin)
    original = source[begin:end]
    for marker in ('homeSelected:boolean', 'if homeSelected then',
                   'local function nearestActiveItem(', 'local function pickObjective('):
        assert marker in original, marker
    assert original.count("local function pickObjective(") == 1
    assert 'if homeSelected then' in original.split('local item,itemDistance=')[0]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(PRELUDE + "\n" + original + "\n" + SUITE, encoding="utf-8")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    build(args.out)
    print("Generated original GQ objective source native Luau test", args.out)
