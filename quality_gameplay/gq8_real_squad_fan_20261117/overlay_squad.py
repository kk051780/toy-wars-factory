#!/usr/bin/env python3
"""Select one reversible true-current31 Swarm source: tight horde squad fan.

The existing Swarm remains the only spawner/combat owner. The patch only changes
the radial positions of at most the existing SPAWN_BATCH neutral soldiers and
does not change existing target sampling, source count, damage, KO or lifetime.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPOSER = ROOT / "handoffs/EGGRUMBLE-LAND-SEA-SKY-20261117/compose_optional32.py"
s = importlib.util.spec_from_file_location("gq8_lss_existing_compose", COMPOSER)
assert s is not None and s.loader is not None
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)

NAME = "EGGRUMBLE_SwarmCombat"
FEATURE = "GQ8_ACTUAL_SWARM_SQUAD_FAN_20261117"
HELPER_ANCHOR = " session.swarm=api\n local lastSpawnAt=os.clock()\n task.spawn(function()\n"
HELPER = """ -- GQ8_ACTUAL_SWARM_SQUAD_FAN_BEGIN
 -- Pure bounded formation math; never writes KO, budget, score or target choice.
 local function gq8SquadFanAngle(bearing:number,index:number,total:number):number
  return bearing+(index-(total+1)*0.5)*0.12
 end
 -- GQ8_ACTUAL_SWARM_SQUAD_FAN_END
"""
OLD = """    for _=1,batch do
     local selected=EncounterFair.chooseIndex(encounterFairState,session,kinds)
      if selected==nil then break end
      local target=candidates[selected]
     local a=math.random()*math.pi*2
     local d=math.random(21,58)
     local at=target+Vector3.new(math.cos(a)*d,0,math.sin(a)*d)
     -- Always in the same wide battle district as its current moving hero.
     addEnemy(Vector3.new(at.X,session.groundY or target.Y-4,at.Z))
    end
"""
NEW = """    -- Keep original SpawnPacing.batch, per-soldier EncounterFair target draw,
    -- same total neutral budget and physical collision clearance.
    local squadBearing=math.random()*math.pi*2
    local fanGroup=math.min(batch,5)
    for squadIndex=1,batch do
     local selected=EncounterFair.chooseIndex(encounterFairState,session,kinds)
     if selected==nil then break end
     local target=candidates[selected]
     local fanSlot=(squadIndex-1)%fanGroup+1
     local a=gq8SquadFanAngle(squadBearing,fanSlot,fanGroup)
     local d=math.random(38,48)
     local at=target+Vector3.new(math.cos(a)*d,0,math.sin(a)*d)
     -- Same battle district; existing 3-attempt collision gate owns spawn.
     addEnemy(Vector3.new(at.X,session.groundY or target.Y-4,at.Z))
    end
