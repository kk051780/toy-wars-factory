#!/usr/bin/env python3
"""Extract and EXECUTE the unchanged author's actual execute() in native Luau VM.

No Roblox physics/Place; intentionally stop living branch at CombatBalance.skill.
The mutant is the unpatched original and MUST fail dead/downed negative tests.
"""
from __future__ import annotations
import argparse
from pathlib import Path
from compose import AUTHOR_REL, compose

PREAMBLE = """-- Native Luau VM test of actual ORIGINAL execute() function, patched only at entry.
local lastByPlayer = {}
local currentChar, currentHum
local called = 0
local CombatBalance = {}
function CombatBalance.skill(role,slot)
 called += 1
 error("GQ_LIVING_PATH_REACHED:" .. role .. ":" .. slot)
end
local function characterOf(p)
 return currentChar, {Position=0}, currentHum
end
"""
CASES = """
local roles={"WARRIOR","MAGE","NINJA","TRAPPER","BUILDER","BEAST","ZOMBIE"}
local modes={"TEAM","BATTLE_ROYALE"}
local scenarios={"dead","downed","live","eliminated","castle_dead","inactive"}
local tested=0
for _,mode in ipairs(modes) do
 for _,role in ipairs(roles) do
  for _,scenario in ipairs(scenarios) do
   local char={downed=scenario=="downed"}
   function char:GetAttribute(k)
    if k=="EGGRUMBLE_Downed" then return self.downed end
    return nil
   end
   local h={Health=(scenario=="dead" and 0 or 75)}
   local player={UserId=12013,Character=char,Parent=true,attrs={
      EGGRUMBLE_Role=role,
      EGGRUMBLE_Eliminated=scenario=="eliminated"
   }}
   function player:GetAttribute(k) return self.attrs[k] end
   function player:SetAttribute(k,v) self.attrs[k]=v end
   local session={
    mode=mode,
    rules={
     phase=(scenario=="inactive" and "LOBBY" or "ACTIVE"),
     castles={["12013"]={alive=scenario~="castle_dead"}}
    }
   }
   called=0;lastByPlayer={};currentChar=char;currentHum=h
   local ok,err=pcall(function() execute(session,player,role,"C") end)
   if scenario=="live" then
    assert(not ok and string.find(tostring(err),"GQ_LIVING_PATH_REACHED:",1,true),
       "live path must arrive at original CombatBalance.skill: "..role..":"..mode)
    assert(called==1,"live path must invoke skill exactly once")
   else
    assert(ok,"negative caster must return BEFORE skill: "..scenario..":"..role..":"..mode.." "..tostring(err))
    assert(called==0,"negative caster reached skill effect")
    assert(lastByPlayer[player.UserId]==nil,"negative caster allocated cooldown")
    assert(player.attrs.EGGRUMBLE_SkillCastSignature==nil,"negative caster signed cast")
   end
   tested+=1
  end
 end
end
assert(tested==84,"expected all TEAM/BR x 7 role x 6 state cases")
print("NATIVE_REAL_AUTHOR_EXECUTE_84_CASES_PASS",tested)
"""

def generate(source: bytes, mutant: bool) -> str:
    actual = compose(source, enabled=not mutant).decode("utf-8")
    left = "local function execute(session:any,p:Player,role:string,slot:string)"
    right = "\nfunction HeroCombat.roleOrder()"
    if actual.count(left) != 1 or actual.count(right) != 1:
        raise ValueError("RED_EXECUTE_PARSE: unique original function absent")
    chunk = actual[actual.index(left):actual.index(right)]
    if "local function blast" not in chunk or 'else healAllies(session,p,root);blast() end' not in chunk:
        raise ValueError("RED_AUTHOR_RUNTIME: body not original seven-role logic")
    return PREAMBLE + "\n" + chunk + "\n" + CASES

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--mutant", action="store_true", help="negative control MUST fail")
    opts = parser.parse_args()
    repo = Path(__file__).resolve().parents[3]
    source = (repo / AUTHOR_REL).read_bytes()
    executable = generate(source, opts.mutant)
    opts.out.write_text(executable, encoding="utf-8")
    print("generated actual execute()", "MUTANT_EXPECT_FAIL" if opts.mutant else "PATCHED_EXPECT_PASS",
          "bytes", len(executable.encode()))

if __name__ == "__main__":
    main()
