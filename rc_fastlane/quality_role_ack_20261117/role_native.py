#!/usr/bin/env python3
"""Native behavioral replay from the REAL selected EGGRUMBLE 31-source Host.

Exercise the original joinQueue function body with mocked Roblox scheduling.
Fail closed on Host drift; no reimplementation of game logic and no RC writes.
"""
from __future__ import annotations
import argparse
import importlib.util
from pathlib import Path

HOST_BEGIN = "local function joinQueue(mode:string,p:Player)\n"
HOST_END = "\n-- Seven job-selection stands:"

PREFIX = r'''-- GQ8 real selected Host joinQueue body executed with isolated Roblox-facing mocks.
local function check(cond,label)
 if not cond then error("GQ8_NATIVE_ROLE_ACK_RED_"..label,2) end
end
local queues = {TEAM={},BATTLE_ROYALE={}}
local sessions = {}
local joined = {}
local chosenRole = {}
local queueEpoch = {TEAM=0,BATTLE_ROYALE=0}
local queueStartedAt = {}
local MODE_SEATS = 16
local COUNTDOWN = 12
local delayed = {}
local spawnCallbacks = {}
local refreshes = {}
local starts = {}
local ticks = 100
local function time() return ticks end
local task = {
 delay=function(seconds,callback)
  table.insert(delayed,{seconds=seconds,callback=callback})
 end,
 spawn=function(callback)
  table.insert(spawnCallbacks,callback)
 end,
 wait=function()
  error("GQ8_TEST_MUST_NOT_EXECUTE_WALL_CLOCK")
 end,
}
local function player(id)
 local p={UserId=id, attributes={}}
 function p:SetAttribute(k,v)
  self.attributes[k]=v
 end
 function p:GetAttribute(k)
  return self.attributes[k]
 end
 return p
end
local function refreshQueueBoard(mode)
 table.insert(refreshes,mode)
end
local function startSession(mode)
 check(sessions[mode]==nil,"START_EXISTS")
 table.insert(starts,mode)
 sessions[mode]={mode=mode}
end
local RoundReplay={}
function RoundReplay.leaveWaitingQueue(mode,p,qs,joinedIds,epochs,liveSessions)
 if liveSessions[mode] or joinedIds[p.UserId]~=mode then return false end
 local q=qs[mode]
 if not q then return false end
 local idx=table.find(q,p)
 if not idx then return false end
 table.remove(q,idx)
 joinedIds[p.UserId]=nil
 if #q==0 then epochs[mode]=(epochs[mode] or 0)+1 end
 return true
end
function RoundReplay.canStartCountdown(mode,expectedEpoch,qs,epochs,liveSessions)
 local waiting=qs[mode]
 return liveSessions[mode]==nil and waiting~=nil and #waiting>0
  and epochs[mode]==expectedEpoch
end

'''
SUFFIX = r'''
-- GQ8 native runtime cases (actual joinQueue byte-body above).
local a=player(101)
-- 1: A client-only attribute must never be trusted as a selected job.
a:SetAttribute("EGGRUMBLE_SelectedRole","MAGE")
joinQueue("TEAM",a)
check(joined[101]==nil and #queues.TEAM==0,"UNSELECTED_ENTERED")
check(a:GetAttribute("EGGRUMBLE_RoleSelectionRequired")==true,"NO_SELECTION_PROMPT")
check(#delayed==0 and #starts==0,"UNSELECTED_TIMER")
-- 2: Valid server-owned selection joins exactly one queue, with one timer.
chosenRole[101]="MAGE"
joinQueue("TEAM",a)
check(joined[101]=="TEAM" and #queues.TEAM==1,"TEAM_JOIN")
check(a:GetAttribute("EGGRUMBLE_QueuedMode")=="TEAM","TEAM_ATTRIBUTE")
check(a:GetAttribute("EGGRUMBLE_RoleSelectionRequired")==nil,"SELECTED_NOT_CLEARED")
check(#delayed==1 and delayed[1].seconds==12,"ONE_COUNTDOWN_TIMER")
check(#spawnCallbacks==1,"ONE_VISUAL_TICKER")
local stale=delayed[1].callback
-- 3: Same-gate second activation cancels without starting a match.
joinQueue("TEAM",a)
check(joined[101]==nil and #queues.TEAM==0,"TOGGLE_CANCEL")
check(a:GetAttribute("EGGRUMBLE_QueuedMode")==nil,"CANCEL_ATTRIBUTE")
check(queueEpoch.TEAM==1,"CANCEL_EPOCH")
stale()
check(#starts==0,"STALE_TIMER_STARTED")
-- 4: Rejoin gets a fresh 12 second timer, not the canceled countdown.
joinQueue("TEAM",a)
check(joined[101]=="TEAM" and #delayed==2,"REJOIN_NEW_TIMER")
check(queueEpoch.TEAM==1,"REJOIN_EPOCH")
stale()
check(#starts==0,"OLD_TIMER_SURVIVED_REJOIN")
-- 5: Switching from TEAM to BR removes old queue membership.
joinQueue("BATTLE_ROYALE",a)
check(joined[101]=="BATTLE_ROYALE","MODE_SWITCH_JOINED")
check(#queues.TEAM==0 and #queues.BATTLE_ROYALE==1,"MODE_SWITCH_QUEUE")
check(queueEpoch.TEAM==2,"MODE_SWITCH_TEAM_EPOCH")
check(#delayed==3,"MODE_SWITCH_TIMER")
delayed[2].callback()
check(#starts==0,"TEAM_TIMER_ENTERED_BR")
-- 6: The valid BR timer starts one real session and blocks duplicate entry.
delayed[3].callback()
check(#starts==1 and starts[1]=="BATTLE_ROYALE","BR_TIMER")
joinQueue("BATTLE_ROYALE",a)
check(#starts==1 and #queues.BATTLE_ROYALE==1,"ACTIVE_JOIN_DUPLICATE")
-- 7: A player in a live BR match cannot cross-queue into TEAM.
joinQueue("TEAM",a)
check(joined[101]=="BATTLE_ROYALE" and #queues.TEAM==0,"LIVE_MATCH_SWITCH")
-- 8: A second user who has not selected a role cannot join even an empty mode.
local b=player(102)
b:SetAttribute("EGGRUMBLE_Role","WARRIOR")
joinQueue("TEAM",b)
check(joined[102]==nil and #queues.TEAM==0,"CLIENT_ROLE_FORGERY")
-- 9: A selected user can still join TEAM while BR is live.
chosenRole[102]="WARRIOR"
joinQueue("TEAM",b)
check(joined[102]=="TEAM" and #queues.TEAM==1,"INDEPENDENT_TEAM")
check(#delayed==4,"TEAM_SEPARATE_TIMER")
delayed[4].callback()
check(#starts==2 and starts[2]=="TEAM","TEAM_SEPARATE_START")
-- 10: Safe early return when entering an active mode with the same player.
local oldCount=#starts
joinQueue("TEAM",b)
check(#starts==oldCount,"ACTIVE_TEAM_DUPLICATION")

-- 11: The full 16-human immediate-start path never bypasses role ACK.
queues={TEAM={},BATTLE_ROYALE={}}
sessions={}
joined={}
chosenRole={}
queueEpoch={TEAM=0,BATTLE_ROYALE=0}
queueStartedAt={}
delayed={}
spawnCallbacks={}
starts={}
for i=1,15 do
 local q=player(200+i)
 chosenRole[q.UserId]="NINJA"
 joinQueue("TEAM",q)
 check(#starts==0,"EARLY_FULL_START_"..tostring(i))
end
local noRole=player(250)
joinQueue("TEAM",noRole)
check(#starts==0 and #queues.TEAM==15,"UNSELECTED_FULL_QUEUE_ADMISSION")
local last=player(216)
chosenRole[last.UserId]="BEAST"
joinQueue("TEAM",last)
check(#queues.TEAM==16 and #starts==1 and starts[1]=="TEAM","FULL16_ROLE_ACK_START")
-- 12: No additional countdown can start a second full-match.
for _,timer in ipairs(delayed) do timer.callback() end
check(#starts==1,"FULL16_DOUBLE_START")
print("GQ8_REAL_HOST_NATIVE_ROLE_ACK_12_SEMANTIC_CASES_PASS")
'''

