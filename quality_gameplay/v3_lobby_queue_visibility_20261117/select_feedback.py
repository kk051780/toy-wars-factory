#!/usr/bin/env python3
"""Host-only overlay: show live TEAM/BR queue size + 12s start ETA on existing portal boards.

No additional server Script/GUI/Remote. Apply AFTER upstream #539 billboard
properties and #544 queue-epoch safety. Anchors must match exactly once;
an existing implementation or drift fails closed. Source count stays 31.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

FEATURE_ID = "GQ_V3_LOBBY_QUEUE_ETA_20261117"
AUTHOR_HOST = "handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116/EGGRUMBLE_LobbyCastleModesPreview.server.luau"
UPSTREAM = {
    "original482": "fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9",
    "board539": "e003d73d516e65e1817dd281eb1743fa866f3770",
    "queue544": "see original RoundReplay queueEpoch contract",
}
CHANGES = [
    (
        'local COUNTDOWN=12 -- seconds for private preview only\n',
        '''local COUNTDOWN=12 -- seconds for private preview only
-- This is presentation state only, not a second countdown or game clock.
local queueStartedAt:{[string]:number}={}
local queueBoards:{[string]:TextLabel}={}
'''
    ),
    (
        'local function getCastlePoint(mode:string,index:number):Vector3\n',
        '''-- Reuse existing TEAM/BR portal BillboardGui; never create a second HUD.
local function refreshQueueBoard(mode:string)
 local label=queueBoards[mode]
 if not label then return end
 local prefix=if mode=="TEAM" then "TEAM｜味方の城を守る" else "BR｜最後の城が勝者"
 if sessions[mode] then
  label.Text=prefix.."\\n試合中｜次の試合を待つ"
  return
 end
 local waiting=queues[mode]
 local count=waiting and #waiting or 0
 if count==0 then
  label.Text=prefix.."\\n参加する｜1人でも開始"
  return
 end
 local started=queueStartedAt[mode] or time()
 local remaining=math.max(0,math.ceil(COUNTDOWN-math.max(0,time()-started)))
 label.Text=prefix.."\\n"..count.."/"..MODE_SEATS.."人｜開始まで"..remaining.."秒"
end
local function getCastlePoint(mode:string,index:number):Vector3
'''
    ),
    (
        'session.world.Name=mode.."_Arena";session.world.Parent=folder\n',
        '''session.world.Name=mode.."_Arena";session.world.Parent=folder
  refreshQueueBoard(mode)
'''
    ),
    (
        '  queues[mode]={}\n  queueEpoch[mode]+=1\n',
        '''  queues[mode]={}
  queueStartedAt[mode]=nil
  queueEpoch[mode]+=1
  refreshQueueBoard(mode)
'''
    ),
    (
        '  if not RoundReplay.leaveWaitingQueue(previous,p,queues,joined,queueEpoch,sessions) then return end\n',
        '''  if not RoundReplay.leaveWaitingQueue(previous,p,queues,joined,queueEpoch,sessions) then return end
  if #queues[previous]==0 then queueStartedAt[previous]=nil end
  refreshQueueBoard(previous)
'''
    ),
    (
        '  if previous==mode then return end\n',
        '  if previous==mode then return end\n'
    ),
    (
        ' if #queues[mode]==1 then\n  local expectedEpoch=queueEpoch[mode]\n',
        ''' if #queues[mode]==1 then
  queueStartedAt[mode]=time()
  local expectedEpoch=queueEpoch[mode]
  -- Visual ticker observes the author-owned queue epoch; it cannot start a match.
  task.spawn(function()
   for _=1,COUNTDOWN do
    if queueEpoch[mode]~=expectedEpoch or sessions[mode] or #queues[mode]==0 then return end
    refreshQueueBoard(mode)
    task.wait(1)
   end
  end)
'''
    ),
    (
        ' if #queues[mode]>=MODE_SEATS then startSession(mode) end\n',
        ''' refreshQueueBoard(mode)
 if #queues[mode]>=MODE_SEATS then
  startSession(mode)
  refreshQueueBoard(mode)
 end
'''
    ),
    (
        'prompt(gateTeam,"参加する","チーム戦（再操作で解除）"',
        '''-- Link exactly the original labels (#539 controls their distance/occlusion).
for mode,gate in pairs({TEAM=gateTeam,BATTLE_ROYALE=gateBR}) do
 local bb=gate:FindFirstChildOfClass("BillboardGui")
 local txt=bb and bb:FindFirstChildOfClass("TextLabel")
 if txt and txt:IsA("TextLabel") then queueBoards[mode]=txt end
 refreshQueueBoard(mode)
end
prompt(gateTeam,"参加する","チーム戦（再操作で解除）"'''
    ),
    (
        '  RoundReplay.leaveWaitingQueue(mode,p,queues,joined,queueEpoch,sessions)\n',
        '''  RoundReplay.leaveWaitingQueue(mode,p,queues,joined,queueEpoch,sessions)
  if #queues[mode]==0 then queueStartedAt[mode]=nil end
  refreshQueueBoard(mode)
'''
    ),
]

def apply(source: str) -> str:
    if "GQ_V3_LOBBY_QUEUE_ETA" in source or "local queueStartedAt:" in source:
        raise ValueError("queue feedback already installed; never duplicate")
    if 'local MODE_SEATS=16' not in source or 'local queueEpoch:' not in source:
        raise ValueError("upstream 16-seat/epoch queue contract missing")
    current=source
    for old,new in CHANGES:
        if source.count(old)!=1:
            raise ValueError(f"unexpected Host anchor multiplicity {source.count(old)}: {old[:70]!r}")
        if old==new:
            continue
        current=current.replace(old,new,1)
    if current==source:
        raise ValueError("no real source delta")
    # Every inserted hunk must reverse to byte-exact upstream Host.
    inverted=current
    for old,new in reversed(CHANGES):
        if old==new:
            continue
        if inverted.count(new)!=1:
            raise ValueError("duplicate or corrupted inserted hunk")
        inverted=inverted.replace(new,old,1)
    if inverted!=source:
        raise ValueError("OFF rollback does not reproduce the source")
    if current.count("task.delay(COUNTDOWN,")!=1 or current.count("startSession(mode)")!=2:
        raise ValueError("original session startup authority was changed")
    if current.count('Instance.new("BillboardGui")')!=source.count('Instance.new("BillboardGui")'):
        raise ValueError("new GUI detected")
    return current

def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--source",type=Path,required=True)
    ap.add_argument("--out-dir",type=Path,required=True)
    args=ap.parse_args()
    source=args.source.read_text(encoding="utf-8")
    changed=apply(source)
    args.out_dir.mkdir(parents=True,exist_ok=True)
    target=args.out_dir/"EGGRUMBLE_Host_QUEUE_ETA.server.luau"
    target.write_text(changed,encoding="utf-8")
    original_blob=subprocess.check_output(["git","hash-object",str(args.source)],text=True).strip()
    receipt={
        "feature_id":FEATURE_ID,
        "source_blob":original_blob,
        "input_sha256":hashlib.sha256(source.encode()).hexdigest(),
        "output_sha256":hashlib.sha256(changed.encode()).hexdigest(),
        "original_author":UPSTREAM,
        "changed_existing_script_count":1,
        "additional_scripts":0,
        "additional_gui_or_remotes":0,
        "OFF_rollback":"BYTE_EXACT_TO_INPUT_HOST",
        "RC_adopted":False,
        "Studio":"NOT_TESTED",
        "Android":"NOT_TESTED",
    }
    (args.out_dir/"QUEUE_ETA_RECEIPT.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(receipt,ensure_ascii=False))
if __name__=="__main__":
    main()
