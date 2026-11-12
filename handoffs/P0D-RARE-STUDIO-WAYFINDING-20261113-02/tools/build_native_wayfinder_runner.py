"""Execute authentic previous #243 FULL game-server source test runner, now with
one additional original Wayfinding Lua module and exact new server candidate.
Only Roblox EXTERNAL engine services are fake (two Player event instances).
"""
from pathlib import Path
import argparse,importlib.util
R=Path(__file__).resolve().parents[1]
PARENT=R.parent/"P0D-RARE-CHILD-CLUE-COMPASS-20261113-01"
PARENT_RUNNER=PARENT/"tools/build_native_clue_runner.py"
spec=importlib.util.spec_from_file_location("p0d_frozen_original_clue_native",PARENT_RUNNER)
assert spec and spec.loader
clue=importlib.util.module_from_spec(spec)
spec.loader.exec_module(clue)
base=clue.base
GUIDE=R/"src/RareStudioGuides.luau"
SERVER=R/"src/RareDiscoveryWayfindingPreview.server.luau"
base.FILES.append(("Guides",GUIDE,"return Guides"))
original_wrap=base.wrap_source
original_build=base.build
ACTIVE={"kind":None}
def wrap(name,text):
    if name=="Guides":
        mapping=[
            ("local Plan = require(script.Parent.RareDiscoveryQAPlan)","local Plan = Plan"),
            ("local Policy = require(script.Parent.RareEncounterPolicy)","local Policy = Policy"),
        ]
        for src,dst in mapping:
            if text.count(src)!=1:raise ValueError("original Guides dependency contract broken")
            text=text.replace(src,dst,1)
        mutants={
          "BAD_ALL_SIGNS_VISIBLE":(
              'markers[id].gui.Enabled=found and id==currentId',
              'markers[id].gui.Enabled=true'),
          "BAD_COLLIDING_SIGN":(
              "marker.CanCollide=false","marker.CanCollide=true"),
          "BAD_SIGNS_ALL_AT_HUB_CENTER":(
              "marker.Position=Vector3.new(base.X,5,base.Z)",
              "marker.Position=Vector3.new(0,5,0)"),
          "BAD_EXPIRY_SIGN_NOT_CLEARED":(
              "markers[id].gui.Enabled=false","markers[id].gui.Enabled=true"),
          "BAD_FALSE_REWARD_ADVERT":(
              'label.Text="いまは ここ！\\n"..Guides.MARKERS[id].title',
              'label.Text="コイン100こ！"'),
        }
        if ACTIVE["kind"] in mutants:
            before,after=mutants[ACTIVE["kind"]]
            if text.count(before)!=1:raise RuntimeError("guide source mutant exact anchor absent: "+ACTIVE["kind"])
            text=text.replace(before,after,1)
    return original_wrap(name,text)
base.wrap_source=wrap

def build(server):
    token="local Guides=require(script.Parent.RareStudioGuides)"
    if server.count(token)!=1:raise RuntimeError("invalid original guide require")
    return original_build(server.replace(token,"local Guides=Guides",1))
base.build=build

# The other 115 source assertions from #243 and #239 remain unchanged.
# Add physically ground-positioned guide checks INSIDE each 26-second slot
# before original server source test destroys the entire owner preview scene.
AFTER_MODEL='    local model,body,prompt,layer=nowEncounter(id)'
EXTRA_PER_SLOT=r'''
    local worldScene=workspace:FindFirstChild("P0D_FourRareRealms")
    local waypoints=worldScene and worldScene:FindFirstChild("P0D_RARE_QA_CURRENT_GUIDES")
    ok(waypoints~=nil,"current stage visible in scene's separate guides folder")
    ok(waypoints:GetAttribute("RewardsOrCoins")=="NONE",
       "waypoints cannot grant any inventory or coins")
    local visible=0
    for _,realm in ipairs(Plan.ORDER) do
        local marker=waypoints:FindFirstChild("GUIDE_"..realm)
        local expected=Plan.point(realm)
        ok(marker~=nil and marker:IsA("BasePart"),"all four original markers exist")
        ok(marker.Anchored==true and marker.CanCollide==false and
           marker.CanTouch==false and marker.CanQuery==false,
           "visible guidance must never block player movement or touch")
        ok(marker.Position.X==expected.X and marker.Position.Z==expected.Z,
           "mark the EXACT current real QA world baseline, not fake center")
        local gui=marker:FindFirstChild("CurrentCreatureOnly")
        local label=gui and gui:FindFirstChild("ChildCurrentRealmGuide")
        ok(gui~=nil and label~=nil and label.TextWrapped==true,
           "readable sign has an original source BillboardGui and wrapped text")
        ok(string.find(label.Text,"いまは ここ！",1,true)~=nil and
           string.find(label.Text,"コイン",1,true)==nil,
           "one current world clue without fabricated payouts")
        if gui.Enabled then
            visible+=1
            ok(realm==id,
               "NEVER point a child to a different expired or next world")
        end
    end
    ok(visible==1,"EXACTLY ONE currently active rare creature sign")
'''
if base.TESTS.count(AFTER_MODEL)!=1:
    raise RuntimeError("original full server native test stage loop changed")
