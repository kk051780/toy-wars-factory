#!/usr/bin/env python3
"""Build a native Luau execution harness from the ACTUAL LSS source's put().

Proves a bounded active Instance budget survives repeated spawn->Destroy
cycles. The old ever-created monotonic budget must go RED on these cases.
"""
from __future__ import annotations
import argparse
from pathlib import Path

SOURCE = Path(__file__).with_name("EGGRUMBLE_LandSeaSkyTraversal.server.luau")
BEGIN = " local function put(parent,name,cf,size,color,material,collide,alpha)\n"
END = "\n end\n local function station("

HEAD = """
local MAX_PARTS_PER_WORLD=3
local liveParts=0
local constructed=0
local function block(...)
 constructed+=1
 local event={subscriber=nil}
 function event:Connect(f) self.subscriber=f end
 local part={Destroying=event,dead=false}
 function part:Destroy()
  if self.dead then return end
  self.dead=true
  assert(self.Destroying.subscriber~=nil,"RED_MISSING_DESTROYING_LISTENER")
  self.Destroying.subscriber()
 end
 return part
end
"""

TEST = """
local p1=put(nil,"a",nil,nil,nil,nil,true,0)
local p2=put(nil,"b",nil,nil,nil,nil,true,0)
local p3=put(nil,"c",nil,nil,nil,nil,true,0)
assert(liveParts==3)
local overCapacity=pcall(function() put(nil,"overflow",nil,nil,nil,nil,true,0) end)
assert(not overCapacity,"RED_PART_CAP_IGNORED")
p1:Destroy()
assert(liveParts==2,"RED_DESTROY_DID_NOT_RELEASE_CAP")
local p4=put(nil,"recycled",nil,nil,nil,nil,true,0)
assert(liveParts==3)
p4:Destroy()
p4:Destroy()
assert(liveParts==2,"RED_DESTROY_IDEMPOTENCY")
for i=1,120 do
 local part=put(nil,"replacement",nil,nil,nil,nil,true,0)
 assert(liveParts==3)
 part:Destroy()
 assert(liveParts==2,"RED_LIFETIME_BUDGET_EXHAUSTION_"..tostring(i))
end
p2:Destroy();p3:Destroy()
assert(liveParts==0)
assert(constructed==124)
print("LSS_ACTUAL_LIVE_PART_BUDGET_NATIVE_120_RECYCLES_PASS")
"""

def extract(source: str) -> str:
    if source.count(BEGIN)!=1 or source.count(END)!=1:
        raise ValueError("RED_LSS_BUDGET_FUNCTION_DRIFT")
    return BEGIN + source.split(BEGIN,1)[1].split(END,1)[0] + "\n end"

def write(out:Path, mutant:Path) -> None:
    actual=SOURCE.read_text(encoding="utf-8")
    body=extract(actual)
    release="liveParts=math.max(0,liveParts-1)"
    if body.count(release)!=1:
        raise ValueError("RED_NO_RELEASE_ON_DESTRUCTION")
    if body.count("assert(liveParts<MAX_PARTS_PER_WORLD")!=1:
        raise ValueError("RED_NO_ACTIVE_PART_CAP")
    out.write_text(HEAD+body+"\n"+TEST,encoding="utf-8")
    mutant.write_text(HEAD+body.replace(release,"liveParts=liveParts",1)+"\n"+TEST,encoding="utf-8")
    print("LSS_NATIVE_LIVE_PART_HARNESS_FROM_REAL_SOURCE_READY")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--mutant",type=Path,required=True)
    a=p.parse_args()
    write(a.out,a.mutant)

if __name__=="__main__":
    main()
