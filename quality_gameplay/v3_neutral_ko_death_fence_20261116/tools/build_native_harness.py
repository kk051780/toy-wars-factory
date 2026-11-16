#!/usr/bin/env python3
"""Run actual authored ModuleScript body, not a Python rewrite, using native Luau."""
from pathlib import Path
import argparse

ROOT=Path(__file__).resolve().parents[1]
def generate():
    original=(ROOT/"EGGRUMBLE_NeutralKoDeathFence.luau").read_text(encoding="utf-8")
    spec=(ROOT/"tests/spec_native.luau").read_text(encoding="utf-8")
    assert original.rstrip().endswith("return Fence")
    assert original.count("function Fence.mayCredit(")==1
    assert original.count("function Fence.decide(")==1
    return original.rsplit("return Fence",1)[0] + "\n" + spec

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    a.out.write_text(generate(),encoding="utf-8")
    print("REAL_KO_FENCE_BODY_NATIVE_HARNESS",a.out)
