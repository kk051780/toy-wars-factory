#!/usr/bin/env python3
"""Extract current #484 real routeClear and build differential native Luau tests.

The harness executes the actual authored Luau function with a deterministic Raycast
stub. It does not claim real Roblox Studio physics or Android behavior.
"""
from __future__ import annotations
import argparse
from pathlib import Path
from source_patch import BEFORE, AFTER


PREFIX = r'''--!strict
local Vec={}
local Vector3={}
function Vector3.new(x,y,z) return setmetatable({X=x,Y=y,Z=z},Vec) end
function Vec.__index(self,key)
 if key=="Magnitude" then return math.sqrt(self.X^2+self.Y^2+self.Z^2) end
 if key=="Unit" then
  local len=math.sqrt(self.X^2+self.Y^2+self.Z^2)
  assert(len>0)
  return Vector3.new(self.X/len,self.Y/len,self.Z/len)
 end
 return rawget(Vec,key)
end
function Vec.__add(a,b) return Vector3.new(a.X+b.X,a.Y+b.Y,a.Z+b.Z) end
function Vec.__sub(a,b) return Vector3.new(a.X-b.X,a.Y-b.Y,a.Z-b.Z) end
function Vec.__mul(a,b)
 if type(a)=="number" then return Vector3.new(a*b.X,a*b.Y,a*b.Z) end
 return Vector3.new(a.X*b,a.Y*b,a.Z*b)
end
local function planar(a,b) return Vector3.new(b.X-a.X,0,b.Z-a.Z) end
local function raycastParams(actors)
 return {RespectCanCollide=true,FilterDescendantsInstances={actors}}
end
local workspace={wallAt=nil,lastCast=nil}
function workspace:Raycast(origin,direction,params)
 assert(params.RespectCanCollide==true)
 self.lastCast=direction.Magnitude
 if self.wallAt and self.lastCast>=self.wallAt then
  return {Instance={CanCollide=true}}
 end
 return nil
end
'''

SUFFIX = r'''
local actor={Name="AI"}
local start=Vector3.new(0,0,0)
local maxMove=30*math.clamp(.3,.05,.3)
assert(maxMove==9)
local destination=Vector3.new(maxMove,0,0)
-- World collision in the last 1 stud of a legal 9-stud navigation step.
workspace.wallAt=8.5
local free=routeClear(start,destination,actor)
assert(free==EXPECT_TAIL_CLEAR,"last-stud wall diagnosis changed")
assert(workspace.lastCast==EXPECTED_RAY_LENGTH,"ray does not match expected original/full step")
-- An ordinary wall in the first 8 studs must remain blocked.
workspace.wallAt=7.5
assert(routeClear(start,destination,actor)==false,"known solid wall was ignored")
-- Open field remains traversable, including a short waypoint step.
workspace.wallAt=nil
assert(routeClear(start,destination,actor)==true,"clear full step was rejected")
local short=Vector3.new(3,0,0)
assert(routeClear(start,short,actor)==true and workspace.lastCast==3,"short step drifted")
-- Distinct TEAM and BATTLE_ROYALE actor tags must share the same safe geometry.
for _,mode in ipairs({"TEAM","BATTLE_ROYALE"}) do
 workspace.wallAt=8.5
 local seat={Name=mode..":AI_1"}
 assert(routeClear(start,destination,seat)==EXPECT_TAIL_CLEAR,"per-mode ray parity failed")
end
print(REPORT_LABEL.." cases=6")
'''


def function_from(content: str) -> str:
    beg = content.index("local function routeClear(")
    end = content.index("\nlocal function resetPath(", beg)
    body = content[beg:end]
    if body.count("workspace:Raycast(") != 1 or "return ray==nil" not in body:
        raise ValueError("single authoritative routeClear function changed")
    return body


def build(source: str, *, patched: bool) -> str:
    body = function_from(source)
    anchor = AFTER if patched else BEFORE
    if body.count(anchor) != 1:
        raise ValueError("expected exact source variant changed")
    suffix = SUFFIX.replace("EXPECT_TAIL_CLEAR", "false" if patched else "true")
    suffix = suffix.replace("EXPECTED_RAY_LENGTH", "9" if patched else "8")
    suffix = suffix.replace("REPORT_LABEL", '"GQ_NATIVE_PATCH_FULLSTEP_RAY"' if patched else '"GQ_NATIVE_ORIGINAL_TRUNCATED_RAY"')
    return PREFIX + "\n" + body + "\n" + suffix


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--patched", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    orig = args.original.read_text(encoding="utf-8")
    patched = args.patched.read_text(encoding="utf-8")
    if patched.replace(AFTER, BEFORE) != orig:
        raise ValueError("not a one-line reversible source overlay")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for mode,content in (("original",orig),("patched",patched)):
        native = build(content, patched=mode=="patched")
        (args.output_dir/f"{mode}.spec.luau").write_text(native,encoding="utf-8")
        print(f"{mode} actual routeClear bytes={len(function_from(content).encode())}")


if __name__ == "__main__":
    main()
