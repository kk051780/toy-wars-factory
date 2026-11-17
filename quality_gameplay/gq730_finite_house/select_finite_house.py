#!/usr/bin/env python3
"""GQ730: patch only the original CastleMatchRules cosmetic coordinate guard.

No gameplay module is copied into the repository. A complete original-author
source is provided as input; OFF is an exact byte-for-byte copy. This selector
is intentionally fail-closed when the author changes the expected block.
"""
import argparse
from pathlib import Path

BEFORE = ' assert(type(piece)=="table" and type(piece.x)=="number" and type(piece.y)=="number" and type(piece.z)=="number","invalid piece")'
AFTER = ' assert(type(piece)=="table" and finiteDecorCoordinate(piece.x) and finiteDecorCoordinate(piece.y) and finiteDecorCoordinate(piece.z),"invalid piece")'
FUNCTION = "function M.placeHouseDecoration(m:any,ownerId:any,actorId:any,piece:any)"
HELPER = """local function finiteDecorCoordinate(value:any):boolean
 return type(value)=="number" and value==value and value>-math.huge and value<math.huge
end
"""

def select(original: str) -> str:
    if original.count(BEFORE) != 1 or original.count(FUNCTION) != 1:
        raise ValueError("RED: CastleMatchRules original coordinate guard changed")
    if "finiteDecorCoordinate(" in original:
        raise ValueError("RED: finite guard already present (double patch)")
    return original.replace(FUNCTION, HELPER + FUNCTION, 1).replace(BEFORE, AFTER, 1)

HARNESS = r'''
local function rejects(label:string, f:()->())
 local ok=pcall(f)
 assert(not ok, "GQ730_NOT_FINITE_REJECTED_"..label)
end
local roster=M.makeRoster("TEAM",{12001,12002},2)
local m=M.new("TEAM",roster,0)
assert(M.placeHouseDecoration(m,"12001","12001",{kind="FLAG",x=24,y=25,z=-24})==1)
assert(M.placeHouseDecoration(m,"12001","12001",{kind="GARDEN",x=-24,y=0,z=24})==2)
for _,v in ipairs({math.huge,-math.huge,0/0}) do
 for _,axis in ipairs({"x","y","z"}) do
  local value={kind="FLAG",x=0,y=1,z=0}
  value[axis]=v
  rejects(axis,function() M.placeHouseDecoration(m,"12001","12001",value) end)
  assert(#m.castles["12001"].homePieces==2,"rejected piece mutated state")
 end
end
rejects("OUTSIDE",function() M.placeHouseDecoration(m,"12001","12001",{kind="FLAG",x=24.001,y=0,z=0}) end)
rejects("NOT_OWNER",function() M.placeHouseDecoration(m,"12001","12002",{kind="FLAG",x=0,y=0,z=0}) end)
rejects("BAD_KIND",function() M.placeHouseDecoration(m,"12001","12001",{kind="WALL",x=0,y=0,z=0}) end)
assert(#m.castles["12001"].homePieces==2)
M.start(m)
rejects("MID_ROUND",function() M.placeHouseDecoration(m,"12001","12001",{kind="FLAG",x=0,y=0,z=0}) end)
print("GQ730_FINITE_DECOR_NATIVE_PASS")
'''

def make_harness(src: str) -> str:
    if not src.rstrip().endswith("return M"):
        raise ValueError("RED: expected original CastleMatchRules tail")
    return src.rstrip()[:-len("return M")] + HARNESS

def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--original",type=Path,required=True)
    p.add_argument("--on",type=Path,required=True)
    p.add_argument("--off",type=Path,required=True)
    p.add_argument("--native",type=Path,required=True)
    p.add_argument("--mutant",type=Path,required=True)
    a=p.parse_args()
    data=a.original.read_bytes()
    src=data.decode("utf-8")
    corrected=select(src)
    for path in (a.on,a.off,a.native,a.mutant):
        path.parent.mkdir(parents=True,exist_ok=True)
    a.on.write_bytes(corrected.encode("utf-8"))
    a.off.write_bytes(data)
    a.native.write_text(make_harness(corrected),encoding="utf-8")
    a.mutant.write_text(make_harness(src),encoding="utf-8")
    assert a.off.read_bytes()==data
    print("GQ730_SELECT_ONLY_CASTLE_COORDINATES_OFF_EXACT_PASS")

if __name__=="__main__":
    main()
