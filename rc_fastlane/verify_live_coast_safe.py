#!/usr/bin/env python3
"""Real Rojo source-equality proof for private sea-view panorama on RC81 ART4+castle."""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from apply_live_coast_safe import AUTHOR_BLOB,TARGET,FEATURE,blob,read,check_author

def verify(dist:Path,place:Path,receipt_path:Path) -> dict:
    before=read(dist)
    assert len(before)==82 and TARGET in before, "EXACT_81_SCRIPTS_REQUIRED"
    check_author(before[TARGET])
    sl=json.loads((dist/"SOURCE_LOCK.json").read_text("utf8"))
    fl=json.loads((dist/"RC_FEATURE_LOCK.json").read_text("utf8"))
    expected_pins={name:blob(code) for name,code in sorted(before.items())}
    assert sl["total_scripts"]==fl["total_sources"]==82
    assert sl["blobs"]==fl["source_gitblobs"]==expected_pins, "SOURCE_LOCK_MISMATCH"
    assert fl["feature_flags"][FEATURE] is True
    side=fl["fb011_live_coast_v1"]
    assert side["old_sources_byte_exact"]==81
    assert side["new_author_gitblob"]==AUTHOR_BLOB
    assert side["owner_accepted"] is False

    raw=place.read_bytes()
    assert 0<len(raw)<10_000_000 and b"<!DOCTYPE" not in raw.upper() and b"<!ENTITY" not in raw.upper()
    actual=collections.Counter()
    named=collections.defaultdict(list)
    for item in ET.fromstring(raw).iter("Item"):
        kind=item.get("class")
        if kind not in ("Script","LocalScript","ModuleScript"): continue
        ps=item.find("Properties")
        if ps is None:continue
        src=ps.find("string[@name='Source']")
        name=ps.find("string[@name='Name']")
        if src is None or name is None:continue
        contents=src.text or ""
        actual[contents]+=1
        named[(kind,name.text)].append(contents)
    expected=collections.Counter(source.decode("utf8") for source in before.values())
    assert expected==actual and sum(actual.values())==82, "ROJO_81_EMBEDDED_SOURCES_MISMATCH"
    for kind,name,path in (
        ("Script","Game","server/Game.server.luau"),
        ("LocalScript","TrapRaidersHUD","client/HUD.client.luau"),
        ("ModuleScript","MapBuilder","server/MapBuilder.luau"),
        ("Script","P0DLiveCastleArt","server/P0DLiveCastleArt.server.luau"),
        ("Script","P0DLiveCoastalVista",TARGET),
        ("Script","H1CoastalSeascape","server/H1CoastalSeascape.server.luau"),
        ("Script","H1SeaGroundRepair","server/H1SeaGroundRepair.server.luau")
    ):
        values=named[(kind,name)]
        assert len(values)==1,("UNEXPECTED_SOURCE_INSTANCE_COUNT",kind,name,len(values))
        assert path in before and values[0]==before[path].decode("utf8"),("INSTANCE_SOURCE_SWAPPED",name)
    base=before["server/MapBuilder.luau"].decode("utf8")
    for required in ('"TRAP_RAIDERS_S1"', '"GrassArena"', '"ARENA_BOUNDARY_N"',
                     '"CenterRoad"', '"RED", "BLUE"', 'Vector3.new(250, 4, 142)'):
        assert required in base,("LIVE_COAST_BASE_MAP_ANCHOR_MISSING",required)
    for name in ("H1CoastalSeascape","H1SeaGroundRepair"):
        assert "if not RunService:IsStudio() then return end" in named[("Script",name)][0]
    live=before[TARGET].decode("utf8")
    assert 'workspace:GetAttribute("P0D_PRIVATE_LIVE_COAST") ~= true' in live
    assert 'if not RunService:IsStudio() and game.PrivateServerId == "" then' in live
    assert "Terrain:Fill" not in live and "p.CanCollide = false" in live
    assert "local MAX_PARTS = 40" in live
    result={
        "schema":"P0D_PRIVATE_LIVE_COAST_RC81_SOURCE_QA_V1",
        "source_count":82,
        "original_81_byte_exact":True,
        "one_new_visual_script":TARGET,
        "real_rojo_source_exact":82,
        "MapBuilder_name_source_and_geometry_anchor":"PASS",
        "Game_HUD_original_authority_name_source":"PASS",
        "old_sea_studio_only_guards":"PRESERVED_UNCHANGED",
        "new_coast_default":"OFF",
        "private_server_opt_in_only":True,
        "public_server_hard_gate_source_verified":True,
        "created_part_budget":40,
        "new_lights_particles_physics_gui":0,
        "live_runtime_actual":"NOT_TESTED",
        "studio_visual_score":"NOT_TESTED",
        "android_15min":"NOT_TESTED",
        "fun_first_3min":"NOT_TESTED",
        "art_decision":"ART_NO_GO",
        "live_art_decision":"LIVE_ART_NO_GO",
        "mobile_decision":"MOBILE_NO_GO",
        "fun_decision":"FUN_NO_GO",
        "owner_accepted":False,
        "formal_rc_adopted":False,
        "place_bytes":len(raw),
        "place_sha256":hashlib.sha256(raw).hexdigest()
    }
    receipt_path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n","utf8")
    print("P0D_PRIVATE_LIVE_COAST_REAL_ROJO_82_EXACT_PASS",result["place_bytes"])
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dist",type=Path,required=True)
    p.add_argument("--place",type=Path,required=True)
    p.add_argument("--receipt",type=Path,required=True)
    a=p.parse_args()
    verify(a.dist,a.place,a.receipt)
