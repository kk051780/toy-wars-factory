#!/usr/bin/env python3
"""Extract the exact selected Host deposit callback into native Luau scenarios.

This does not simulate Studio physics. It executes actual selected source callback,
including the security predicate and existing Rules.depositEggs invocation.
"""
from __future__ import annotations
import argparse
from pathlib import Path
from select_deposit import body, FLAG

PREFIX = r'''--!strict
local attempts=0
local refreshed=0
local joined={}
local sessions={}
local entry={id="101"}
local session={
  mode="TEAM",
  rules={phase="ACTIVE",castles={["101"]={alive=true,heldEggs=2}}},
  refresh=function() refreshed+=1 end
}
local Rules={}
Rules.depositEggs=function(rules,id,amount)
  assert(rules.phase=="ACTIVE")
  assert(id=="101" and amount>0)
  attempts+=1
  return 1
end
local function claim(p)
'''
SUFFIX = r'''
end
local function check(label, id, member, sameSession, active, alive, eggs, expected)
  joined={}
  if member~=nil then joined[id]=member end
  session.rules=if active then {
    phase="ACTIVE",castles={["101"]={alive=alive,heldEggs=eggs}}
  } else nil
  sessions={TEAM=if sameSession then session else {mode="TEAM"}}
  local before=attempts
  local refreshedBefore=refreshed
  local ok,why=pcall(function() claim({UserId=id}) end)
  assert(ok,label.." RUNTIME_ERROR "..tostring(why))
  assert(attempts-before==expected,
    label.." deposited="..tostring(attempts-before).." expected="..tostring(expected))
  assert(refreshed-refreshedBefore==expected,label.." refresh incorrect")
end
check("ACTIVE_OWNER",101,"TEAM",true,true,true,2,1)
check("OLD_MODE_REJOIN",101,"BATTLE_ROYALE",true,true,true,2,0)
check("DISCONNECTED_OWNER",101,nil,true,true,true,2,0)
check("RETIRED_SESSION_SAME_MODE",101,"TEAM",false,true,true,2,0)
check("WRONG_OWNER",102,"TEAM",true,true,true,2,0)
check("NO_RULES",101,"TEAM",true,false,true,2,0)
check("DESTROYED_CASTLE",101,"TEAM",true,true,false,2,0)
check("EMPTY_CARRIER",101,"TEAM",true,true,true,0,0)
print("GQ_DEPOSIT_CURRENT_SESSION_ACTUAL_HOST_NATIVE_8_CASES_PASS")
'''
def build(host: Path, out: Path):
    source=host.read_text(encoding="utf-8")
    if source.count(FLAG)!=1:
        raise ValueError("RED_ACTUAL_SELECTED_HOST_FLAG_MISSING")
    callback=body(source)
    for required in ("joined[p.UserId]~=session.mode",
                     "sessions[session.mode]~=session",
                     "Rules.depositEggs(session.rules,entry.id,c.heldEggs)",
                     "if ok then session.refresh() end"):
        if required not in callback:
            raise ValueError("RED_CALLBACK_SOURCE_DIFFERENT_" + required)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(PREFIX+callback+SUFFIX,encoding="utf-8")
    print("GQ586_EXACT_SELECTED_HOST_CALLBACK_NATIVE_HARNESS_GENERATED")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--host",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    build(a.host,a.out)
if __name__=="__main__":
    main()
