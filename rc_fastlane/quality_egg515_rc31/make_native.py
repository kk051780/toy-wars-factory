#!/usr/bin/env python3
"""Build author-original 18-scenario native Luau harness, no fake game engine."""
import argparse
import hashlib
from pathlib import Path

BLOB="3114c469169ad667978485d5b8d0b038a2dbd4f5"
ap=argparse.ArgumentParser()
ap.add_argument("--policy",type=Path,required=True)
ap.add_argument("--spec",type=Path,required=True)
ap.add_argument("--out",type=Path,required=True)
a=ap.parse_args()
source=a.policy.read_bytes()
sha=hashlib.sha1(b"blob "+str(len(source)).encode()+b"\0"+source).hexdigest()
if sha!=BLOB:raise ValueError("RED_GQ515_AUTHOR_POLICY_BLOB_DRIFT")
body=source.decode("utf-8")
if not body.rstrip().endswith("return Drop") or body.count("function Drop.recover(")!=1:
 raise ValueError("RED_GQ515_NATIVE_POLICY_STRUCTURE_CHANGED")
spec=a.spec.read_text(encoding="utf-8")
if "EGGRUMBLE_FIELD_EGG_RECOVERY_NATIVE_PASS" not in spec or "check(c.x==-215" not in spec:
 raise ValueError("RED_GQ515_NATIVE_NEGATIVE_SCENARIOS_MISSING")
a.out.parent.mkdir(parents=True,exist_ok=True)
a.out.write_text(body.rsplit("return Drop",1)[0]+"\n"+spec,encoding="utf-8")
print("GQ515_NATIVE_REAL_AUTHOR_18_CASES_HARNESS_SOURCE_EXACT_PASS")
