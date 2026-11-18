#!/usr/bin/env python3
"""Execute original author #777 REAL Luau with current-human stale target/healer mutants."""
from __future__ import annotations
import argparse,importlib.util
from pathlib import Path
from compose_fence import CURRENT_GUARD,CURRENT_MARK,ALLY_GUARD,ALLY_MARK

def load_harness(original_harness:Path):
 spec=importlib.util.spec_from_file_location("original_mage_vm777",str(original_harness))
 mod=importlib.util.module_from_spec(spec)
 spec.loader.exec_module(mod)
 return mod.HARNESS

def write_cases(patched_source:Path,original_harness:Path,out:Path):
 src=patched_source.read_text(encoding="utf-8")
 if not src.rstrip().endswith("return Rescue") or src.count(CURRENT_GUARD)!=1 or src.count(ALLY_GUARD)!=1:
  raise ValueError("RED_FENCED_SOURCE_NOT_GENUINE")
 body=src.rstrip()[:-len("return Rescue")]
 raw=load_harness(original_harness)
 original='["13"]={alive=true,team="BLUE"}}}}\nmod.attach(session,patient,"WARRIOR")'
 replacement='["13"]={alive=true,team="BLUE"}}}}\n' + (
  'session.isCurrentHuman=function(player)\n'
  ' return player.Parent==Players and (player==patient or player==healer or player==enemy)\n'
  'end\n'
  'local originalCurrent=session.isCurrentHuman\n'
  'mod.attach(session,patient,"WARRIOR")\n'
  'session.isCurrentHuman=function(player) return player~=patient and originalCurrent(player) end\n'
  'h.Health=18;h.HealthChanged:Fire(18)\n'
  'assert(patient:GetAttribute("EGGRUMBLE_Downed")~=true,"RED_STALE_TARGET_DOWNED")\n'
  'h.Health=100;h.HealthChanged:Fire(100)\n'
  'session.isCurrentHuman=originalCurrent'
 )
 if raw.count(original)!=1:raise ValueError("RED_ORIGINAL_MEMBER_TEST_FIXTURE")
 text=raw.replace(original,replacement,1)
 before='prompt.Triggered:Fire(healer)\nassert(patient:GetAttribute("EGGRUMBLE_Downed")==false,"RED_MAGE_REVIVE_FAILED")'
 after=('session.isCurrentHuman=function(player) return player~=healer and originalCurrent(player) end\n'
    'prompt.Triggered:Fire(healer)\n'
    'assert(patient:GetAttribute("EGGRUMBLE_Downed")==true,"RED_STALE_HEALER_REVIVE")\n'
    'session.isCurrentHuman=originalCurrent\n'+before)
 if text.count(before)!=1:raise ValueError("RED_ORIGINAL_HEALER_FIXTURE")
 text=text.replace(before,after,1)
 out.mkdir(parents=True,exist_ok=True)
 for name,variant in (("good",body),
   ("target_mutant",body.replace(CURRENT_GUARD,CURRENT_MARK,1).replace(" or not s.isCurrentHuman(target)","",1)),
   ("healer_mutant",body.replace(ALLY_GUARD,ALLY_MARK,1))):
  (out/(name+".luau")).write_text(text.replace("__MODULE__",variant),encoding="utf-8")
 print("GQ8_MAGE_MEMBERSHIP_REAL_NATIVE_GOOD_AND_2_MUTANTS_EMITTED")

if __name__=="__main__":
 p=argparse.ArgumentParser()
 for name in ("source","harness","out"):p.add_argument("--"+name,required=True,type=Path)
 a=p.parse_args()
 write_cases(a.source,a.harness,a.out)