def load_source(project: Path):
    helper = Path(__file__).with_name("select_role_ready.py")
    spec = importlib.util.spec_from_file_location("gq8_role_select", helper)
    if not spec or not spec.loader:
        raise RuntimeError("RED_IMPORT_HELPER")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _, files, host = module.mapping(project)
    if len(files) != 31:
        raise ValueError("RED_31_ONLY")
    source = files[host].read_text(encoding="utf-8")
    if source.count(HOST_BEGIN) != 1 or source.count(HOST_END) != 1:
        raise ValueError("RED_SELECTED_HOST_ANCHOR_DRIFT")
    if source.count(module.MARKER) != 1 or source.count(module.JOIN_PATCH) != 1:
        raise ValueError("RED_EXACT_ROLE_ACK_NOT_PRESENT")
    a = source.index(HOST_BEGIN)
    b = source.index(HOST_END,a)
    body = source[a:b]
    if body.rstrip().splitlines()[-1].strip() != "end":
        raise ValueError("RED_JOINQUEUE_NOT_COMPLETE")
    if "task.delay(COUNTDOWN," not in body:
        raise ValueError("RED_ORIGINAL_COUNTDOWN_MISSING")
    return body

def render(body: str, mutant: bool=False):
    if mutant:
        before = "if chosenRole[p.UserId]==nil then"
        if body.count(before) != 1:
            raise ValueError("RED_MUTANT_ANCHOR_DRIFT")
        body = body.replace(before,"if false then",1)
    # Luau standalone uses the exact function body; Player is a Roblox-only type.
    body = body.replace("mode:string,p:Player","mode:string,p:any",1)
    return PREFIX+body+SUFFIX

def main():
    cli=argparse.ArgumentParser()
    cli.add_argument("--project",type=Path,required=True)
    cli.add_argument("--out",type=Path,required=True)
    cli.add_argument("--mutant",type=Path,required=True)
    a=cli.parse_args()
    body=load_source(a.project)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(render(body),encoding="utf-8")
    a.mutant.write_text(render(body,True),encoding="utf-8")
    print("GQ8_REAL_SELECTED_31_SOURCE_ROLE_ACK_NATIVE_HARNESS_GENERATED")

if __name__ == "__main__":
    main()
