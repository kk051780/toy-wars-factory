"""Execute the ORIGINAL immutable #281 pure XP engine with the new LevelJourneyView
in an actual pinned native Luau binary, not a Python reinterpretation.
"""
from pathlib import Path
import argparse
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]
POLICY=(ROOT/"src"/"ProgressionRules.luau").read_text(encoding="utf-8")
VIEW=(ROOT/"src"/"LevelJourneyView.luau").read_text(encoding="utf-8")
LUAU_TEST= r"""
local P=(function()
__POLICY__
end)()
local View=(function()
__VIEW__
end)().new(P)
local passed=0
local function verify(cond,name)
    assert(cond,name)
    passed+=1
end
local p=P.newProfile(42)
verify(p~=nil,"valid player profile")
local initial=View.snapshot(p,nil,nil,1)
verify(initial~=nil,"initial view")
verify(initial.account.level==1,"initial Lv1")
verify(initial.account.xp==0,"initial zero XP")
verify(initial.account.needed==60,"original Lv1 threshold")
verify(initial.account.percent==0,"zero progress")
verify(initial.account.remaining==60,"remaining XP")
verify(initial.account.nextReward.level==2,"next Lv2 cosmetic")
verify(initial.account.nextReward.claimStatus=="PREVIEW_ONLY","no fake grant")
verify(initial.focus.level==1,"match focus initial")
verify(initial.focus.needed==25,"focus next threshold")
verify(initial.gameplayStatsIncreased==false,"no p2w")
verify(initial.requiresPaidPurchase==false,"no paid XP")
verify(View.snapshot(p,nil,nil,0)==nil,"reject 0 revision")
verify(View.snapshot(p,nil,nil,-1)==nil,"reject negative revision")
verify(View.snapshot(p,nil,nil,1.25)==nil,"reject fractional revision")
verify(View.snapshot(p,nil,nil,2147483648)==nil,"reject too big revision")
local r=P.newRound("e1-42",42,"SCORE","starter_scout",true)
verify(r~=nil,"round creation")
verify(P.recordEvent(r,"pickup-1","PICKUP",true),"server pickup")
local f1=View.snapshot(p,r,"starter_scout",2)
verify(f1~=nil and f1.focus.level==1,"one pickup level1")
verify(f1.focus.percent==40,"focus 10/25")
verify(f1.mastery.level==1,"starter mastery visible")
verify(f1.mastery.needed==24,"mastery first threshold")
verify(f1.mastery.nextReward.level==3,"mastery next cosmetic")
verify(P.recordEvent(r,"deposit-1","DEPOSIT",true),"server deposit")
verify(View.snapshot(p,r,"starter_scout",3).focus.level==2,"focused Lv2")
verify(P.recordEvent(r,"defend-1","DEFEND",true),"server defend")
verify(P.recordEvent(r,"equip-1","EQUIP_USE",true),"server actual item use")
verify(P.recordEvent(r,"escort-1","ESCORT",true),"server escort")
verify(P.recordEvent(r,"pickup-2","PICKUP",true),"server additional pickup")
verify(View.snapshot(p,r,"starter_scout",4).focus.level==3,"focused Lv3")
verify(View.snapshot(p,r,"starter_scout",4).focus.percent==100,"focus max")
verify(View.snapshot(p,r,"starter_scout",4).focus.nextGoal=="試合内成長MAX！","focus message")
local before={level=p.level,playerUserId=p.playerUserId}
local receipt=P.commit(p,r,"LOSS",60,true)
verify(receipt~=nil,"real source settle")
verify(receipt.grantedXp>=60 and receipt.grantedXp<=150,"capped earned XP")
verify(p.level==2,"first match levels account up")
local result=View.settlement(before,p,receipt,"starter_scout",5)
verify(result~=nil,"display settlement")
verify(result.kind=="SETTLEMENT","settlement schema")
verify(result.playerLeveled==true,"celebration on level")
verify(result.accountLevelAfter==2,"level2 banner")
verify(result.accountMilestones[1].id=="WELCOME_BANNER","actual source milestone id")
verify(result.accountMilestones[1].claimStatus=="PREVIEW_ONLY","not grant")
verify(result.entitlementState=="NOT_GRANTED_BY_THIS_MODULE","no cosmetic entitlements")
verify(result.masteryLevelAfter==nil,"not raw mastery field exposed")
verify(View.settlement(before,p,{rewardKind="BAD",accountLevelBefore=1,
    accountLevelAfter=2,grantedXp=1,gameplayStatsIncreased=false,
    requiresPaidPurchase=false},"starter_scout",6)==nil,"reject invalid receipt")
verify(View.settlement(before,p,{rewardKind="FAIR_PROGRESS_ONLY",accountLevelBefore=1,
    accountLevelAfter=2,grantedXp=1000,gameplayStatsIncreased=false,
    requiresPaidPurchase=false},"starter_scout",6)==nil,"reject inflated receipt")
local current=View.snapshot(p,nil,"starter_scout",6)
verify(current.account.level==2,"level retained")
verify(current.account.nextReward.level==5,"next account prize")
verify(current.account.percent>=0 and current.account.percent<=100,"safe progress")
verify(View.snapshot({playerUserId=42,level=1,xp=-1,mastery={}},nil,nil,7)==nil,
    "no negative xp")
verify(View.snapshot({playerUserId=42,level=1,xp=60,mastery={}},nil,nil,7)==nil,
    "no overflow at current level")
verify(View.snapshot({playerUserId=42,level=1,xp=0/0,mastery={}},nil,nil,7)==nil,
    "no nan xp")
verify(View.snapshot({playerUserId=42,level=1,xp=math.huge,mastery={}},nil,nil,7)==nil,
    "no infinite xp")
verify(View.snapshot({playerUserId=42,level=51,xp=0,mastery={}},nil,nil,7)==nil,
    "reject invalid level51")
verify(View.snapshot({playerUserId=42,level=50,xp=12,mastery={}},nil,nil,7)==nil,
    "max-level residual prohibited")
local capped=View.snapshot({playerUserId=42,level=50,xp=0,mastery={}},nil,nil,7)
verify(capped~=nil and capped.account.percent==100 and capped.account.max,"max level safe")
verify(capped.account.nextReward==nil,"no milestone after Lv50")
verify(View.snapshot(p,{closed=true,playerUserId=42,focusXp=0},"starter_scout",7)==nil,
    "closed round cannot be shown as live")
verify(View.snapshot(p,{closed=false,playerUserId=99,focusXp=0},"starter_scout",7)==nil,
    "reject cross-player round")
verify(View.snapshot(p,{closed=false,playerUserId=42,focusXp=-1},"starter_scout",7)==nil,
    "negative focus rejected")
verify(View.snapshot(p,nil,{},8)==nil,"invalid item id rejected")
verify(View.snapshot(p,nil,string.rep("x",97),8)==nil,"overlong item id rejected")
local madeUp={playerUserId=42,level=10,xp=0}
local cross=View.settlement({playerUserId=42,level=1},madeUp,
 {rewardKind="FAIR_PROGRESS_ONLY",gameplayStatsIncreased=false,
 requiresPaidPurchase=false,accountLevelBefore=1,accountLevelAfter=10,
 grantedXp=150,masteryLevelBefore=2,masteryLevelAfter=10,focusLevel=3},
 "starter_scout",10)
verify(cross~=nil,"multiple-level hypothetical preview")
verify(#cross.accountMilestones==3,"cross account2 5 10")
verify(cross.accountMilestones[1].level==2,"account milestone 2")
verify(cross.accountMilestones[2].level==5,"account milestone 5")
verify(cross.accountMilestones[3].level==10,"account milestone 10")
verify(#cross.masteryMilestones==3,"mastery3 6 10")
verify(cross.masteryMilestones[1].level==3,"mastery3")
verify(cross.masteryMilestones[2].level==6,"mastery6")
verify(cross.masteryMilestones[3].level==10,"mastery10")
verify(cross.itemLeveled==true,"mastery celebration")
verify(cross.requiresPaidPurchase==false,"reward free")
local badPaid={rewardKind="FAIR_PROGRESS_ONLY",gameplayStatsIncreased=false,
 requiresPaidPurchase=true,accountLevelBefore=1,accountLevelAfter=2,grantedXp=70}
verify(View.settlement({playerUserId=42,level=1},
    {playerUserId=42,level=2},badPaid,nil,12)==nil,"paid outcome rejected")
verify(View.settlement({playerUserId=42,level=1},
    {playerUserId=999,level=2},receipt,nil,12)==nil,"mismatched owner denied")
verify(P.commit(p,r,"LOSS",60,true)==nil,"original policy duplicate settle rejected")
print("P0D_LEVEL_JOURNEY_ACTUAL_NATIVE_PASS_"..passed)
"""
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--luau",required=True)
    parser.add_argument("--compiler",required=True)
    args=parser.parse_args()
    for source in (ROOT/"src"/"ProgressionRules.luau",ROOT/"src"/"LevelJourneyView.luau",
                   ROOT/"demo"/"LevelJourneyPreview.server.luau",
                   ROOT/"demo"/"LevelJourneyHUD.client.luau"):
        result=subprocess.run([args.compiler,str(source)],capture_output=True,text=True)
        if result.returncode:
            raise RuntimeError(f"Compiler failed for {source}: {result.stderr}")
        print(f"NATIVE_COMPILE_PASS {source.name}")
    harness=LUAU_TEST.replace("__POLICY__",POLICY).replace("__VIEW__",VIEW)
    with tempfile.TemporaryDirectory(prefix="p0d_level_native_") as tmp:
        path=Path(tmp)/"test_level_journey.luau"
        path.write_text(harness,encoding="utf-8")
        result=subprocess.run([args.luau,str(path)],capture_output=True,text=True)
        if result.returncode:
            raise RuntimeError("Genuine Luau failed:\n"+result.stdout+"\n"+result.stderr)
        print(result.stdout.strip())
        if "P0D_LEVEL_JOURNEY_ACTUAL_NATIVE_PASS_" not in result.stdout:
            raise RuntimeError("Genuine assertion witness not found")
if __name__=="__main__":
    main()
