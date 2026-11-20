#!/usr/bin/env python3
"""Extract and execute the ACTUAL #518 selected boss Luau LOS helper via pinned native CLI.

Mock world raycast only; never mislabel these native cases as real Roblox Studio.
"""
import argparse
from pathlib import Path

HELPER_START = " local function shockwaveClear(character:Model?,root:BasePart):boolean"

def make(original: Path, out: Path):
    src=original.read_text(encoding="utf-8")
    assert src.count(HELPER_START)==1, "must use exact #518 generated Luau"
    assert src.count("and shockwaveClear(c,root) then")==1
    pos=src.index(HELPER_START)
    end=src.index("\n end\n",pos)+len("\n end\n")
    helper=src[pos:end]
    assert "workspace:Raycast(origin,direction,params)==nil" in helper
    vm=r'''local mt={}
mt.__index=function(self,key)
 if key=="Magnitude" then return math.sqrt(self.X*self.X+self.Y*self.Y+self.Z*self.Z) end
 return nil
end
mt.__add=function(a,b)
 return setmetatable({X=a.X+b.X,Y=a.Y+b.Y,Z=a.Z+b.Z},mt)
end
mt.__sub=function(a,b)
 return setmetatable({X=a.X-b.X,Y=a.Y-b.Y,Z=a.Z-b.Z},mt)
end
Vector3={new=function(x,y,z) return setmetatable({X=x,Y=y,Z=z},mt) end}
Enum={RaycastFilterType={Exclude="Exclude"}}
RaycastParams={new=function() return {} end}
local blocked=false
local rays=0
local at=Vector3.new(0,0,0)
local model={}
workspace={Raycast=function(_,origin,direction,params)
 rays+=1
 assert(params.RespectCanCollide==true)
 assert(params.FilterType=="Exclude")
 assert(#params.FilterDescendantsInstances==2)
 assert(params.FilterDescendantsInstances[1]==model)
 assert(origin.Y==2.5)
 assert(direction.Magnitude>0)
 if blocked then return {Instance={CanCollide=true}} end
 return nil
end}
'''
    vm+=helper
    vm+=r'''local character={}
local root={Position=Vector3.new(0,0,8)}
assert(shockwaveClear(character,root)==true,"open battlefield expected hit")
blocked=true
assert(shockwaveClear(character,root)==false,"collidable castle wall expected block")
assert(rays==2)
assert(shockwaveClear(nil,root)==false,"missing avatar must fail closed")
assert(rays==2)
root.Position=Vector3.new(0,0,0)
assert(shockwaveClear(character,root)==true,"zero-length torso direction is safe")
assert(rays==2)
blocked=false
root.Position=Vector3.new(0,0,5)
assert(shockwaveClear(character,root)==true,"open near-origin human expected legal")
assert(rays==3)
print("GQ518_ACTUAL_AUTHORED_LUAU_BOSS_OCCLUSION_5_CASES_PASS")
'''
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(vm,encoding="utf-8")
    print("GQ518_NATIVE_VM_GENERATED_FROM_REAL_PATCHED_BOSS_ONLY")


if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--patched",type=Path,required=True)
    a.add_argument("--out",type=Path,required=True)
    o=a.parse_args()
    make(o.patched,o.out)
