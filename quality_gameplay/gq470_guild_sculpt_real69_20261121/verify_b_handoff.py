#!/usr/bin/env python3
"""B220 admission packet truth: reject stale, forged, extra-file and fake GO inputs.

This is A-only source provenance validation. It does NOT grant B writer auth.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path

BASE="e80973c354f14a0d0088577f3cc1a875454f0f8f"
ROUTE="ServerScriptService/GQ805_LobbyGuildShop"
SOURCE="selected_sources/ServerScriptService/GQ805_LobbyGuildShop.server.luau"
FILES={SOURCE,"B220_GUILD_MANIFEST.json","GQ470_GUILD_SOURCE_QA.json"}
ORIGINAL_SHA="139fb22fd8051635dc2f5a892777983c37dbe16cf741eb82cd213a829993ba6d"
CANDIDATE_SHA="0e679224cc36242384ce9f698838c356892a12daf15c3edf7a252b5b5d8446f3"
FEATURE="GQ470_FB015_GUILD_GUARDIAN_SCULPT_REAL69_20261121"

def guard(ok:bool,why:str)->None:
    if not ok:
        raise ValueError("RED_GQ470_B220_GUILD_"+why)

def check(manifest:dict,qa:dict,source:bytes,paths:set[str],head:str)->None:
    guard(set(paths)==FILES,"EXTRA_OR_MISSING_FILES")
    guard(len(head)==40 and all(c in "0123456789abcdef" for c in head),"HEAD_FORMAT")
    guard(manifest.get("candidate_head_exact")==head,"STALE_CANDIDATE_HEAD")
    guard(manifest.get("formal_base_head")==BASE==qa.get("formal_base_head"),"BASE_CHANGED")
    guard(manifest.get("feature_id")==FEATURE==qa.get("feature_id"),"FEATURE_COLLISION")
    guard(manifest.get("source_route")==ROUTE==qa.get("candidate_route"),"ROUTE_CHANGED")
    guard(manifest.get("class")=="Script","ROUTE_CLASS_CHANGED")
    guard(manifest.get("selected_source_path")==SOURCE,"SOURCE_PATH_CHANGED")
    guard(manifest.get("source_before_sha256")==ORIGINAL_SHA==qa.get("source_sha_before"),
          "ORIGINAL_PROVENANCE_CHANGED")
    guard(manifest.get("source_after_sha256")==CANDIDATE_SHA==qa.get("source_sha_after"),
          "CANDIDATE_SHA_CHANGED")
    guard(hashlib.sha256(source).hexdigest()==CANDIDATE_SHA,"BYTES_NOT_APPROVED")
    guard(manifest.get("other_selected_routes_byte_exact")==68 and
          qa.get("other_selected_byte_exact")==68,"OTHER68_NOT_PRESERVED")
    guard(manifest.get("candidate_source_count")==69 and
          qa.get("selected_script_count")==69,"SOURCE_ROUTE_COUNT")
    guard(manifest.get("original_artifact_id")==14610422120,"ORIGINAL_ARTIFACT")
    guard(manifest.get("new_part_count")==1 and qa.get("extra_decorative_parts")==1,
          "PART_BUDGET")
    guard(manifest.get("new_gameplay_authority") is False and
          qa.get("purchase_authority_changed") is False,"GAMEPLAY_AUTHORITY")
    guard(manifest.get("whole_pr_merge_forbidden") is True and
          manifest.get("A_no_formal_rc_write") is True and
          manifest.get("B_writer_must_reget_formal_sha_and_class") is True,
          "A_B_AUTHORITY")
    guard(manifest.get("source_only_if_same_head_success") is True and
          qa.get("rollback_byte_exact") is True,"ROLLBACK_OR_CI")
    guard(manifest.get("studio")==qa.get("studio")=="NOT_TESTED","FAKE_STUDIO_PASS")
    guard(manifest.get("android")==qa.get("android")=="NOT_TESTED","FAKE_ANDROID_PASS")
    guard(manifest.get("art_gate")==qa.get("art_gate")=="ART_NO_GO","FAKE_ART_GO")
    guard(manifest.get("owner_accepted") is False and
          qa.get("owner_accepted") is False,"FAKE_OWNER_ACCEPTED")
    guard(qa.get("official_rc_adopted") is False,"FAKE_FORMAL_RC")

def verify_bundle(root:Path,head:str)->int:
    files={str(p.relative_to(root)):p.read_bytes() for p in root.rglob("*") if p.is_file()}
    guard(set(files)==FILES,"ACTUAL_PACKET_FILES")
    m=json.loads(files["B220_GUILD_MANIFEST.json"])
    qa=json.loads(files["GQ470_GUILD_SOURCE_QA.json"])
    check(m,qa,files[SOURCE],set(files),head)
    negatives=[
        ("candidate HEAD", {"candidate_head_exact":"f"*40},{},None,None),
        ("formal BASE", {"formal_base_head":"f"*40},{},None,None),
        ("feature", {"feature_id":"OTHER_ID"},{},None,None),
        ("route", {"source_route":"ServerScriptService/EGGRUMBLE_Game"},{},None,None),
        ("class", {"class":"ModuleScript"},{},None,None),
        ("source path", {"selected_source_path":"selected_sources/bad.lua"},{},None,None),
        ("source before SHA", {"source_before_sha256":"0"*64},{},None,None),
        ("source after SHA", {"source_after_sha256":"0"*64},{},None,None),
        ("source payload", {},{},files[SOURCE]+b"forged",None),
        ("extra path", {},{},None,set(files)|{"forged.log"}),
        ("other source count", {"other_selected_routes_byte_exact":67},{},None,None),
        ("new parts", {"new_part_count":900},{},None,None),
        ("invented game authority", {"new_gameplay_authority":True},{},None,None),
        ("whole PR merge", {"whole_pr_merge_forbidden":False},{},None,None),
        ("disable B identity", {"B_writer_must_reget_formal_sha_and_class":False},{},None,None),
        ("hide engine warning", {"art_gate":"ART_GO"},{},None,None),
        ("fake owner", {"owner_accepted":True},{},None,None),
        ("fake android", {},{"android":"PASSED"},None,None),
        ("fake studio", {},{"studio":"PASSED"},None,None),
        ("fake RC", {},{"official_rc_adopted":True},None,None),
    ]
    count=0
    for label,dm,dq,bytechange,pathchange in negatives:
        try:
            check({**m,**dm},{**qa,**dq},files[SOURCE] if bytechange is None else bytechange,
                  set(files) if pathchange is None else pathchange,head)
        except ValueError:
            count+=1
        else:
            raise AssertionError("RED_GQ470_B220_GUILD_MUTANT_ACCEPTED_"+label)
    guard(count==len(negatives)==20,"MUTATION_CASE_COUNT")
    print("GQ470_GUILD_B220_REAL_PACKET_20_NEGATIVES_PASS",head,
          "file_count",len(files),"source_sha256",CANDIDATE_SHA)
    return count

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--bundle",type=Path,required=True)
    parser.add_argument("--candidate-head",required=True)
    a=parser.parse_args()
    verify_bundle(a.bundle,a.candidate_head)
