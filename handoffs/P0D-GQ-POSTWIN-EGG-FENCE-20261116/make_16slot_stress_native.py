#!/usr/bin/env python3
"""Source-exact real Rules multi-seed TEAM/BR 16-slot invariants and negative mutant.
Imports the EXISTING #509 authoritative one-hunk provenance checker, no source
duplicated and no game logic rewritten in Python.
"""
import argparse
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parent
PATCH_MODULE=ROOT/"native_and_provenance.py"
RULES=ROOT.parent/"P0D-PQG-SEVEN-HERO-PLAYABLE-20261116"/"EGGRUMBLE_CastleMatchRules.luau"
STRESS=ROOT/"terminal_conservation_16slot.spec.luau"

def main():
 p=argparse.ArgumentParser()
 p.add_argument("--original",type=Path,required=True)
 p.add_argument("--out",type=Path,required=True)
 p.add_argument("--mutant-out",type=Path,required=True)
 a=p.parse_args()
 assert a.out.resolve()!=a.mutant_out.resolve()
 spec=importlib.util.spec_from_file_location("gq509_provenance",PATCH_MODULE)
 proof=importlib.util.module_from_spec(spec)
 spec.loader.exec_module(proof)
 source=proof.check_exact(a.original.resolve(strict=True),RULES.resolve(strict=True))
 test=STRESS.read_text(encoding="utf-8")
 assert test.count("local Rules=M")==1
 a.out.parent.mkdir(parents=True,exist_ok=True)
 a.out.write_text(proof.make_harness(source,test),encoding="utf-8")
 needle=' if m.phase~="ACTIVE" or m.winner~=nil then return 0,{} end\n'
 assert source.count(needle)==1
 mutant=source.replace(needle,"",1)
 a.mutant_out.write_text(proof.make_harness(mutant,test),encoding="utf-8")
 print("GQ509_16SLOT_STRESS_EXACT_RULES_AND_UNFENCED_MUTANT_READY")

if __name__=="__main__":main()
