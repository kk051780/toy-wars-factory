#!/usr/bin/env python3
"""GQ732: reject exact duplicates of one decorative piece in a castle plot.

Operate on the ORIGINAL author source or the current31 source. No second
castle controller or new runtime scripts. The 'off' output is the exact
unmodified input source, allowing feature-only rollback.
"""
from __future__ import annotations
import argparse
from pathlib import Path

ANCHOR = ' table.insert(c.homePieces,{kind=piece.kind,x=piece.x,y=piece.y,z=piece.z,collidable=false,combatBonus=0})'
PATCH = ''' -- Repeated identical geometry z-fights and wastes one of 48 mobile decor slots.
 -- Compare before mutating; permit deliberate different-kind composites.
 for _,existing in ipairs(c.homePieces) do
  assert(not (existing.kind==piece.kind and existing.x==piece.x
   and existing.y==piece.y and existing.z==piece.z),
   "duplicate decoration in this plot")
 end
''' + ANCHOR
FUNCTION = 'function M.placeHouseDecoration(m:any,ownerId:any,actorId:any,piece:any)'
MARKER = '"duplicate decoration in this plot"'
CASES = '''
local function rejected(tag:string, f:()->())
 local ok=pcall(f)
 assert(not ok,"GQ732_DUPLICATE_REJECT_MISSING_"..tag)
end
local roster=M.makeRoster("TEAM",{10001,10002},2)
local match=M.new("TEAM",roster,0)
local function put(kind:string,x:number,y:number,z:number):number
 return M.placeHouseDecoration(match,"10001","10001",{kind=kind,x=x,y=y,z=z})
end
assert(put("FLAG",1,2,3)==1)
rejected("REPEAT_FLAG",function() put("FLAG",1,2,3) end)
assert(#match.castles["10001"].homePieces==1,"duplicate mutated slots")
assert(put("STATUE",1,2,3)==2,"other kind may share a design coordinate")
rejected("REPEAT_STATUE",function() put("STATUE",1,2,3) end)
assert(put("FLAG",1,2,4)==3,"different position must remain valid")
rejected("NOT_OWNER",function()
 M.placeHouseDecoration(match,"10001","10002",{kind="FLAG",x=4,y=2,z=3})
end)
rejected("OUTSIDE",function() put("FLAG",25,0,0) end)
-- 48 unique slots remain available, not an unnecessary tighter art cap.
for i=4,48 do
 local x=-23+(i-4)%16
 local z=-23+math.floor((i-4)/16)
 assert(put("FLAG",x,0,z)==i,"valid placement cap changed")
end
rejected("FULL",function() put("FLAG",22,0,22) end)
assert(#match.castles["10001"].homePieces==48)
M.start(match)
rejected("ACTIVE",function() put("FLAG",22,0,22) end)
print("GQ732_DUPLICATE_HOUSE_DECOR_REAL_RULES_NATIVE_PASS")
'''

def select(src:str)->str:
    if src.count(ANCHOR)!=1 or src.count(FUNCTION)!=1:
        raise ValueError("RED: original CastleMatchRules plot anchor drift")
    if MARKER in src or PATCH in src:
        raise ValueError("RED: duplicate patch")
    new=src.replace(ANCHOR,PATCH,1)
    if off(new)!=src: raise ValueError("RED: OFF does not restore exact source")
    return new

def off(src:str)->str:
    if src.count(PATCH)!=1:
        raise ValueError("RED: selected decorator patch drift")
    return src.replace(PATCH,ANCHOR,1)

def native(src:str)->str:
    trimmed=src.rstrip()
    if not trimmed.endswith("return M") or trimmed.count("\nreturn M")!=1:
        raise ValueError("RED: source module tail drift")
    return trimmed[:-len("return M")]+CASES

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--original",type=Path,required=True)
    p.add_argument("--on",type=Path,required=True)
    p.add_argument("--off",type=Path,required=True)
    p.add_argument("--native",type=Path,required=True)
    p.add_argument("--mutant",type=Path,required=True)
    a=p.parse_args()
    original=a.original.read_bytes()
    before=original.decode("utf-8")
    after=select(before)
    for name in ("on","off","native","mutant"):
        getattr(a,name).parent.mkdir(parents=True,exist_ok=True)
    a.on.write_bytes(after.encode("utf-8"))
    a.off.write_bytes(original)
    a.native.write_text(native(after),encoding="utf-8")
    a.mutant.write_text(native(before),encoding="utf-8")
    assert a.off.read_bytes()==original
    print("GQ732_DUPLICATE_CASTLE_DECOR_SOURCE_ONE_GUARD_OFF_EXACT_PASS")

if __name__=="__main__":
    main()
