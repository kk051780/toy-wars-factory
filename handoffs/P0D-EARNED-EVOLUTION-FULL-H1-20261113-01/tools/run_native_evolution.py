"""Execute the original EvolutionRules.luau using a real pinned native Luau VM.
This tests source bytes, NOT Roblox Studio, 3D effects, DataStore or human fun.
"""
from pathlib import Path
import argparse, subprocess, tempfile

ROOT=Path(__file__).resolve().parents[1]
SOURCE=(ROOT/"inputs"/"EvolutionRules.luau").read_text(encoding="utf8")
TEST=r"""
local E=(function()
__SOURCE__
end)()
local count=0
local function check(test,context)
    assert(test,context)
    count+=1
end
local p=E.newProfile(101)
local own={starter_scout=1,forest_scout=1,star_scout=1}
check(p~=nil and p.userId==101,"server profile")
check(E.newProfile(0)==nil,"zero uid refused")
check(E.newProfile(-1)==nil,"negative uid refused")
check(E.newProfile(1.5)==nil,"fractional uid refused")
check(E.newProfile("101")==nil,"string uid refused")
check(p.fragments==0,"fragments start 0")
check(E.form(p,"starter_scout",own).stage==0,"baby stage")
check(E.form(p,"starter_scout",own).formId=="starter_scout_S0","stable first form")
check(E.form(p,"forest_scout",own).stage==0,"forest first")
check(E.form(p,"no_item",own)==nil,"unknown item")
check(E.form(p,"forest_scout",{})==nil,"must own")
check(E.form(p,"demo_ice_spell",own)==nil,"unowned fake demo type")
check(E.form(p,"star_scout",own).additionalPvpStatMultiplier==0,"no stacked permanent pvp bonus")
check(E.form(p,"star_scout",own).actualCombatImplemented==false,"no fake 3d combat")
check(E.form(p,"star_scout",own).requiresPaidPurchase==false,"not sold evolution")
check(E.catalog().demo_signal_trap.category=="TRAP","six-category source schema")
check(E.catalog().demo_ice_spell.category=="SPELL","spell schema")
check(E.catalog().demo_cloud_mount.category=="MOUNT","mount schema")
check(E.catalog().demo_ward_item.category=="ITEM","item schema")
check(E.catalog().demo_zombie.category=="ZOMBIE","zombie schema")
check(E.catalog().star_scout.liveId==true,"real #275 star item")
check(E.catalog().demo_signal_trap.liveId==false,"demo not live")
local first=E.nextEvolution(p,"star_scout",own,1,1)
check(first.toStage==1,"first stage")
check(first.fragmentCost==2,"first cost")
check(first.accountLevelRequired==10,"first level gate")
check(first.masteryRequired==3,"first mastery gate")
check(first.available==false,"first locked")
check(E.creditRound(p,"job:round:0",0,240,true)==false,"afk grants zero")
check(E.creditRound(p,"job:round:0",3,30,true)==false,"short-match exploit denied")
check(E.creditRound(p,"job:round:0",3,240,false)==false,"client cannot credit")
check(E.creditRound(p,"",3,240,true)==false,"empty match receipt")
local good,earned,status=E.creditRound(p,"job:round:1",1,240,true)
check(good and earned==1 and status=="CREDITED","first legit round gets1")
check(p.fragments==1,"one fragment credited")
good,earned,status=E.creditRound(p,"job:round:1",20,240,true)
check(good and earned==1 and status=="ALREADY_CREDITED","round replay idempotent")
check(p.fragments==1,"round replay no mint")
good,earned,status=E.creditRound(p,"job:round:2",2,240,true)
check(good and earned==2,"two real actions gets2")
check(p.fragments==3,"three fragments total")
check(E.nextEvolution(p,"star_scout",own,9,3).available==false,"level gate")
check(E.nextEvolution(p,"star_scout",own,10,2).available==false,"mastery gate")
check(E.nextEvolution(p,"star_scout",own,10,3).available==true,"first evolution ready")
check(E.evolve(p,"star_scout",own,10,3,"ACTIVE","evo1","NONE",true)==false,
    "no evolve during combat")
check(E.evolve(p,"star_scout",own,10,3,"LOBBY","evo1","ASSAULT",true)==false,
    "cannot choose branch at stage1")
check(E.evolve(p,"star_scout",own,10,3,"LOBBY","evo1","NONE",false)==false,
    "fake client evolve")
local ok,receipt,remark=E.evolve(p,"star_scout",own,10,3,"LOBBY","evo1","NONE",true)
check(ok and remark=="EVOLVED" and receipt.stage==1,"grown form granted")
check(p.fragments==1,"shards deducted stage1")
check(E.form(p,"star_scout",own).stage==1,"grown read only")
check(E.form(p,"star_scout",own).formId=="star_scout_S1","grown form stable id")
ok,receipt,remark=E.evolve(p,"star_scout",own,10,3,"LOBBY","evo1","NONE",true)
check(ok and remark=="ALREADY_EVOLVED","evolution retry replay")
check(p.fragments==1,"no double cost")
check(E.evolve(p,"forest_scout",own,10,3,"LOBBY","evo1","NONE",true)==false,
    "receipt cannot transfer to different item")
check(E.evolve(p,"star_scout",own,10,3,"LOBBY","evo1","ASSAULT",true)==false,
    "receipt mismatched branch rejected")
check(E.nextEvolution(p,"star_scout",own,24,6).available==false,"stage2 level gate")
check(E.nextEvolution(p,"star_scout",own,25,5).available==false,"stage2 mastery gate")
check(E.evolve(p,"star_scout",own,25,6,"LOBBY","evo2","GUARD",true)==false,
    "insufficient stage2 shards")
for i=3,6 do
    local success=E.creditRound(p,"job:round:"..i,2,240,true)
    check(success,"extra legit rounds")
end
check(p.fragments==9,"enough shards for branches")
check(E.evolve(p,"star_scout",own,25,6,"LOBBY","evo2","NONE",true)==false,
    "must choose branch at stage2")
ok,receipt,remark=E.evolve(p,"star_scout",own,25,6,"LOBBY","evo2","ASSAULT",true)
check(ok and receipt.stage==2 and receipt.branch=="ASSAULT","assault branch")
check(p.fragments==4,"stage2 shard cost")
check(E.form(p,"star_scout",own).abilityDesignId=="SKY_HUNTER",
    "assault beast design ability")
check(E.form(p,"star_scout",own).additionalPvpStatMultiplier==0,
    "no damage stacking with #285")
check(E.nextEvolution(p,"star_scout",own,39,10).available==false,
    "mythic account gate")
check(E.nextEvolution(p,"star_scout",own,40,9).available==false,
    "mythic mastery gate")
check(E.switchBranch(p,"star_scout",own,"ACTIVE","s1","GUARD",true)==false,
    "branch change lobby only")
ok,receipt,remark=E.switchBranch(p,"star_scout",own,"LOBBY","s1","GUARD",true)
check(ok and receipt.branch=="GUARD" and receipt.cost==3,"free earned respec")
check(p.fragments==1,"respec earned material deducted")
check(E.form(p,"star_scout",own).abilityDesignId=="EGG_GUARDIAN",
    "actual branch alternative contract")
ok,receipt,remark=E.switchBranch(p,"star_scout",own,"LOBBY","s1","GUARD",true)
check(ok and remark=="ALREADY_SWITCHED","respec idempotent")
check(p.fragments==1,"no doubled deduction for respec")
check(E.switchBranch(p,"star_scout",own,"LOBBY","s1","ASSAULT",true)==false,
    "receipt conflict blocks differing branch")
check(E.switchBranch(p,"star_scout",own,"LOBBY","s2","ASSAULT",true)==false,
    "no fragments no switch")
for i=7,12 do
    local yes=E.creditRound(p,"job:round:"..i,2,240,true)
    check(yes,"real repeat-game resources")
end
check(p.fragments==13,"pre-mythic shards")
check(E.evolve(p,"star_scout",own,40,10,"LOBBY","evo3","GUARD",true)==false,
    "final evolution inherits branch, choice NONE")
ok,receipt,remark=E.evolve(p,"star_scout",own,40,10,"LOBBY","evo3","NONE",true)
check(ok and receipt.stage==3 and receipt.branch=="GUARD","mythic earned")
check(E.form(p,"star_scout",own).formId=="star_scout_S3_GUARD","mythic stable")
check(E.form(p,"star_scout",own).formToken=="MYTHIC","mythic presentation")
check(p.fragments==3,"mythic shard cost")
check(E.nextEvolution(p,"star_scout",own,50,10).complete==true,
    "no fourth stage fake")
check(E.evolve(p,"star_scout",own,50,10,"LOBBY","evo4","NONE",true)==false,
    "cannot repeat final")
ok,receipt,remark=E.switchBranch(p,"star_scout",own,"LOBBY","s3","ASSAULT",true)
check(ok and receipt.stage==3 and receipt.branch=="ASSAULT",
    "mythic branch can change without losing stage")
check(p.fragments==0,"earned material consumed")
check(E.form(p,"star_scout",own).formId=="star_scout_S3_ASSAULT",
    "new mythic path")
check(E.form(p,"forest_scout",own).stage==0,"other beast untouched")
check(E.form(p,"starter_scout",own).stage==0,"starter stays original")
check(E.evolve(p,"demo_ice_spell",own,50,10,"LOBBY","x","NONE",true)==false,
    "unowned demo spell cannot evolve")
local sp={demo_ice_spell=1}
check(E.form(p,"demo_ice_spell",sp).category=="SPELL",
    "future spell schema if canon grants owned")
check(E.form(p,"demo_ice_spell",sp).isCurrentPlayableId==false,
    "future spell never falsely live")
local u=E.newProfile(456)
u.roundCount=E.MAX_ROUND_RECEIPTS
check(E.creditRound(u,"job:max",2,240,true)==false,"round ledger full")
u.evoCount=E.MAX_EVOLUTION_RECEIPTS
check(E.evolve(u,"star_scout",own,50,10,"LOBBY","new","NONE",true)==false,
    "cannot evolve if insufficient resources")
print("P0D_EVOLUTION_ORIGINAL_NATIVE_PASS_"..count)
"""
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--luau",required=True)
    ap.add_argument("--compiler",required=True)
    args=ap.parse_args()
    source=ROOT/"src"/"EvolutionRules.luau"
    c=subprocess.run([args.compiler,str(source)],capture_output=True,text=True)
    if c.returncode: raise RuntimeError(f"NATIVE COMPILER FAILED: {c.stderr}")
    print("EVOLUTION_POLICY_NATIVE_COMPILE_PASS")
    with tempfile.TemporaryDirectory(prefix="p0d_evolution_test_") as temp:
        t=Path(temp)/"test_evolution.luau"
        t.write_text(TEST.replace("__SOURCE__",SOURCE),encoding="utf8")
        out=subprocess.run([args.luau,str(t)],capture_output=True,text=True)
        if out.returncode: raise RuntimeError("Native Luau runtime failed:\n"+out.stdout+"\n"+out.stderr)
        print(out.stdout.strip())
        if "P0D_EVOLUTION_ORIGINAL_NATIVE_PASS_" not in out.stdout:
            raise RuntimeError("Genuine execution witness not found")
if __name__=="__main__":
    main()
