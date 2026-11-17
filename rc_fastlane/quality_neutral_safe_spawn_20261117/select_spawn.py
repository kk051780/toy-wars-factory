#!/usr/bin/env python3
"""GQ8 neutral soldier spawn: valid walkable footprint + wall overlap gate.
One canonical Swarm source replacement, 30 others byte-identical; reversible.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import os
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

sys.path.insert(0,str(Path("rc_fastlane/quality_rc81_hit042_v3").resolve()))
from select_hit042 import flatten, class_for

FEATURE="GQ8_NEUTRAL_SPAWN_CLEARANCE_20261117"
MODULE="EGGRUMBLE_SwarmCombat"
MARK="-- GQ8_NEUTRAL_SPAWN_CLEARANCE_BEGIN"
BLOCK_ANCHOR=" local function addEnemy(at:Vector3)\n"
INSERT=''' -- GQ8_NEUTRAL_SPAWN_CLEARANCE_BEGIN
 -- Bound spawn checks: no new AI owner, loop, player state or remote.
 local SPAWN_ATTEMPTS=3
 local spawnFloor=session.world:FindFirstChild("TacticalBattlefield")
 local spawnOverlap=OverlapParams.new()
 spawnOverlap.FilterType=Enum.RaycastFilterType.Exclude
 spawnOverlap.FilterDescendantsInstances={all}
 spawnOverlap.RespectCanCollide=true
 local function neutralWithinArena(point:Vector3,floor:BasePart):boolean
  local margin=6
  return floor.Size.X>margin*2 and floor.Size.Z>margin*2
   and math.abs(point.X-floor.Position.X)<=floor.Size.X*.5-margin
   and math.abs(point.Z-floor.Position.Z)<=floor.Size.Z*.5-margin
 end
 local function neutralSpawnClear(point:Vector3):boolean
  if not spawnFloor or not spawnFloor:IsA("BasePart") then return false end
  if not neutralWithinArena(point,spawnFloor) then return false end
  -- Keep entire lightweight 5-stud-tall neutral body out of collidable parts.
  local parts=workspace:GetPartBoundsInBox(
   CFrame.new(point+Vector3.new(0,2.6,0)),Vector3.new(2.8,5.1,2.8),spawnOverlap)
  for _,obstacle in ipairs(parts) do
   if obstacle.CanCollide then return false end
  end
  return true
 end
 -- GQ8_NEUTRAL_SPAWN_CLEARANCE_END
'''
GUARD='''  -- Validate BEFORE reserving neutral budget or creating a Humanoid.
  local usable:Vector3?=nil
  for _attempt=1,SPAWN_ATTEMPTS do
   local point=if _attempt==1 then at else
    at+Vector3.new(math.random(-12,12),0,math.random(-12,12))
   if neutralSpawnClear(point) then
    usable=point
    break
   end
  end
  if not usable then return end
  at=usable
'''
NEW_BLOCK=INSERT+BLOCK_ANCHOR+GUARD
SELECT_NAME="EGGRUMBLE_GQ8_NeutralSafeSpawn.luau"
RECEIPT="GQ8_NEUTRAL_SAFE_SPAWN_RECEIPT.json"

def sha256(raw:bytes)->str:return hashlib.sha256(raw).hexdigest()
def lookup(paths:dict)->tuple:
 target=[r for r in paths if r[-1]==MODULE]
 if len(target)!=1:raise ValueError("RED_NON_SINGLETON_SWARM")
 return target[0]

def patch(text:str)->str:
 if text.count(BLOCK_ANCHOR)!=1:
  raise ValueError("RED_SPAWN_OR_SWARM_DRIFT")
 if MARK in text or "neutralSpawnClear(point)" in text:
  raise ValueError("RED_DUPLICATE_SPAWN_PATCH")
 revised=text.replace(BLOCK_ANCHOR,NEW_BLOCK,1)
 if unpatch(revised)!=text:raise ValueError("RED_NONEXACT_ROLLBACK")
 return revised

def unpatch(text:str)->str:
 if text.count(NEW_BLOCK)!=1:
  raise ValueError("RED_REVERSE_DRIFT")
 return text.replace(NEW_BLOCK,BLOCK_ANCHOR,1)

def prepare(base:Path,out:Path)->None:
 if out.exists():raise ValueError("RED_PROJECT_ALREADY_EXISTS")
 proj,paths=flatten(base)
 route=lookup(paths)
 original=paths[route].read_bytes()
 changed=patch(original.decode("utf-8")).encode("utf-8")
 target=out.parent/SELECT_NAME
 if target.exists():raise ValueError("RED_PATCH_FILE_ALREADY_EXISTS")
 target.write_bytes(changed)
 edit=copy.deepcopy(proj)
 edit["name"]="EGGRUMBLE_V3_GQ8_NEUTRAL_SAFE_SPAWN_RC31"
 def rewrite(node,prefix=()):
  for key,v in node.items():
   if key.startswith("$"):continue
   r=prefix+(key,)
   if "$path" in v:
    v["$path"]=os.path.relpath(target if r==route else paths[r],
                                out.parent).replace(os.sep,"/")
   else:rewrite(v,r)
 rewrite(edit["tree"])
 out.write_text(json.dumps(edit,ensure_ascii=False,indent=2)+"\n")
 _,selected=flatten(out)
 if set(paths)!=set(selected):raise ValueError("RED_SELECTED_ROUTES_CHANGED")
 changed_paths=[r for r in paths if paths[r].read_bytes()!=selected[r].read_bytes()]
 if changed_paths!=[route]:raise ValueError("RED_NON_SWARM_CHANGED_"+str(changed_paths))
 print("GQ8_NEUTRAL_CURRENT31_SINGLE_SWARM_30_UNCHANGED_OFF_EXACT_PASS")

def scripts_in_place(place:Path)->dict:
 actual={}
 for item in ET.parse(place).getroot().iter("Item"):
  cls=item.get("class")
  if cls not in ("Script","LocalScript","ModuleScript"):continue
  props=item.find("Properties")
  if props is None:raise ValueError("RED_NO_PROPERTIES")
  name=props.findtext("string[@name='Name']")
  src=props.findtext("ProtectedString[@name='Source']")
  if src is None:src=props.findtext("string[@name='Source']")
  if not name or src is None or name in actual:raise ValueError("RED_ROJO_DUPLICATE")
  actual[name]=(cls,src.replace("\r\n","\n"))
 return actual

def verify(base:Path,out:Path,place:Path)->None:
 _,original=flatten(base)
 _,current=flatten(out)
 target=lookup(original)
 if set(original)!=set(current) or len(current)!=31:
  raise ValueError("RED_INCONSISTENT_31")
 for route in original:
  before=original[route].read_bytes()
  after=current[route].read_bytes()
  if route==target:
   if after!=patch(before.decode("utf-8")).encode("utf-8"):
    raise ValueError("RED_EXPECTED_SWARM_SOURCE")
   if unpatch(after.decode("utf-8")).encode("utf-8")!=before:
    raise ValueError("RED_SWARM_ROLLBACK")
  elif before!=after:raise ValueError("RED_OTHER30_CHANGED_"+str(route))
 embedded=scripts_in_place(place)
 if len(embedded)!=31 or set(embedded)!={r[-1] for r in current}:
  raise ValueError("RED_ROJO31_MISMATCH")
 for route,p in current.items():
  expected=(class_for(p),p.read_text(encoding="utf-8").replace("\r\n","\n"))
  if embedded[route[-1]]!=expected:raise ValueError("RED_SOURCE_OR_CLASS_"+str(route))
 receipt={
  "feature_id":FEATURE,
  "source_count":31,"changed_existing_source":"/".join(target),
  "other30_byte_exact":True,"off_returns_previous_swarm_exact":True,
  "spawn_attempts_max_per_requested_soldier":3,
  "obstacle_gate":"world GetPartBoundsInBox / RespectCanCollide true",
  "bounds_gate":"actual TacticalBattlefield footprint minus 6 studs",
  "no_additional_score_remote_game_or_spawn_controller":True,
  "real_rojo_source_class_exact":"31/31",
  "place_bytes":place.stat().st_size,"place_sha256":sha256(place.read_bytes()),
  "native":"TESTED_IN_SAME_HEAD_WORKFLOW",
  "studio_2client":"NOT_TESTED","android_15min":"NOT_TESTED",
  "owner_fun":"NO_GO","formal_rc":"CI_CANDIDATE_NOT_YET_ADOPTED"}
 (out.parent/RECEIPT).write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
 print("GQ8_NEUTRAL_SAFE_SPAWN_REAL_ROJO31_SOURCE_CLASS_EXACT_PASS",receipt["place_bytes"])

def native(project:Path,out:Path,mutant:Path)->None:
 _,files=flatten(project)
 source=files[lookup(files)].read_text(encoding="utf-8")
 key=" local function neutralWithinArena(point:Vector3,floor:BasePart):boolean\n"
 if source.count(key)!=1:raise ValueError("RED_NO_ACTUAL_ARENA_POLICY")
 policy=key+source.split(key,1)[1].split("\n end\n",1)[0]+"\n end\n"
 tests='''local floor={Position={X=0,Z=0},Size={X=200,Z=100}}
assert(neutralWithinArena({X=0,Z=0},floor))
assert(neutralWithinArena({X=94,Z=44},floor))
assert(not neutralWithinArena({X=95,Z=44},floor))
assert(not neutralWithinArena({X=94,Z=45},floor))
assert(not neutralWithinArena({X=-95,Z=0},floor))
assert(not neutralWithinArena({X=0,Z=-45},floor))
assert(not neutralWithinArena({X=0,Z=0},{Position={X=0,Z=0},Size={X=11,Z=100}}))
assert(neutralWithinArena({X=500,Z=5},{Position={X=500,Z=0},Size={X=200,Z=100}}))
print("GQ8_ACTUAL_SWARM_ARENA_FOOTPRINT_LUAU_NATIVE_8_PASS")
'''
 out.write_text(policy+tests)
 mutant.write_text(policy.replace("local margin=6","local margin=0",1)+tests)
 print("GQ8_ACTUAL_SELECTED_SWARM_POLICY_NATIVE_FIXTURE_CREATED")

def selftest()->None:
 original='local ignore=7\n'+BLOCK_ANCHOR+" local timer=true\nreturn ok\n"
 updated=patch(original)
 assert unpatch(updated)==original
 assert updated.count("GetPartBoundsInBox")==1
 assert updated.count("SPAWN_ATTEMPTS=3")==1
 assert updated.count("neutralWithinArena(point,spawnFloor)")==1
 for bad in (updated,original.replace(BLOCK_ANCHOR,""),original.replace(BLOCK_ANCHOR,BLOCK_ANCHOR*2)):
  try:patch(bad)
  except ValueError:pass
  else:raise AssertionError("RED_DRIFT_ACCEPTED")
 try:unpatch(original)
 except ValueError:pass
 else:raise AssertionError("RED_ROLLBACK_ACCEPTED")
 print("GQ8_SOURCE_PATCH_INVERSE_DRIFT_DUPLICATION_TESTS_PASS")

def main():
 a=argparse.ArgumentParser()
 a.add_argument("action",choices=("selftest","prepare","native","verify"))
 a.add_argument("--base",type=Path)
 a.add_argument("--out",type=Path)
 a.add_argument("--place",type=Path)
 a.add_argument("--mutant",type=Path)
 args=a.parse_args()
 if args.action=="selftest":selftest();return
 if not args.base or not args.out:a.error("--base --out required")
 if args.action=="prepare":prepare(args.base.resolve(strict=True),args.out.resolve())
 elif args.action=="verify":
  if not args.place:a.error("--place required")
  verify(args.base.resolve(strict=True),args.out.resolve(strict=True),args.place.resolve(strict=True))
 else:
  if not args.mutant:a.error("--mutant required")
  native(args.base.resolve(strict=True),args.out.resolve(),args.mutant.resolve())
if __name__=="__main__":main()
