#!/usr/bin/env python3
"""Run the REAL selected Luau takeover closure against seven match states."""
from __future__ import annotations
import argparse
from pathlib import Path

def build(selected: str) -> str:
    begin = selected.index(' session.takeover=function(id:string):boolean')
    end_marker = '\n end\nend\nreturn BotActors'
    stop = selected.index(end_marker, begin) + len('\n end')
    fragment = selected[begin:stop]
    assert fragment.count('session.takeover=function') == 1
    return '''-- Actual selected original-author BotActors takeover callback.
local home=setmetatable({}, {__add=function(left,right) return {position="at-home"} end})
local Vector3={new=function(x,y,z) return {x=x,y=y,z=z} end}
local folder={Parent=true}
local actors={Parent=true}
local bots={}
local spawnCount=0
local spawnActor=function(parent,id,at,team)
 spawnCount+=1
 return {Parent=parent, ID=id, position=at, team=team}
end
local session={
 rules={phase="ACTIVE",castles={}},
 castleLocations={["123"]=home}
}
''' + fragment + '''
local cases=0
local function check(label,phase,parent,alive,occupied,hasHome,expected)
 folder.Parent=parent
 session.rules.phase=phase
 session.rules.castles["123"]={alive=alive,isAI=false,team="RED"}
 session.castleLocations["123"]=if hasHome then home else nil
 bots["123"]=if occupied then {Parent=actors} else nil
 local before=spawnCount
 local result=session.takeover("123")
 assert(result==expected,label..": bad return")
 if expected then
  assert(spawnCount==before+1,label..": actor not spawned")
  assert(session.rules.castles["123"].isAI==true,label..": no AI promotion")
 else
  assert(spawnCount==before,label..": phantom actor created")
  assert(session.rules.castles["123"].isAI==false,label..": phantom promotion")
 end
 cases+=1
end
check("ACTIVE", "ACTIVE",true,true,false,true,true)
check("FINISHED", "FINISHED",true,true,false,true,false)
check("LOBBY", "LOBBY",true,true,false,true,false)
check("DESTROYED_WORLD", "ACTIVE",nil,true,false,true,false)
check("DEAD_CASTLE", "ACTIVE",true,false,false,true,false)
check("ALREADY_HAS_BOT", "ACTIVE",true,true,true,true,false)
check("NO_CASTLE_HOME", "ACTIVE",true,true,false,false,false)
print("GQ_AI_TAKEOVER_TERMINAL_NATIVE_PASS",cases)
'''

if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--selected",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    args.out.write_text(build(args.selected.read_text(encoding="utf-8")), encoding="utf-8")