"""


def patch(source: str) -> str:
    if source.count(HELPER_ANCHOR) != 1 or source.count(OLD) != 1:
        ix=source.find("SPAWN_BATCH")
        it=source.find("for _=1,math.min(SPAWN_BATCH")
        mid=source.find("session.swarm=api")
        pacing=source.find("lastSpawnAt=os.clock()")
        snippet=source[max(0,it-180):it+750] if it>=0 else source[max(0,pacing-80):pacing+2600]
        raise ValueError("RED_CURRENT_SWARM_FORMATION_ANCHOR_DRIFT"
           +" helper="+str(source.count(HELPER_ANCHOR))
           +" old="+str(source.count(OLD))
           +" mid="+repr(source[max(0,mid-40):mid+145])
           +" spawn="+repr(snippet))
    if "GQ8_ACTUAL_SWARM_SQUAD_FAN_BEGIN" in source:
        raise ValueError("RED_ALREADY_SELECTED")
    if "neutralSpawnClear(point)" not in source or "GetPartBoundsInBox" not in source:
        raise ValueError("RED_NO_EXISTING_PHYSICAL_SPAWN_CLEARANCE")
    new = source.replace(HELPER_ANCHOR, HELPER_ANCHOR + HELPER, 1)
    new = new.replace(OLD, NEW, 1)
    if unpatch(new) != source:
        raise ValueError("RED_INVERSE_NOT_EXACT")
    return new


def unpatch(source: str) -> str:
    if source.count(HELPER) != 1 or source.count(NEW) != 1:
        raise ValueError("RED_ROLLBACK_DRIFT")
    return source.replace(NEW, OLD, 1).replace(HELPER_ANCHOR+HELPER, HELPER_ANCHOR, 1)


def find(paths: dict) -> tuple:
    matches=[p for p in paths if p[-1]==NAME]
    if len(paths)!=31 or len(matches)!=1:
        raise ValueError("RED_NOT_CURRENT_SINGLE31_SWARM")
    return matches[0]


def compose(base: Path, out: Path) -> dict:
    base=base.resolve(strict=True)
    out=out.resolve()
    if base==out or out.exists():
        raise ValueError("RED_EXISTING_OUTPUT_OR_SOURCE")
    model, sources=m.flat(base)
    sw=find(sources)
    old=sources[sw].read_bytes()
    altered=patch(old.decode("utf-8")).encode("utf-8")
    selected=out.parent/"EGGRUMBLE_GQ8_REAL_SQUAD_FAN.luau"
    if selected.exists():
        raise ValueError("RED_PREEXISTING_PATCH_SOURCE")
    out.parent.mkdir(parents=True,exist_ok=True)
    selected.write_bytes(altered)
    candidate=copy.deepcopy(model)
    candidate["name"]="EGGRUMBLE_GQ8_REAL_SQUAD_FAN_CURRENT31"
    def rewrite(node, path=()):
        for key,val in node.items():
            if key.startswith("$"):continue
            route=path+(key,)
            if "$path" in val:
                val["$path"]=os.path.relpath(selected if route==sw else sources[route],out.parent).replace(os.sep,"/")
            else:rewrite(val,route)
    rewrite(candidate["tree"])
    out.write_text(json.dumps(candidate,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    _, after=m.flat(out)
    if set(after)!=set(sources) or len(after)!=31:
        raise ValueError("RED_SOURCE_SET_DRIFT")
    for route,oldpath in sources.items():
        before=oldpath.read_bytes()
        after_bytes=after[route].read_bytes()
        if route==sw:
            if after_bytes!=altered or unpatch(after_bytes.decode("utf-8")).encode("utf-8")!=before:
                raise ValueError("RED_EXPECTED_ONE_SWARM_PATCH")
        elif before!=after_bytes:
            raise ValueError("RED_OTHER_30_CHANGED "+"/".join(route))
    receipt={
      "feature_id":FEATURE,
      "base_project":str(base),
      "selected_project":str(out),
      "selected_squad_source":str(selected),
      "selected_source_count":31,
      "changed_existing":"/".join(sw),
      "other30_byte_exact":True,
      "off_original31_byte_exact":True,
      "same_original_target_selection":True,
      "same_shared_spawn_pacing_and_fair_target_choice":True,
      "actual_added_soldiers":0,
      "spawn_clearance_owner_untouched":True,
      "old_swarm_sha256":hashlib.sha256(old).hexdigest(),
      "new_swarm_sha256":hashlib.sha256(altered).hexdigest(),
      "formal_rc_adopted":False,
      "studio_android_fun":"NOT_TESTED"
    }
    out.with_suffix(".receipt.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n")
    print("GQ8_REAL_SWARM_SQUAD_FAN_ONE_CHANGED_30_EXACT_OFF31_PASS")
    return receipt


def native(source:Path, out:Path, mutant:Path):
    text=source.read_text(encoding="utf-8")
    start=" local function gq8SquadFanAngle(bearing:number,index:number,total:number):number\n"
    end=" end\n"
    if text.count(start)!=1:raise ValueError("RED_NATIVE_SOURCE_NOT_SELECTED")
    expression=start+text.split(start,1)[1].split(end,1)[0]+end
    harness=expression+"""
local function valid(total:number)
 local bearing=1.4
 local angles={}
 for i=1,total do
  local a=gq8SquadFanAngle(bearing,i,total)
  table.insert(angles,a)
  assert(a>0 and a<math.pi*2)
  if i>1 then
   assert(math.abs(a-angles[i-1]-.12)<1e-8)
   local chord=2*44*math.sin((a-angles[i-1])*.5)
   assert(chord>4.7 and chord<6.0)
  end
 end
 assert(math.abs(angles[1]+angles[#angles]-2*bearing)<1e-8)
 assert(math.abs(angles[#angles]-angles[1])<=.49)
end
for n=1,5 do valid(n) end
print("GQ8_REAL_SWARM_SQUAD_FAN_LUAU_NATIVE_5_BATCH_CASES_PASS")
"""
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(harness)
    mutant.write_text(harness.replace(")*0.12",")*0.35",1))
    print("GQ8_ACTUAL_SELECTED_SWARM_NATIVE_MATH_HARNESS_READY")


def selftest():
    before=HELPER_ANCHOR+OLD+" -- neutralSpawnClear(point)\n -- GetPartBoundsInBox\n"
    selected=patch(before)
    assert unpatch(selected)==before
    assert selected.count("EncounterFair.chooseIndex(encounterFairState,session,kinds)")==1
    assert selected.count("for squadIndex=1,batch do")==1
    assert selected.count("addEnemy(Vector3.new(at.X,session.groundY or target.Y-4,at.Z))")==1
    for invalid in [selected,before.replace(OLD,""),before.replace(OLD,OLD*2),
                    before.replace("GetPartBoundsInBox","")]:
        try:patch(invalid)
        except ValueError:pass
        else:raise AssertionError("RED_PATCH_DRIFT_WAS_ACCEPTED")
    print("GQ8_REAL_SWARM_FAN_PATCH_ROLLBACK_MUTANT_RED_PASS")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("action",choices=["selftest","compose","native"])
    p.add_argument("--base",type=Path)
    p.add_argument("--out",type=Path)
    p.add_argument("--mutant",type=Path)
    a=p.parse_args()
    if a.action=="selftest":return selftest()
    if not a.base or not a.out:p.error("base and out are required")
    if a.action=="compose":compose(a.base,a.out)
    else:
        if not a.mutant:p.error("native needs mutant")
        native(a.base,a.out,a.mutant)


if __name__=="__main__":main()
