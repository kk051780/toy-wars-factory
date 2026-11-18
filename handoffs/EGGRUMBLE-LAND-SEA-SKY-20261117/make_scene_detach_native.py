#!/usr/bin/env python3
"""Extract and execute the real Luau detach predicate; mutations must fail."""
from __future__ import annotations
import argparse
from pathlib import Path

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/"EGGRUMBLE_LandSeaSkyTraversal.server.luau"
BEGIN="-- GQ8_LSS_SCENE_DETACH_RETIRE_20261118_BEGIN"
END="-- GQ8_LSS_SCENE_DETACH_RETIRE_20261118_END"
PREDICATES=(
 "worldParentName~=LOBBY",
 "not withinWorkspace",
 "not sceneIsChild",
)
HARNESS=r"""
local LOBBY="EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW"
__ACTUAL_HELPER__
assert(shouldRetireDetachedScene(LOBBY,true,true)==false,"CURRENT_SCENE_FALSE")
assert(shouldRetireDetachedScene(nil,false,true)==true,"WORLD_UNPARENTED_TRUE")
assert(shouldRetireDetachedScene(LOBBY,false,true)==true,"OUTSIDE_WORKSPACE_TRUE")
assert(shouldRetireDetachedScene(LOBBY,true,false)==true,"DETACHED_VISUAL_TRUE")
assert(shouldRetireDetachedScene("OTHER_LOBBY",true,true)==true,"PARENT_CHANGED_TRUE")
assert(shouldRetireDetachedScene("TEAM_Arena",true,true)==true,"PARENT_REPLACED_TRUE")
assert(shouldRetireDetachedScene(LOBBY,true,true)==false,"HEALTHY_SCENE_RETAINS")
print("GQ8_LSS_SCENE_DETACH_NATIVE_7_CASES_PASS")
"""

def actual_helper(source:str|None=None)->str:
 s=SOURCE.read_text(encoding="utf-8") if source is None else source
 if s.count(BEGIN)!=1 or s.count(END)!=1:
  raise ValueError("RED_DETACH_MARKER_DRIFT")
 helper=s.split(BEGIN,1)[1].split(END,1)[0]
 if helper.count("local function shouldRetireDetachedScene(")!=1:
  raise ValueError("RED_DETACH_REAL_HELPER_ABSENT")
 for p in PREDICATES:
  if helper.count(p)!=1:
   raise ValueError("RED_DETACH_PREDICATE_DRIFT:"+p)
 if s.count("shouldRetireDetachedScene(\n")!=1:
  raise ValueError("RED_DETACH_NOT_WIRED_TO_HEARTBEAT")
 if "retireScene(true)" not in s or "world.Destroying:Connect(function() retireScene(false) end)" not in s:
  raise ValueError("RED_DETACH_RETIRE_MISSING")
 return helper

def generate(out_dir:Path)->None:
 helper=actual_helper()
 out_dir.mkdir(parents=True,exist_ok=True)
 (out_dir/"good.luau").write_text(HARNESS.replace("__ACTUAL_HELPER__",helper),encoding="utf-8")
 for i,p in enumerate(PREDICATES):
  mutated=helper.replace(p,"false",1)
  (out_dir/f"mutant{i}.luau").write_text(
   HARNESS.replace("__ACTUAL_HELPER__",mutated),encoding="utf-8")

if __name__=="__main__":
 ap=argparse.ArgumentParser()
 ap.add_argument("--out-dir",type=Path,required=True)
 args=ap.parse_args()
 generate(args.out_dir)
