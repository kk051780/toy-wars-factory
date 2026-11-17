#!/usr/bin/env python3
"""Extract the EXACT selected real Swarm function into runnable Luau native regressions.

Runs source-under-test instead of reimplementing the gating logic in Python.
The negative mutant reverts only the human-alive check and must exit nonzero.
"""
import argparse
from pathlib import Path
from select_alive import scan, SWARM, scoped, AFTER, BEFORE

HARNESS = """
local Players={items={}}
function Players:GetPlayers() return self.items end
local session={rules={castles={}},botActors={}}
<<FUNCTION>>
local function char(tag,hp,rootExists)
 local root=if rootExists then {Position=tag} else nil
 local hum=if hp~=nil then {Health=hp} else nil
 return {
  FindFirstChild=function(self,name)
   if name=="HumanoidRootPart" then return root end
   return nil
  end,
  FindFirstChildOfClass=function(self,klass)
   if klass=="Humanoid" then return hum end
   return nil
  end
 }
end
local live=char("LIVE",90,true)
local dead=char("DEAD",0,true)
local noHum=char("NO_HUM",nil,true)
local noRoot=char("NO_ROOT",60,false)
local notMember=char("NOT_MEMBER",100,true)
Players.items={
 {UserId=1,Character=live},
 {UserId=2,Character=dead},
 {UserId=3,Character=noHum},
 {UserId=4,Character=noRoot},
 {UserId=5,Character=notMember}
}
for id=1,4 do session.rules.castles[tostring(id)]={alive=true} end
session.rules.castles["BOT"]={alive=true}
session.botActors.BOT={Parent=true,PrimaryPart={Position="BOT"}}
local found=aliveTargets()
assert(#found==2 and found[1]=="LIVE" and found[2]=="BOT",
 "GQ8_SWARM_LIVING_AVATAR_MUTANT_RED: dead/noHum/noRoot/notMember included")
session.botActors.BOT=nil
found=aliveTargets()
assert(#found==1 and found[1]=="LIVE","GQ8_LIVING_HUMAN_SINGLE_FAILED")
live.FindFirstChildOfClass=function() return {Health=0} end
found=aliveTargets()
assert(#found==0,"GQ8_DEAD_AT_LATEST_TICK_INCLUDED")
print("GQ8_LIVING_AVATAR_TRUE_SOURCE_NATIVE_6_CASES_PASS")
"""

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--project",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--mutant",type=Path,required=True)
    v=ap.parse_args()
    _, files=scan(v.project.resolve(strict=True))
    source=files[SWARM].read_text(encoding="utf-8")
    func=scoped(source)
    if AFTER not in func or BEFORE in func:
        raise ValueError("RED_NOT_SELECTED_SWARM_LIVE_FENCE")
    v.out.write_text(HARNESS.replace("<<FUNCTION>>",func)+"\n",encoding="utf-8")
    mutant=func.replace(AFTER,BEFORE)
    if mutant==func or AFTER in mutant:
        raise ValueError("RED_MUTANT_NOT_CREATED")
    v.mutant.write_text(HARNESS.replace("<<FUNCTION>>",mutant)+"\n",encoding="utf-8")
    print("GQ8_SWARM_REAL_SELECTED_FUNCTION_NATIVE_AND_EXPECTED_RED_GENERATED")

if __name__=="__main__":
    main()
