#!/usr/bin/env python3
"""Generate real extracted orphan-craft Luau owner decision and negative mutants."""
from pathlib import Path
import importlib.util
import sys

ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("craft_owner_contract",ROOT/"test_orphan_craft.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
out=Path(sys.argv[1])
out.mkdir(parents=True,exist_ok=True)
base=mod.native_program()
mutants={
 "STALE_MATCH":(
  "if not matchHuman(owner,mode,world,role) then return false end",
  "if false then return false end",
  "GQ8_STALE_MATCH_CRAFT_KEPT"),
 "DEAD_OWNER":(
  "return hum~=nil and hum.Health>0",
  "return hum~=nil",
  "GQ8_DEAD_CRAFT_KEPT"),
 "NO_CHARACTER":(
  "local ch=owner.Character",
  "local ch=owner.noCharacter",
  "GQ8_VALID_CRAFT_WRONGLY_REMOVED"),
 "ALWAYS_TRUE":(
  "return hum~=nil and hum.Health>0",
  "return true",
  "GQ8_DEAD_CRAFT_KEPT"),
}
(out/"good.luau").write_text(base,encoding="utf-8")
for tag,(find,repl,expected_error) in mutants.items():
 assert base.count(find)==1,(tag,"SOURCE_DRIFT")
 mutant=base.replace(find,repl,1)
 assert mutant!=base
 (out/("mutant_"+tag+".luau")).write_text(mutant,encoding="utf-8")
 (out/("mutant_"+tag+".expected.txt")).write_text(expected_error+"\n",encoding="utf-8")
print("GQ8_LSS_OWNER_NATIVE_ACTUAL_EXTRACT_AND_4_MUTANTS_READY")
