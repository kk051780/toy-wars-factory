#!/usr/bin/env python3
"""Native Luau tests use the exact GIT-BLOB pinned real production director module."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
feature=ROOT/"rc_fastlane/features/talking_npc"
def blob(b):
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\x00"+b).hexdigest()
def run(out):
    raw=(feature/"TalkingNPCDirector.luau").read_bytes()
    lock=json.loads((feature/"PREP_SOURCE_LOCK.json").read_text("utf8"))
    assert blob(raw)==lock["files"]["TalkingNPCDirector.luau"],"DIRECTOR_PIN_DRIFT"
    pure=raw.decode("utf8")
    assert pure.rstrip().endswith("return Director"),"DIRECTOR_RETURN_DRIFT"
    tests=(Path(__file__).with_name("p0d_talking_director_native.luau")).read_text("utf8")
    assert tests.count('check("')==42
    assert 'assert(n==42' in tests
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text("-- SOURCE EXTRACTED AND PINNED\n"+pure.rsplit("return Director",1)[0]+"\n"+tests,"utf8")
    print("P0D_TALK_DIRECTOR_SOURCE_EXACT_NATIVE_READY",blob(raw))
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();run(a.out)
