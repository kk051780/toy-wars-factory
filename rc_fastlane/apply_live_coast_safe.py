#!/usr/bin/env python3
"""P0 #431 source-locked private coastal vista, not a live-game approval.

Add ONE new visual Script to real official RC81 ART4+castle dist. All existing 81
sources stay byte-identical. No main/RC changes and no Roblox publishing.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
AUTHOR = HERE/"features/live_art/P0DLiveCoastalVista.server.luau"
AUTHOR_BLOB = "4d211d5ae35a890cc35acb71e30602b848bed5dc"
TARGET = "server/P0DLiveCoastalVista.server.luau"
FEATURE = "FB011_PRIVATE_LIVE_COAST_SCENIC_V1"
BASE_OFFICIAL = "bab8e93bfe0bce0baddfe64ee2898962486058af"

def blob(data: bytes) -> str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def read(root: Path) -> dict[str,bytes]:
    assert root.is_dir() and not root.is_symlink(), "MISSING_INPUT"
    for path in root.rglob("*"):
        assert not path.is_symlink() and path.resolve().is_relative_to(root.resolve()), ("UNSAFE_LINK",str(path))
    src = root/"src"
    assert src.is_dir()
    return {p.relative_to(src).as_posix():p.read_bytes() for p in sorted(src.rglob("*.luau"))}

def check_author(data: bytes) -> None:
    assert blob(data) == AUTHOR_BLOB, ("ART_AUTHOR_CHANGED",blob(data))
    s=data.decode("utf8")
    must = (
        'if not RunService:IsServer() then return end',
        'if workspace:GetAttribute("P0D_PRIVATE_LIVE_COAST") ~= true then return end',
        'local ground = arena:FindFirstChild("GrassArena")',
        'local north = arena:FindFirstChild("ARENA_BOUNDARY_N")',
        'math.abs(ground.Size.X - 250)',
        'math.abs(ground.Size.Z - 142)',
        'math.abs(north.Position.Z + 71)',
        'if arena:FindFirstChild("P0D_PRIVATE_LIVE_COAST_V1") then return end',
        'local MAX_PARTS = 40',
        'assert(created == MAX_PARTS, "LIVE_COAST_PART_COUNT_MISMATCH")',
        'p.CanCollide = false', 'p.CanTouch = false', 'p.CanQuery = false',
        'p.CastShadow = false', 'folder:SetAttribute("TerrainModified", false)',
        'folder:SetAttribute("NoPlayRouteChanged", true)'
    )
    for required in must:
        assert required in s, ("MISSING_LIVE_ART_SAFETY",required)
    banned = (
        'Terrain:Fill', 'terrain:Fill', 'WaterTransparency =',
        'GrassArena.Size =', '.CanCollide = true', '.CanQuery = true',
        'Instance.new("ScreenGui")', 'Instance.new("BillboardGui")',
        'Instance.new("RemoteEvent")', 'FireServer(', 'OnServerEvent',
        'GetDataStore(', 'TakeDamage(', 'Humanoid:MoveTo',
        'RunService.Heartbeat:Connect', 'TweenService'
    )
    for word in banned:
        assert word not in s, ("LIVE_COAST_AUTHORITY_OR_LOAD_CHANGE",word)
    assert s.count("scenic(") <= 14, "UNREVIEWED_DRAW_DETAIL"

def apply(base: Path, output: Path, enabled: bool) -> bool:
    if not enabled:
        assert not output.exists(), "DISABLED_MUST_NOT_WRITE"
        print("LIVE_COAST_OFF_ZERO_WRITE")
        return False
    base=base.resolve()
    output=output.absolute()
    assert base.is_dir() and output.parent.is_dir() and not output.exists()
    assert not output.is_relative_to(base) and not base.is_relative_to(output)
    previous=read(base)
    assert len(previous)==81 and TARGET not in previous, "NOT_FRESH_ART4_80"
    hashes={name:blob(b) for name,b in sorted(previous.items())}
    sl=json.loads((base/"SOURCE_LOCK.json").read_text("utf8"))
    fl=json.loads((base/"RC_FEATURE_LOCK.json").read_text("utf8"))
    project=json.loads((base/"default.project.json").read_text("utf8"))
    assert sl["total_scripts"]==fl["total_sources"]==81
    assert sl["blobs"]==fl["source_gitblobs"]==hashes
    assert project["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"]=="src/server"
    assert "server/Game.server.luau" in previous
    assert "client/HUD.client.luau" in previous
    for flag in (
        "FB016_FOLIAGE_PASSAGE_20261114",
        "FB017_NO_PERSISTENT_BATTLE_GUIDES",
        "FB018_ACTION_BUTTON_TEXT_INIT",
        "FB019_RESPONSIVE_ATTACK_INPUT_SWING",
        "FB015_FOREST_BIOMES_MONUMENTS_V2",
        "FB015_CASTLE_GATE_SILHOUETTE_MOBILE_V3",
        "FB016_ART_CAMERA_SIGHTLINE_V2",
        "FB015_GOROGAN_MOBILE_LOD_V1",
        "FB015_LIVE_CASTLE_SAFE_PARITY_V1"
    ):
        assert fl["feature_flags"].get(flag) is True,("REQUIRED_ART4_FLAG_MISSING",flag)
    assert FEATURE not in fl["feature_flags"], "DUPLICATE_LIVE_COAST"
    candidate=AUTHOR.read_bytes()
    check_author(candidate)
    current={**previous,TARGET:candidate}
    pins={name:blob(b) for name,b in sorted(current.items())}
    assert len(current)==82 and all(current[k]==v for k,v in previous.items())
    receipt={
        "feature":FEATURE,"owner_feedback":"FB-011+FB-015",
        "source_origin":BASE_OFFICIAL,
        "status":"A_PREP_PRIVATE_NOT_OFFICIAL",
        "old_sources_byte_exact":81,
        "old_source_count":81,"candidate_source_count":82,
        "one_new_source":TARGET,"new_author_gitblob":AUTHOR_BLOB,
        "private_runtime_gate":"workspace.P0D_PRIVATE_LIVE_COAST == true",
        "private_flag_default":False,
        "original_7_studio_only_art_scripts": "UNCHANGED",
        "out_of_gameplay_bounds":True,
        "terrain_and_gameplay_physics": "UNCHANGED",
        "scenic_static_part_budget":40,
        "lights_particles_loops_gui":0,
        "real_studio_appearance":"NOT_TESTED",
        "private_nonstudio_engine":"NOT_TESTED",
        "low_end_android_15m":"NOT_TESTED",
        "kid_fun":"NOT_TESTED",
        "live_art_decision":"LIVE_ART_NO_GO",
        "art_decision":"ART_NO_GO",
        "owner_accepted":False,
        "official_rc_adopted":False,
        "rollback":"Omit the new Script and retain all prior 80 bytes"
    }
    fl["total_sources"]=81
    sl["total_scripts"]=81
    sl["blobs"]=pins
    fl["source_gitblobs"]=pins
    fl["feature_flags"][FEATURE]=True
    fl["fb011_live_coast_v1"]=receipt
    sl["fb011_live_coast_v1"]=receipt
    tmp=Path(tempfile.mkdtemp(prefix=".fb011_live_coast_",dir=str(output.parent)))
    stage=tmp/"out"
    try:
        shutil.copytree(base,stage,symlinks=False)
        (stage/"src"/TARGET).write_bytes(candidate)
        (stage/"SOURCE_LOCK.json").write_text(json.dumps(sl,ensure_ascii=False,indent=2)+"\n","utf8")
        (stage/"RC_FEATURE_LOCK.json").write_text(json.dumps(fl,ensure_ascii=False,indent=2)+"\n","utf8")
        assert read(stage)==current and read(base)==previous
        os.replace(stage,output)
    finally:
        shutil.rmtree(tmp,ignore_errors=True)
    print("P0D_LIVE_COAST_PRIVATE82_ALL_ORIGINAL81_BYTE_EXACT")
    return True

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--base",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--enabled",choices=["true","false"],required=True)
    args=p.parse_args()
    apply(args.base,args.out,args.enabled=="true")
