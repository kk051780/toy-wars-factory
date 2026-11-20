#!/usr/bin/env python3
"""Execute original-boss session fencing in a REAL Luau VM, independent of Roblox Studio."""
from pathlib import Path
import argparse
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"EGGRUMBLE_BossSessionFence.luau"
def build(path:Path):
    s=SOURCE.read_text(encoding="utf-8").rstrip()
    if not s.endswith("\nreturn Fence"):
        raise ValueError("BossSessionFence module return unexpectedly changed")
    checks=r'''
local team={rules={phase="ACTIVE",winner=nil,castles={["101"]={alive=true},["102"]={alive=false}}}}
local br={rules={phase="ACTIVE",winner=nil,castles={["201"]={alive=true},["202"]={alive=true}}}}
local sessions={TEAM=team,BATTLE_ROYALE=br}
local joined={[101]="TEAM",[102]="TEAM",[201]="BATTLE_ROYALE",[202]="BATTLE_ROYALE"}
assert(Fence.active("TEAM",team,sessions))
assert(Fence.active("BATTLE_ROYALE",br,sessions))
assert(Fence.mayEngage("TEAM",team,sessions,joined,101,false))
assert(Fence.mayEngage("BATTLE_ROYALE",br,sessions,joined,201,false))
assert(not Fence.mayEngage("TEAM",team,sessions,joined,201,false),"BR participant must never receive TEAM boss damage")
assert(not Fence.mayEngage("BATTLE_ROYALE",br,sessions,joined,101,false),"TEAM participant must never receive BR boss damage")
assert(not Fence.mayEngage("TEAM",team,sessions,joined,102,false),"fallen castle cannot be targeted")
assert(not Fence.mayEngage("TEAM",team,sessions,joined,101,true),"eliminated character cannot attack or be hit")
assert(not Fence.mayEngage("TEAM",team,sessions,joined,999,false),"unknown human denied")
team.rules.phase="FINISHED"
assert(not Fence.active("TEAM",team,sessions))
assert(not Fence.mayEngage("TEAM",team,sessions,joined,101,false),"finished round fenced")
team.rules.phase="ACTIVE"
team.rules.winner="BLUE"
assert(not Fence.active("TEAM",team,sessions),"winner means session complete")
team.rules.winner=nil
joined[101]="BATTLE_ROYALE"
assert(not Fence.mayEngage("TEAM",team,sessions,joined,101,false),"changed queue membership denied")
joined[101]="TEAM"
sessions.TEAM={rules={phase="ACTIVE",winner=nil,castles={["101"]={alive=true}}}}
assert(not Fence.mayEngage("TEAM",team,sessions,joined,101,false),"stale session object forbidden")
assert(not Fence.active("INVALID",br,sessions))
print("[EGGRUMBLE NATIVE BOSS SESSION FENCE] PASS",15,"match-isolation and anti-ghost-hit checks")
'''
    path.write_text(s[:-len("\nreturn Fence")]+checks,encoding="utf-8")
if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",required=True,type=Path)
    args=parser.parse_args()
    build(args.out)
