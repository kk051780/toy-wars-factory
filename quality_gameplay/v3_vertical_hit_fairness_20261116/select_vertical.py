#!/usr/bin/env python3
"""Original-owner EGGRUMBLE AttackGeometry vertical reach guard; source-only."""
import argparse
import hashlib
import json
from pathlib import Path

ORIGINAL_BLOB = "a47b1d803ed9bb80c27a8ac86e6bad74a337aa79"
ANCHOR = ("function Geometry.allowed(origin:Vector3,center:Vector3,target:Vector3,radius:number,shape:string):boolean\n"
          " if radius<=0 or radius>22 then return false end\n"
          " local dx=target.X-center.X\n")
SELECTED = ("function Geometry.allowed(origin:Vector3,center:Vector3,target:Vector3,radius:number,shape:string):boolean\n"
            " -- Vertical separation must not be ignored on stacked castles, bridges or sky routes.\n"
            " if radius~=radius or radius<=0 or radius>22 then return false end\n"
            " local dy=target.Y-center.Y\n"
            " if dy~=dy or math.abs(dy)>math.min(radius,14) then return false end\n"
            " local dx=target.X-center.X\n")

def git_blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()

def apply(raw: str) -> str:
    if raw.count(ANCHOR) != 1 or "math.abs(dy)>math.min(radius,14)" in raw:
        raise ValueError("RED original singleton AttackGeometry anchor absent/duplicated/already fixed")
    result = raw.replace(ANCHOR, SELECTED, 1)
    if result.replace(SELECTED, ANCHOR, 1) != raw:
        raise AssertionError("RED cannot reverse exactly")
    if result.count("function Geometry.allowed(") != 1:
        raise AssertionError("RED duplicate source authority")
    return result

def native(source: str, fixed: bool) -> str:
    assert source.count("return Geometry") == 1
    scenario = """
local function at(x,y,z) return {X=x,Y=y,Z=z} end
local origin=at(0,0,0)
local center=at(0,0,10)
local cases=0
local function check(name,target,radius,shape,expected)
 local observed=Geometry.allowed(origin,center,target,radius,shape)
 assert(observed==expected,name .. " actual=" .. tostring(observed))
 cases+=1
end
check("flat_circle",at(0,0,10),20,"CIRCLE",true)
check("near_upper_circle",at(0,4,10),20,"CIRCLE",true)
check("near_lower_fan",at(0,-4,10),20,"BLADE",true)
check("near_upper_rail",at(0,2,10),20,"RAIL",true)
check("too_far_horizontal",at(25,0,10),20,"CIRCLE",false)
check("zero_radius",at(0,0,10),0,"CIRCLE",false)
check("vertical_50_circle",at(0,50,10),20,"CIRCLE",__VERTICAL_FALSE__)
check("vertical_50_fan",at(0,50,10),20,"BLADE",__VERTICAL_FALSE__)
check("vertical_50_rail",at(0,50,10),20,"RAIL",__VERTICAL_FALSE__)
check("vertical_minus_22",at(0,-22,10),20,"CIRCLE",__VERTICAL_FALSE__)
check("vertical_14_boundary",at(0,14,10),20,"CIRCLE",true)
check("vertical_14_1",at(0,14.1,10),20,"CIRCLE",__VERTICAL_FALSE__)
check("small_radius_8_y9",at(0,9,10),8,"CIRCLE",__VERTICAL_FALSE__)
check("small_radius_8_y8",at(0,8,10),8,"CIRCLE",true)
print("GQ_VERTICAL_HIT_ORIGINAL_LUAU_" .. __STATE__ .. "_PASS",cases)
"""
    scenario = scenario.replace("__VERTICAL_FALSE__", "false" if fixed else "true")
    scenario = scenario.replace("__STATE__", '"AFTER"' if fixed else '"BEFORE"')
    return source.replace("return Geometry",scenario+"\n",1)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--original",type=Path,required=True)
    p.add_argument("--out-dir",type=Path,required=True)
    a=p.parse_args()
    raw=a.original.read_bytes()
    if git_blob(raw)!=ORIGINAL_BLOB:
        raise ValueError("RED source drift: expected original author Git blob")
    original=raw.decode("utf-8")
    selected=apply(original)
    a.out_dir.mkdir(parents=True,exist_ok=True)
    (a.out_dir/"EGGRUMBLE_AttackGeometry_VERTICAL_SAFE.luau").write_text(selected,encoding="utf-8")
    (a.out_dir/"BEFORE.native.spec.luau").write_text(native(original,False),encoding="utf-8")
    (a.out_dir/"AFTER.native.spec.luau").write_text(native(selected,True),encoding="utf-8")
    receipt={"status":"SOURCE_ONLY_NOT_OFFICIAL_RC","source_original_git_blob":ORIGINAL_BLOB,
        "source_changed":"EGGRUMBLE_AttackGeometry","changes_to_game_authority":0,
        "inverse_rollback_exact":selected.replace(SELECTED,ANCHOR,1)==original,
        "source_original_sha256":hashlib.sha256(raw).hexdigest(),
        "source_selected_sha256":hashlib.sha256(selected.encode()).hexdigest(),
        "vertical_hit_reach_studs":14,
        "engine_studio_tested":False,"android_tested":False,"owner_accepted":False}
    (a.out_dir/"SOURCE_RECEIPT.json").write_text(json.dumps(receipt,indent=2)+"\n")
    print("GQ_VERTICAL_HIT_SELECTED_FROM_ORIGINAL_AUTHOR",ORIGINAL_BLOB)

if __name__=="__main__":
    main()
