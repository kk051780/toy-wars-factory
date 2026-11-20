#!/usr/bin/env python3
"""Exact two-file, single selected source B220 admission packet for FB015 SkillFX.
Not an official branch write, Roblox publish, art pass or game-playable assertion.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import tempfile
from pathlib import Path
from patch_skillfx69 import BASE, FEATURE, ROUTE, OFF, RECEIPT, selected, sha, transform, require

PACKET="B220_SKILLFX_ONE_SELECTED_SOURCE_NOT_FORMAL"
MANIFEST="B220_SKILLFX_PREP_READY_MANIFEST.json"
SOURCE_PATH="selected_sources/"+ROUTE+".luau"

def evidence(root:Path,head:str)->tuple[bytes,dict]:
    require(bool(re.fullmatch(r"[a-f0-9]{40}",head)) and head!=BASE,
            "CANDIDATE_HEAD_EXACT")
    current=selected(root)
    previous=selected(root/OFF)
    require(len(current)==len(previous)==69 and set(current)==set(previous),
            "CANONICAL69_SOURCE_SETS")
    require({name for name in current
             if current[name].read_bytes()!=previous[name].read_bytes()}=={ROUTE},
            "ONLY_SKILLFX_SELECTED_ROUTE_CHANGED")
    original=previous[ROUTE].read_bytes()
    modified=current[ROUTE].read_bytes()
    require(transform(original.decode("utf-8")).encode("utf-8")==modified,
            "ACTUAL_TRANSFORM_COMMITTED")
    receipt=json.loads((root/RECEIPT).read_text())
    hashes={name:sha(path.read_bytes()) for name,path in current.items()}
    require(receipt.get("build_head")==BASE and receipt.get("canonical_build") is True
            and receipt.get("source_hashes")==hashes and len(hashes)==69,
            "SELECTED69_HASH_LOCK")
    row=receipt.get("gq470_skillfx_shard_flash",{})
    require(row.get("feature_id")==FEATURE
            and row.get("source_route")==ROUTE
            and row.get("source_sha_after")==sha(modified)
            and row.get("source_sha_before")==sha(original)
            and row.get("other_selected_sources_byte_exact")==68
            and row.get("official_rc_adopted") is False,
            "ACTUAL_ART_HONESTY")
    return modified,{
        "P0D_PREP_READY_V1":"YES_SOURCE_ONLY",
        "PINNED_HEAD":head,
        "BASE_RC":BASE,
        "FEATURE_IDS":[FEATURE],
        "SOURCE_LOCK":{
            "selected_route":ROUTE,"original_sha256":sha(original),
            "candidate_sha256":sha(modified),
            "changed_selected_routes":1,"unchanged_selected_routes":68,
            "on_off_selected_route_count":69
        },
        "ROLLBACK":OFF,
        "SOURCE_SELECT_ONLY":True,
        "source_class":"ModuleScript",
        "NoAddedGameHostCombatHPScoreStoreRemote":True,
        "no_new_visual_instances":True,
        "part_count_before_after":[1,1],
        "formal_rc_adopted":False,
        "studio_solo":"NOT_TESTED",
        "studio_2client":"NOT_TESTED",
        "android15min":"NOT_TESTED",
        "human_art":"NOT_TESTED",
        "fun":"NOT_TESTED",
        "owner_accepted":False,
        "art_gate":"ART_NO_GO",
        "product_gate":"PRODUCT_NO_GO",
        "highest_priorities":["P0_910_PLAYABLE_LOOP","ART6_931"],
        "authorized_admission":"#220_ONLY_FRESH_EXPECTED_SHA_NONFORCE_CAS"
    }

def validate_packet(source:bytes,manifest:dict,target:Path)->None:
    require(target.is_dir(),"PACKET_MISSING")
    actual={f.relative_to(target).as_posix() for f in target.rglob("*") if f.is_file()}
    require(actual=={MANIFEST,SOURCE_PATH},"EXTRA_OR_MISSING_FILE")
    path=target/SOURCE_PATH
    require(path.read_bytes()==source,"SOURCE_EXACT_BYTES")
    supplied=json.loads((target/MANIFEST).read_text())
    require(supplied==manifest,"MANIFEST_DRIFT")
    require(supplied["SOURCE_LOCK"]["candidate_sha256"]==sha(source)
            and supplied["SOURCE_SELECT_ONLY"] is True
            and supplied["owner_accepted"] is False
            and supplied["formal_rc_adopted"] is False,
            "PACKET_SAFETY")

def build(root:Path,target:Path,head:str)->None:
    source,manifest=evidence(root,head)
    require(not target.exists(),"OUT_ALREADY_EXISTS")
    (target/SOURCE_PATH).parent.mkdir(parents=True)
    (target/SOURCE_PATH).write_bytes(source)
    (target/MANIFEST).write_text(
        json.dumps(manifest,sort_keys=True,ensure_ascii=False,indent=2)+"\n")
    validate_packet(source,manifest,target)
    print("B220_SKILLFX_ONLY_ONE_SOURCE_PREP_READY",sha(source))

def self_test()->None:
    dummy=b"-- valid stub\n"
    row={"SOURCE_LOCK":{"candidate_sha256":sha(dummy)},
         "SOURCE_SELECT_ONLY":True,"owner_accepted":False,"formal_rc_adopted":False}
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)/"packet"
        (root/SOURCE_PATH).parent.mkdir(parents=True)
        (root/SOURCE_PATH).write_bytes(dummy)
        (root/MANIFEST).write_text(json.dumps(row))
        validate_packet(dummy,row,root)
        for label,action in (
            ("SOURCE_DRIFT",lambda:(root/SOURCE_PATH).write_bytes(b"tampered")),
            ("MANIFEST_DRIFT",lambda:(root/MANIFEST).write_text("{}")),
            ("EXTRA_FILE",lambda:(root/"hidden.luau").write_text("injected")),
        ):
            # restore before each test
            (root/SOURCE_PATH).write_bytes(dummy)
            (root/MANIFEST).write_text(json.dumps(row))
            (root/"hidden.luau").unlink(missing_ok=True)
            action()
            try:validate_packet(dummy,row,root)
            except ValueError:continue
            raise AssertionError("RED_B220_"+label+"_MUTANT_ACCEPTED")
    print("B220_SKILLFX_3_ADMISSION_MUTANTS_REJECTED")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--candidate",type=Path)
    p.add_argument("--out",type=Path)
    p.add_argument("--head")
    p.add_argument("--check",action="store_true")
    args=p.parse_args()
    if args.self_test:
        self_test()
    else:
        require(args.candidate is not None and args.out is not None
                and args.head is not None,"REQUIRED_ARGS")
        source,manifest=evidence(args.candidate,args.head)
        if args.check:
            validate_packet(source,manifest,args.out)
            print("B220_SKILLFX_SOURCE_RECHECK_PASS")
        else:
            build(args.candidate,args.out,args.head)
