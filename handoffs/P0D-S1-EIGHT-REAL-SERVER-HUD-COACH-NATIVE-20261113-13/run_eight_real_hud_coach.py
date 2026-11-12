#!/usr/bin/env python3
"""Authentic eight-safe original S1 Game -> HUD + Coach packet replay in ONE Luau VM.

Existing seven full Game/Map/Config/Rules/Lobby/Trap/Coach real source harness and
the real original eight HUD source run together. Only external Roblox APIs mocked.
Never game-source writes, Roblox Studio, or live network/publish claims.
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

EIGHT = "7b4f95a3f424741bbe8ff1c555c5f5a2ed64d4bd"
SEVEN = "6cc131d3de06fe8799d00f475fc446a526e4b2c4"
SEVEN_QA = "b92372d27c1ed498a06b9135d0931e944bdcd39a"
SEVEN_QA_PATH = "handoffs/P0D-S1-SEVEN-SAFE-REAL-ORDER-CROSS-QA-20261112-08/tools/seven_safe_real_native.py"
SEVEN_QA_BLOB = "da36055e63788fa0af9f9c3830d07a83e56232a6"
HUD_QA = "82847cb97d06394f8fba5ec5c88e644dce0a336b"
HUD_QA_PATH = "handoffs/P0D-S1-HUD-SNAPSHOT-ORDER-20261112-09/tools/check_hud_native.py"
HUD_QA_BLOB = "192fe6051b93e5aa931c824e09e4734e4d4844b7"
ROOT = "releases/P0D_S1_KIDS_RC01/"
GAME = "src/server/Game.server.luau"
COACH = "src/shared/FirstMinuteModel.luau"
HUD = "src/client/HUD.client.luau"
GAME_BLOB = "e684ca79b8f5ed279bcdf033f4118bf77d552abb"
COACH_BLOB = "d8dda6b1781375612c123f8c83b6f23fe45d09f1"
HUD_BLOB = "50823390853989ccdda78e28c16ea4757bbe0715"
PREVIOUS_HUD_BLOB = "b3d3996c40c690e19007a36a847d5b10fc6a1522"
PREVIEW_MANIFEST_SHA256_HUD = "ab9155c3e62522cf32f69ba18a042ff3f32c3e6064e483f48147e8c043edeee8"

def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()

def read(repo: Path, commit: str, file: str, expected: str | None = None) -> bytes:
    p=subprocess.run(["git","-C",str(repo),"show",commit+":"+file],
                     capture_output=True,check=False,timeout=25)
    if p.returncode:
        raise RuntimeError("PINNED_GIT_SOURCE_NOT_FOUND_"+file)
    if expected and git_blob(p.stdout)!=expected:
        raise RuntimeError("PINNED_GIT_BLOB_MISMATCH_"+file)
    return p.stdout

def namespace(script: bytes, label: str) -> dict:
    env={"__name__":"_frozen_original_eight_hud_"+label}
    exec(compile(script.decode("utf8"),label,"exec"),env)
    return env

def exactly(text: str,old: str,new: str,label: str) -> str:
    c=text.count(old)
    if c!=1:
        raise RuntimeError("AMBIGUOUS_"+label+"_COUNT_"+str(c))
    return text.replace(old,new,1)

# Original Game's REAL packet objects are captured immediately after the
# original controller emits them, not reconstructed from synthetic HUD fixtures.
ANCHORS = [
    ('eq(last(pBlue).phase,"LOBBY","blue_lobby")',"lobby"),
    ('eq(last(pBlue).role,"GUARDIAN","role_lobby_allowed")',"guardian"),
    ('eq(last(pRed).phase,"COUNTDOWN","two_player_countdown")',"countdown"),
    ('eq(last(pRed).serial,1,"first_round")',"active"),
    ('eq(last(pRed).carrying,"BLUE","stolen_enemy_egg")',"egg"),
    ('eq(last(pRed).scores.RED,1,"first_score")',"scored"),
    ('eq(last(pRed).phase,"RESULTS","winning_result_phase")',"results"),
    ('eq(last(pRed).serial,2,"new_serial_for_rematch")',"rematch"),
]

HUD_REPLAY = r'''
-- Same ONE native Luau VM as the actual Game and real Guardian Coach modules.
-- All packets are untouched actual server SNAPSHOT messages for the BLUE client.
do
local t=__eightTrace
local function p(k)
    local record=t[k]
    if type(record)~="table" or record.kind~="SNAPSHOT" then
        error("EIGHT_REAL_NO_SERVER_SNAPSHOT_"..k,0)
    end
    return record
end
-- Strict actual server-generated ordinal relationships.
eq(p("lobby").phase,"LOBBY","eight_real_lobby_from_original_game")
eq(p("guardian").role,"GUARDIAN","eight_real_guardian_from_original_game")
eq(p("active").phase,"ACTIVE","eight_real_active_from_original_game")
eq(p("scored").scores.RED,1,"eight_real_red_capture_original_server")
eq(p("results").phase,"RESULTS","eight_real_results_original_server")
eq(p("rematch").serial,2,"eight_real_rematch_original_server")
local order={"lobby","guardian","countdown","active","egg","scored","results","rematch"}
for i=2,#order do
    eq(p(order[i]).updateId>p(order[i-1]).updateId,true,
       "eight_real_server_order_monotonic_"..order[i])
end
end

-- Client Roblox UI external API fakes; exact HUD original Luau is unedited.
do
__HUD_LUAU_SETUP__
__HUD_LOAD_BEGIN__
__REAL_HUD_FULL_SOURCE__
__HUD_LOAD_END__
local service=setupServices()
local app=loadOriginalHud()
local gui=app.gui
local score=gui.children.Score
local status=gui.children.Status
local attack=gui.children.Attack
local trap=gui.children.GuardianTrap
local raider=gui.children.RaiderRole
local guardianButton=gui.children.GuardianRole
local function send(record) service.remote.OnClientEvent:Fire(record) end
local t=__eightTrace

local coach=__real_Coach.new()
local function accept(snapshot,seconds,tag)
    send(snapshot)
    eq(__real_Coach.consume(coach,snapshot,seconds),true,tag)
end

-- First server lobby record, then actual server-side GUARDIAN role choice.
accept(t.lobby,0,"real_client_lobby_coach_accept")
eq(raider.Visible,true,"real_client_lobby_raider_visible")
eq(attack.Visible,false,"real_client_lobby_attack_hidden")
accept(t.guardian,.1,"real_client_guardian_coach_accept")
eq(string.find(score.Text,"守護")~=nil,true,"real_client_guardian_lobby_role")
accept(t.countdown,1,"real_client_countdown_coach_accept")
eq(attack.Visible,false,"real_client_countdown_attack_hidden")
accept(t.active,7,"real_client_active_coach_accept")
eq(attack.Visible,true,"real_client_active_attack_visible")
eq(trap.Visible,true,"real_client_active_guardian_trap_visible")
eq(raider.Visible,false,"real_client_active_role_menu_hidden")
eq(guardianButton.Visible,false,"real_client_active_guardian_role_menu_hidden")
eq(__real_Coach.view(coach,7).title,"守護：卵を守ろう！",
   "real_client_active_guardian_coach_title")
-- An actual previous server lobby packet arrives late AFTER active.
send(t.guardian)
eq(__real_Coach.consume(coach,t.guardian,8),false,
   "real_client_late_guardian_lobby_coach_reject")
eq(trap.Visible,true,"real_client_late_lobby_trap_still_visible")
eq(attack.Visible,true,"real_client_late_lobby_attack_still_visible")
eq(string.find(status.Text,"対戦中")~=nil,true,"real_client_late_lobby_text_not_rolled_back")
accept(t.egg,10,"real_client_egg_event_coach_accept")
accept(t.scored,12,"real_client_real_score_coach_accept")
eq(string.find(score.Text,"🔴 1")~=nil,true,
   "real_client_real_server_red_score_visible")
-- Delayed older genuine same-serial score packet MUST NOT overwrite RED=1.
send(t.egg)
eq(__real_Coach.consume(coach,t.egg,13),false,
   "real_client_late_egg_coach_reject")
eq(string.find(score.Text,"🔴 1")~=nil,true,
   "real_client_real_score_does_not_rollback")
eq(trap.Visible,true,"real_client_guardian_buttons_survive_late_score")
accept(t.results,14,"real_client_real_results_coach_accept")
eq(attack.Visible,false,"real_client_results_attack_hidden")
eq(trap.Visible,false,"real_client_results_trap_hidden")
eq(string.find(status.Text,"次の準備")~=nil,true,
   "real_client_results_rematch_status_visible")
send(t.scored)
eq(__real_Coach.consume(coach,t.scored,15),false,
   "real_client_late_active_after_results_coach_reject")
eq(attack.Visible,false,"real_client_late_active_after_results_hud_reject")
-- Actual server reset changes serial and global updateId, both clients accept.
accept(t.rematch,23,"real_client_rematch_coach_accept")
eq(t.rematch.phase,"ACTIVE","real_client_rematch_active_original")
eq(trap.Visible,true,"real_client_guardian_trap_reenabled_rematch")
eq(attack.Visible,true,"real_client_attack_reenabled_rematch")
send(t.results)
eq(__real_Coach.consume(coach,t.results,24),false,
   "real_client_old_result_new_serial_coach_reject")
eq(trap.Visible,true,"real_client_old_result_new_serial_hud_reject")
eq(coach.serial,2,"real_client_coach_new_serial_kept")
-- GUI sends only an intent, never chosen damage, arbitrary position or loot.
attack.MouseButton1Click:Fire()
trap.MouseButton1Click:Fire()
eq(#service.remote.sent,2,"real_client_two_intents_only")
eq(service.remote.sent[1].action,"ATTACK","real_client_attack_intent")
eq(service.remote.sent[2].action,"PLACE_TRAP","real_client_trap_intent")
eq(service.remote.sent[1].damage,nil,"real_client_no_damage_authority")
eq(service.remote.sent[2].position,nil,"real_client_no_teleport_authority")
eq(service.remote.sent[1].seq,1,"real_client_first_intent_seq")
eq(service.remote.sent[2].seq,2,"real_client_second_intent_seq")
print("P0D_EIGHT_REAL_GAME_COACH_HUD_SAME_VM_PASS assertions="..tostring(count))
end
'''

HUD_MUTANTS = (
    ("hud_accept_old_update",
     "or id <= lastUpdateId then return end",
     "or id < -1 then return end",
     "HUD_S1_ASSERT_real_client_late_lobby_trap_still_visible"),
    ("hud_hide_guardian_trap",
     'trapButton.Visible = s.phase == "ACTIVE" and s.role == "GUARDIAN"',
     "trapButton.Visible = false",
     "HUD_S1_ASSERT_real_client_active_guardian_trap_visible"),
)
GAME_MUTANTS = (
    ("server_ordinal_never_increments",
     "snapshotUpdateId += 1",
     "-- snapshotUpdateId += 1",
     "GAME_S1_ASSERT_real_coach_tracks_first_update_id"),
)

def load(repo: Path):
    upstream=namespace(read(repo,SEVEN_QA,SEVEN_QA_PATH,SEVEN_QA_BLOB),SEVEN_QA_PATH)
    hudmod=namespace(read(repo,HUD_QA,HUD_QA_PATH,HUD_QA_BLOB),HUD_QA_PATH)
    prior,engine,base,sources,coach,order=upstream["prepare_native"](repo)
    game=read(repo,EIGHT,ROOT+GAME,GAME_BLOB).decode("utf8")
    current_coach=read(repo,EIGHT,ROOT+COACH,COACH_BLOB).decode("utf8")
    hud=read(repo,EIGHT,ROOT+HUD,HUD_BLOB).decode("utf8")
    original_hud=read(repo,SEVEN,ROOT+HUD,PREVIOUS_HUD_BLOB)
    if game!=sources["Game"] or current_coach!=coach:
        raise RuntimeError("EIGHT_SERVER_COACH_NOT_EXACT_PRIOR_SEVEN")
    hud_original=read(repo,HUD_QA,hudmod["CANDIDATE"].as_posix(),HUD_BLOB)
    if hud.encode("utf8")!=hud_original:
        raise RuntimeError("EIGHT_HUD_NOT_EXACT_FULL_NATIVE_VETTED_SOURCE")
    baseline=json.loads(read(repo,SEVEN,ROOT+"BUILD_MANIFEST.json"))
    updated=json.loads(read(repo,EIGHT,ROOT+"BUILD_MANIFEST.json"))
    a={row["path"]:row for row in baseline["files"]}
    b={row["path"]:row for row in updated["files"]}
    if len(a)!=37 or len(b)!=37 or set(a)!=set(b):
        raise RuntimeError("EIGHT_MANIFEST_COUNT_CHANGED")
    if {p for p in a if a[p]!=b[p]}!={HUD}:
        raise RuntimeError("EIGHT_MANIFEST_NOT_ONLY_HUD_UPDATED")
    if b[HUD]["sha256"]!=PREVIEW_MANIFEST_SHA256_HUD or b[HUD]["size"]!=9549:
        raise RuntimeError("EIGHT_HUD_UNPINNED_BYTES")
    for row in updated["files"]:
        binary=read(repo,EIGHT,ROOT+row["path"])
        if len(binary)!=row["size"] or hashlib.sha256(binary).hexdigest()!=row["sha256"]:
            raise RuntimeError("EIGHT_37_SOURCE_BAD_SHA_"+row["path"])
    if "local D07_D08_RELEASE_REVIEW_APPROVED = false" not in game:
        raise RuntimeError("OPTIONAL_BOSS_NOT_DISABLED")
    if len(HUD_MUTANTS)!=2 or len(GAME_MUTANTS)!=1:
        raise RuntimeError("UNSAFE_NEGATIVE_TEST_COUNT_CHANGED")
    return prior,engine,base,sources,coach,game,hud,hudmod

def compose(prior,engine,base,sources,coach,hud,hudmod) -> str:
    local=dict(base)
    test=local["LUAU_TEST"]
    for i,(anchor,name) in enumerate(ANCHORS):
        if i==0:
            test=exactly(test,anchor,"local __eightTrace={}\n"+anchor+"\n__eightTrace."+name+"=last(pBlue)","eight_packet_"+name)
        else:
            test=exactly(test,anchor,anchor+"\n__eightTrace."+name+"=last(pBlue)","eight_packet_"+name)
    local["LUAU_TEST"]=test
    composed=prior["compose"](engine,local,sources,coach)
    replay=HUD_REPLAY
    for key,value in [
        ("__HUD_LUAU_SETUP__",hudmod["LUAU_SETUP"]),
        ("__HUD_LOAD_BEGIN__",hudmod["HUD_LOAD_BEGIN"]),
        ("__REAL_HUD_FULL_SOURCE__",hud),
        ("__HUD_LOAD_END__",hudmod["HUD_LOAD_END"]),
    ]:
        replay=exactly(replay,key,value,key)
    return composed+"\n"+replay

def invoke(luau: str, testfile: Path,script: str):
    testfile.write_text(script,encoding="utf8")
    p=subprocess.run([luau,str(testfile)],capture_output=True,text=True,check=False,timeout=55)
    return p.returncode,p.stdout+p.stderr

def execute(repo: Path, luau: str) -> int:
    prior,engine,base,sources,coach,game,hud,hudmod=load(repo)
    with TemporaryDirectory(prefix="p0d_eight_real_game_hud_coach_") as td:
        file=Path(td)/"eight_original_game_hud_coach.luau"
        script=compose(prior,engine,base,sources,coach,hud,hudmod)
        rc,log=invoke(luau,file,script)
        m=re.search(r"P0D_EIGHT_REAL_GAME_COACH_HUD_SAME_VM_PASS assertions=(\d+)",log)
        if rc or not m or int(m.group(1))<35:
            raise RuntimeError("EIGHT_REAL_SERVER_HUD_COACH_POSITIVE_FAILED "+log[-3000:])
        if "P0D_NATIVE_ORIGINAL_GAME_MAP_COMPOSED_PASS" not in log:
            raise RuntimeError("ORIGINAL_GAME_TRACE_DID_NOT_RUN")
        print("P0D_EIGHT_REAL_SERVER_HUD_COACH_SUCCESS assertions="+m.group(1))
        for label,needle,unsafe,marker in HUD_MUTANTS:
            bad_hud=exactly(hud,needle,unsafe,label)
            rc,result=invoke(luau,file,compose(prior,engine,base,sources,coach,bad_hud,hudmod))
            if rc==0 or marker not in result:
                raise RuntimeError("EIGHT_DANGEROUS_CLIENT_MUTANT_NOT_REJECTED_"+label+" "+result[-1400:])
            print("P0D_EIGHT_REAL_HUD_MUTANT_REJECTED "+label)
        for label,needle,unsafe,marker in GAME_MUTANTS:
            mutated=dict(sources)
            mutated["Game"]=exactly(mutated["Game"],needle,unsafe,label)
            rc,result=invoke(luau,file,compose(prior,engine,base,mutated,coach,hud,hudmod))
            if rc==0 or marker not in result:
                raise RuntimeError("EIGHT_DANGEROUS_SERVER_MUTANT_NOT_REJECTED_"+label+" "+result[-1400:])
            print("P0D_EIGHT_REAL_SERVER_MUTANT_REJECTED "+label)
        print("P0D_EIGHT_REAL_SERVER_HUD_COACH_NATIVE_FULL_PASS mutants=3")
    return 0

def selftest():
    assert len(EIGHT)==len(SEVEN)==len(HUD_BLOB)==40
    assert git_blob(b"abc")=="f2ba8f84ab5c1bce84a7b441cb1959cfc709b7f"
    assert len(ANCHORS)==8 and len(HUD_MUTANTS)==2 and len(GAME_MUTANTS)==1
    assert len({x[1] for x in ANCHORS})==8
    assert "P0D_EIGHT_REAL_GAME_COACH_HUD_SAME_VM_PASS" in HUD_REPLAY
    assert "real_client_real_score_does_not_rollback" in HUD_REPLAY
    assert "real_client_old_result_new_serial_hud_reject" in HUD_REPLAY
    assert exactly("abc","b","x","test")=="axc"
    try:exactly("foofoo","foo","bar","neg")
    except RuntimeError:pass
    else:raise AssertionError("UNSAFE_ANCHOR_NOT_REJECTED")
    print("P0D_EIGHT_REAL_HUD_COACH_SELFTEST_PASS checks=9")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo",type=Path)
    p.add_argument("--luau")
    p.add_argument("--selftest",action="store_true")
    p.add_argument("--source-only",action="store_true")
    args=p.parse_args()
    if args.selftest:
        selftest();return 0
    if not args.repo: p.error("--repo is required")
    if args.source_only:
        load(args.repo.resolve())
        print("P0D_EIGHT_REAL_HUD_COACH_37_SOURCE_EXACT_PASS")
        return 0
    if not args.luau: p.error("--luau native CLI is required")
    return execute(args.repo.resolve(),args.luau)

if __name__=="__main__":
    try:
        sys.exit(main())
    except (RuntimeError,AssertionError,ValueError,OSError,UnicodeError,subprocess.TimeoutExpired) as e:
        print("P0D_EIGHT_REAL_SERVER_HUD_COACH_BLOCKED "+str(e),file=sys.stderr)
        sys.exit(2)
