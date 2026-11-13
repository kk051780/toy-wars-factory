"""Runs ORIGINAL EvolutionRules and FormDex source in genuine pinned native Luau.
No Roblox/Studio, persistence, or in-game catalog eligibility asserted.
"""
from pathlib import Path
import argparse
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]
EVO=(ROOT/"src/EvolutionRules.luau").read_text(encoding="utf-8")
DEX=(ROOT/"src/EvolutionFormDex.luau").read_text(encoding="utf-8")
TEST= r"""
local E=(function()
__EVO__
end)()
local Dex=(function()
__DEX__
end)().new(E)
local n=0
local function check(v,label)
    assert(v,label)
    n+=1
end
local owned={forest_scout=1}
local p=E.newProfile(777)
local dex,status=Dex.snapshot(p,owned)
check(status=="OK" and dex~=nil,"initial owned")
check(dex.itemCount==1 and dex.discoveredCount==1,"owned starts baby")
check(dex.items[1].activeStage==0,"baby active")
check(dex.items[1].activeFormId=="forest_scout_S0","baby form")
check(dex.items[1].discoveredCount==1,"form count")
check(dex.items[1].totalPossibleForms==6,"six total forms")
check(dex.items[1].missingForms==5,"five to discover")
check(dex.items[1].isCurrentPlayableId==true,"original owned real item")
check(dex.items[1].discoveredForms[1].canEquipDirectly==false,"no client equip")
check(dex.grantEntitlements==false,"not granting")
check(dex.serverReadOnly==true,"pure projection")
check(dex.schema=="EGG_RUMBLE_FORM_DEX_V1","version")
check(p.formDex==nil,"profile not changed by snapshot")
check(E.newProfile(0)==nil,"normal profile validation unchanged")
local blank=Dex.snapshot(p,{})
check(blank~=nil and blank.discoveredCount==0,"unowned empty")
check(blank.itemCount==0,"unowned zero rows")
check(Dex.snapshot(p,{}).items[1]==nil,"no ghost discovery")
check(Dex.snapshot({},owned)==nil,"reject missing profile")
check(Dex.snapshot(p,nil)==nil,"reject missing ownership")
check(Dex.snapshot(p,{forest_scout=0}).itemCount==0,"count0 not owned")
local noBuy={demo_ice_spell=1}
local demo=Dex.snapshot(p,noBuy)
check(demo.items[1].isCurrentPlayableId==false,"future demo never live")
check(demo.items[1].discoveredCount==1,"future demo only hypothetical")

local function earn(count,beginIdx)
    for i=beginIdx,beginIdx+count-1 do
        local ok,amount=E.creditRound(p,"match:"..i,2,240,true)
        check(ok and amount==2,"original genuine credited round"..i)
    end
end
earn(12,1)
check(p.fragments==24,"earned fragments")
local before=E.form(p,"forest_scout",owned)
check(before.stage==0,"original pre-evolution")
local ok,receipt=E.evolve(p,"forest_scout",owned,10,3,
    "LOBBY","grown-01","NONE",true)
check(ok and receipt.stage==1,"level10 grown")
dex,status=Dex.snapshot(p,owned)
check(status=="OK","grown valid")
check(dex.items[1].discoveredCount==2,"baby and grown")
check(dex.items[1].activeFormId=="forest_scout_S1","grown active")
check(dex.items[1].discoveredForms[1].formId=="forest_scout_S0","ordered baby")
check(dex.items[1].discoveredForms[2].formId=="forest_scout_S1","ordered grown")
check(dex.items[1].discoveredForms[1].active==false,"old form is history")
check(dex.items[1].discoveredForms[2].active==true,"current mark")

ok,receipt=E.evolve(p,"forest_scout",owned,25,6,
    "LOBBY","assault-01","ASSAULT",true)
check(ok and receipt.stage==2,"real stage2 assault")
dex,status=Dex.snapshot(p,owned)
check(dex.items[1].discoveredCount==3,"stage2 assault discovered")
check(dex.items[1].activeBranch=="ASSAULT","stage2 active assault")
check(dex.items[1].discoveredForms[3].formId=="forest_scout_S2_ASSAULT","stage2 discovered id")
ok,receipt=E.switchBranch(p,"forest_scout",owned,"LOBBY","guard-01","GUARD",true)
check(ok and receipt.stage==2,"branch respec")
dex,status=Dex.snapshot(p,owned)
check(status=="OK","after branch dex")
check(dex.items[1].discoveredCount==4,"guard and assault history preserved")
check(dex.items[1].activeBranch=="GUARD","guard active")
check(dex.items[1].discoveredForms[3].formId=="forest_scout_S2_ASSAULT","assault remembered")
check(dex.items[1].discoveredForms[4].formId=="forest_scout_S2_GUARD","guard remembered")
check(dex.items[1].discoveredForms[3].active==false,"assault no longer active")
check(dex.items[1].discoveredForms[4].active==true,"guard current")
ok,receipt=E.evolve(p,"forest_scout",owned,40,10,
    "LOBBY","mythic-01","NONE",true)
check(ok and receipt.stage==3,"mythic guardian")
dex,status=Dex.snapshot(p,owned)
check(dex.items[1].discoveredCount==5,"five forms")
check(dex.items[1].activeFormId=="forest_scout_S3_GUARD","mythic guard")
ok,receipt=E.switchBranch(p,"forest_scout",owned,"LOBBY","mythic-assault-01","ASSAULT",true)
check(ok and receipt.stage==3,"mythic assault respec")
dex,status=Dex.snapshot(p,owned)
check(status=="OK" and dex.discoveredCount==6,"six discovery completed")
check(dex.items[1].discoveredCount==6,"single item full album")
check(dex.items[1].missingForms==0,"album complete")
check(dex.items[1].discoveredForms[5].formId=="forest_scout_S3_ASSAULT","stage3 assault order")
check(dex.items[1].discoveredForms[6].formId=="forest_scout_S3_GUARD","stage3 guard order")
check(dex.items[1].discoveredForms[5].active==true,"active assault")
check(dex.items[1].discoveredForms[6].active==false,"previous mythic guard persists")
check(p.formDex==nil,"no hidden profile writes")
local oldCount=dex.discoveredCount
local prior=E.evolve(p,"forest_scout",owned,10,3,
    "LOBBY","grown-01","NONE",true)
check(prior==true,"original replay idempotent")
dex,status=Dex.snapshot(p,owned)
check(dex.discoveredCount==oldCount,"retry cannot duplicate forms")

local snapshotBefore=E.form(p,"forest_scout",owned).formId
-- Corrupt a canonical receipt: fail CLOSED, never grant a fake discovered form.
p.evoReceipts.fake={
    itemId="forest_scout",action="EVOLVE",stage=3,branch="GUARD",
    choice="NONE",formId="forest_scout_S3_ASSAULT"
}
local rejected,reason=Dex.snapshot(p,owned)
check(rejected==nil and reason=="INVALID_EVOLUTION_RECEIPT","fake form rejected")
check(E.form(p,"forest_scout",owned).formId==snapshotBefore,"no profile mutation")
p.evoReceipts.fake=nil
p.evoReceipts.future={
    itemId="forest_scout",action="EVOLVE",stage=4,branch="GUARD",
    choice="NONE",formId="forest_scout_S4_GUARD"
}
check(Dex.snapshot(p,owned)==nil,"stage4 invalid")
p.evoReceipts.future=nil
p.evoReceipts.client={
    itemId="forest_scout",action="SWITCH",stage=2,branch="ASSAULT",
    choice="GUARD",formId="forest_scout_S2_ASSAULT"
}
check(Dex.snapshot(p,owned)==nil,"mismatched switch choice")
p.evoReceipts.client=nil
p.evoReceipts.unknown={
    itemId="forest_scout",action="MAGIC_GRANT",stage=2,branch="ASSAULT",
    choice="ASSAULT",formId="forest_scout_S2_ASSAULT"
}
check(Dex.snapshot(p,owned)==nil,"unknown action rejected")
p.evoReceipts.unknown=nil
p.evoReceipts.invalid={
    itemId="forest_scout",action="EVOLVE",stage=2,branch="ASSAULT",
    choice="ASSAULT",formId="forest_scout_S2_GUARD"
}
check(Dex.snapshot(p,owned)==nil,"invalid receipt form ID rejected")
p.evoReceipts.invalid=nil
-- Extra legacy form from another unowned item must not appear.
local more=E.newProfile(778)
more.evoReceipts.foreign={
   itemId="star_scout",action="EVOLVE",stage=1,branch="NONE",choice="NONE",
   formId="star_scout_S1"
}
local foreignDex=Dex.snapshot(more,{forest_scout=1})
check(foreignDex.discoveredCount==1,"not owned foreign does not grant")
check(foreignDex.itemCount==1,"one owned item only")
-- Test malformed untrusted canonical ownership/form state.
local invalid=E.newProfile(779)
invalid.forms.forest_scout={stage=2,branch="NONE"}
local row,why=Dex.snapshot(invalid,owned)
check(row==nil and why=="INVALID_CANONICAL_FORM","bad canonical branch rejected")
invalid.forms.forest_scout={stage=2,branch="ASSAULT"}
invalid.evoReceipts.higher={
    itemId="forest_scout",action="EVOLVE",stage=3,branch="ASSAULT",
    choice="NONE",formId="forest_scout_S3_ASSAULT"
}
row,why=Dex.snapshot(invalid,owned)
check(row==nil and why=="FUTURE_RECEIPT_FORM","future receipt rejected")
check(Dex.snapshot(E.newProfile(780),{forest_scout=0/0}).itemCount==0,
    "nan owner count rejected")
check(Dex.snapshot(E.newProfile(781),{forest_scout=math.huge}).itemCount==0,
    "inf owned count rejected")
print("P0D_FORM_DEX_NATIVE_PASS_"..n)
"""
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--luau",required=True)
    parser.add_argument("--compiler",required=True)
    opts=parser.parse_args()
    for filename in ("EvolutionRules.luau","EvolutionFormDex.luau"):
        source=ROOT/"src"/filename
        run=subprocess.run([opts.compiler,str(source)],capture_output=True,text=True)
        if run.returncode: raise RuntimeError(f"Native compile failed {source}:\n{run.stderr}")
        print("FORM_DEX_NATIVE_COMPILE_PASS",filename)
    with tempfile.TemporaryDirectory(prefix="p0d_form_dex_") as d:
        out=Path(d)/"test.luau"
        out.write_text(TEST.replace("__EVO__",EVO).replace("__DEX__",DEX),encoding="utf-8")
        result=subprocess.run([opts.luau,str(out)],capture_output=True,text=True)
        if result.returncode:
            raise RuntimeError("Native Luau error:\n"+result.stdout+"\n"+result.stderr)
        print(result.stdout.strip())
        if "P0D_FORM_DEX_NATIVE_PASS_" not in result.stdout:
            raise RuntimeError("Missing native execution witness")
if __name__=="__main__":
    main()
