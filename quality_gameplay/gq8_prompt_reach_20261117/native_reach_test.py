#!/usr/bin/env python3
"""Run the *real selected Guard* inside native Luau with fake Roblox objects."""
from pathlib import Path
import argparse

PRELUDE = r'''
local function vec(x,y,z)
 local m=math.sqrt(x*x+y*y+z*z)
 local t={X=x,Y=y,Z=z,Magnitude=m}
 return setmetatable(t,{
  __add=function(a,b) return vec(a.X+b.X,a.Y+b.Y,a.Z+b.Z) end,
  __sub=function(a,b) return vec(a.X-b.X,a.Y-b.Y,a.Z-b.Z) end,
 })
end
Vector3={new=vec}
Enum={RaycastFilterType={Exclude="Exclude"}}
RaycastParams={new=function() return {} end}
local blocker=nil
workspace={Raycast=function(_,origin,cast,params) return blocker end}
'''
SCENARIOS = r'''
local parent={}
local h={Health=100}
local root={Position=Vector3.new(0,0,0)}
local ch={}
function ch:FindFirstChildOfClass(t) if t=="Humanoid" then return h end end
function ch:FindFirstChild(t) if t=="HumanoidRootPart" then return root end end
local player={Parent=parent, Character=ch, UserId=10401}
local part={Parent=parent, Name="PORTAL", Position=Vector3.new(0,0,0), Size=Vector3.new(2,2,2)}
local active={}
function part:GetChildren() return active end
function part:GetClosestPointOnSurface(pos) return self.Position end
local function p(verb,dist,on)
 return {ActionText=verb,MaxActivationDistance=dist,Enabled=on,
  IsA=function(_,class) return class=="ProximityPrompt" end}
end
local count=0
local function expect(value,verb)
 Guard.clear(player)
 local got=Guard.allow(player,part,verb or "参加する",part.Name)
 assert(got==value,"unexpected authorize at test "..tostring(count+1))
 count+=1
end
active={p("参加する",14,true)}
root.Position=Vector3.new(15.5,0,0);expect(false) -- old 16+1.3 incorrectly allowed
root.Position=Vector3.new(15.1,0,0);expect(true)  -- configured 14+1.3 tolerance
assert(Guard.allow(player,part,"参加する",part.Name)==false,"cooldown bypass")
count+=1
active={p("参加する",8,true)}
root.Position=Vector3.new(9.5,0,0);expect(false)
root.Position=Vector3.new(8.9,0,0);expect(true)
active={};root.Position=Vector3.new(0,0,0);expect(false)
active={p("参加する",14,false)};expect(false)
active={p("参加する",14,true),p("参加する",14,true)};expect(false)
active={p("装備する",14,true)};expect(false) -- mismatched verb
active={p("参加する",0,true)};expect(false)
active={p("参加する",14,true)}
h.Health=0;expect(false);h.Health=100
blocker={Instance={}};expect(false);blocker=nil
part.Parent=nil;expect(false);part.Parent=parent
print("GQ8_NATIVE_REAL_GUARD_PROMPT_REACH_"..tostring(count).."_CASES_PASS")
'''
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--selected",type=Path,required=True)
 p.add_argument("--out",type=Path,required=True)
 a=p.parse_args()
 chosen=a.selected.read_text(encoding="utf-8")
 assert chosen.rstrip().endswith("return Guard"), "UNEXPECTED_GUARD_MODULE_END"
 guard=chosen.rstrip().removesuffix("return Guard")
 a.out.write_text(PRELUDE+"\n"+guard+"\n"+SCENARIOS,encoding="utf-8")
if __name__=="__main__":
 main()
