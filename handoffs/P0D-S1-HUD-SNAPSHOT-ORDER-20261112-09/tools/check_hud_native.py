#!/usr/bin/env python3
"""Exact original P0D S1 seven-safe HUD client Luau native functional replay QA.

Runs the ENTIRE HUD original source with only Roblox external Instances/events
faked. It is not a physical Roblox Studio, GUI rendering, latency, or phone QA.
Source and full bytes are frozen with real Git blobs; mutations alter only a
temporary test copy. No protected official RC or other owner branch changes.
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory

PARENT = "6cc131d3de06fe8799d00f475fc446a526e4b2c4"
BASE_HUD = "releases/P0D_S1_KIDS_RC01/src/client/HUD.client.luau"
BASE_HUD_BLOB = "b3d3996c40c690e19007a36a847d5b10fc6a1522"
BASE_GAME = "releases/P0D_S1_KIDS_RC01/src/server/Game.server.luau"
BASE_GAME_BLOB = "e684ca79b8f5ed279bcdf033f4118bf77d552abb"
ROOT = Path("handoffs/P0D-S1-HUD-SNAPSHOT-ORDER-20261112-09")
CANDIDATE = ROOT / "candidate/src/client/HUD.client.luau"
CANDIDATE_BLOB = "50823390853989ccdda78e28c16ea4757bbe0715"

PATCHES = [
    (
        "local lastSerial = -1\nlocal bossVisual:",
        "local lastSerial = -1\n"
        "local lastUpdateId = -1 -- never reset between rounds; view-only HUD ordering\n"
        "local bossVisual:",
    ),
    (
        '    if type(s.serial) ~= "number" or s.serial < lastSerial then return end\n'
        '    if type(s.scores) ~= "table" or type(s.hp) ~= "table" then return end',
        '    if type(s.serial) ~= "number" or s.serial < lastSerial then return end\n'
        '    -- Same-round stale SNAPSHOTs must never roll back score, phase or buttons.\n'
        '    -- Use the same numeric and legacy-upgrade policy as FirstMinuteModel.\n'
        '    local id = s.updateId\n'
        '    if id ~= nil then\n'
        '        if type(id) ~= "number" or id ~= id or id < 0\n'
        '            or id > 1000000000 or id % 1 ~= 0\n'
        '            or id <= lastUpdateId then return end\n'
        '    elseif lastUpdateId >= 0 then\n'
        '        return\n'
        '    end\n'
        '    if type(s.scores) ~= "table" or type(s.hp) ~= "table" then return end',
    ),
    (
        '    lastSerial = s.serial\n    top.Text = string.format(',
        '    lastSerial = s.serial\n'
        '    if id ~= nil then lastUpdateId = id end\n'
        '    top.Text = string.format(',
    ),
]
MUTANTS = [
    ("ignore_update_id", "local id = s.updateId",
     "local id = nil", "HUD_S1_ASSERT_late_same_serial_role_rejected"),
    ("allow_duplicate", "id <= lastUpdateId then return end",
     "id < lastUpdateId then return end", "HUD_S1_ASSERT_duplicate_snapshot_rejected"),
    ("allow_fractional", "or id > 1000000000 or id % 1 ~= 0",
     "or id > 1000000000 or false", "HUD_S1_ASSERT_fractional_update_id_rejected"),
    ("allow_legacy_downgrade", "elseif lastUpdateId >= 0 then",
     "elseif false then", "HUD_S1_ASSERT_unversioned_after_upgrade_rejected"),
    ("reset_id_each_new_serial", "if id ~= nil then lastUpdateId = id end",
     "if id ~= nil then lastUpdateId = id end\n"
     "    if s.serial > lastSerial then lastUpdateId = -1 end",
     "HUD_S1_ASSERT_old_cross_round_update_id_rejected"),
    ("allow_same_round_old_results", "id <= lastUpdateId then return end",
     "id < -1 then return end", "HUD_S1_ASSERT_late_same_serial_role_rejected"),
]

LUAU_SETUP = r'''
local count=0
local function eq(actual,expected,label)
    count+=1
    if actual~=expected then
        error("HUD_S1_ASSERT_"..label..
              " EXPECTED="..tostring(expected).." GOT="..tostring(actual),0)
    end
end
local function evt()
    local subscribers={}
    return {
        Connect=function(self,callback) subscribers[#subscribers+1]=callback end,
        Fire=function(self,...)
            for _,f in ipairs(subscribers) do f(...) end
        end,
    }
end
local function object(class)
    local t={children={},ClassName=class}
    setmetatable(t,{
        __index=function(self,key)
            if key=="WaitForChild" then
                return function(owner,name)
                    local found=owner.children[name]
                    if found==nil then error("MISSING_ROBLOX_SERVICE_CHILD "..name) end
                    return found
                end
            end
            return self.children[key]
        end,
        __newindex=function(self,key,value)
            rawset(self,key,value)
            if key=="Parent" and value then
                value.children[self.Name or class]=self
            end
        end,
    })
    if class=="TextButton" then t.MouseButton1Click=evt() end
    return t
end
Instance = {new=object}
Color3 = {new=function(...)return {...}end,fromRGB=function(...)return {...}end}
UDim2={new=function(...)return {...}end,fromOffset=function(...)return {...}end}
UDim={new=function(...)return {...}end}
Vector2={new=function(...)return {...}end}
Enum={
    ZIndexBehavior={Sibling="Sibling"},
    Font={GothamBold="GothamBold"},
    KeyCode={F="F",T="T"},
}
local game
local workspace={GetServerTimeNow=function()return 25 end}
local function setupServices()
    local player=object("Player")
    local pg=object("PlayerGui");pg.Name="PlayerGui";pg.Parent=player
    local players={LocalPlayer=player}
    local remote=object("RemoteEvent")
    remote.Name="TrapRaidersS1Remote"
    remote.sent={}
    remote.OnClientEvent=evt()
    remote.FireServer=function(self,payload)
        self.sent[#self.sent+1]=payload
    end
    local rs=object("ReplicatedStorage")
    remote.Parent=rs
    local uis={InputBegan=evt()}
    game={GetService=function(_,name)
        if name=="Players" then return players end
        if name=="ReplicatedStorage" then return rs end
        if name=="UserInputService" then return uis end
        error("UNKNOWN_ROBLOX_SERVICE "..name)
    end}
    return {player=player,remote=remote,uis=uis}
end
'''

LUAU_TESTS = r'''
local service=setupServices()
local app=loadOriginalHud()
local gui=app.gui
local score=gui.children.Score
local status=gui.children.Status
local attack=gui.children.Attack
local trap=gui.children.GuardianTrap
local raider=gui.children.RaiderRole
local guardian=gui.children.GuardianRole
local function send(packet)
    service.remote.OnClientEvent:Fire(packet)
end
local function snapshot(serial,id,phase,role,ownScore,carry)
    return {
        kind="SNAPSHOT",serial=serial,updateId=id,phase=phase,
        team="BLUE",role=role,scores={RED=0,BLUE=ownScore},
        hp={RED=300,BLUE=300},redPlayers=1,bluePlayers=1,
        carrying=carry or "",time=200,alarm="IDLE",alarmTime=0,trapCooldown=0,
        winner=if phase=="RESULTS" then "BLUE" else "",
        reason=if phase=="RESULTS" then "EGG_CAPTURE" else "",
    }
end
-- First valid server packet and role menu.
send(snapshot(0,1,"LOBBY","RAIDER",0))
eq(raider.Visible,true,"initial_lobby_raider_button")
eq(guardian.Visible,true,"initial_lobby_guardian_button")
eq(attack.Visible,false,"initial_lobby_attack_hidden")
eq(trap.Visible,false,"initial_lobby_trap_hidden")
eq(string.find(status.Text,"準備中")~=nil,true,"initial_lobby_copy")
-- Same-round role and attacking HUD updates, from a current Game SNAPSHOT.
local current=snapshot(1,5,"ACTIVE","GUARDIAN",0)
send(current)
eq(attack.Visible,true,"active_attack_visible")
eq(trap.Visible,true,"active_guardian_trap_visible")
eq(raider.Visible,false,"active_role_selection_hidden")
eq(string.find(score.Text,"守護")~=nil,true,"active_guardian_score")
-- The same round's delayed old phase/role must not turn guardian trap off.
local old=snapshot(1,4,"LOBBY","RAIDER",0)
send(old)
eq(attack.Visible,true,"late_same_serial_attack_preserved")
eq(trap.Visible,true,"late_same_serial_role_rejected")
eq(string.find(status.Text,"対戦中")~=nil,true,"late_same_serial_copy_preserved")
-- Same ID replay must not reset the role/buttons even if phase changes.
send(snapshot(1,5,"LOBBY","RAIDER",0))
eq(trap.Visible,true,"duplicate_snapshot_rejected")
-- Demonstrate the real HUD is still submitting intent-only payloads.
attack.MouseButton1Click:Fire()
trap.MouseButton1Click:Fire()
eq(#service.remote.sent,2,"intent_only_remote_twice")
eq(service.remote.sent[1].action,"ATTACK","attack_intent_sent")
eq(service.remote.sent[2].action,"PLACE_TRAP","trap_intent_sent")
eq(service.remote.sent[1].seq,1,"attack_seq_1")
eq(service.remote.sent[2].seq,2,"trap_seq_2")
eq(service.remote.sent[1].damage,nil,"intent_damage_forbidden")
eq(service.remote.sent[1].targetId,nil,"intent_target_forbidden")
eq(service.remote.sent[2].position,nil,"intent_client_place_forbidden")
-- A newer actual game results state; old ACTIVE must not roll it back.
local result=snapshot(1,10,"RESULTS","GUARDIAN",2)
send(result)
eq(attack.Visible,false,"results_attack_hidden")
eq(trap.Visible,false,"results_trap_hidden")
eq(string.find(status.Text,"勝利！")~=nil,true,"results_correct_winner_text")
eq(string.find(score.Text,"🔵 2")~=nil,true,"results_scores_two")
send(snapshot(1,9,"ACTIVE","GUARDIAN",1))
eq(attack.Visible,false,"old_active_after_results_rejected")
eq(string.find(score.Text,"🔵 2")~=nil,true,"late_score_does_not_rollback")
-- Invalid ids must leave all HUD fields untouched.
send(snapshot(1,10.5,"ACTIVE","RAIDER",99))
eq(attack.Visible,false,"fractional_update_id_rejected")
send(snapshot(1,"fake","ACTIVE","RAIDER",99))
eq(attack.Visible,false,"string_update_id_rejected")
send(snapshot(1,-2,"ACTIVE","RAIDER",99))
eq(attack.Visible,false,"negative_update_id_rejected")
send(snapshot(1,nil,"ACTIVE","RAIDER",99))
eq(attack.Visible,false,"unversioned_after_upgrade_rejected")
-- A new match serial with an old global ordinal must not downgrade.
send(snapshot(2,8,"ACTIVE","GUARDIAN",99))
eq(attack.Visible,false,"old_cross_round_update_id_rejected")
eq(string.find(score.Text,"🔵 2")~=nil,true,"old_new_match_global_ordinal_rejected")
send(snapshot(2,11,"LOBBY","RAIDER",0))
eq(raider.Visible,true,"valid_next_round_accepted")
eq(attack.Visible,false,"new_lobby_attack_hidden")
-- Existing boss event path must still reject wrong seq and not submit intents.
send(snapshot(3,12,"ACTIVE","GUARDIAN",0))
send({kind="BOSS_VISUAL",serial=3,bossId="GOROGAN",eventId="G07_3",
      seq=1,serverSentAt=24,visualKind="START"})
send({kind="BOSS_VISUAL",serial=3,bossId="GOROGAN",eventId="G07_3",
      seq=2,serverSentAt=24,visualKind="STOMP"})
eq(string.find(status.Text,"踏みつけ")~=nil,true,"existing_boss_visual_stomp_display")
send({kind="BOSS_VISUAL",serial=3,bossId="GOROGAN",eventId="G07_3",
      seq=2,serverSentAt=24,visualKind="END"})
eq(string.find(status.Text,"踏みつけ")~=nil,true,"boss_visual_duplicate_ignored")
eq(#service.remote.sent,2,"boss_visual_never_sends_remote")
-- Fresh independent HUD session accepts legacy unversioned messages and
-- upgrades to sequenced; a late unversioned message then cannot downgrade.
service=setupServices()
app=loadOriginalHud()
gui=app.gui
attack=gui.children.Attack
trap=gui.children.GuardianTrap
raider=gui.children.RaiderRole
send(snapshot(0,nil,"LOBBY","RAIDER",0))
eq(raider.Visible,true,"fresh_legacy_lobby")
send(snapshot(1,nil,"ACTIVE","GUARDIAN",0))
eq(trap.Visible,true,"legacy_active_guardian")
send(snapshot(1,14,"RESULTS","GUARDIAN",2))
eq(trap.Visible,false,"legacy_upgrade_versioned")
send(snapshot(1,nil,"ACTIVE","GUARDIAN",1))
eq(trap.Visible,false,"legacy_replay_after_upgrade_rejected")
eq(string.find(gui.children.Score.Text,"🔵 2")~=nil,true,"legacy_score_roll_back_blocked")
print("P0D_S1_ACTUAL_HUD_NATIVE_CLIENT_PASS assertions="..tostring(count))
'''
# In the original HUD we return the exact original local Gui, no code change.
HUD_LOAD_BEGIN = "local function loadOriginalHud()\n"
HUD_LOAD_END = "\nreturn {gui=gui}\nend\n"
MIN_ASSERTIONS = 43


def blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()


def exact(source: str, old: str, new: str, label: str) -> str:
    count=source.count(old)
    if count!=1:
        raise RuntimeError(f"NON_UNIQUE_PATCH_{label}_COUNT_{count}")
    return source.replace(old,new,1)


def read_git(repo: Path, commit: str, path: str, sha: str) -> str:
    p=subprocess.run(["git","-C",str(repo),"show",commit+":"+path],
                     check=False,timeout=25,capture_output=True)
    if p.returncode or blob(p.stdout)!=sha:
        raise RuntimeError("FROZEN_ORIGINAL_SOURCE_BLOB_CHANGED_"+path)
    return p.stdout.decode("utf8")


def prepare(repo: Path) -> tuple[str,str]:
    original=read_git(repo,PARENT,BASE_HUD,BASE_HUD_BLOB)
    server=read_git(repo,PARENT,BASE_GAME,BASE_GAME_BLOB)
    if "updateId = snapshotUpdateId" not in server:
        raise RuntimeError("SEVEN_SAFE_SERVER_UPDATE_ID_FIELD_MISSING")
    if server.count("snapshotUpdateId += 1")!=1:
        raise RuntimeError("SEVEN_SAFE_SERVER_ORDINAL_NON_UNIQUE")
    expected=original
    for i,(old,new) in enumerate(PATCHES):
        expected=exact(expected,old,new,"HUD_ACTUAL_SOURCE_"+str(i))
    candidate=(repo/CANDIDATE)
    if not candidate.is_file() or candidate.is_symlink():
        raise RuntimeError("CANDIDATE_HUD_FILE_MISSING")
    actual=candidate.read_bytes()
    if blob(actual)!=CANDIDATE_BLOB or actual!=expected.encode("utf8"):
        raise RuntimeError("CANDIDATE_NOT_EXACT_THREE_HUNK_HUD_SOURCE_PATCH")
    if 'UDim2.new(1, -140, 1, -110)' not in expected:
        raise RuntimeError("SAFE_MOBILE_TRAP_BUTTON_LOST")
    if 'action("PLACE_TRAP", nil)' not in expected:
        raise RuntimeError("SERVER_AUTHORIZED_TRAP_ACTION_CHANGED")
    print("P0D_S1_SEVEN_SAFE_HUD_EXACT_3_HUNK_SOURCE_PASS")
    return original,actual.decode("utf8")


def invoke(luau: str, dest: Path, hud: str):
    source=LUAU_SETUP+"\n"+HUD_LOAD_BEGIN+hud+HUD_LOAD_END+LUAU_TESTS
    dest.write_text(source,encoding="utf8")
    p=subprocess.run([luau,str(dest)],check=False,capture_output=True,text=True,timeout=25)
    return p.returncode,p.stdout+p.stderr


def execute(repo: Path, luau: str):
    _,hud=prepare(repo)
    with TemporaryDirectory(prefix="p0d-hud-native-") as directory:
        dest=Path(directory)/"actual_original_hud.luau"
        rc,out=invoke(luau,dest,hud)
        m=re.search(r"P0D_S1_ACTUAL_HUD_NATIVE_CLIENT_PASS assertions=(\d+)",out)
        if rc!=0 or not m or int(m.group(1))<MIN_ASSERTIONS:
            raise RuntimeError("ACTUAL_HUD_FUNCTIONAL_NATIVE_FAILED "+out[-1700:])
        print("P0D_S1_SEVEN_SAFE_ACTUAL_HUD_LUAU_NATIVE_PASS assertions="+m.group(1))
        for name,old,new,expected in MUTANTS:
            mutant=exact(hud,old,new,name)
            code,log=invoke(luau,dest,mutant)
            if code==0 or expected not in log:
                raise RuntimeError("UNDETECTED_HUD_MUTANT_"+name+" "+log[-1000:])
            print("P0D_S1_HUD_BAD_SOURCE_MUTANT_REJECTED "+name)
        print("P0D_S1_SEVEN_SAFE_HUD_NATIVE_AND_MUTANTS_PASS mutants="+str(len(MUTANTS)))


def selftest():
    assert len(PARENT)==len(BASE_HUD_BLOB)==len(CANDIDATE_BLOB)==40
    assert blob(b"abc")=="f2ba8f84ab5c1bce84a7b441cb1959cfc7093b7f"
    assert len(PATCHES)==3 and len(MUTANTS)==6
    assert len({m[0] for m in MUTANTS})==6
    assert "HUD_S1_ASSERT_duplicate_snapshot_rejected" in (LUAU_TESTS.replace("eq(","HUD_S1_ASSERT_"))
    assert "old_cross_round_update_id_rejected" in LUAU_TESTS
    assert exact("a@b","@","x","good")=="axb"
    for item,key in [("text","missing"),("two two","two")]:
        try:exact(item,key,"x","invalid")
        except RuntimeError:pass
        else:raise AssertionError("DUPLICATE_PATCH_ANCHOR_ACCEPTED")
    print("P0D_S1_HUD_NATIVE_SELFTEST_PASS checks=8")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--repo",type=Path)
    p.add_argument("--luau")
    p.add_argument("--selftest",action="store_true")
    p.add_argument("--source-only",action="store_true")
    args=p.parse_args()
    if args.selftest:
        selftest()
        return 0
    if not args.repo:
        p.error("--repo required")
    if args.source_only:
        prepare(args.repo.resolve())
        return 0
    if not args.luau:
        p.error("--luau required for genuine native execution")
    execute(args.repo.resolve(),args.luau)
    return 0


if __name__=="__main__":
    try:
        sys.exit(main())
    except (RuntimeError,ValueError,OSError,UnicodeError) as e:
        print("P0D_S1_HUD_NATIVE_BLOCKED "+str(e),file=sys.stderr)
        sys.exit(2)
