#!/usr/bin/env python3
"""Run rows from the ACTUAL patched original host with native Luau geometry assertions."""
from __future__ import annotations
import argparse
from pathlib import Path
from patch_field_eggs import ROWS_LINE, REPLACEMENT_LINE

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--patched",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    source=a.patched.read_text(encoding="utf-8")
    assert source.count(ROWS_LINE)==1
    assert source.count(REPLACEMENT_LINE)==1
    tested='''local function rowFor(mode:string,row:number):number
'''+ROWS_LINE+''' return rowZ[row+1]
end
local function castle(mode:string,i:number):(number,number)
 if mode=="TEAM" then
  local red=i%2==1
  local localIndex=math.floor((i-1)/2)
  local col=localIndex%2
  local row=math.floor(localIndex/2)
  return if red then -885+col*124 else -475+col*124,260+row*146
 end
 local col=(i-1)%4
 local row=math.floor((i-1)/4)
 return 620+(col-1.5)*122,280+row*112
end
local function collisionCount(mode:string,old:boolean):number
 local blocked=0
 local coords={}
 for i=1,24 do
  local col=(i-1)%8
  local row=math.floor((i-1)/8)
  local worldX=if mode=="TEAM" then -620 else 620
  local x=worldX+(col-3.5)*93
  local z=if old then 290+row*200 else rowFor(mode,row)
  coords[x..":"..z]=true
  assert(math.abs(x-worldX)+1.3<445)
  assert(math.abs(z-465)+1.65<525)
  for j=1,16 do
   local cx,cz=castle(mode,j)
   if math.abs(cx-x)<36+1.3 and math.abs(cz-z)<36+1.65 then
    blocked+=1
   end
  end
 end
 local unique=0
 for _ in pairs(coords) do unique+=1 end
 assert(unique==24)
 return blocked
end
assert(collisionCount("TEAM",true)==8,"original TEAM overlap must reproduce")
assert(collisionCount("BATTLE_ROYALE",true)==4,"original BR overlap must reproduce")
assert(collisionCount("TEAM",false)==0,"patched TEAM egg/castle overlap")
assert(collisionCount("BATTLE_ROYALE",false)==0,"patched BR egg/castle overlap")
print("GQ_FIELD_EGG_ACTUAL_LUAU_SOURCE_TEAM8_BR4_TO_ZERO_4_CASES_PASS")
'''
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(tested,encoding="utf-8")

if __name__=="__main__":
    main()
