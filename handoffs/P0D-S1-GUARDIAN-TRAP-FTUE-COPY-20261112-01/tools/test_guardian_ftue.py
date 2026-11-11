#!/usr/bin/env python3
"""Original V6 S1 FirstMinuteModel guardian-trap child guidance native Luau QA.

Only string presentation copy and two role-specific view branches are added.
Model authority, state, consume, server, HUD, trap physics and network remain
identical to the current RC. This is NOT Roblox Studio/real phone evidence.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory

RC="1263a03701211a652b99b91d2339575dc8104eff"
ROOT=Path(__file__).resolve().parent.parent
BASE="releases/P0D_S1_KIDS_RC01/"
BLOBS={
 "src/shared/FirstMinuteModel.luau":"fcdc399bf95b6cd0532691718f5a54e8a4fd84b4",
 "src/server/S1TrapRules.luau":"feabd705e4cfa5483d440e506277080f226343ef",
 "src/server/Game.server.luau":"7c5229f600f17537bc1bbbb0b96b6a2435875374",
 "src/client/HUD.client.luau":"ee594fbc34e6bf938518fae32c0642c852f11f9e",
}
PATCHES=[
 ("速攻は足が速い／守護は体力が多い。2人そろうとスタート！",
  "速攻は足が速い／守護は体力が多く、罠を置ける！2人でスタート！"),
 ("自分のお城の卵を守りながら敵を追い返そう。攻撃は右下！",
  "自分の卵を守ろう！右下の罠ボタンで足止め。敵が踏むと足が遅くなるよ！"),
 ('    if elapsed < 32 then\n        return {title = "卵を取ると得点チャンス！", detail = "敵の卵 → 自分の城の納品台。取られたら追いかけよう。", visible = true, tone = "normal"}\n    end',
  '    if elapsed < 32 then\n        if s.role == "GUARDIAN" then\n            return {title = "守護：罠を置こう！", detail = "自分の陣地でTキーか右下の罠ボタンを押そう。敵を足止めできるよ！", visible = true, tone = "normal"}\n        end\n        return {title = "卵を取ると得点チャンス！", detail = "敵の卵 → 自分の城の納品台。取られたら追いかけよう。", visible = true, tone = "normal"}\n    end'),
 ('    return {title = "城を攻める作戦もあるよ", detail = "敵のお城のコアは右下の攻撃で壊せる。まずは卵を探そう！", visible = true, tone = "normal"}',
  '    if s.role == "GUARDIAN" then\n        return {title = "守護：仲間を守ろう！", detail = "罠は自分の陣地で置こう。20秒たてば次の罠！敵の卵も奪えるよ。", visible = true, tone = "normal"}\n    end\n    return {title = "城を攻める作戦もあるよ", detail = "敵のお城のコアは右下の攻撃で壊せる。まずは卵を探そう！", visible = true, tone = "normal"}'),
]
CAND=ROOT/"candidate/src/shared/FirstMinuteModel.luau"
MANIFEST=ROOT/"BUILD_MANIFEST.json"
TEST=r'''
local Coach=__actual_Coach
local count=0
local function eq(actual,expected,label)
 count+=1
 if actual~=expected then
  error("P0D_TRAP_FTUE_ASSERT_"..label.." actual="..tostring(actual)..
      " expected="..tostring(expected),0)
 end
end
local function contains(text,substring,label)
 count+=1
 if type(text)~="string" or not string.find(text,substring,1,true) then
  error("P0D_TRAP_FTUE_ASSERT_"..label.." missing="..substring,0)
 end
end
local function packet(role,phase,serial,t)
 return {
  kind="SNAPSHOT",serial=serial,phase=phase,time=t,
  scores={RED=0,BLUE=0},hp={RED=300,BLUE=300},
  role=role,team=role=="GUARDIAN" and "BLUE" or "RED",
  carrying="",trapRole=role=="GUARDIAN",trapCooldown=0,
  winner="",reason="",redPlayers=1,bluePlayers=1
 }
end
local guard=Coach.new()
local fast=Coach.new()
local function observe(state,p,now)
 eq(Coach.consume(state,p,now),true,"real_valid_snapshot")
 local view=Coach.view(state,now)
 eq(view.visible,true,"visible_during_relevant_phase")
 return view
end
local lobbyGuard=packet("GUARDIAN","LOBBY",0,0)
local lobbyFast=packet("RAIDER","LOBBY",0,0)
local g=observe(guard,lobbyGuard,0)
local f=observe(fast,lobbyFast,0)
eq(g.title,"まず役職をえらぼう","lobby_title_kept")
contains(g.detail,"守護は体力が多く、罠を置ける！","guardian_lobby_trap_described")
eq(g.detail,f.detail,"both_players_same_lobby_help")
g=observe(guard,packet("GUARDIAN","COUNTDOWN",0,7),2)
eq(g.title,"もうすぐ対戦！","guardian_countdown_same")
f=observe(fast,packet("RAIDER","COUNTDOWN",0,7),2)
eq(f.title,"もうすぐ対戦！","raider_countdown_same")
local pG=packet("GUARDIAN","ACTIVE",1,360)
local pR=packet("RAIDER","ACTIVE",1,360)
g=observe(guard,pG,7)
f=observe(fast,pR,7)
eq(guard.serial,1,"guardian_round_one")
eq(fast.serial,1,"raider_round_one")
eq(g.title,"守護：卵を守ろう！","original_guardian_first_title_preserved")
contains(g.detail,"右下の罠ボタン","guardian_first_right_button")
contains(g.detail,"足が遅くなる","guardian_first_slows_enemy")
eq(f.title,"敵のお城の卵をねらおう！","raider_first_same")
eq(f.detail,"移動して敵の卵に近づこう。出たボタンをタップして取れるよ。","raider_first_description_same")
for _,elapsed in ipairs({0,11.99}) do
 g=observe(guard,pG,7+elapsed)
 f=observe(fast,pR,7+elapsed)
 eq(g.title,"守護：卵を守ろう！","guardian_0_to_12")
 eq(f.title,"敵のお城の卵をねらおう！","raider_0_to_12")
end
for _,elapsed in ipairs({12,17,31.99}) do
 g=observe(guard,pG,7+elapsed)
 f=observe(fast,pR,7+elapsed)
 eq(g.title,"守護：罠を置こう！","guardian_12_to_32")
 contains(g.detail,"自分の陣地で","guardian_own_area_only")
 contains(g.detail,"Tキー","guardian_keyboard_help")
 contains(g.detail,"右下の罠ボタン","guardian_touch_help")
 eq(f.title,"卵を取ると得点チャンス！","raider_12_to_32_preserved")
end
for _,elapsed in ipairs({32,45,60}) do
 g=observe(guard,pG,7+elapsed)
 f=observe(fast,pR,7+elapsed)
 eq(g.title,"守護：仲間を守ろう！","guardian_32_to_60")
 contains(g.detail,"20秒","accurate_guardian_cooldown")
 contains(g.detail,"自分の陣地で","late_own_side_only")
 eq(f.title,"城を攻める作戦もあるよ","raider_32_to_60_preserved")
end
eq(Coach.view(guard,67.01).visible,false,"guardian_auto_hide_after_60")
eq(Coach.view(fast,67.01).visible,false,"raider_auto_hide_after_60")
Coach.setHidden(guard,false)
g=Coach.view(guard,68)
eq(g.visible,true,"manual_help_after_60")
eq(g.title,"守護：仲間を守ろう！","manual_late_guardian_help")
Coach.setHidden(guard,true)
eq(Coach.view(guard,68).visible,false,"close_trap_help")
Coach.setHidden(guard,false)
eq(Coach.view(guard,68).visible,true,"reopen_trap_help")
-- carrying/scored always outrank optional Guardian trap information
local carrying=packet("GUARDIAN","ACTIVE",1,280)
carrying.carrying="RED"
g=observe(guard,carrying,69)
eq(g.title,"卵をゲット！","guardian_carrying_priority")
eq(g.detail,"自分の色のお城へ！ 光る納品台に近づいてタップ。","original_carry_detail_kept")
local score=packet("GUARDIAN","ACTIVE",1,275)
score.scores.BLUE=1
g=observe(guard,score,70)
eq(g.title,"得点できたね！","guardian_scored_priority")
eq(g.tone,"success","score_success_tone")
local results=packet("GUARDIAN","RESULTS",1,9)
results.winner="BLUE";results.reason="EGG_CAPTURE"
g=observe(guard,results,75)
eq(g.title,"つぎの対戦も挑戦しよう！","result_rematch_help_preserved")
eq(g.detail,"数秒後に自動で再戦。もう一度卵を運んでみよう！","result_copy_unchanged")
g=observe(guard,packet("GUARDIAN","LOBBY",1,0),84)
eq(g.title,"まず役職をえらぼう","return_lobby_help")
g=observe(guard,packet("GUARDIAN","COUNTDOWN",2,7),85)
eq(guard.serial,2,"serial_reset_on_next_round")
g=observe(guard,packet("GUARDIAN","ACTIVE",2,360),92)
eq(guard.scored,false,"score_reset_on_round2")
eq(guard.carried,false,"carry_reset_on_round2")
eq(guard.activeAt,92,"active_epoch_reset_round2")
eq(g.title,"守護：卵を守ろう！","guardian_new_round_first_help")
local latest=guard.latest
eq(Coach.consume(guard,results,93),false,"old_result_replay_rejected")
eq(guard.latest,latest,"stale_snapshot_no_overwrite")
local bad=packet("HACKER","ACTIVE",2,350)
eq(Coach.consume(guard,bad,93),false,"malformed_role_rejected")
bad=packet("GUARDIAN","ACTIVE",0/0,350)
eq(Coach.consume(guard,bad,93),false,"nan_serial_rejected")
bad=packet("GUARDIAN","ACTIVE",2,350)
bad.carrying="FORGED_EGG"
eq(Coach.consume(guard,bad,93),false,"forged_egg_rejected")
eq(guard.latest,latest,"bad_packets_preserve_true_state")
if count<110 then error("P0D_TRAP_FTUE_TOO_FEW_ASSERTIONS "..count,0) end
print("P0D_REAL_V6_GUARDIAN_FTUE_LUAU_PASS assertions="..count)
'''
MUTATIONS=[
 ("guardian_tutorial_missing",
  "右下の罠ボタンで足止め","右下の攻撃ボタンで攻撃",
  "P0D_TRAP_FTUE_ASSERT_guardian_first_right_button"),
 ("guardian_mid_absent",
  'if s.role == "GUARDIAN" then\n            return {title = "守護：罠を置こう！"',
  'if false then\n            return {title = "守護：罠を置こう！"',
  "P0D_TRAP_FTUE_ASSERT_guardian_12_to_32"),
 ("wrong_cooldown_copy","20秒たてば次の罠","10秒たてば次の罠",
  "P0D_TRAP_FTUE_ASSERT_accurate_guardian_cooldown"),
 ("wrong_trap_placement_copy","罠は自分の陣地で置こう","罠は敵の陣地で置こう",
  "P0D_TRAP_FTUE_ASSERT_late_own_side_only"),
 ("raider_trap_only","卵を取ると得点チャンス！","罠を置くと得点チャンス！",
  "P0D_TRAP_FTUE_ASSERT_raider_12_to_32_preserved"),
 ("stale_result_accepted","packet.serial < state.serial","false",
  "P0D_TRAP_FTUE_ASSERT_old_result_replay_rejected"),
 ("score_priority_missing","if state.scored then","if false then",
  "P0D_TRAP_FTUE_ASSERT_guardian_scored_priority"),
 ("hide_help_disabled","state.dismissed = hidden","state.dismissed = false",
  "P0D_TRAP_FTUE_ASSERT_close_trap_help"),
]

def assertok(flag,msg):
 if not flag: raise RuntimeError(msg)

def blobsha(b):
 return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def frozen(repo):
 out={}
 for path,sha in BLOBS.items():
  p=subprocess.run(["git","-C",repo,"show",RC+":"+BASE+path],
   capture_output=True,check=False,timeout=30)
  assertok(p.returncode==0,"CURRENT_RC_MISSING_"+path)
  assertok(blobsha(p.stdout)==sha,"CURRENT_RC_SOURCE_DRIFT_"+path)
  out[path]=p.stdout.decode("utf8")
 return out

def patch(original):
 s=original
 for old,new in PATCHES:
  assertok(s.count(old)==1,"COPY_PATCH_NONUNIQUE_"+old[:30])
  s=s.replace(old,new,1)
 return s

def contract(repo):
 sources=frozen(repo)
 model=sources["src/shared/FirstMinuteModel.luau"]
 candidate=(ROOT/"candidate/src/shared/FirstMinuteModel.luau").read_text("utf8")
 assertok(candidate==patch(model),"CANDIDATE_CHANGED_MODEL_LOGIC_NOT_ONLY_COPY")
 assertok(candidate.count('function Coach.consume(')==1 and
   candidate.count('function Coach.view(')==1 and
   'Instance.new("RemoteEvent")' not in candidate and
   "FireServer" not in candidate and
   "DataStore" not in candidate,
   "CAN_NOT_ADD_GAME_AUTHORITY_TO_COACH")
 rules=sources["src/server/S1TrapRules.luau"]
 server=sources["src/server/Game.server.luau"]
 hud=sources["src/client/HUD.client.luau"]
 for tok in ("TrapRules.COOLDOWN = 20","s.role ~= \"GUARDIAN\"",
             "TrapRules.SLOW_SECONDS = 3","TrapRules.SLOW_RATIO = 0.55"):
  assertok(tok in rules,"COPY_NOT_MATCHING_ACTUAL_TRAP_RULE_"+tok)
 for tok in ('data.action == "PLACE_TRAP"','trapCooldown = math.max(',
             'trapRole = (roles[player] or "RAIDER") == "GUARDIAN"'):
  assertok(tok in server,"ACTUAL_SERVER_TRAP_WIRING_MISSING_"+tok)
 for tok in ('"GuardianTrap"','action("PLACE_TRAP", nil)',
             "s.role == \"GUARDIAN\"","Enum.KeyCode.T"):
  assertok(tok in hud,"ACTUAL_HUD_TAP_KEY_BINDING_MISSING_"+tok)
 print("P0D_TRAP_FTUE_SOURCE_EXACT_4_PRESENTATION_PATCHES_PASS")
 print("P0D_TRAP_FTUE_REAL_RC_TRAP_GAME_HUD_RULES_4_BLOBS_PASS")
 return candidate

def check_manifest():
 obj=json.loads((ROOT/"BUILD_MANIFEST.json").read_text("utf8"))
 assertok(set(obj)=={"format","game_id","work_id","packet_id",
                    "public_source_allowed","files"},"MANIFEST_BAD_SCHEMA")
 assertok(obj["format"]=="P0D_PUBLIC_SOURCE_V1"
   and obj["game_id"]=="TRAP_RAIDERS" and obj["work_id"]=="p0d-siege-v19"
   and obj["packet_id"]=="P0D-S1-GUARDIAN-TRAP-FTUE-COPY-20261112-01"
   and obj["public_source_allowed"] is True,"MANIFEST_WRONG_PACKET")
 expected={
  "candidate/src/shared/FirstMinuteModel.luau",
  "tools/test_guardian_ftue.py",
  "README.md"
 }
 assertok(type(obj["files"]) is list and len(obj["files"])==3,"MANIFEST_BAD_SIZE")
 seen=set()
 for entry in obj["files"]:
  assertok(type(entry) is dict and set(entry)=={"path","sha256","size"},
           "MANIFEST_BAD_RECORD")
  path=entry["path"]
  assertok(type(path) is str and path in expected and path not in seen,
           "MANIFEST_UNEXPECTED_PATH")
  b=(ROOT/path).read_bytes()
  assertok(type(entry["size"]) is int and entry["size"]==len(b) and
           type(entry["sha256"]) is str and
           hashlib.sha256(b).hexdigest()==entry["sha256"],
           "MANIFEST_BYTE_HASH_MISMATCH_"+path)
  seen.add(path)
 assertok(seen==expected,"MANIFEST_MISSING_SOURCE")
 print("P0D_TRAP_FTUE_KEYLESS_MANIFEST_PASS files=3/3")

def actual_run(luau,module):
 code="local __actual_Coach=(function()\n"+module+"\nend)()\n"+TEST
 with TemporaryDirectory(prefix="p0d_guardian_ftue_") as folder:
  p=Path(folder)/"guardian_ftue_native.luau"
  p.write_text(code,"utf8")
  result=subprocess.run([luau,str(p)],capture_output=True,text=True,
                        check=False,timeout=30)
  return result.returncode,result.stdout+result.stderr

def main():
 parser=argparse.ArgumentParser()
 parser.add_argument("--repo",required=True)
 parser.add_argument("--luau",required=True)
 opts=parser.parse_args()
 check_manifest()
 candidate=contract(opts.repo)
 status,out=actual_run(opts.luau,candidate)
 m=re.search(r"P0D_REAL_V6_GUARDIAN_FTUE_LUAU_PASS assertions=(\d+)",out)
 assertok(status==0 and m is not None and int(m.group(1))>=110,
          "NATIVE_V6_FTUE_REAL_CODE_FAILED_"+out[-1300:])
 print(m.group(0))
 for name,anchor,repl,expected in MUTATIONS:
  assertok(candidate.count(anchor)==1,"NEGATIVE_ANCHOR_NOT_UNIQUE_"+name)
  bad=candidate.replace(anchor,repl,1)
  rc,out=actual_run(opts.luau,bad)
  assertok(rc!=0 and expected in out,
           "UNSAFE_MODEL_COPY_MUTATION_NOT_REJECTED_"+name+"_"+out[-400:])
  print("P0D_GUARDIAN_FTUE_NEGATIVE_REJECTED "+name)
 try:
  original=frozen(opts.repo)["src/shared/FirstMinuteModel.luau"]
  contract_fake=candidate.replace("state.dismissed = hidden",
                                  "state.dismissed = false",1)
  assertok(contract_fake==patch(original),"UNAUTHORIZED_MODEL_STATE_NOT_BLOCKED")
 except RuntimeError:
  print("P0D_GUARDIAN_FTUE_NEGATIVE_REJECTED state_source_diff")
 else:
  raise RuntimeError("UNAUTHORIZED_COACH_STATE_SOURCE_MUTATION_ACCEPTED")
 print("P0D_GUARDIAN_FTUE_NEGATIVE_CONTROLS=9/9")
 print("P0D_GUARDIAN_FTUE_COPY_NATIVE_QA_PASS_NO_STUDIO")
 return 0

if __name__=="__main__":
 try:sys.exit(main())
 except (RuntimeError,ValueError,UnicodeError,OSError,subprocess.TimeoutExpired) as exc:
  print("P0D_GUARDIAN_FTUE_NATIVE_BLOCKED "+str(exc),file=sys.stderr)
  sys.exit(1)
