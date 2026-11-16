#!/usr/bin/env python3
"""Source-exact original-author diff + native Luau positive and mutant harness.

This never writes source into a protected RC and never claims Roblox Studio QA.
"""
import argparse
import subprocess
from pathlib import Path

REPO=Path(__file__).resolve().parents[2]
ORIGINAL_REL="handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116/EGGRUMBLE_CastleMatchRules.luau"
ORIGINAL_BLOB="27da5ca1e9e6d9a7afe0674030e387f094ee7492"
PATCH_BLOB="ed87d70e7df94279af737871e8e439b9fc108d4f"
FIND="function M.onCarrierEliminated(m:any,id:any)\n local c=castleOf(m,id)\n"
REPLACE="""function M.onCarrierEliminated(m:any,id:any)
 -- Late Humanoid.Died callbacks may arrive after the decisive castle fall.
 -- The terminal result is immutable: do not mint field tokens or rewrite egg
 -- ownership/score events after winner is known. Keep active death idempotent.
 if m.phase~="ACTIVE" or m.winner~=nil then return 0,{} end
 local c=castleOf(m,id)
"""

def git_blob(path:Path)->str:
    return subprocess.check_output(["git","hash-object",str(path)],text=True).strip()

def make_harness(source:str, spec:str)->str:
    assert source.rstrip().endswith("\nreturn M")
    body=source.rstrip()[:-len("\nreturn M")]
    return body+"\n"+spec

def check_exact(original:Path,patched:Path)->str:
    assert git_blob(original)==ORIGINAL_BLOB, "author input source-lock changed"
    assert git_blob(patched)==PATCH_BLOB, "patched input source-lock changed"
    before=original.read_text(encoding="utf-8")
    after=patched.read_text(encoding="utf-8")
    assert before.count(FIND)==1, "original anchor missing or duplicated"
    assert after==before.replace(FIND,REPLACE), "unapproved author line changed"
    assert after.count('if m.phase~="ACTIVE" or m.winner~=nil then return 0,{} end')==1
    print("EXACT_AUTHOR_DIFF_PASS 1 function 6 insertion lines")
    return after

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--original",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--mutant-out",type=Path,required=True)
    args=p.parse_args()
    patched=REPO/ORIGINAL_REL
    source=check_exact(args.original,patched)
    spec=(Path(__file__).parent/"postwin_egg_fence_native.spec.luau").read_text(encoding="utf-8")
    valid=make_harness(source,spec)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(valid,encoding="utf-8")
    # Mutation control: deliberately remove only this fence and demand the same
    # native behavioral tests fail; static pattern checks alone are insufficient.
    mutant=source.replace(
        ' if m.phase~="ACTIVE" or m.winner~=nil then return 0,{} end\n',"",1)
    assert mutant!=source
    args.mutant_out.write_text(make_harness(mutant,spec),encoding="utf-8")
    print("NATIVE_HARNESSES_READY positive and negative")

if __name__=="__main__":
    main()