base.TESTS=base.TESTS.replace(AFTER_MODEL,AFTER_MODEL+"\n"+EXTRA_PER_SLOT,1)
AFTER_EXPIRY='    ok(nowEncounter(id)==nil,"expired/hidden creature is not interactable")'
EXTRA_EXPIRY=r'''
    local closed=workspace:FindFirstChild("P0D_FourRareRealms")
    local signFolder=closed and closed:FindFirstChild("P0D_RARE_QA_CURRENT_GUIDES")
    local activeAfter=0
    for _,realm in ipairs(Plan.ORDER) do
        local marker=signFolder:FindFirstChild("GUIDE_"..realm)
        if marker:FindFirstChild("CurrentCreatureOnly").Enabled then activeAfter+=1 end
    end
    ok(activeAfter==0,"all 4 signs hidden as soon as creature expires")
'''
if base.TESTS.count(AFTER_EXPIRY)!=1:raise RuntimeError("original full native expiry test changed")
base.TESTS=base.TESTS.replace(AFTER_EXPIRY,AFTER_EXPIRY+"\n"+EXTRA_EXPIRY,1)
base.TESTS+=r'''
local actualGuides=Guides.validate()
ok(actualGuides,"new Guide module validation in original native runtime")
originalPrint("P0D_RARE_WAYFINDING_FULL_SERVER_NATIVE_PASS assertions="..tostring(assertCount)..
    " simulated_players=2 four_hub_markers=true current_one_only=true")
'''

def emit(out,name,src,mutation=None):
    ACTIVE["kind"]=mutation
    generated=base.build(src)
    ACTIVE["kind"]=None
    file=out/(name+".luau")
    file.write_text(generated,encoding="utf-8")
    print("P0D_CURRENT_WAYFINDING_ORIGINAL_LUAU_TEST",name,file)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",required=True)
    a=p.parse_args()
    out=Path(a.output)
    out.mkdir(parents=True,exist_ok=True)
    src=SERVER.read_text(encoding="utf-8")
    if not src.startswith("--!strict\n"):raise ValueError("candidate source not strict Luau")
    emit(out,"positive",src)
    for k in ("BAD_ALL_SIGNS_VISIBLE","BAD_COLLIDING_SIGN",
              "BAD_SIGNS_ALL_AT_HUB_CENTER","BAD_EXPIRY_SIGN_NOT_CLEARED",
              "BAD_FALSE_REWARD_ADVERT"):
        emit(out,k,src,k)
    server_mutations={
       "BAD_SERVER_HIGHLIGHTS_WRONG_CREATURE":(
          'guides:show(id)','guides:show("SPACE")'),
       "BAD_SERVER_SKIPS_CLEAR":(
          'guides:clear()','-- guides:clear()'),
    }
    for k,(old,new) in server_mutations.items():
        if src.count(old)!=1:raise ValueError("original server mutation anchor absent")
        emit(out,k,src.replace(old,new,1))
    if len(list(out.glob("*.luau")))!=8:raise RuntimeError("wrong positive/negative case count")
if __name__=="__main__":
    main()
