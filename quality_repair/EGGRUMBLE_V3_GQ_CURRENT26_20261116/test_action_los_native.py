#!/usr/bin/env python3
"""Execute the real GQ AI action-LOS function in native Luau with a controllable
first-hit Raycast stub. Verifies short-wall, correct-target and height boundaries.
No Roblox Studio execution or claims of engine proof.
"""
from __future__ import annotations
import argparse
import subprocess
import tempfile
from pathlib import Path

BOT = Path("handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116/EGGRUMBLE_BotActors.luau")
HEADER = r"""
local Vector3={}
local V={}
V.__index=function(self,key)
 if key=="Magnitude" then return math.sqrt(self.X*self.X+self.Y*self.Y+self.Z*self.Z) end
 return rawget(V,key)
end
function Vector3.new(x,y,z)return setmetatable({X=x,Y=y,Z=z},V) end
function V.__add(a,b)return Vector3.new(a.X+b.X,a.Y+b.Y,a.Z+b.Z) end
function V.__sub(a,b)return Vector3.new(a.X-b.X,a.Y-b.Y,a.Z-b.Z) end
local RaycastParams={new=function()return {} end}
local Enum={RaycastFilterType={Exclude="Exclude"}}
local nextHit=nil
local raycasts=0
local workspace={Raycast=function(_,start,segment,params)
 raycasts+=1
 assert(segment.Magnitude>0,"zero distance must not invoke ray")
 assert(params.RespectCanCollide==true)
 return nextHit and {Instance=nextHit} or nil
end}
local actor={position=Vector3.new(0,1,0)}
function actor:GetPivot()return {Position=self.position} end
local actors={}
local targetPart={Name="EggVault"}
local wall={Name="CastleSideWall"}
"""
FOOTER = r"""
local cases=0
local function check(desc,pos,goal,obstacle,expected,interactable)
 actor.position=pos
 nextHit=obstacle
 raycasts=0
 local actual=clearActionPath(actor,actors,goal,interactable)
 assert(actual==expected,desc.." expected "..tostring(expected).." got "..tostring(actual))
 if math.abs(pos.Y-goal.Y)<=4 and (goal-(pos+Vector3.new(0,.4,0))).Magnitude>.01 then
  assert(raycasts==1,desc.." must perform full-length raycast")
 else
  assert(raycasts==0,desc.." invalid height/zero-length should not raycast")
 end
 cases+=1
end
check("short 3 studs solid castle wall",Vector3.new(0,1,0),Vector3.new(3,1,0),wall,false,targetPart)
check("short 3 studs correct vault hit",Vector3.new(0,1,0),Vector3.new(3,1,0),targetPart,true,targetPart)
check("short 3 studs wrong interactable hit",Vector3.new(0,1,0),Vector3.new(3,1,0),wall,false,wall==targetPart and wall or targetPart)
check("short 3 studs no collision",Vector3.new(0,1,0),Vector3.new(3,1,0),nil,true,targetPart)
check("long 13 studs wall",Vector3.new(0,1,0),Vector3.new(13,1,0),wall,false,targetPart)
check("long 13 studs clear",Vector3.new(0,1,0),Vector3.new(13,1,0),nil,true,targetPart)
check("target part missing blocks hit",Vector3.new(0,1,0),Vector3.new(3,1,0),targetPart,false,nil)
check("excessive height delta",Vector3.new(0,1,0),Vector3.new(3,9,0),nil,false,targetPart)
check("near-zero segment",Vector3.new(0,1,0),Vector3.new(0,1.4,0),nil,true,targetPart)
print("GQ_ACTION_LOS_NATIVE_PASS cases="..cases)
"""

def extracted(source: str) -> str:
    left = source.index("local function clearActionPath(")
    right = source.index("local function clearHeroStrike(",left)
    f = source[left:right]
    assert "workspace:Raycast(start,segment,params)" in f, "full LOS missing"
    assert "hit.Instance==targetPart" in f, "target identity guard missing"
    return f

def run(luau: Path, body: str) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory(prefix="gq-action-los-") as td:
        file = Path(td) / "actual_function.spec.luau"
        file.write_text(HEADER + body + FOOTER,encoding="utf-8")
        return subprocess.run([str(luau),str(file)],text=True,capture_output=True,check=False)

def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--luau",type=Path,required=True)
    args=ap.parse_args()
    assert args.luau.is_file()
    original=extracted(BOT.read_text(encoding="utf-8"))
    good=run(args.luau,original)
    assert good.returncode==0,(good.stdout,good.stderr)
    assert "GQ_ACTION_LOS_NATIVE_PASS cases=9" in good.stdout,good.stdout
    # Deliberate old-vulnerability mutation must make the native test RED.
    bypass=original.replace(
       "if segment.Magnitude<=0.01 then return true end",
       "if segment.Magnitude<=4 then return true end")
    assert bypass!=original
    bad=run(args.luau,bypass)
    assert bad.returncode!=0,"native test failed to detect old short-distance bypass"
    # Deliberate wrong-target permission mutation must also make test RED.
    wrong=original.replace("hit.Instance==targetPart","hit.Instance~=nil")
    assert wrong!=original
    bad=run(args.luau,wrong)
    assert bad.returncode!=0,"native test failed to detect wrong-target collision permission"
    print(good.stdout.strip())
    print("GQ_ACTION_LOS_MUTANT_NEGATIVE_2_OF_2_PASS")

if __name__=="__main__":
    main()
