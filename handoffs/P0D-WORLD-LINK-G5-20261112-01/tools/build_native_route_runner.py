"""Build native Luau contract tests from EXACT original WorldLinkRoutes source."""
from pathlib import Path
import argparse

ROOT=Path(__file__).resolve().parents[1]
FILE=ROOT/"src/WorldLinkRoutes.luau"

CASES=r'''
local count=0
local function ok(cond,reason)
    count+=1
    assert(cond,"G5_NATIVE_ROUTES_FAIL #" .. tostring(count) .. " " .. reason)
end
local valid,description=Routes.validate()
ok(valid, "all links valid: "..tostring(description))
ok(Routes.VERSION=="WORLD_LINK_G5_V1","version")
ok(#Routes.LINKS==5,"exactly five paths")
ok(Routes.NODES.LAND~=nil,"land")
ok(Routes.NODES.SEA_DOCK~=nil,"dock")
ok(Routes.NODES.SEA_CASTLE~=nil,"sea")
ok(Routes.NODES.SKY_CASTLE~=nil,"sky")
ok(Routes.reachable("LAND","SEA_DOCK"),"port reachable")
ok(Routes.reachable("LAND","SEA_CASTLE"),"sea castle reachable")
ok(Routes.reachable("LAND","SKY_CASTLE"),"sky castle reachable")
ok(Routes.reachable("SEA_CASTLE","LAND"),"sea exit")
ok(Routes.reachable("SKY_CASTLE","LAND"),"sky exit")
ok(Routes.reachable("SEA_CASTLE","SKY_CASTLE"),"sea to sky via hub")
ok(Routes.reachable("SKY_CASTLE","SEA_CASTLE"),"sky to sea via hub")
ok(not Routes.reachable("MISSING","LAND"),"unknown node")
ok(not Routes.reachable("LAND","MISSING"),"unknown destination")
ok(#Routes.edgesFrom("LAND")==4,"four hub direct routes including two sky")
ok(#Routes.edgesFrom("SEA_CASTLE")==2,"two sea ingress routes")
ok(#Routes.edgesFrom("SKY_CASTLE")==2,"two sky ingress routes")
ok(#Routes.edgesFrom("MISSING")==0,"unknown source has no edges")
local ids={}
for _,edge in ipairs(Routes.LINKS) do
    ok(edge.free==true,"everyone free to walk")
    ok(edge.direction=="both","both directions")
    ok(#edge.child_cue>2,"kid cue")
    ok(#edge.counterplay>2,"defense")
    ok(ids[edge.id]==nil,"duplicate route")
    ids[edge.id]=true
end
print("WORLD_LINK_G5_NATIVE_GRAPH_PASS assertions="..tostring(count))
'''
def runner(source):
    if not source.startswith("--!strict\n") or not source.rstrip().endswith("return Routes"):
        raise ValueError("cannot transform unknown route source")
    return ("local Routes=(function()\n"+source.replace("--!strict\n","",1)
           +"\nend)()\n"+CASES)
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--dir",required=True)
    args=ap.parse_args()
    d=Path(args.dir)
    d.mkdir(parents=True,exist_ok=True)
    source=FILE.read_text(encoding="utf-8")
    variants={
        "positive":source,
        "BAD_PAID_ROUTE":source.replace("free=true","free=false",1),
        "BAD_UNKNOWN_NODE":source.replace('to="SEA_CASTLE"','to="NO_CASTLE"',1),
        "BAD_DUPLICATE_ROUTE_ID":source.replace('id="SKY_RAINBOW_B"','id="SKY_RAINBOW_A"',1),
        "BAD_NO_RETURN_ROUTE":source.replace('direction="both"','direction="one-way"',1),
    }
    if len(set(variants.values()))!=len(variants):
        raise RuntimeError("must mutate real source and distinguish variants")
    for name,src in variants.items():
        dest=d/(name+".luau")
        dest.write_text(runner(src),encoding="utf-8")
        print("G5_NATIVE_SOURCE_RUNNER_WRITTEN",name,dest)
if __name__=="__main__":
    main()
