#!/usr/bin/env python3
"""Native ORIGINAL Game.server => actual FirstMinuteModel cross-module FTUE replay.

The true S1 Game.server emits all SNAPSHOT tables. The real, unmodified
FirstMinuteModel consumes each. Only Roblox host services/MapBuilder are mocks.
NOT a Roblox Studio, two-client networking or phone visual-play test.
"""
import argparse
import hashlib
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory

import native_actual_game_lifecycle_gate as original_game

RC="5dc6c958ea5549b1e859d6d250e6179e731181fb"
MODEL_PATH="releases/P0D_S1_KIDS_RC01/src/shared/FirstMinuteModel.luau"
MODEL_BLOB="fcdc399bf95b6cd0532691718f5a54e8a4fd84b4"

TESTS=r'''
local Coach=__actual_first_minute_model
local assertions=0
local function eq(a,b,id)
 assertions+=1
 if a~=b then error("FTUE_INTEGRATED_ASSERT_"..id.." got="..tostring(a).." want="..tostring(b),0) end
end
local function fresh(player,model,now)
 eq(Coach.consume(model,player.last,now),true,"accept_actual_snapshot")
 return Coach.view(model,now)
end
local function move(p,pos) p.Character.root.Position=pos end
local function steal(p,team)
 arena.teams[team].eggPrompt.Triggered:Fire(p)
end
local function score(p,team)
 arena.teams[team].scorePrompt.Triggered:Fire(p)
end
local red=Coach.new()
local blue=Coach.new()
local older=nil
local latest=nil
eq(#remotes,1,"single_real_game_remote")
eq(#rootTasks,1,"one_real_game_clock_owner")
eq(pRed.Team.Name,"RED","red_team")
eq(pBlue.Team.Name,"BLUE","blue_team")
local view=fresh(pRed,red,0)
eq(view.title,"まず役職をえらぼう","real_join_lobby_help")
eq(view.visible,true,"lobby_help_visible")
eq(red.serial,0,"lobby_serial_zero")
eq(red.activeAt,nil,"lobby_not_active")
send(pBlue,"ROLE",1,{role="GUARDIAN"})
view=fresh(pBlue,blue,0)
eq(view.title,"まず役職をえらぼう","guardian_lobby_help")
eq(blue.latest.role,"GUARDIAN","native_snapshot_role")
tick(0)
view=fresh(pRed,red,0)
eq(view.title,"もうすぐ対戦！","real_countdown_message")
eq(view.tone,"normal","countdown_normal")
view=fresh(pBlue,blue,0)
eq(view.title,"もうすぐ対戦！","second_player_countdown")
tick(6.99)
view=fresh(pRed,red,6.99)
eq(view.title,"もうすぐ対戦！","countdown_before_deadline")
tick(7)
view=fresh(pRed,red,7)
eq(view.title,"敵のお城の卵をねらおう！","raider_first_12_sec")
eq(red.activeAt,7,"actual_active_epoch")
eq(red.serial,1,"real_game_round_epoch")
eq(red.initialScore,0,"initial_real_score")
view=fresh(pBlue,blue,7)
eq(view.title,"守護：卵を守ろう！","guardian_role_first_12_sec")
eq(blue.activeAt,7,"guardian_independent_epoch")
local boundaries={
 {elapsed=0,want="敵のお城の卵をねらおう！"},
 {elapsed=11.99,want="敵のお城の卵をねらおう！"},
 {elapsed=12,want="卵を取ると得点チャンス！"},
 {elapsed=31.99,want="卵を取ると得点チャンス！"},
 {elapsed=32,want="城を攻める作戦もあるよ"},
 {elapsed=59.99,want="城を攻める作戦もあるよ"},
 {elapsed=60,want="城を攻める作戦もあるよ"}
}
for _,case in ipairs(boundaries) do
 local t=7+case.elapsed
 tick(t)
 view=fresh(pRed,red,t)
 eq(view.title,case.want,"tuned_guide_boundary_"..tostring(case.elapsed))
 eq(view.visible,true,"visible_through_60_"..tostring(case.elapsed))
 eq(red.scored,false,"no_fake_score_"..tostring(case.elapsed))
end
tick(67.01)
view=fresh(pRed,red,67.01)
eq(view.visible,false,"auto_hide_after_60")
eq(view.title,"","expired_help_empty")
eq(red.manualHelp,false,"normal_help_not_manual")
Coach.setHidden(red,false)
view=Coach.view(red,67.01)
eq(view.visible,true,"manual_reopen_after_60")
eq(red.manualHelp,true,"manual_help_mode_enabled")
eq(view.title,"城を攻める作戦もあるよ","manual_restore_climax")
Coach.setHidden(red,true)
view=Coach.view(red,67.01)
eq(view.visible,false,"close_help_dismisses")
eq(red.dismissed,true,"dismissal_state")
Coach.setHidden(red,false)
eq(Coach.view(red,67.01).visible,true,"help_reopen_after_close")
-- A real GAME-owned egg prompt modifies the authentic outbound server SNAPSHOT.
tick(68)
move(pRed,arena.teams.BLUE.egg.Position)
steal(pRed,"BLUE")
view=fresh(pRed,red,68)
eq(red.carried,true,"real_server_egg_owned")
eq(red.latest.carrying,"BLUE","no_invented_carried_egg")
eq(view.title,"卵をゲット！","actual_carried_egg_tutorial")
eq(view.tone,"success","egg_success_tone")
move(pRed,arena.teams.RED.scorePad.Position)
score(pRed,"RED")
view=fresh(pRed,red,68)
eq(red.latest.scores.RED,1,"real_server_score_one")
eq(red.scored,true,"real_first_score_seen")
eq(view.title,"得点できたね！","scored_guide_visible")
eq(view.tone,"success","scored_tone")
-- Own genuine game scores again; RESULTS copy and actual model must agree.
move(pRed,arena.teams.BLUE.egg.Position)
steal(pRed,"BLUE")
view=fresh(pRed,red,68)
eq(view.title,"卵をゲット！","second_legit_egg")
move(pRed,arena.teams.RED.scorePad.Position)
score(pRed,"RED")
view=fresh(pRed,red,68)
eq(red.latest.phase,"RESULTS","genuine_game_results")
eq(red.latest.winner,"RED","real_winner")
eq(red.latest.reason,"EGG_CAPTURE","real_win_reason")
eq(view.title,"つぎの対戦も挑戦しよう！","result_rematch_guide")
eq(view.tone,"success","results_tone")
view=fresh(pBlue,blue,68)
eq(view.title,"つぎの対戦も挑戦しよう！","losing_client_result_help")
eq(blue.latest.winner,"RED","other_client_same_winner")
-- RESULT remains 9s, then server-owned lobby/new round. No client starts one.
tick(76.99)
view=fresh(pRed,red,76.99)
eq(view.title,"つぎの対戦も挑戦しよう！","results_not_early")
older=red.latest
tick(77)
view=fresh(pRed,red,77)
eq(view.title,"まず役職をえらぼう","lobby_after_result")
tick(77.1)
view=fresh(pRed,red,77.1)
eq(view.title,"もうすぐ対戦！","second_round_countdown")
tick(84.1)
view=fresh(pRed,red,84.1)
eq(red.serial,2,"second_round_serial_reset")
eq(red.initialScore,0,"round2_initial_score_zero")
eq(red.scored,false,"round2_previous_score_not_carried")
eq(red.carried,false,"round2_previous_egg_not_carried")
eq(red.activeAt,84.1,"round2_epoch_origin")
eq(view.title,"敵のお城の卵をねらおう！","round2_first_12_seconds")
view=fresh(pBlue,blue,84.1)
eq(blue.serial,2,"other_client_epoch_reset")
eq(view.title,"守護：卵を守ろう！","guardian_round2_guide")
latest=red.latest
eq(Coach.consume(red,older,84.2),false,"stale_snapshot_rejected")
eq(red.latest,latest,"stale_packet_does_not_rewrite_latest")
eq(red.serial,2,"stale_never_rewinds_serial")
-- Genuine game sent no such invalid input: attacker-provided fake UI snapshot
-- may never override accurate role/score/carry/phase in help memory.
local function clone(t)
 local n={}
 for k,v in pairs(t) do n[k]=v end
 return n
end
local bad=clone(latest);bad.role="HACKER"
eq(Coach.consume(red,bad,85),false,"bad_role_rejected")
bad=clone(latest);bad.carrying="FAKE_EGG"
eq(Coach.consume(red,bad,85),false,"bad_carry_rejected")
bad=clone(latest);bad.serial=0/0
eq(Coach.consume(red,bad,85),false,"nan_serial_rejected")
bad=clone(latest);bad.scores={RED=1e30,BLUE=0}
eq(Coach.consume(red,bad,85),false,"out_of_range_score_rejected")
bad=clone(latest);bad.time=-1
eq(Coach.consume(red,bad,85),false,"negative_time_rejected")
bad=clone(latest);bad.phase="PAID_GODMODE"
eq(Coach.consume(red,bad,85),false,"unknown_phase_rejected")
bad=clone(latest);bad.kind="BOSS_VISUAL"
eq(Coach.consume(red,bad,85),false,"boss_visual_not_snapshot")
eq(Coach.consume(red,latest,0/0),false,"nan_local_clock_rejected")
eq(red.latest,latest,"invalid_packets_do_not_replace_real_snapshot")
eq(red.activeAt,84.1,"bad_packets_cannot_advance_tutorial")
if assertions<85 then error("FTUE_INSUFFICIENT_ASSERTIONS "..tostring(assertions),0) end
print("P0D_ACTUAL_GAME_FTUE_NATIVE_INTEGRATION_PASS assertions="..assertions)
'''
MUTATIONS=[
 ("accept_stale_snapshot",'packet.serial < state.serial','false','FTUE_INTEGRATED_ASSERT_stale_snapshot_rejected'),
 ("defeat_auto_hide",'if elapsed > 60 and not state.manualHelp then','if false then','FTUE_INTEGRATED_ASSERT_auto_hide_after_60'),
 ("skip_scored_milestone",'if own > state.initialScore then state.scored = true end','if false then state.scored = true end','FTUE_INTEGRATED_ASSERT_real_first_score_seen'),
 ("ignore_guardian_role",'if s.role == "GUARDIAN" then','if false then','FTUE_INTEGRATED_ASSERT_guardian_role_first_12_sec'),
 ("never_hide_manual",'state.dismissed = hidden','state.dismissed = false','FTUE_INTEGRATED_ASSERT_close_help_dismisses'),
]
def verified_model(repo):
 p=subprocess.run(["git","-C",repo,"show",RC+":"+MODEL_PATH],capture_output=True,check=False)
 if p.returncode: raise RuntimeError("OFFICIAL_RC_MODEL_UNAVAILABLE")
 raw=p.stdout
 sha=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
 if sha!=MODEL_BLOB: raise RuntimeError("OFFICIAL_MODEL_BLOB_NOT_PINNED "+sha)
 return raw.decode("utf8")

