#!/usr/bin/env python3
"""Use actual immutable checked-out P0D-018 Luau source to build Native test payload."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
MANIFEST=ROOT/"PREP_SOURCE_LOCK.json"
REPO=ROOT.parents[2]
def git_blob(b:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\x00"+b).hexdigest()

def generate(out:Path)->None:
    manifest=json.loads(MANIFEST.read_text("utf8"))
    assert manifest["schema"]=="P0D_CAPTURE_PREP_SOURCE_LOCK_V1"
    assert manifest["feature_id"]=="P0D-018"
    assert manifest["game_wired"] is False
    policy=(REPO/manifest["module_source"]).read_bytes()
    native=(REPO/manifest["native_fixture"]).read_bytes()
    assert git_blob(policy)==manifest["module_blob"],"CAPTURE_POLICY_BLOB_DRIFT"
    assert git_blob(native)==manifest["native_blob"],"CAPTURE_NATIVE_BLOB_DRIFT"
    src=policy.decode("utf8")
    suite=native.decode("utf8")
    assert src.count("return Capture")==1
    assert suite.count("check(")-1==18
    assert "assert(tests==18" in suite
    assert "Capture.begin(" in src and "Capture.rescue(" in src
    assert "OnServerEvent" not in src and "FireServer(" not in src
    code=src.rsplit("return Capture",1)[0]+"\n"+suite
    assert "print(\"CAPTURE_NATIVE_18_PASS\")" in code
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(code,encoding="utf8")
    print("P0D018_CAPTURE_EXACT_SOURCE_LOCK_PASS native18_not_yet_executed")

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    generate(args.out)
