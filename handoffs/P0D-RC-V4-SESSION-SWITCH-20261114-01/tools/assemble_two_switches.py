#!/usr/bin/env python3
"""RC rich51 source-exact two-feature overlay; ORIGINAL source files stay untouched.

Invokes existing pinned author assembler and changes only isolated DIST copies:
- V4 Training Bridge server (preview ON/OFF)
- V4 Trial Overlay client (display ON/OFF)
- H1 Fun World (SKY V5 boot-only ON/OFF; sea+fantasy creatures always retained)
No second Game, Store, Remote, paid API, score or egg ownership.
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from patch_sky import gitblob,transform

ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parents[1]
PARENT=REPO/"handoffs/P0D-RC-H1-RESULT47-WAYPOINT-V4-SESSION-20261114-01"
BASE=PARENT/"dist/P0D_RICH47_WAYPOINT_V4_6SKILL_SESSION_PRIVATE"
DIST=ROOT/"dist/P0D_RICH51_V4_AND_SKY_SWITCH_PRIVATE"
LOCKED_SOURCE_HEAD="79123d35cd7afdd5f4f9941675bc2d2cf382ac4e"
OLD={
    "server/H1FunWorld.server.luau":"7a90affd4eb7eebcdfba39d833a2875ff665d5cf",
    "server/V4TrainingBridge.server.luau":"326ec2cadbc71ef9d1d3a08e797479d1c6e08203",
    "client/V4TrialOverlay.client.luau":"0859702fdd050e0b66a2c0672c419e5c7adb812a",
}
NEW={
    "server/H1FunWorld.server.luau":"6e8324bba70a25ba0348a3dfae807f9c9a2e827a",
    "server/V4TrainingBridge.server.luau":"06491af532efb6a0e9c29e6ebed7f12b200df69e",
    "client/V4TrialOverlay.client.luau":"90ce2e89b59385d25d2405c91deb00074567abd4",
}
LOCAL={
    "server/V4TrainingBridge.server.luau":ROOT/"src/V4TrainingBridge.server.luau",
    "client/V4TrialOverlay.client.luau":ROOT/"src/V4TrialOverlay.client.luau",
}
def scripts(root):
    return {p.relative_to(root/"src").as_posix():p.read_bytes()
            for p in sorted((root/"src").rglob("*.luau"))}

def build():
    if BASE.exists() or DIST.exists():
        raise ValueError("NO_OVERWRITE_REQUIRE_FRESH_CHECKOUT")
    # Original author validates its 47 game sources + exact original 4 V4 module sources.
    subprocess.run([sys.executable,"-B",str(PARENT/"tools/assemble.py"),"--assemble"],
                   cwd=REPO,check=True)
    original=scripts(BASE)
    if len(original)!=51:
        raise ValueError("ORIGINAL_51_COUNT_DRIFT")
    original_lock=json.loads((BASE/"SOURCE_LOCK.json").read_text("utf8"))
    if original_lock.get("total_scripts")!=51 or original_lock.get("blobs")!={p:gitblob(data) for p,data in original.items()}:
        raise ValueError("ORIGINAL_AUTHOR_LOCK_DRIFT")
    for name,expect in OLD.items():
        if gitblob(original[name])!=expect:
            raise ValueError("BASE_SOURCE_DRIFT:"+name)
    # Keep source files exactly in own unique overlay folder only.
    extras={name:p.read_bytes() for name,p in LOCAL.items()}
    for name in LOCAL:
        if gitblob(extras[name])!=NEW[name]:
            raise ValueError("NEW_V4_SOURCE_DRIFT:"+name)
    sky=transform(original["server/H1FunWorld.server.luau"])
    if gitblob(sky)!=NEW["server/H1FunWorld.server.luau"]:
        raise ValueError("NEW_SKY_SOURCE_DRIFT")
    shutil.copytree(BASE,DIST)
    changes={**extras,"server/H1FunWorld.server.luau":sky}
    for name,raw in changes.items():
        (DIST/"src"/name).write_bytes(raw)
    project=DIST/"default.project.json"
    cfg=json.loads(project.read_text("utf8"))
    cfg["name"]="P0D_RC_RICH51_TWO_SWITCHES_PRIVATE"
    project.write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+"\n","utf8")
    result=scripts(DIST)
    if set(result)!=set(original) or len(result)!=51:
        raise ValueError("GAME_MODULE_SET_DRIFT")
    modified=sorted(p for p in result if original[p]!=result[p])
    if modified!=sorted(NEW):
        raise ValueError("UNEXPECTED_GAME_SOURCE_MODIFICATIONS:"+str(modified))
    if sum(result[p]==original[p] for p in result)!=48:
        raise ValueError("ORIGINAL_48_NOT_PRESERVED")
    if sum(p=="server/Game.server.luau" for p in result)!=1:
        raise ValueError("GAME_AUTHORITY_DRIFT")
    if sum(p.endswith(".server.luau") for p in result)!=3:
        raise ValueError("SCRIPT_TYPE_DRIFT")
    game=result["server/Game.server.luau"].decode("utf8")
    if game.count('remote.OnServerEvent:Connect(')!=1 or game.count('remote.Name = "TrapRaidersS1Remote"')!=1:
        raise ValueError("DUPLICATE_REMOTE_OR_SERVER_HANDLER")
    for name in NEW:
        new=result[name].decode("utf8")
        if "GetDataStore(" in new or "UpdateAsync(" in new or "OnServerEvent:Connect(" in new or "MarketplaceService" in new:
            raise ValueError("NEW_AUTHORITY_FORBIDDEN:"+name)
    lock={
        "schema":"P0D_RICH51_TWO_SWITCH_SOURCE_LOCK_V1",
        "status":"OWNER_PRIVATE_SOURCE_CANDIDATE_ONLY_NOT_OFFICIAL_RC",
        "original_canonical_rich51_source_sha":LOCKED_SOURCE_HEAD,
        "source_count":51,
        "old_source_bodies_preserved":48,
        "modified_source_paths":modified,
        "one_game":True,"one_original_remote_and_store":True,
        "feature_ids":["V4_SIX_SKILL_SESSION","H1_SKYV5"],
        "v4_server_attribute":"ServerStorage.P0D_RC_ENABLE_V4_SESSION",
        "sky_boot_attribute":"ServerStorage.P0D_RC_ENABLE_H1_SKYV5",
        "sky_boot_only":True,"sea_and_fantasy_creatures_always_stay":True,
        "rollback_source_commit":LOCKED_SOURCE_HEAD,
        "studio_1client":"NOT_TESTED","studio_2client":"NOT_TESTED",
        "android":"NOT_TESTED","owner_fun":"NOT_TESTED",
        "six_skill_persistence":False,"paid":False,"published":False,
        "official_rc_adopted":False,
        "blobs":{p:gitblob(raw) for p,raw in sorted(result.items())},
    }
    (DIST/"SOURCE_LOCK.json").write_text(json.dumps(lock,ensure_ascii=False,indent=2)+"\n","utf8")
    print("P0D_TWO_SWITCH_51_EXACT_SOURCE_PASS",NEW)
    return lock

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--assemble",action="store_true",required=True)
    ap.parse_args()
    build()
