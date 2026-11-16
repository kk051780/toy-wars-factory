#!/usr/bin/env python3
"""Verify the exact original RC artifact, isolated Host repair, and fail-closed cases."""
import argparse
import importlib.util
import json
from pathlib import Path
import xml.etree.ElementTree as ET

spec=importlib.util.spec_from_file_location("lobby",Path(__file__).with_name("patch_official_place.py"))
assert spec and spec.loader
lib=importlib.util.module_from_spec(spec)
spec.loader.exec_module(lib)

def expect_fail(fn, label):
    try:
        fn()
    except ValueError as exc:
        assert "RED_GQ8_LOBBY_VOID_" in str(exc), (label,exc)
    else:
        raise AssertionError("MISSING_NEGATIVE_GATE: "+label)

def run(original:Path,candidate:Path,receipt_path:Path):
    before=ET.fromstring(original.read_bytes())
    after=ET.fromstring(candidate.read_bytes())
    x=lib.scripts(before)
    y=lib.scripts(after)
    lib.require(lib.sha(original.read_bytes())==lib.PINNED_PLACE_SHA256,"ORIGINAL_SHA")
    receipt=lib.prove(before,after)
    assert receipt["source_count"]==31 and receipt["unchanged_source_count"]==30
    assert receipt["rollback_exact"]
    assert lib.sha(y[lib.HOST][2].replace(lib.INSERT,"",1).encode()) == lib.PINNED_HOST_SHA256
    recorded=json.loads(receipt_path.read_text())
    assert recorded["private_candidate_sha256"]==lib.sha(candidate.read_bytes())
    assert recorded["pinned_official_head"]==lib.PINNED_OFFICIAL_HEAD
    # New code must be strictly reversible and must not affect the 7-job,
    # field, combat, castle, neutral soldier, item, or balance owner scripts.
    assert len(set(x)-{lib.HOST})==30
    for k in x:
        if k!=lib.HOST:
            assert x[k][2]==y[k][2]
    expect_fail(lambda:lib.patch(x[lib.HOST][2]+"\n-- mutation\n"),"UNPINNED_AUTHOR")
    expect_fail(lambda:lib.patch(y[lib.HOST][2]),"DOUBLE_BOOTSTRAP")
    bad=ET.fromstring(candidate.read_bytes())
    lib.scripts(bad)[lib.HOST][1].text=lib.scripts(bad)[lib.HOST][2].replace(
        "lobbySafetyFloor.CanCollide=true","lobbySafetyFloor.CanCollide=false",1)
    expect_fail(lambda:lib.prove(before,bad),"NONCOLLIDING_FLOOR")
    bad=ET.fromstring(candidate.read_bytes())
    s=lib.scripts(bad)[lib.HOST]
    s[1].text=s[2].replace("if mode and sessions[mode] then return end","if false then return end",1)
    expect_fail(lambda:lib.prove(before,bad),"ACTIVE_PLAYER_TELEPORT")
    bad=ET.fromstring(candidate.read_bytes())
    s=lib.scripts(bad)[lib.HOST]
    s[1].text=s[2].replace('Instance.new("SpawnLocation")','Instance.new("Part")',1)
    expect_fail(lambda:lib.prove(before,bad),"NO_SPAWNLOCATION")
    bad=ET.fromstring(candidate.read_bytes())
    other=next(k for k in x if k!=lib.HOST)
    s=lib.scripts(bad)[other]
    s[1].text=s[2]+"\n-- mutation\n"
    expect_fail(lambda:lib.prove(before,bad),"FOREIGN_SCRIPT_CHANGED")
    print("GQ8_LOBBY_VOID_ORIGINAL_RC31_31_EXACT_6_NEGATIVES_PASS")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--original",required=True,type=Path)
    p.add_argument("--candidate",required=True,type=Path)
    p.add_argument("--receipt",required=True,type=Path)
    a=p.parse_args()
    run(a.original,a.candidate,a.receipt)
