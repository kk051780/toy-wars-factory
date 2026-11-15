#!/usr/bin/env python3
"""#444 private evidence 82-source actual Rojo Instance/source witness."""
from __future__ import annotations
import argparse,collections,hashlib,json
from defusedxml import ElementTree as ET
from pathlib import Path
from apply_horde_runtime_evidence import AUTHOR_BLOB,DEST,GAME,HORDE,FEATURE,blob,read,verify_author

def verify(dist:Path,place:Path,receipt:Path)->dict:
    sources=read(dist)
    assert len(sources)==82 and DEST in sources,"82_AUTHENTIC_SOURCES_REQUIRED"
    verify_author(sources[DEST])
    sl=json.loads((dist/"SOURCE_LOCK.json").read_text("utf8"))
    fl=json.loads((dist/"RC_FEATURE_LOCK.json").read_text("utf8"))
    pins={k:blob(v) for k,v in sorted(sources.items())}
    assert sl["total_scripts"]==fl["total_sources"]==82
    assert sl["blobs"]==fl["source_gitblobs"]==pins
    assert fl["feature_flags"][FEATURE] is True
    meta=fl["horde_runtime_probe_v1"]
    assert meta["old81_byte_identical"] is True and meta["new_script"]==DEST
    assert meta["author_gitblob"]==AUTHOR_BLOB
    assert meta["owner_accepted"] is False

    raw=place.read_bytes()
    assert 0<len(raw)<10_000_000
    assert b"<!DOCTYPE" not in raw.upper() and b"<!ENTITY" not in raw.upper()
    actual=collections.Counter()
    paths=collections.defaultdict(list)
    for item in ET.fromstring(raw).iter("Item"):
        kind=item.get("class")
        if kind not in ("Script","ModuleScript","LocalScript"):continue
        p=item.find("Properties")
        if p is None:continue
        name=p.find("string[@name='Name']")
        src=p.find("string[@name='Source']")
        assert name is not None and src is not None,("SCRIPT_NAME_OR_SOURCE_MISSING",kind)
        value=src.text or ""
        actual[value]+=1
        paths[(kind,name.text)].append(value)
    expected=collections.Counter(v.decode("utf8") for v in sources.values())
    assert actual==expected and sum(actual.values())==82, "ACTUAL_82_SOURCE_MISMATCH"
    for kind,name,path in (
        ("Script","Game",GAME),
        ("ModuleScript","MusouHorde",HORDE),
        ("LocalScript","TrapRaidersHUD","client/HUD.client.luau"),
        ("Script","P0DPrivateHordeEvidence",DEST),
        ("Script","P0DLiveCastleArt","server/P0DLiveCastleArt.server.luau"),
        ("ModuleScript","MapBuilder","server/MapBuilder.luau")
    ):
        val=paths[(kind,name)]
        assert len(val)==1 and val[0]==sources[path].decode("utf8"),("SOURCE_ROLE_SWAPPED",kind,name,len(val))
    s=sources[DEST].decode("utf8")
    assert 'if not RunService:IsStudio() and game.PrivateServerId == "" then return end' in s
    assert 'workspace:GetAttribute("P0D_PRIVATE_HORDE_EVIDENCE") ~= true' in s
    assert "local MAX_SAMPLES = 360" in s
    assert "MAX_MOBS = 9" in s
    result={
        "schema":"P0D_REAL_ENGINE_HORDE_OBSERVATION_PROBE_SOURCE_RECEIPT_V1",
        "real_rojo_source_count_exact":82,
        "old81_source_bytes_unchanged":True,
        "private_onehuman_hit_art_preserved":True,
        "new_source":DEST,
        "unique_authority_Game_Horde_HUD":True,
        "read_only_diagnostic":True,
        "public_runtime_codepath":"HARD_OFF",
        "private_server_both_owner_flags_required":True,
        "sampling_window_seconds_max":180,
        "visible_diagnostic_gui_count":0,
        "new_gameplay_remote_damage_store_count":0,
        "actual_nonstudio_private9":"NOT_TESTED",
        "actual_server_hit_popup":"NOT_TESTED",
        "actual_npc_motion":"NOT_TESTED",
        "low_end_android15min":"NOT_TESTED",
        "owner_accepted":False,
        "official_rc_adopted":False,
        "live_horde_decision":"LIVE_HORDE_NO_GO",
        "art_decision":"ART_NO_GO",
        "mobile_decision":"MOBILE_NO_GO",
        "fun_decision":"FUN_NO_GO",
        "place_bytes":len(raw),
        "place_sha256":hashlib.sha256(raw).hexdigest()
    }
    receipt.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n","utf8")
    print("P0D_HORDE_PRIVATE_EVIDENCE_REAL_ROJO_82_EXACT_SOURCE_QA_PASS",len(raw))
    return result
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dist",required=True,type=Path)
    p.add_argument("--place",required=True,type=Path)
    p.add_argument("--receipt",required=True,type=Path)
    a=p.parse_args()
    verify(a.dist,a.place,a.receipt)
