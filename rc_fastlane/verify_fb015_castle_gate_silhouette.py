#!/usr/bin/env python3
"""FB015 castle V3 candidate real Studio Place source-exact proof."""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from apply_fb015_castle_gate_silhouette import (
    TARGET,BASE_BLOB,FEATURE,read,blob
)

def verify(dist:Path, place:Path, receipt:Path) -> dict:
    scripts=read(dist)
    assert len(scripts)==80 and TARGET in scripts
    sl=json.loads((dist/"SOURCE_LOCK.json").read_text("utf8"))
    fl=json.loads((dist/"RC_FEATURE_LOCK.json").read_text("utf8"))
    expected={k:blob(v) for k,v in sorted(scripts.items())}
    assert sl["total_scripts"]==fl["total_sources"]==80
    assert sl["blobs"]==fl["source_gitblobs"]==expected,"SOURCE_LOCK_DRIFT"
    assert fl["feature_flags"][FEATURE] is True
    meta=fl["fb015_castle_v3"]
    assert meta["author_blob"]==BASE_BLOB
    assert meta["new_blob"]==expected[TARGET]
    assert meta["other_79_sources_byte_identical"] is True
    assert meta["new_parts_total_both_castles"]==36
    expected_counter=collections.Counter(v.decode("utf8") for v in scripts.values())
    actual_counter=collections.Counter()
    by_name=collections.defaultdict(list)
    for item in ET.parse(place).iter("Item"):
        if item.get("class") not in {"Script","LocalScript","ModuleScript"}:
            continue
        props=item.find("Properties")
        if props is None: continue
        source=props.find("string[@name='Source']")
        name=props.find("string[@name='Name']")
        if source is not None:
            actual_counter[source.text or ""]+=1
            if name is not None:
                by_name[(item.get("class"),name.text)].append(source.text or "")
    assert expected_counter==actual_counter and sum(actual_counter.values())==80,\
           "REAL_ROJO_EMBEDDED_80_SOURCES_MISMATCH"
    for kind,name,path in (
        ("Script","Game","server/Game.server.luau"),
        ("Script","CastleDetailArt",TARGET),
        ("LocalScript","TrapRaidersHUD","client/HUD.client.luau"),
        ("LocalScript","BattleHUDGovernor","client/BattleHUDGovernor.client.luau"),
    ):
        instances=by_name[(kind,name)]
        assert len(instances)==1,("MISSING_OR_DUPLICATE_REAL_INSTANCE",name,len(instances))
        assert instances[0]==scripts[path].decode("utf8"),("REAL_INSTANCE_SOURCE_SWAP",name)
    castle=scripts[TARGET].decode("utf8")
    for required in ("V3_GATE_PARAPET_BEAM_",
                     "V3_GATE_MERLON_COPING_",
                     "V3_TEAM_COLOR_STANDARD_",
                     "FB015_CASTLE_GATE_SILHOUETTE_MOBILE_V3",
                     'folder:SetAttribute("OwnerArtAccepted",false)',
                     'p.CanCollide = false',
                     'p.CanQuery = false'):
        assert required in castle, ("CASTLE_ART_CRITICAL_SOURCE_MISSING",required)
    for forbidden in ("TakeDamage(", "FireServer(", "OnServerEvent:Connect(",
                      "CanCollide = true", "CanQuery = true",
                      'Instance.new("ScreenGui")', "GetDataStore("):
        assert forbidden not in castle, ("CASTLE_ART_AUTHORITY_OR_UI_VIOLATION",forbidden)
    result={
        "feedback_id":"FB-015",
        "feature_id":FEATURE,
        "status":"PRIVATE_SOURCE_QA_ONLY_NOT_FORMAL_RC",
        "real_luau_sources":80,
        "rojo_embedded_sources_exact":80,
        "game_hud_castle_instance_source_identity":"PASS",
        "modified_source":[TARGET],
        "other79_byte_identical":True,
        "new_large_visual_parts":36,
        "new_collision_parts":0,
        "new_dynamic_lights":0,
        "pc_real_visual_grade":"NOT_TESTED",
        "android_15min_performance":"NOT_TESTED",
        "kid_fun_first3minutes":"NOT_TESTED",
        "art_decision":"ART_NO_GO",
        "fun_decision":"FUN_NO_GO",
        "owner_accepted":False,
        "official_rc_adopted":False,
        "place_bytes":place.stat().st_size,
        "place_sha256":hashlib.sha256(place.read_bytes()).hexdigest()
    }
    receipt.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n","utf8")
    print("FB015_CASTLE_V3_PRIVATE_RC80_EXACT_SOURCE_AND_ORIGINAL_AUTHORITY_PASS",result["place_bytes"])
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dist",required=True,type=Path)
    p.add_argument("--place",required=True,type=Path)
    p.add_argument("--receipt",required=True,type=Path)
    args=p.parse_args()
    verify(args.dist,args.place,args.receipt)
