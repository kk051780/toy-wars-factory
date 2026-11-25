#!/usr/bin/env python3
"""Run true 31-source selective original #583 Rules Native/Rojo acceptance.

Executes original author source tests and original vs fixed actual Luau VM;
checks other 30 exact and output Place XML 31/31 source/class. Not Studio.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess
import sys

import select_original_roster583 as s


def run(*args):
    subprocess.run([str(a) for a in args], check=True)


def build(base: Path, out: Path, compiler: Path, vm: Path, rojo: Path) -> dict:
    source = Path("_gq583_original/quality_gameplay/v3_roster_hardcap16_20261116")
    run(sys.executable,"-B","-m","unittest","discover","-s",source,"-p","test_*.py","-v")
    run(sys.executable,"-B","-m","unittest","discover","-s",
        "rc_fastlane/quality_roster583_rc31","-p","test_selection.py","-v")
    author, original, fixed = s.load_author()
    project, before = s.map_sources(base)
    route = next(r for r in before if r[-1] == s.RULES)
    old_raw = before[route].read_bytes()
    if s.git_blob(old_raw) != s.ORIGINAL_RULES_BLOB:
        raise ValueError("RED Rules in latest actual RC31 is not exact original #482")
    if original != old_raw.decode("utf-8"):
        raise ValueError("RED original source diverged from current existing Rules")
    receipt = s.select(base,out,s.ORIGINAL_RULES_BLOB)
    selected_proj = out/"GQ583_SELECTED31.project.json"
    _, current = s.map_sources(selected_proj)
    if len(current)!=31:
        raise ValueError("RED must keep 31 actual scripts")
    for path in current.values():
        with open("/dev/null", "wb") as discard:
            subprocess.run([str(compiler),"--text",str(path)],check=True,stdout=discard)
    print("GQ583_CURRENT_OFFICIAL31_ALL_NATIVE_PASS",flush=True)
    for what,source_text,allow in [("original",original,True),("fixed",fixed,False)]:
        harness = out/f"GQ583_{what.upper()}_NATIVE.spec.luau"
        harness.write_text(author.native_harness(source_text,allow),encoding="utf-8")
        with open("/dev/null", "wb") as discard:
            subprocess.run([str(compiler),"--text",str(harness)],check=True,stdout=discard)
        run(vm,harness)
    print("GQ583_ORIGINAL_TEAM_BR_16_AND_REJECT_17_32_NATIVE_DIFFERENTIAL_PASS",flush=True)
    place = out/"GQ583_CURRENT_31_TRUE_ROJO.rbxlx"
    run(rojo,"build",selected_proj,"-o",place)
    verified = s.verify(base,selected_proj,place)
    if not (verified["source_exact"]=="31/31"
            and verified["other_30_scripts_byte_exact"]
            and verified["existing_only_one_rules_changed"]
            and verified["off_rollback_byte_exact"]
            and receipt["changed_guards"]==2):
        raise ValueError("RED original #583 candidate verification failed")
    (out/"GQ583_REAL_ROJO_RECEIPT.json").write_text(
        json.dumps(verified,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"
    )
    print("GQ583_ORIGINAL_TWO_GUARDS_ONE_RULES_OTHER30_TRUE_ROJO_PASS",
          verified["place_bytes"],verified["place_sha256"],flush=True)
    return verified


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--base",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--compiler",type=Path,default=Path("/tmp/gq530_all31_native/luau-compile"))
    p.add_argument("--vm",type=Path,default=Path("/tmp/gq530_all31_native/luau"))
    p.add_argument("--rojo",type=Path,default=Path("/tmp/gq530-all31-rojo"))
    x=p.parse_args()
    print(json.dumps(build(x.base,x.out,x.compiler,x.vm,x.rojo),indent=2))
