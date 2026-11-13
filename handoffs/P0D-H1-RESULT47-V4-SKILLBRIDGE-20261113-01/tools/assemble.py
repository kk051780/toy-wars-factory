#!/usr/bin/env python3
"""Build optional combined H1 47 existing gameplay + exact-author V4 six-skill session UI.
Isolated preview only. All 47 source bytes MUST remain identical, Game/Store untouched.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
REPO=Path(__file__).resolve().parents[3]
PARENT=REPO/"handoffs/P0D-RC-H1-SKYV5-DOJO-RESULT-20261113-01"
BASE=PARENT/"dist/P0D_H1_SKYV5_DOJO_RESULT7_STUDIO_PRIVATE"
DIST=ROOT/"dist/P0D_H1_RESULT47_V4_SIXSKILL_SESSION_BRIDGE_PRIVATE"
MODEL=ROOT/"src/SessionSixSkillXPPreview.luau"
SCHEDULER=ROOT/"src/FocusTrainingScheduler.luau"
SERVER=ROOT/"src/V4TrainingBridge.server.luau"
CLIENT=ROOT/"src/V4TrialOverlay.client.luau"

def blob(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def sources(root):
    return {p.relative_to(root/"src").as_posix():p.read_bytes()
            for p in sorted((root/"src").rglob("*.luau"))}

def build():
    assert not BASE.exists() and not DIST.exists(), "NO_OVERWRITE_ALREADY_BUILT"
    assert blob(MODEL.read_bytes())=="ceb8f4f6caca37954cb3d61ef3e1756368b966e0", "V4_MODEL_AUTHOR_DRIFT"
    assert blob(SCHEDULER.read_bytes())=="a00caf954aacfca03c92a75b0165c1bafd4de8fd", "V4_SCHEDULER_AUTHOR_DRIFT"
    client=CLIENT.read_text("utf8")
    server=SERVER.read_text("utf8")
    for x in (client,server):
        assert 'if not RunService:IsStudio() then return end' in x,"STUDIO_ONLY"
    for forbidden in ("GetDataStore(","UpdateAsync(","FireServer(","OnServerEvent:Connect(","MarketplaceService","PromptProductPurchase("):
        assert forbidden not in server and forbidden not in client,forbidden
    assert "Scheduler.settle(" in server and "Model.apply(" in server
    assert 'verifiedFriends(player,record,now)' in server
    assert 'player:IsFriendsWith(other.UserId)' in server
    assert 'NoSavedXP' in server and "NoCombatBuff" in server
    assert '保存なし' in server and '保存なし' in client
    subprocess.run([sys.executable,"-B",str(PARENT/"tools/assemble.py"),"--assemble"],
                   cwd=REPO,check=True)
    original=sources(BASE)
    assert len(original)==47, len(original)
    original_lock=json.loads((BASE/"SOURCE_LOCK.json").read_text("utf8"))
    assert original_lock["total_scripts"]==47
    assert original_lock["official_rc_adopted"] is False
    assert original_lock["blobs"]=={p:blob(x) for p,x in original.items()}
    shutil.copytree(BASE,DIST)
    added={
        "server/FocusTrainingScheduler.luau":SCHEDULER,
        "server/SessionSixSkillXPPreview.luau":MODEL,
        "server/V4TrainingBridge.server.luau":SERVER,
        "client/V4TrialOverlay.client.luau":CLIENT,
    }
    for rel,src in added.items():
        dst=DIST/"src"/rel
        assert not dst.exists(),rel
        dst.write_bytes(src.read_bytes())
    cfg=DIST/"default.project.json"
    data=json.loads(cfg.read_text("utf8"))
    assert data["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"]=="src/server"
    starter=data["tree"]["StarterPlayer"]["StarterPlayerScripts"]
    assert starter["ResultNextStep"]["$path"]=="src/client/ResultNextStep.client.luau"
    assert "V4TrialOverlay" not in starter
    starter["V4TrialOverlay"]={"$path":"src/client/V4TrialOverlay.client.luau"}
    data["name"]="P0D_H1_RESULT47_V4_SIXSKILL_SESSION_BRIDGE_PRIVATE"
    cfg.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n","utf8")
    final=sources(DIST)
    assert len(final)==51,len(final)
    assert len(original)==47 and all(final[p]==v for p,v in original.items()),"ORIGINAL_47_DRIFT"
    assert sorted(set(final)-set(original))==sorted(added),"BAD_DELTA"
    assert sum(p=="server/Game.server.luau" for p in final)==1
    assert sum(p.endswith(".server.luau") for p in final)==3
    assert sum(p.endswith(".client.luau") for p in final)==8
    game=final["server/Game.server.luau"].decode("utf8")
    assert game.count('remote.OnServerEvent:Connect(')==1
    assert game.count('remote.Name = "TrapRaidersS1Remote"')==1
    assert game.count('Dojo.tick(')==1
    assert game.count('scorePrompt.Triggered:Connect(')==1
    for name in ("server/FocusTrainingScheduler.luau","server/SessionSixSkillXPPreview.luau"):
        assert blob(final[name]) in (
          "a00caf954aacfca03c92a75b0165c1bafd4de8fd",
          "ceb8f4f6caca37954cb3d61ef3e1756368b966e0")
    lock={
        "status":"P0D_UNSELECTED_STUDIO_PRIVATE_H1_47_PLUS_V4_4_51_SCRIPTS",
        "base_author_source_head":"4f6c335508ffb6dd9939b1664256c917e1c9e199",
        "v4_author_source_head":"2cc2fa5b2f0026cf938438826e20e016a3a70b0a",
        "original_47_byte_identical":47,
        "new_v4_author_modules":[
          "server/FocusTrainingScheduler.luau","server/SessionSixSkillXPPreview.luau"],
        "new_adapter_scripts":["server/V4TrainingBridge.server.luau",
                               "client/V4TrialOverlay.client.luau"],
        "total_scripts":51,"one_original_Game":True,"one_original_Remote":True,
        "studio_only":True,"six_skill_v4_session_xp_preview":True,
        "existing_beast_weapon_H1_dojo_unchanged":True,
        "v4_persistent_xp":False,"v4_daily_quota_persistent":False,
        "v4_combat_buffs":False,"v4_paid_chooser":False,
        "original_H1_result_7sec_unchanged":True,
        "published":False,"product_private_trial_selected":False,
        "official_rc_adopted":False,"studio_1client":"NOT_TESTED",
        "studio_2client":"NOT_TESTED","android":"NOT_TESTED",
        "owner_fun":"NOT_TESTED",
        "blobs":{p:blob(v) for p,v in sorted(final.items())}
    }
    (DIST/"SOURCE_LOCK.json").write_text(json.dumps(lock,ensure_ascii=False,indent=2)+"\n","utf8")
    print("P0D_PRIVATE51_BRIDGE_47_ORIGINAL_EXACT_PLUS_4_V4_SOURCES_PASS")
    return lock

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--assemble",action="store_true",required=True)
    p.parse_args()
    build()