def build(real_game,model):
 raw=original_game.build(real_game)
 if raw.count(original_game.LUAU_TEST)!=1:
  raise RuntimeError("NATIVE_GAME_HARNESS_NOT_UNIQUE")
 coach=original_game.wrap("__actual_first_minute_model",model)
 return raw.replace(original_game.LUAU_TEST,coach+TESTS,1)

def run(luau,path,game,model):
 path.write_text(build(game,model),encoding="utf8")
 p=subprocess.run([luau,str(path)],capture_output=True,text=True,check=False,timeout=30)
 return p.returncode,p.stdout+p.stderr

def main():
 parser=argparse.ArgumentParser()
 parser.add_argument("--repo",required=True)
 parser.add_argument("--luau",required=True)
 args=parser.parse_args()
 game=original_game.original(args.repo)
 model=verified_model(args.repo)
 with TemporaryDirectory(prefix="p0d_real_ftue_") as d:
  path=Path(d)/"real_game_ftue.luau"
  status,out=run(args.luau,path,game,model)
  m=re.search(r"P0D_ACTUAL_GAME_FTUE_NATIVE_INTEGRATION_PASS assertions=(\d+)",out)
  if status!=0 or not m or int(m.group(1))<85:
   raise RuntimeError("REAL_GAME_FTUE_FAILED "+out[-1100:])
  print(m.group(0))
  for name,old,new,expected in MUTATIONS:
   if model.count(old)!=1:
    raise RuntimeError("AMBIGUOUS_MUTATION "+name+" count="+str(model.count(old)))
   altered=model.replace(old,new,1)
   status,fail=run(args.luau,path,game,altered)
   if status==0 or expected not in fail:
    raise RuntimeError("UNDETECTED_MODEL_MUTATION "+name+" "+fail[-300:])
   print("FTUE_ORIGINAL_MODEL_MUTATION_REJECTED "+name)
  print("P0D_ACTUAL_GAME_FTUE_NEGATIVE_CONTROLS="+str(len(MUTATIONS)))
  print("P0D_OFFICIAL_RC_GAME_AND_FTUE_NATIVE_SUCCESS")
 return 0

if __name__=="__main__":
 try: sys.exit(main())
 except (OSError,UnicodeError,RuntimeError,subprocess.TimeoutExpired) as exc:
  print("P0D_NATIVE_GAME_FTUE_BLOCKED "+str(exc),file=sys.stderr)
  sys.exit(1)
