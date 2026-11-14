#!/usr/bin/env python3
"""#431: source-exact real Rojo 81-source private live-castle candidate."""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
from defusedxml import ElementTree as ET
from pathlib import Path
from apply_live_castle_safe import AUTHOR_BLOB,DEST,FEATURE,blob,read_sources,verify_author

def verify(dist:Path,place:Path,receipt:Path)->dict:
    old=read_sources(dist)
    assert len(old)==81 and DEST in old
    verify_author(old[DEST])
    pins={k:blob(v) for k,v in sorted(old.items())}
    sl=json.loads((dist/"SOURCE_LOCK.json").read_text("utf8"))
    fl=json.loads((dist/"RC_FEATURE_LOCK.json").read_text("utf8"))
    assert sl["total_scripts"]==fl["total_sources"]==81
    assert pins==sl["blobs"]==fl["source_gitblobs"]
    assert fl["feature_flags"][FEATURE] is True
    item=fl["fb015_live_castle_production"]
    assert item["all_old80_byte_identical"] is True and item["new_game_authority"]==0
    assert item["author_git_blob"]==AUTHOR_BLOB
    raw=place.read_bytes()
    assert 0<len(raw)<10_000_000 and b"<!DOCTYPE" not in raw.upper()
    assert b"<!ENTITY" not in raw.upper(),"MALICIOUS_XML_REJECTED"
    actual=collections.Counter()
    by_name=collections.defaultdict(list)
    for source in ET.fromstring(raw).iter("Item"):
        cls=source.get("class")
        if cls not in ("Script","LocalScript","ModuleScript"):continue
        ps=source.find("Properties")
        if ps is None:continue
        name=ps.find("string[@name='Name']")
        content=ps.find("string[@name='Source']")
        if content is None or name is None:continue
        actual[content.text or ""]+=1
        by_name[(cls,name.text)].append(content.text or "")
    expected=collections.Counter(v.decode("utf8") for v in old.values())
    assert expected==actual and sum(actual.values())==81,"NOT_81_REAL_AUTHOR_SOURCES"
    for kind,name,path in (
        ("Script","Game","server/Game.server.luau"),
        ("LocalScript","TrapRaidersHUD","client/HUD.client.luau"),
        ("Script","P0DLiveCastleArt",DEST),
        ("Script","Owner361CastleBattlefield","server/Owner361CastleBattlefield.server.luau")
    ):
        values=by_name[(kind,name)]
        assert len(values)==1 and values[0]==old[path].decode("utf8"),(
            "ROJO_SCRIPT_NAME_OR_AUTHORITY_MISMATCH",name,len(values))
    source=old[DEST].decode("utf8")
    assert 'if RunService:IsStudio() and script:GetAttribute("EnablePrivatePreview") ~= true then' in source
    assert "local BUDGET = 36" in source and "p.CanQuery = false" in source
    assert "p.CanCollide = false" in source and "p.CastShadow = false" in source
    result={
        "schema":"P0D_LIVE_CASTLE_PRIVATE81_SOURCE_QA_V1",
        "feature":FEATURE,"status":"PRIVATE_A_SOURCE_READY",
        "live_art_owner_issue":"#431",
        "rojo_scripts_exact":81,
        "original_80_sources_byte_unchanged":True,
        "one_Game_and_HUD_original":True,
        "one_new_visual_only_script":True,
        "new_script_activates_in_nonstudio":"STATIC_CODE_PATH_ONLY_NOT_ENGINE_TESTED",
        "private_Studio_preview_requires_attribute":True,
        "part_budget":36,"new_lights":0,"new_collisions":0,
        "real_PC_android_fps":"NOT_TESTED",
        "studio_appearance":"NOT_TESTED",
        "owner_accepted":False,
        "live_art_decision":"LIVE_ART_NO_GO",
        "art_decision":"ART_NO_GO",
        "mobile_decision":"MOBILE_NO_GO",
        "official_rc_adopted":False,
        "place_bytes":len(raw),
        "place_sha256":hashlib.sha256(raw).hexdigest(),
    }
    receipt.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n","utf8")
    print("P0D_LIVE_CASTLE_PRIVATE_ROJO_81_ALL_SOURCES_EXACT_PASS",result["place_bytes"])
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dist",type=Path,required=True)
    p.add_argument("--place",type=Path,required=True)
    p.add_argument("--receipt",type=Path,required=True)
    a=p.parse_args()
    verify(a.dist,a.place,a.receipt)
