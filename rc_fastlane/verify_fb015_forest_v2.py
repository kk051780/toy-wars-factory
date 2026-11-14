#!/usr/bin/env python3
"""FB015 forest v2: source-exact REAL Roblox Studio private Place verification."""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
from defusedxml import ElementTree as ET
from pathlib import Path
from apply_fb015_forest_v2 import read,blob,TARGET,FEATURE,BASE_BLOB

def verify(dist:Path,place:Path,receipt:Path)->None:
    src=read(dist)
    pins={p:blob(data) for p,data in sorted(src.items())}
    sl=json.loads((dist/"SOURCE_LOCK.json").read_text("utf8"))
    fl=json.loads((dist/"RC_FEATURE_LOCK.json").read_text("utf8"))
    assert len(src)==sl["total_scripts"]==fl["total_sources"]==80
    assert sl["blobs"]==fl["source_gitblobs"]==pins
    assert fl["feature_flags"][FEATURE] is True
    assert fl["feature_flags"].get("FB019_REAL_HIT_VISIBLE_SERVER_CONFIRMED_V2") is True
    assert fl["fb019_hit_visibility"]["id"]=="FB019_REAL_HIT_VISIBLE_SERVER_CONFIRMED_V2"
    detail=fl["fb015_forest_v2"]
    assert detail["base_world_git_blob"]==BASE_BLOB
    assert detail["new_world_git_blob"]==pins[TARGET]
    assert detail["other79_byte_identical"] is True
    expected=collections.Counter(x.decode("utf8") for x in src.values())
    actual=collections.Counter()
    names=collections.Counter()
    for item in ET.parse(place).iter("Item"):
        if item.get("class") not in ("Script","LocalScript","ModuleScript"):
            continue
        properties=item.find("Properties")
        if properties is None:continue
        value=properties.find("string[@name='Source']")
        if value is not None:
            actual[value.text or ""]+=1
        name=properties.find("string[@name='Name']")
        if name is not None:
            names[(item.get("class"),name.text)]+=1
    assert expected==actual and sum(actual.values())==80, "ROJO_80_SOURCE_DRIFT"
    assert names[("Script","Game")]==1, "AUTHORITATIVE_GAME_MISSING_OR_DUPLICATE"
    assert names[("LocalScript","TrapRaidersHUD")]==1
    assert names[("Script","FantasyWorldArt")]==1, "FOREST_SCRIPT_MISSING"
    assert 'fb019' in json.dumps(fl).lower(), "FB019_PARENT_MISSING"
    forest=src[TARGET].decode("utf8")
    assert forest.count("AncientForestGate_")==1
    assert forest.count("LeafMass_BiomeBlossom_")==1
    assert 'folder:SetAttribute("ForestArtPartBudgetExpectedMax",226)' in forest
    for b in ("CanCollide=true","CanQuery=true","OnServerEvent:Connect(","FireServer(","TakeDamage("):
        assert b not in forest,b
    info={
       "owner_feedback":"FB-015","status":"PRIVATE_SOURCE_QA_NOT_OFFICIAL",
       "lua_sources":80,"rojo_sources_exact":80,
       "source_differences":[TARGET],"other79_byte_exact":True,
       "one_game":True,"forest_gates":4,"biome_canopy_accent_parts":36,
       "visual_no_physics":True,
       "studio_pc":"NOT_TESTED","android":"NOT_TESTED",
       "owner_art":"ART_NO_GO","official_rc_adopted":False,
       "place_bytes":place.stat().st_size,
       "place_sha256":hashlib.sha256(place.read_bytes()).hexdigest(),
    }
    receipt.write_text(json.dumps(info,ensure_ascii=False,indent=2)+"\n","utf8")
    print("FB015_FOREST_V2_RC80_ALL80_ROJO_SOURCE_EXACT_PASS",info["place_bytes"],info["place_sha256"])
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dist",type=Path,required=True)
    p.add_argument("--place",type=Path,required=True)
    p.add_argument("--receipt",type=Path,required=True)
    a=p.parse_args()
    verify(a.dist,a.place,a.receipt)
