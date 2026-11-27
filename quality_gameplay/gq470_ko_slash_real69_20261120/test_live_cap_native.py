#!/usr/bin/env python3
from argparse import ArgumentParser
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

from patch_ko_slash69 import apply_owner_live_cap, must, transform

FIXTURE = r'''
local now=0
local parts, expiration = {}, {}
local world={Parent=true}
local vector={}
vector.__index=function(v,key)
 if key=="Magnitude" then return math.sqrt(v.X^2+v.Y^2+v.Z^2) end
 if key=="Unit" then return vector.new(v.X/v.Magnitude,v.Y/v.Magnitude,v.Z/v.Magnitude) end
end
vector.__add=function(a,b) return vector.new(a.X+b.X,a.Y+b.Y,a.Z+b.Z) end
function vector.new(x,y,z) return setmetatable({X=x,Y=y,Z=z},vector) end
local frame={}
frame.__mul=function(a,b) return a end
local function cf(at,look) return setmetatable({Position=at,LookVector=look},frame) end
local function clearDue()
 for part,expires in pairs(expiration) do
  if expires<=now then part.Parent=nil;expiration[part]=nil end
 end
end
local function loadBody(raw)
 now=0
 table.clear(parts);table.clear(expiration)
 local services={
  Debris={AddItem=function(_,part,ttl) assert(ttl==.30);expiration[part]=now+ttl end},
  TweenService={Create=function(_,part,ttl,goal)
   assert(ttl==.23 and goal.Transparency==1)
   return {Play=function() end}
  end},
 }
 local enum=setmetatable({}, {__index=function(_,kind)
  return setmetatable({}, {__index=function(_,key) return kind.."."..key end})
 end})
 local env=setmetatable({
  game={GetService=function(_,key) return assert(services[key]) end},
  Instance={new=function(class)
   local part={ClassName=class};table.insert(parts,part);return part
  end},
  Enum=enum, os={clock=function() return now end}, Vector3=vector,
  Color3={fromRGB=function(r,g,b) return {r,g,b} end},
  TweenInfo={new=function(ttl) return ttl end},
  CFrame={lookAt=function(at,to)
   assert(to.X==0 and to.Z==-1)
   return cf(at,to)
  end,new=function(x,y,z) return cf(vector.new(x,y,z)) end,Angles=function() return cf() end},
 },{__index=getfenv()})
 local chunk=assert(loadstring(raw))
 setfenv(chunk,env)
 return chunk()
end
local function countLive()
 local count=0
 for _,part in ipairs(parts) do
  if part.Parent then
   count+=1
   assert(part.ClassName=="WedgePart" and part.Material=="Material.SmoothPlastic"
    and not part.CanCollide and not part.CanQuery and not part.CanTouch and not part.CastShadow)
  end
 end
 return count
end
local function run(old,fixed)
 local victim={PrimaryPart={CFrame=cf(vector.new(0,0,0),vector.new(0,1,0))}}
 for mode,source in ipairs({old,fixed}) do
  local feedback=loadBody(source)
  now=.99
  for _=1,6 do assert(feedback.ko(world,victim,"MAGE")) end
  assert(not feedback.ko(world,victim,"MAGE") and countLive()==12)
  now=1.01
  for _=1,6 do assert(feedback.ko(world,victim,"MAGE")==(mode==1)) end
  assert(countLive()==(if mode==1 then 24 else 12))
  print("KO_SECOND_BOUNDARY",mode,countLive())
  now=2.2
  if mode==2 then
   assert(not feedback.ko(world,victim,"MAGE"))
   parts[1].Parent=nil
   assert(not feedback.ko(world,victim,"MAGE") and countLive()==11)
   parts[2].Parent=nil
   assert(feedback.ko(world,victim,"MAGE") and countLive()==12)
   world.Parent=nil
   assert(not feedback.ko(world,victim,"MAGE"))
   world.Parent=true
   print("KO_RECLAIM_FULL_PAIR_ONLY",countLive())
  end
  now=3
  clearDue()
  assert(countLive()==0)
 end
end
'''


def quote(raw):
    text = raw.decode("utf-8")
    marker = "="
    while "]" + marker + "]" in text:
        marker += "="
    return "[" + marker + "[" + text + "]" + marker + "]"


def main():
    parser = ArgumentParser()
    for key in ("luau", "official-source", "selected-source"):
        parser.add_argument("--" + key, type=Path, required=True)
    args = parser.parse_args()
    old = transform(args.official_source.read_text()).encode()
    fixed = args.selected_source.read_bytes()
    must(fixed == apply_owner_live_cap(old), "NATIVE_ACTUAL_SELECTED_BODY")
    for altered in (old[:-1], old.replace(b"Enum.Material.SmoothPlastic", b"Enum.Material.Neon"), fixed):
        try:
            apply_owner_live_cap(altered)
        except ValueError:
            continue
        raise ValueError("RED_KO_SLASH_ACCEPTED_SOURCE_DRIFT")
    with TemporaryDirectory(prefix="eggrumble-ko-native-") as temp:
        path = Path(temp) / "native.luau"
        path.write_text(FIXTURE + "\nrun(" + quote(old) + "," + quote(fixed) + ")\n")
        result = subprocess.run([str(args.luau), str(path)], capture_output=True, timeout=45, check=False)
    must(result.returncode == 0 and not result.stderr, "NATIVE_ACTUAL_F46: " + result.stderr.decode())
    must(result.stdout.splitlines() == [
        b"KO_SECOND_BOUNDARY\t1\t24", b"KO_SECOND_BOUNDARY\t2\t12", b"KO_RECLAIM_FULL_PAIR_ONLY\t12",
    ], "NATIVE_EXACT_OUTPUT")
    print(result.stdout.decode(), end="")


if __name__ == "__main__":
    main()
