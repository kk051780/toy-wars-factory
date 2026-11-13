#!/usr/bin/env python3
"""Isolated WCS F01 exact RC57 -> 58 source-candidate admission.
This file NEVER writes the canonical RC, main or Roblox. #220 is sole writer.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
AUTH = REPO / "handoffs/P0D-WCS-F01-RC57-SAFE-HANDOFF-20261114-01"
FEATURE = "WCS_F01_C01_FLOATING_CANYON"
DEST = "server/WCS_CrystalCanyon.server.luau"
PINNED_GIT_BLOB = "9b891ae8b0dd579ccf1cd477b8b012e03415c0b0"

def gitblob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()

def inventory(src: Path) -> dict[str, bytes]:
    return {p.relative_to(src).as_posix(): p.read_bytes()
            for p in sorted(src.rglob("*.luau"))}

def verify_original(dist: Path) -> tuple[dict,dict|None,dict[str,bytes]]:
    src = dist / "src"
    before = inventory(src)
    assert len(before)==57, ("NOT_CANONICAL_RICH57",len(before))
    assert DEST not in before, "DUPLICATE_WCS_SCRIPT"
    game=before["server/Game.server.luau"].decode("utf8")
    assert game.count('remote.OnServerEvent:Connect(')==1, "SECOND_GAME_EVENT_HANDLER"
    assert game.count('remote.Name = "TrapRaidersS1Remote"')==1, "SECOND_REMOTE"
    assert "ScoutSpecies.attack(" in game, "SCOUT_SPECIES_MISSING"
    assert "SavedBeastEvolution.choose(" in game, "SAVED_BEAST_MISSING"
    assert "SavedPvePolicy.mergeWithEarned(" in game, "SAVED_WEAPON_MISSING"
    project=json.loads((dist/"default.project.json").read_text("utf8"))
    assert project["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"]=="src/server", "ROJO_SERVER_PATH"
    pins={path:gitblob(data) for path,data in before.items()}
    lock=json.loads((dist/"SOURCE_LOCK.json").read_text("utf8"))
    assert lock["total_scripts"]==57 and lock["blobs"]==pins, "ORIGINAL_SOURCE_PIN_DRIFT"
    extra=None
    extra_path=dist/"RC_FEATURE_LOCK.json"
    if extra_path.exists():
        extra=json.loads(extra_path.read_text("utf8"))
        assert extra["total_sources"]==57 and extra["source_gitblobs"]==pins, "ORIGINAL_FEATURE_PIN_DRIFT"
        assert FEATURE not in extra.get("feature_flags",{}), "DUPLICATE_FEATURE"
    return lock,extra,before

def apply(dist: Path, enabled: bool) -> None:
    lock,feature,before=verify_original(dist)
    if not enabled:
        print("P0D_WCS_F01_OFF_RETURNS_BYTE_EXACT_CANONICAL57")
        return
    author_lock=json.loads((AUTH/"SOURCE_LOCK.json").read_text("utf8"))
    assert author_lock["author_script_git_blob"]==PINNED_GIT_BLOB
    assert author_lock["feature_id"]==FEATURE
    assert author_lock["canonical_head_at_source_authoring"]=="34d6d384d04ba1d4a394331a3e5c74f798e57a22"
    raw=(AUTH/"src/WCS_CrystalCanyon.server.luau").read_bytes()
    assert gitblob(raw)==PINNED_GIT_BLOB, "AUTHOR_WCS_SHA_MISMATCH"
    newcode=raw.decode("utf8")
    assert 'if not RunService:IsStudio() then' in newcode
    assert 'GetAttribute("P0D_RC_ENABLE_WCS_F01_C01")==false' in newcode
    assert "playerIsInGateClosureZone()" in newcode
    assert 'math.abs(localPoint.X) <= 3.5' in newcode
    assert 'nextOpenAllowed = os.clock() + REOPEN_COOLDOWN' in newcode
    for forbidden in ("OnServerEvent:Connect(", "UpdateAsync(", "SetAsync(",
                      "GetAsync(", "Instance.new(\"RemoteEvent\")"):
        assert forbidden not in newcode, ("WCS_SECOND_AUTHORITY",forbidden)
    after=dict(before)
    after[DEST]=raw
    assert len(after)==58
    assert sorted(set(after)-set(before))==[DEST]
    pins={p:gitblob(data) for p,data in sorted(after.items())}
    lock["total_scripts"]=58
    lock["blobs"]=pins
    lock["rc_wcs_f01_candidate_overlay"]={
        "id":FEATURE,"stage":"ISOLATED_NATIVE_ROJO_CANDIDATE_NOT_OFFICIAL_RC",
        "new_script":DEST,"original_57_source_bodies_identical":True,
        "game_hud_store_remote_original_unchanged":True,
        "studio_only":True,"default_studio_feature_on":True,
        "rollback":["omit script from build for exact canonical57",
                    "set ServerStorage attribute P0D_RC_ENABLE_WCS_F01_C01=false at boot"],
        "engine_studio":"NOT_TESTED","android":"NOT_TESTED"}
    if feature is not None:
        feature["total_sources"]=58
        feature["source_gitblobs"]=pins
        feature.setdefault("feature_flags",{})[FEATURE]=True
        feature["wcs_f01_stage"]="ISOLATED_CANDIDATE_NOT_RC_ADOPTED"

    # Fail-close on all predictable source/authority/lock errors before writes.
    (dist/"src"/DEST).write_bytes(raw)
    (dist/"SOURCE_LOCK.json").write_text(
        json.dumps(lock,ensure_ascii=False,indent=2)+"\n","utf8")
    if feature is not None:
        (dist/"RC_FEATURE_LOCK.json").write_text(
            json.dumps(feature,ensure_ascii=False,indent=2)+"\n","utf8")
    print("P0D_WCS_F01_AUTHENTIC_RICH57_TO_58_ONLY_ONE_WORLD_SCRIPT_ADDED")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--dist",required=True,type=Path)
    ap.add_argument("--enabled",choices=("on","off"),required=True)
    args=ap.parse_args()
    apply(args.dist,args.enabled=="on")
