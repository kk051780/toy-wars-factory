#!/usr/bin/env python3
"""Destructive upload/ART receipt mutants. Genuine A data is separately re-downloaded.
This test intentionally expects every forgery to be rejected, not accepted as ART_GO.
"""
from __future__ import annotations
import argparse
import json
import shutil
import tempfile
from pathlib import Path
from xml.etree import ElementTree as ET

from verify_postupload import verify, B_MANIFEST, B_SOURCE, ART, NEW_PLACE, ORIGINAL_PLACE

def rewrite_json(path: Path, field: str, value):
    data = json.loads(path.read_text(encoding="utf-8"))
    data[field] = value
    path.write_text(json.dumps(data,ensure_ascii=False),encoding="utf-8")

def corrupt(path: Path):
    path.write_bytes(path.read_bytes()+b"\nFAKE_TAMPERED_NOT_OFFICIAL\n")

def mutate(code: str, a: Path, o: Path, c: Path) -> None:
    if code.startswith("MANIFEST:"):
        field,value = json.loads(code.split(":",1)[1])
        rewrite_json(a/B_MANIFEST,field,value)
    elif code.startswith("REPORT:"):
        field,value = json.loads(code.split(":",1)[1])
        rewrite_json(a/ART,field,value)
    elif code.startswith("RECEIPT:"):
        field,value = json.loads(code.split(":",1)[1])
        rewrite_json(a/"on70/GQ470_PLAYER_CONTACT_SHADOW_SOURCE_RECEIPT.json",field,value)
    elif code == "ORIGINAL_PLACE":
        corrupt(o/ORIGINAL_PLACE)
    elif code == "CANDIDATE_PLACE":
        corrupt(a/NEW_PLACE)
    elif code == "B_SOURCE":
        corrupt(a/B_SOURCE)
    elif code == "HEAD_SOURCE":
        corrupt(c)
    elif code == "EXTRA_FILE":
        (a/"UNEXPECTED_ADOPTION_APPROVAL.txt").write_text("ART_GO\n")
    elif code == "MISSING_ART":
        (a/ART).unlink()
    else:
        raise AssertionError("BAD_TEST_"+code)

MUTATIONS = [
    'MANIFEST:["formal_integrated",true]',
    'MANIFEST:["owner_accepted",true]',
    'MANIFEST:["art_status","ART_GO"]',
    'MANIFEST:["candidate_selected_sources",69]',
    'MANIFEST:["original_selected_sources_preserved",1]',
    'MANIFEST:["new_source_sha256","fake"]',
    'MANIFEST:["new_script_class","ServerScript"]',
    'MANIFEST:["candidate_place_bytes",0]',
    'REPORT:["comparison_image_count",32]',
    'REPORT:["studio_solo","PASS"]',
    'RECEIPT:["formal_integrated",true]',
    'ORIGINAL_PLACE',
    'CANDIDATE_PLACE',
    'B_SOURCE',
    'HEAD_SOURCE',
    'EXTRA_FILE',
    'MISSING_ART',
]

def run(artifact: Path, original: Path, current: Path) -> None:
    before = verify(artifact,original,current)
    assert before["stage"] == "POSTUPLOAD_SOURCE_EXACT_NOT_STUDIO"
    for code in MUTATIONS:
        with tempfile.TemporaryDirectory(prefix="gq470_mutant_") as td:
            root=Path(td)
            a,o,c=root/"a",root/"off",root/"source.luau"
            shutil.copytree(artifact,a)
            shutil.copytree(original,o)
            c.write_bytes(current.read_bytes())
            mutate(code,a,o,c)
            try:
                verify(a,o,c)
            except (ValueError, FileNotFoundError, ET.ParseError, KeyError):
                pass
            else:
                raise AssertionError("RED_UPLOADED_FORGERY_ACCEPTED:"+code)
    print("GQ470_PLAYER_CONTACT_SHADOW_POSTUPLOAD_"+str(len(MUTATIONS))+"_FORGED_RECEIPTS_REJECTED")

if __name__ == "__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--artifact",type=Path,required=True)
    ap.add_argument("--original",type=Path,required=True)
    ap.add_argument("--current",type=Path,required=True)
    a=ap.parse_args()
    run(a.artifact,a.original,a.current)
