#!/usr/bin/env python3
"""Extract ACTUAL patched Luau sight helper, execute it with a 3D ray mock."""
import argparse
from pathlib import Path


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--patched",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    text=a.patched.read_text(encoding="utf-8")
    begin="local function stompVisible("
    assert text.count(begin)==1
    start=text.index(begin)
    end=text.index("\nend\n",start)+len("\nend\n")
    helper=text[start:end]
    assert "RespectCanCollide=true" in helper
    test='''local mt={}
mt.__index=function(self,key)
 if key=="Magnitude" then return math.sqrt(self.X*self.X+self.Y*self.Y+self.Z*self.Z) end
 return nil
end
mt.__sub=function(a,b)
 return setmetatable({X=a.X-b.X,Y=a.Y-b.Y,Z=a.Z-b.Z},mt)
end
Vector3={new=function(x,y,z) return setmetatable({X=x,Y=y,Z=z},mt) end}
Enum={RaycastFilterType={Exclude="Exclude"}}
RaycastParams={new=function() return {} end}
local blocked=false
local rayCount=0
workspace={Raycast=function(_,origin,direction,params)
 rayCount+=1
 assert(params.RespectCanCollide==true)
 assert(params.FilterType=="Exclude")
 assert(#params.FilterDescendantsInstances==2)
 assert(origin.Y==3)
 assert(direction.Magnitude>0)
 if blocked then return {Instance={CanCollide=true}} end
 return nil
end}
'''
    test+=helper
    test+='''local boss={}
local human={}
local root={Position=Vector3.new(0,0,8)}
local at=Vector3.new(0,0,0)
assert(stompVisible(boss,at,human,root)==true, "open battlefield must receive shockwave")
blocked=true
assert(stompVisible(boss,at,human,root)==false, "solid castle wall must protect")
assert(rayCount==2)
root.Position=Vector3.new(0,2,0)
assert(stompVisible(boss,at,human,root)==true, "degenerate no-ray case must be safe")
assert(rayCount==2)
print("GQ_BOSS_ACTUAL_LUAU_STOMP_LOS_3_CASES_PASS")
'''
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(test,encoding="utf-8")


if __name__=="__main__":
    main()
