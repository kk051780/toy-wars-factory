#!/usr/bin/env python3
"""Source-exact native harness: original #482 Rules + original #515 policy.
No Python simulation of gameplay. Original source bodies preserved byte-for-byte.
"""
import argparse
import hashlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
POLICY=ROOT/"EGGRUMBLE_FieldEggDropBounds.luau"
SPEC=ROOT/"tests/spec_real_rules_cross_domain.luau"

def digest(blob:bytes)->str:
    return hashlib.sha256(blob).hexdigest()

def build(original:Path,output:Path):
    raw=original.resolve(strict=True).read_bytes()
    policy=POLICY.read_bytes()
    assert raw.rstrip().endswith(b"return M"),"original castle rules changed"
    assert policy.rstrip().endswith(b"return Drop"),"authored drop policy changed"
    assert raw.count(b"function M.onCarrierEliminated(")==1
    assert raw.count(b"function M.auditEggConservation(")==1
    assert raw.count(b"function M.takeFieldEgg(")==1
    assert policy.count(b"function Drop.recover(")==1
    script=(
        b"local function loadOriginalRules()\n"+raw+b"\nend\n"
        +b"local function loadCandidateBounds()\n"+policy+b"\nend\n"
        +SPEC.read_bytes()
    )
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_bytes(script)
    receipt=output.with_suffix(".receipt.txt")
    receipt.write_text(
        "ORIGINAL_RULES_SHA256="+digest(raw)+"\n"
        +"CANDIDATE_BOUNDS_SHA256="+digest(policy)+"\n"
        +"NATIVE_HARNESS_SHA256="+digest(script)+"\n"
        +"NO_MOCKED_CASTLE_RULES=TRUE\n",
        encoding="utf-8"
    )
    print("GQ515_REAL_ORIGINAL_RULES_NATIVE_HARNESS_READY",digest(raw),digest(policy))

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--rules",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    build(args.rules,args.out)
