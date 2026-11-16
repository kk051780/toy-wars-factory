#!/usr/bin/env python3
"""Execute the actual extracted V3 Host queue and PlayerRemoving Luau functions."""
import argparse
import re
import subprocess
from pathlib import Path

def generate(source: str) -> str:
    a = source.index("local function joinQueue(mode:string,p:Player)")
    b = source.index("\n-- Seven job-selection stands:", a)
    join = source[a:b]
    assert join.strip().endswith("end"), "broken joinQueue extractor"
    a = source.index("Players.PlayerRemoving:Connect(function(p)")
    b = source.index("\nend)\nprint(\"[EGGRUMBLE V3]", a)
    remove = source[a:b+5]
    remove = remove.replace("Players.PlayerRemoving:Connect(function(p)", "local function removePlayer(p)", 1)
    assert remove.endswith("end)")
    remove = remove[:-4] + "end"
    pre = """local queues={TEAM={},BATTLE_ROYALE={}}
local joined={}
local chosenDefense={}
local chosenRole={}
local queueEpoch={TEAM=0,BATTLE_ROYALE=0}
local sessions={}
local MODE_SEATS=16
local COUNTDOWN=12
local clock=0
local delayed={}
local started={}
local task={}
function task.delay(dt,fn) table.insert(delayed,{at=clock+dt,fn=fn}) end
local InteractionGuard={clear=function(_) end}
local SevenRoleCombat={clear=function(_) end}
local root=Vector3
local function startSession(mode)
 if sessions[mode] then return end
 sessions[mode]={}
 table.insert(started,{mode=mode,at=clock})
end
local function person(id)
 return {UserId=id,Parent=true,SetAttribute=function(self,key,value)self[key]=value end}
end
local function advance(to)
 while true do
  local idx=nil
  for i,entry in ipairs(delayed) do
   if entry.at<=to and (not idx or entry.at<delayed[idx].at) then idx=i end
  end
  if not idx then break end
  local entry=table.remove(delayed,idx)
  clock=entry.at
  entry.fn()
 end
 clock=to
end
local function reset()
 queues={TEAM={},BATTLE_ROYALE={}}
 joined={}
 chosenDefense={}
 chosenRole={}
 queueEpoch={TEAM=0,BATTLE_ROYALE=0}
 sessions={}
 delayed={}
 started={}
 clock=0
end
"""
    checks = """
-- A leaves before the first timer fires; B must receive a full countdown.
reset()
local a=person(101)
joinQueue("TEAM",a)
advance(2)
removePlayer(a)
assert(queueEpoch.TEAM==1,"empty queue must revoke old epoch")
advance(5)
local b=person(102)
joinQueue("TEAM",b)
advance(12)
assert(#started==0,"RED: old A timer incorrectly starts B after only 7s")
advance(16.99)
assert(#started==0,"B still owed full countdown")
advance(17)
assert(#started==1 and started[1].at==17,"B starts exactly after full countdown")
advance(100)
assert(#started==1,"no duplicate timer start")

-- A continuous occupied queue keeps its original countdown.
reset()
a=person(201);b=person(202)
joinQueue("TEAM",a)
advance(4)
joinQueue("TEAM",b)
advance(5)
removePlayer(a)
assert(queueEpoch.TEAM==0,"do not revoke with B still waiting")
advance(12)
assert(#started==1 and started[1].at==12,"continuous queue cadence changed")

-- TEAM abandonment cannot cancel BR.
reset()
a=person(301);b=person(302)
joinQueue("TEAM",a)
joinQueue("BATTLE_ROYALE",b)
advance(3)
removePlayer(a)
advance(12)
assert(#started==1 and started[1].mode=="BATTLE_ROYALE","other mode canceled")
assert(sessions.TEAM==nil,"abandoned TEAM unexpectedly started")

-- Late entrant after an abandoned timer expires still receives 12 seconds.
reset()
a=person(401)
joinQueue("TEAM",a)
advance(1)
removePlayer(a)
advance(20)
b=person(402)
joinQueue("TEAM",b)
advance(31)
assert(#started==0,"late entrant started early")
advance(32)
assert(#started==1,"late entrant did not start")

print("GQ_QUEUE_ACTUAL_HOST_NATIVE_4_SCENARIOS_PASS")
"""
    return pre + "\n" + join + "\n" + remove + "\n" + checks

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source",required=True)
    ap.add_argument("--luau",required=True)
    ap.add_argument("--output",required=True)
    args=ap.parse_args()
    source=Path(args.source).read_text()
    harness=generate(source)
    Path(args.output).write_text(harness)
    done=subprocess.run([args.luau,args.output],text=True,capture_output=True)
    print(done.stdout,end="")
    if done.stderr: print(done.stderr,end="")
    if done.returncode or "GQ_QUEUE_ACTUAL_HOST_NATIVE_4_SCENARIOS_PASS" not in done.stdout:
        raise SystemExit("RED: real Host native queue scenario failed")
if __name__=="__main__":
    main()
