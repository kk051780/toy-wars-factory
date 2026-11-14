#!/usr/bin/env python3
"""FB-015 ART-WORLD isolated Studio-only scene, original RC66 -> private67.
No official branch mutation; OFF is an exact zero-write no-op.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

BASE=Path(__file__).resolve().parent
FEATURE="FB015_ART_WORLD_LIGHT_FOLIAGE_V1"
MODULE="server/FantasyWorldArt.server.luau"
SCRIPT=BASE/"features/fb015_world/FantasyWorldArt.server.luau"
SCRIPT_SHA="9e4dfba571807252ada1cc6ddd174e9b63fcc83d"

def blob(data:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+bytes([0])+data).hexdigest()
def sources(dist:Path)->dict[str,bytes]:
    return {p.relative_to(dist/"src").as_posix():p.read_bytes()
            for p in sorted((dist/"src").rglob("*.luau"))}
def apply(dist:Path,enabled:bool)->None:
    if not enabled:
        print("P0D_FB015_WORLD_ART_OFF_CANONICAL66_ZERO_WRITE_PASS")
        return
    sw=json.loads((BASE/"FEATURE_SWITCHES.json").read_text("utf8"))["features"][FEATURE]
    assert sw["enabled"] is True and sw["official_rc_adopted"] is False
    assert sw["source_git_blob"]==SCRIPT_SHA
    data=SCRIPT.read_bytes()
    assert blob(data)==SCRIPT_SHA, "ART_SOURCE_DRIFT"
    assert data.startswith(b"--!strict")
    assert b'if not RunService:IsStudio() then return end' in data
    assert b'folder:SetAttribute("OfficialOwnerAccepted",false)' in data
    for prohibited in (b"DataStoreService",b"RemoteEvent",b"OnServerEvent",b"UpdateAsync",
            b"FireServer",b"TakeDamage",b"MarketplaceService",b"GetDataStore",
            b"FillRegion",b"FillBlock",b"FillBall",b"OnHeartbeat",b"Heartbeat:Connect"):
        assert prohibited not in data,prohibited
    original=sources(dist)
    assert len(original)==66,("EXPECTED_CANONICAL66",len(original))
    assert MODULE not in original
    lockfile=dist/"SOURCE_LOCK.json"
    featfile=dist/"RC_FEATURE_LOCK.json"
    projectfile=dist/"default.project.json"
    lock=json.loads(lockfile.read_text("utf8"))
    feat=json.loads(featfile.read_text("utf8"))
    project=json.loads(projectfile.read_text("utf8"))
    pinned={k:blob(raw) for k,raw in sorted(original.items())}
    assert lock["total_scripts"]==66 and feat["total_sources"]==66
    assert lock["blobs"]==feat["source_gitblobs"]==pinned
    assert project["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"]=="src/server"
    assert sum(x=="server/Game.server.luau" for x in original)==1
    assert original["server/Game.server.luau"].count(b"remote.OnServerEvent:Connect(")==1
    # All preflight checks above must succeed before a single write to scratch dist.
    (dist/"src"/MODULE).write_bytes(data)
    finished=sources(dist)
    assert len(finished)==67 and finished[MODULE]==data
    assert all(finished[k]==v for k,v in original.items())
    newpins={k:blob(raw) for k,raw in sorted(finished.items())}
    mark={"id":FEATURE,"official_rc_adopted":False,"studio_art_review":"NOT_TESTED",
        "one_added_decorative_script":MODULE,"original66_bytes_identical":True,
        "no_gameplay_collision_or_damage_authority":True,"source_git_blob":SCRIPT_SHA,
        "art_owner_acceptance":"NO_GO"}
    lock["total_scripts"]=67
    lock["blobs"]=newpins
    lock["rc_fb015_world_visual_overlay"]=mark
    feat["total_sources"]=67
    feat["source_gitblobs"]=newpins
    feat["feature_flags"][FEATURE]=True
    feat["rc_fb015_world_visual_overlay"]=mark
    lockfile.write_text(json.dumps(lock,ensure_ascii=False,indent=2)+"\n","utf8")
    featfile.write_text(json.dumps(feat,ensure_ascii=False,indent=2)+"\n","utf8")
    assert sources(dist)==finished
    print("P0D_FB015_WORLD_ART_REAL_67_SOURCE_ORIGINAL66_EXACT_PASS")

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--dist",required=True)
    parser.add_argument("--enabled",choices=["true","false"],required=True)
    args=parser.parse_args()
    apply(Path(args.dist),args.enabled=="true")
