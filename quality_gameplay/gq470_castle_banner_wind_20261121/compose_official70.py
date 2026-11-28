#!/usr/bin/env python3
"""A-only source exact REAL69 -> REAL70 optional banner art.
Official RC and active S1 remain unchanged. No engine, mobile or ART claims.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

THIS=Path(__file__).resolve().parent
sys.path.insert(0,str(THIS.parent/"gq8_rc85_rc86_real68_nonloss_20261120"))
from verify_nonloss import project_scan

BASE="e80973c354f14a0d0088577f3cc1a875454f0f8f"
PLACE_SHA="fc63171149a86f6b39779ba6ebe7e18fcb7099fbde98ad2ec33a7cb92b3a9934"
PLACE_SIZE=798390
PROJECT="EGGRUMBLE_REAL69.project.json"
ORIGINAL_PLACE="EGGRUMBLE_REAL69_PRIVATE.rbxlx"
RECEIPT="REAL69_LEGACY_INTAKE_RECEIPT.json"
ROUTE="StarterPlayer/StarterPlayerScripts/EGGRUMBLE_CastleBannerWind"
TARGET="sources/StarterPlayer/StarterPlayerScripts/EGGRUMBLE_CastleBannerWind.client.luau"
NEW=THIS/"EGGRUMBLE_CastleBannerWind.client.luau"
FEATURE="GQ470_FB015_CASTLE_BANNER_WIND_20261121"
REPORT="GQ470_BANNER_REAL70_CANDIDATE_RECEIPT.json"
B_PACKET="B220_BANNER_ONE_NEW_CLIENT_NOT_FORMAL"
MANIFEST="SOURCE_SELECT_MANIFEST.json"

def require(cond:bool, code:str):
    if not cond: raise ValueError("RED_GQ470_BANNER_"+code)

def digest(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()

def compose(original:Path, out:Path):
    original,out=original.resolve(),out.resolve()
    require(original.is_dir() and not out.exists() and original!=out,"INPUT")
    raw=(original/ORIGINAL_PLACE).read_bytes()
    require(len(raw)==PLACE_SIZE and digest(raw)==PLACE_SHA,"OFFICIAL_PLACE")
    receipt=json.loads((original/RECEIPT).read_text())
    require(receipt["canonical_build"] is True and
            receipt["build_head"]==BASE and receipt["selected_source_count"]==69 and
            receipt["official_branch"]=="rc/p0d-s1-kids-rc01","OFFICIAL_RECEIPT")
    old=project_scan(original,PROJECT)
    require(len(old)==69 and ROUTE not in old and
            set(old)==set(receipt["source_hashes"])==set(receipt["source_classes"]),"SOURCE69_SET")
    for key,obj in old.items():
        require(obj["sha256"]==receipt["source_hashes"][key] and
                obj["class"]==receipt["source_classes"][key],"SOURCE69_LOCK")
    # Assert precisely the existing field and preference owner; not new authority.
    field=old["ServerScriptService/EGGRUMBLE_FlagshipFieldArt"]
    field_body=(original/field["path"]).read_text()
    require('add("FB015Banner"' in field_body and
            'deco.Parent=castle' in field_body and
            'castle:FindFirstChild("StandardCore")' in field_body,"REAL_EXISTING_BANNERS")
    combat=old["StarterPlayer/StarterPlayerScripts/EGGRUMBLE_CombatFeel"]
    flag='player:GetAttribute("EGGRUMBLE_ReducedEffects")'
    require(flag in (original/combat["path"]).read_text() and
            flag in NEW.read_text(),"EXISTING_ACCESSIBILITY_PREF")
    shutil.copytree(original,out)
    proj=json.loads((out/PROJECT).read_text())
    scripts=proj["tree"]["StarterPlayer"]["StarterPlayerScripts"]
    require(ROUTE.rsplit("/",1)[-1] not in scripts,"NO_DUPLICATE_CLIENT")
    scripts[ROUTE.rsplit("/",1)[-1]]={"$path":TARGET}
    path=out/TARGET
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(NEW.read_bytes())
    (out/PROJECT).write_text(json.dumps(proj,indent=2,ensure_ascii=False)+"\n")
    now=project_scan(out,PROJECT)
    require(len(now)==70 and set(now)==set(old)|{ROUTE} and
            all(now[name]==value for name,value in old.items()),"ORIGINAL69_EXACT")
    require(now[ROUTE]["class"]=="LocalScript" and
            now[ROUTE]["sha256"]==digest(NEW.read_bytes()),"NEW_LOCAL_SCRIPT")
    info={
        "schema":"GQ470_BANNER_REAL70_PRIVATE_A_SOURCE_V1",
        "feature_id":FEATURE,
        "official_branch":"rc/p0d-s1-kids-rc01",
        "formal_base_sha":BASE,
        "candidate_current_git_sha":"SEE_PR_HEAD_AND_SAME_HEAD_CI",
        "candidate_script_count":70,
        "original_script_count_exact":69,
        "only_new_route":ROUTE,
        "only_new_source_sha256":digest(NEW.read_bytes()),
        "new_gameplay_authorities":0,
        "new_visual_parts":0,
        "animated_existing_parts_max":20,
        "max_distance_studs":110,
        "max_sway_degrees":3.5,
        "on_mobile_tick_seconds":0.32,
        "formal_rc_modified":False,
        "source_gate":"BUILD_PENDING",
        "native_off69_on70":"PENDING",
        "rojo_off69_on70":"PENDING",
        "studio_solo":"NOT_TESTED",
        "studio_2client":"NOT_TESTED",
        "android_15min":"NOT_TESTED",
        "comparison_screenshots":"0/32",
        "human_art":"NOT_TESTED",
        "art_gate":"ART_NO_GO",
        "fun_gate":"FUN_NO_GO",
        "owner_accepted":False,
        "b_admission":"DEFER_P0_PLAYER_NOT_VISIBLE_AND_910_PLAYABLE_FIRST",
        "rollback":"omit the optional new route; preserve all original 69 scripts byte exact",
    }
    (out/REPORT).write_text(json.dumps(info,indent=2,ensure_ascii=False)+"\n")
    print("GQ470_BANNER_ORIGINAL69_EXACT_PLUS_1_LOCAL70_PASS",digest(NEW.read_bytes()))
    return info

def export_b(on:Path,place:Path):
    on,place=on.resolve(),place.resolve()
    meta=json.loads((on/REPORT).read_text())
    route_map=project_scan(on,PROJECT)
    require(meta["official_branch"]=="rc/p0d-s1-kids-rc01" and
            meta["formal_base_sha"]==BASE and
            meta["candidate_script_count"]==70 and
            meta["original_script_count_exact"]==69 and
            meta["only_new_route"]==ROUTE and
            meta["formal_rc_modified"] is False and
            meta["art_gate"]=="ART_NO_GO" and meta["owner_accepted"] is False,"NOT_FALSE_GATE")
    raw=(on/TARGET).read_bytes()
    require(len(route_map)==70 and route_map[ROUTE]["class"]=="LocalScript" and
            digest(raw)==route_map[ROUTE]["sha256"]==meta["only_new_source_sha256"],"SOURCE_LOCK")
    require(place.is_file() and place.stat().st_size>PLACE_SIZE and
            digest(place.read_bytes())!=PLACE_SHA,"REAL_ON70_PLACE")
    packet=on/B_PACKET
    require(not packet.exists(),"NO_OVERWRITE")
    selected=packet/"selected_sources"/TARGET.removeprefix("sources/")
    selected.parent.mkdir(parents=True)
    selected.write_bytes(raw)
    manifest={
        "schema":"GQ470_BANNER_B220_SINGLE_NEW_SOURCE_V1",
        "feature_id":FEATURE,"formal_branch":"rc/p0d-s1-kids-rc01",
        "formal_base_sha":BASE,"new_source_route":ROUTE,
        "new_source_class":"LocalScript",
        "new_source_file":"selected_sources/"+TARGET.removeprefix("sources/"),
        "new_source_sha256":digest(raw),"new_source_bytes":len(raw),
        "original_sources_preserved":69,"candidate_sources":70,
        "candidate_place_bytes":place.stat().st_size,
        "candidate_place_sha256":digest(place.read_bytes()),
        "formal_rc_integrated":False,"b_admission":"DEFER_P0_FIRST",
        "authenticated_b220_writer_required":True,
        "studio_android":"NOT_TESTED",
        "art":"ART_NO_GO","owner_accepted":False
    }
    (packet/MANIFEST).write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+"\n")
    verify_b(packet,place)
    selftest(packet,place)
    print("GQ470_BANNER_B220_ONE_NEW_LOCAL_SOURCE_PACKET_PASS",place.stat().st_size)
    return manifest

def verify_b(packet:Path,place:Path):
    manifest=json.loads((packet/MANIFEST).read_text())
    expected={"selected_sources/"+TARGET.removeprefix("sources/"),MANIFEST}
    actual={x.relative_to(packet).as_posix() for x in packet.rglob("*") if x.is_file()}
    require(actual==expected,"EXACT_PACKET_FILE_SET")
    raw=(packet/manifest.get("new_source_file","missing")).read_bytes()
    require(manifest["schema"]=="GQ470_BANNER_B220_SINGLE_NEW_SOURCE_V1" and
            manifest["formal_base_sha"]==BASE and
            manifest["new_source_route"]==ROUTE and
            manifest["new_source_class"]=="LocalScript" and
            manifest["new_source_file"] in expected and
            manifest["new_source_sha256"]==digest(raw) and
            manifest["new_source_bytes"]==len(raw) and
            manifest["original_sources_preserved"]==69 and
            manifest["candidate_sources"]==70 and
            manifest["formal_rc_integrated"] is False and
            manifest["art"]=="ART_NO_GO" and
            manifest["owner_accepted"] is False and
            manifest["authenticated_b220_writer_required"] is True and
            manifest["candidate_place_bytes"]==place.stat().st_size and
            manifest["candidate_place_sha256"]==digest(place.read_bytes()),"MANIFEST_LOCK")

def selftest(packet:Path,place:Path):
    original=(packet/MANIFEST).read_bytes()
    for k,v in (
        ("formal_rc_integrated",True),
        ("art","ART_GO"),
        ("original_sources_preserved",1),
        ("new_source_sha256","0"*64),
        ("new_source_route","ServerScriptService/EGGRUMBLE_GameHost"),
        ("authenticated_b220_writer_required",False),
    ):
        try:
            x=json.loads(original)
            x[k]=v
            (packet/MANIFEST).write_text(json.dumps(x))
            try: verify_b(packet,place)
            except (ValueError,KeyError,FileNotFoundError):pass
            else:raise AssertionError("RED_B_PACKET_MUTANT_"+k)
        finally:(packet/MANIFEST).write_bytes(original)
    extra=packet/"FORBIDDEN_EXTRA.txt"
    extra.write_text("unexpected source")
    try:
        try:verify_b(packet,place)
        except ValueError:pass
        else:raise AssertionError("RED_B_PACKET_EXTRA_FILE")
    finally:extra.unlink()
    verify_b(packet,place)
    print("GQ470_BANNER_B220_SEVEN_FAIL_CLOSED_NEGATIVES_PASS")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--official",type=Path)
    p.add_argument("--out",type=Path)
    p.add_argument("--export-b",type=Path)
    p.add_argument("--place",type=Path)
    o=p.parse_args()
    if o.export_b is not None:
        require(o.place is not None,"PLACE_MISSING")
        export_b(o.export_b,o.place)
    else:
        require(o.official is not None and o.out is not None,"INPUT_MISSING")
        compose(o.official,o.out)
