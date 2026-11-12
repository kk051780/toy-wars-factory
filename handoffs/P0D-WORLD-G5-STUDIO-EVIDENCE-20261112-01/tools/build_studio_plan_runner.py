"""Native Luau test runner of the EXACT checkpoint module, no rewritten logic."""
from pathlib import Path
import argparse
ROOT=Path(__file__).resolve().parents[1]
FILE=ROOT/"src/G5StudioCheckpointPlan.luau"
TESTS=r'''
local count=0
local function ok(x,reason)
    count+=1
    assert(x,"G5_REAL_STUDIO_PLAN_NATIVE_FAIL #"..tostring(count).." "..reason)
end
local valid,reason=Plan.validate()
ok(valid,"official plan valid: "..tostring(reason))
ok(Plan.VERSION=="G5_STUDIO_CHECKPOINTS_V1","plan identity")
ok(Plan.MAX_SPEED_STUDS_PER_SEC==58,"teleport threshold safely bounded")
ok(Plan.SAMPLE_INTERVAL>=0.1 and Plan.SAMPLE_INTERVAL<=0.25,"sampling budget")
ok(#Plan.ROUTE_ORDER==5,"exactly five free routes")
ok(#Plan.ROUTES.SEA_BRIDGE==5,"blue port round-trip")
ok(#Plan.ROUTES.SEA_BUBBLE_A==9,"blue sea castle round-trip")
ok(#Plan.ROUTES.SEA_BUBBLE_B==5,"green sea shortcut round-trip")
ok(#Plan.ROUTES.SKY_RAINBOW_A==7,"yellow sky castle round-trip")
ok(#Plan.ROUTES.SKY_RAINBOW_B==7,"purple sky castle round-trip")
for _,id in ipairs(Plan.ROUTE_ORDER) do
    local route=Plan.ROUTES[id]
    local stage=1
    local wrongStage,wrongDone=Plan.advance(id,stage,900,900,900)
    ok(wrongStage==1 and wrongDone==false,"cannot finish from nowhere")
    for i,point in ipairs(route) do
        local outsideStage,outsideDone=Plan.advance(id,stage,point.x+50,point.y,point.z)
        ok(outsideStage==stage and not outsideDone,"cannot skip exact checkpoint")
        stage,done=Plan.advance(id,stage,point.x,point.y,point.z)
        ok(stage==i+1,"one checkpoint step advance")
        ok(done==(i==#route),"outbound and return finish only at end")
    end
    local already,done2=Plan.advance(id,stage,0,3,0)
    ok(already==stage and done2==true,"completed route stable")
    ok(route[1].label=="草原へ戻った" and route[#route].label=="草原へ戻った",
       "must start and physically return to free land")
end
local n,d=Plan.advance("MISSING",1,0,3,0)
ok(n==1 and not d,"invalid route rejects")
local n2,d2=Plan.advance("SEA_BRIDGE",0,0,3,0)
ok(n2==1 and not d2,"invalid stage rejects")
local n3,d3=Plan.advance("SEA_BRIDGE",1,0/0,3,0)
ok(n3==1 and not d3,"NaN input rejected")
local sea=Plan.ROUTES.SEA_BUBBLE_B
ok(sea[3].x==-205 and sea[3].z==30,"green sea castle checkpoint at actual geometry")
local sky=Plan.ROUTES.SKY_RAINBOW_B
ok(sky[4].x==175 and sky[4].y==50 and sky[4].z==33,
   "purple sky castle actual geometry")
print("G5_NATIVE_ACTUAL_STUDIO_CHECKPOINT_PLAN_PASS assertions="..tostring(count))
'''
def main():
    p=argparse.ArgumentParser();p.add_argument("--dir",required=True);a=p.parse_args()
    out=Path(a.dir);out.mkdir(parents=True,exist_ok=True)
    source=FILE.read_text(encoding="utf-8")
    if not source.startswith("--!strict\n") or not source.rstrip().endswith("return Plan"):
        raise RuntimeError("not original Plan source")
    mods={
      "positive":source,
      "BAD_NO_RETURN":source.replace("skyPurpleLow, hub}", "skyPurpleLow, skyPurpleHigh}",1),
      "BAD_CHEAT_SPEED":source.replace("Plan.MAX_SPEED_STUDS_PER_SEC = 58","Plan.MAX_SPEED_STUDS_PER_SEC = 99999",1),
      "BAD_HUGE_RADIUS":source.replace('local bridge = p(-68,3,-15,12,','local bridge = p(-68,3,-15,999,',1),
      "BAD_SEA_CASTLE_TARGET":source.replace('local seaGreenCastle = p(-205,-20,30,14,','local seaGreenCastle = p(-1000,-20,30,14,',1),
      "BAD_REPEATED_ROUTE_ID":source.replace('"SEA_BUBBLE_B","SKY_RAINBOW_A"','"SEA_BUBBLE_B","SEA_BUBBLE_B"',1)
    }
    if len(set(mods.values()))!=len(mods):
        raise RuntimeError("source mutations failed")
    for name,s in mods.items():
        text="local Plan=(function()\n"+s.replace("--!strict\n","",1)+"\nend)()\n"+TESTS
        f=out/(name+".luau")
        f.write_text(text,encoding="utf-8")
        print("G5_STUDIO_PLAN_NATIVE_RUNNER",name,f)
if __name__=="__main__":main()
