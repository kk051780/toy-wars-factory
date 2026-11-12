"""Execute EXACT original rare encounter Policy + moving Models on real native Luau.
External Roblox Instance/Color3/CFrame APIs alone are emulated; no Lua model rewrites.
Frozen 4-world Catalog is embedded byte-for-byte from issue #230's original root.
"""
from pathlib import Path
import argparse
ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT.parent/"P0D-WORLD-RARE-4REALMS-3D-20261112-01/src/RareRealmCatalog.luau"
POLICY=ROOT/"src/RareEncounterPolicy.luau"
MODELS=ROOT/"src/RareEncounterModels.luau"

MOCKS=r'''
local V={}
V.__add=function(a,b)return setmetatable({X=a.X+b.X,Y=a.Y+b.Y,Z=a.Z+b.Z},V) end
V.__sub=function(a,b)return setmetatable({X=a.X-b.X,Y=a.Y-b.Y,Z=a.Z-b.Z},V) end
V.__index=function(v,k)
    if k=="Magnitude" then return math.sqrt(v.X*v.X+v.Y*v.Y+v.Z*v.Z) end
end
local function vec(x,y,z)return setmetatable({X=x,Y=y,Z=z},V) end
Vector3={new=vec}
Color3={fromRGB=function(r,g,b)return {r=r,g=g,b=b} end}
CFrame={new=function(pos)return {Position=pos} end}
Enum={Material={SmoothPlastic="SmoothPlastic"},PartType={Ball="Ball"},
    Font={GothamBold="GothamBold"}}
UDim2={fromOffset=function(x,y)return {x=x,y=y} end,
    fromScale=function(x,y)return {x=x,y=y} end}
local function Obj(kind)
    local data={ClassName=kind,Name=kind,_children={},attrs={}}
    local obj
    obj=setmetatable({},{
        __index=function(_,key)
            if key=="IsA" then
                return function(self,class)
                    return class==kind or class=="Instance" or
                        (class=="BasePart" and kind=="Part")
                end
            end
            if key=="GetChildren" then return function(self) return data._children end end
            if key=="SetAttribute" then
                return function(self,name,value)data.attrs[name]=value end
            end
            if key=="GetAttribute" then
                return function(self,name)return data.attrs[name] end
            end
            if key=="FindFirstChild" then
                return function(self,name)
                    for _,child in ipairs(data._children) do
                        if child.Name==name then return child end
                    end
                    return nil
                end
            end
            if key=="PivotTo" then
                return function(self,cf)
                    assert(kind=="Model","can only PivotTo Model")
                    local primary=self.PrimaryPart
                    assert(primary~=nil,"missing PrimaryPart")
                    local delta=cf.Position-primary.Position
                    for _,child in ipairs(self:GetChildren()) do
                        if child:IsA("BasePart") then
                            child.Position=child.Position+delta
                        end
                    end
                    data.LastCFrame=cf
                end
            end
            if key=="Destroy" then
                return function(self) self.Parent=nil;data.destroyed=true end
            end
            return data[key]
        end,
        __newindex=function(_,key,value)
            if key=="Parent" then
                if data.Parent then
                    for i,c in ipairs(data.Parent._children) do
                        if c==obj then table.remove(data.Parent._children,i);break end
                    end
                end
                data.Parent=value
                if value then table.insert(value._children,obj) end
            else data[key]=value end
        end
    })
    return obj
end
Instance={new=Obj}
'''

CASES=r'''
local count=0
local function ok(value,why)
    count+=1
    assert(value,"RARE_NEUTRAL_NATIVE_FAIL assertion="..tostring(count).." "..why)
end
local function near(a,b)return math.abs(a-b)<0.001 end
local good,reason=Catalog.validate()
ok(good,"original frozen #230 catalog valid "..tostring(reason))
local valid,description=Policy.validate()
ok(valid,"safe encounter preview rate limits "..tostring(description))
ok(Policy.WINDOW_SECONDS==45,"one opportunity per fortyfive seconds")
ok(Policy.SPAWN_CHANCE==0.12,"configured test chance only")
ok(Policy.MAX_ACTIVE==1,"global active max one")
ok(Policy.TELEGRAPH_SECONDS>=2,"kid sees creature before prompt")
ok(Policy.LIFETIME_SECONDS<=28,"bounded encounter life")
ok(Policy.MIN_INTERACTION_DISTANCE<=14,"no remote touching")
ok(#Policy.ROUTE_ORDER==4,"four rare worlds")
for index,id in ipairs(Policy.ROUTE_ORDER) do
    ok(Policy.worldForWindow(index-1)==id,"round robin deterministic world")
    ok(Catalog.WORLDS[id]~=nil,"no mismatched world catalog")
    ok(Policy.CREATURES[id]~=nil,"one original rarity per realm")
end
ok(Policy.worldForWindow(-1)==nil,"reject invalid window")
ok(Policy.worldForWindow(0/0)==nil,"reject NaN window")
ok(Policy.validNow(0),"now zero valid")
ok(not Policy.validNow(-1),"time cannot be negative")
local initial=Policy.newState()
ok(initial.lastWindow==-1 and initial.activeId==nil,"new state empty")
local missed,e=Policy.step(initial,0,0.55)
ok(e.kind=="MISSED" and missed.lastWindow==0,"normal no-spawn")
ok(initial.lastWindow==-1,"pure next state must not mutate original")
local same,e2=Policy.step(missed,20,0)
ok(e2.kind=="NONE" and same==missed,"repeat chance cannot spawn in same window")
local never,e3=Policy.step(missed,45,1)
ok(e3.kind=="RNG_INVALID" and never.activeId==nil,"invalid RNG fail-closed")
local boundary,eb=Policy.step(initial,0,0.12)
ok(eb.kind=="MISSED","exact chance bound misses")
local star,es=Policy.step(initial,0,0.1199)
ok(es.kind=="SPAWN" and es.id=="SPACE","at most one star whale on first chance")
ok(star.serial==1 and near(star.activeUntil,28),"bounded generation/expiry")
local active,ea=Policy.step(star,20,0.01)
ok(ea.kind=="NONE" and active.activeId=="SPACE","cannot resummon while active")
local expired,ex=Policy.step(star,28,0.01)
ok(ex.kind=="DESPAWN" and expired.activeId==nil,"life expiry removes neutral")
local noAgain,ex2=Policy.step(expired,29,0)
ok(ex2.kind=="NONE","same world interval may not reroll")
local pegasus,ep=Policy.step(expired,45,0.01)
ok(ep.kind=="SPAWN" and ep.id=="CELESTIAL","next rare world rotates")
local pegasusOff,ex3=Policy.step(pegasus,73,0.01)
ok(ex3.kind=="DESPAWN","one active generation cleared before next")
local mole,em=Policy.step(pegasusOff,90,0.01)
ok(em.kind=="SPAWN" and em.id=="EMBER","ember turns on its own chance window")
local moleOff,ex4=Policy.step(mole,118,0)
local eclipse,ee=Policy.step(moleOff,135,0.01)
ok(ee.kind=="SPAWN" and ee.id=="ECLIPSE","eclipse turn after ember")
local bogus,ebi=Policy.step(nil,10,0)
ok(ebi.kind=="INVALID","invalid state rejected")
for _,id in ipairs(Policy.ROUTE_ORDER) do
    local a=Policy.motion(id,0)
    local b=Policy.motion(id,7)
    ok(a.alpha>=0 and a.alpha<=1 and b.alpha>=0 and b.alpha<=1,
        "visual transparency constrained")
    ok(a.description~="INVALID" and b.description~="INVALID",
        "different original movement descriptions")
    ok(math.abs(a.x)<=15 and math.abs(a.z)<=15 and a.y>=0 and a.y<=21,
        "original gentle motion always around its own realm")
    ok(math.abs(a.x-b.x)+math.abs(a.y-b.y)+math.abs(a.z-b.z)>0.5,
        "creature actually changes 3D position over 7 sec")
end
ok(Policy.motion("UNKNOWN",1).description=="INVALID","unknown creature rejects")
ok(Policy.motion("SPACE",0/0).description=="INVALID","invalid movement time rejected")
ok(Policy.motion("EMBER",6).alpha>0.5,"mole actually hides")
ok(Policy.motion("EMBER",2).alpha==0,"mole appears again")
ok(Policy.motion("ECLIPSE",31).description=="月の側","eclipse changes announced side")

local parent=Instance.new("Folder")
local built={}
for _,id in ipairs(Policy.ROUTE_ORDER) do
    local pet=Models.create(id,parent)
    built[id]=pet
    ok(pet.model.Name=="RARE_NEUTRAL_"..id,"original model distinct")
    ok(pet.model.Parent==parent and pet.model.ClassName=="Model",
        "physical Roblox Model created")
    ok(pet.model.PrimaryPart==pet.body,"pivot foundation exists")
    ok(pet.model:GetAttribute("NonCanonicalD18")==true,
        "collection character ownership not taken")
    ok(pet.model:GetAttribute("NoDropsNoCurrencyNoDamage")==true,
        "zero award, no attacks")
    ok(pet.originalParts>=7 and pet.originalParts<=12,
        "bounded geometric model part count")
    local bodyParts=0
    for _,child in ipairs(pet.model:GetChildren()) do
        if child:IsA("BasePart") then
            bodyParts+=1
            ok(child.Anchored==true,"neutral creature all parts anchored")
            ok(child.CanCollide==false,"neutral never blocks walking")
            ok(child.CanQuery==false and child.CanTouch==false,
                "no touch effects or hidden physical query")
        end
    end
    ok(bodyParts==pet.originalParts,"physical parts count matches real source")
    ok(pet.prompt.ClassName=="ProximityPrompt","actual discovery engine prompt")
    ok(pet.prompt.ActionText=="みつけた!","child accessible safe discover cue")
    ok(pet.prompt.HoldDuration>=0 and pet.prompt.HoldDuration<=0.5,
        "small child can discover quickly")
    ok(pet.prompt.MaxActivationDistance<=Policy.MIN_INTERACTION_DISTANCE,
        "no remote click accepted")
    local label=pet.body:FindFirstChild("VisibleRareDiscoveryCue")
    ok(label and label.ClassName=="BillboardGui",
        "unique real BillboardGui source")
    local txt=label:FindFirstChild("FriendlyRareName")
    ok(txt and txt.TextScaled==true and #txt.Text>=5,
        "child-readable local-language model name")

    local base=Vector3.new(id=="SPACE" and 240 or id=="EMBER" and -240 or 0,
        id=="CELESTIAL" and 30 or 0,
        id=="CELESTIAL" and 240 or id=="ECLIPSE" and -240 or 0)
    local path=Models.update(pet,base,0)
    ok(pet.model:GetAttribute("CreatureMood")==path.description,
        "same original moving visual mood")
    ok(near(pet.body.Position.X,base.X+path.x) and
        near(pet.body.Position.Y,base.Y+path.y) and
        near(pet.body.Position.Z,base.Z+path.z),
        "actual Model:PivotTo moved ALL original parts to realm coordinates")
    local before=pet.body.Position
    local later=Models.update(pet,base,7)
    ok((pet.body.Position-before).Magnitude>0.5,
        "actual Model moves through time, not static rare sculpture")
    ok(near(pet.model:GetAttribute("VisualHideAlpha"),later.alpha),
        "animation alpha reflects exact active state")
end
ok(#parent:GetChildren()==4,"four separate original moving visual models available")
print("RARE_NEUTRAL_REAL_ORIGINAL_LUAU_NATIVE_PASS assertions="..tostring(count)..
    " noncombat_models=4 spawn_cap=1 free_prompt=true")
'''

def source(name, ending):
    s=Path(name).read_text(encoding="utf-8")
    if not s.startswith("--!strict\n") or not s.rstrip().endswith(ending):
        raise ValueError("Unfamiliar original source: "+str(name))
    return s.replace("--!strict\n","",1)
def main():
    a=argparse.ArgumentParser()
    a.add_argument("--output-dir",required=True)
    args=a.parse_args()
    out=Path(args.output_dir)
    out.mkdir(parents=True,exist_ok=True)
    catalog=source(OLD,"return Catalog")
    policy=source(POLICY,"return P")
    models=source(MODELS,"return M")
    needle="local Policy = require(script.Parent.RareEncounterPolicy)"
    if models.count(needle)!=1:raise ValueError("Models source contract changed")
    changes={
        "positive":(policy,models),
        "BAD_ODDS_ALWAYS_SPAWN":(policy.replace("P.SPAWN_CHANCE = 0.12","P.SPAWN_CHANCE = 0.99",1),models),
        "BAD_MULTIPLE_SIMULTANEOUS":(policy.replace("P.MAX_ACTIVE = 1","P.MAX_ACTIVE = 4",1),models),
        "BAD_NO_DISCOVERY_TELEGRAPH":(policy.replace("P.TELEGRAPH_SECONDS = 2","P.TELEGRAPH_SECONDS = 0",1),models),
        "BAD_TOO_FAST_REROLL":(policy.replace("P.WINDOW_SECONDS = 45","P.WINDOW_SECONDS = 8",1),models),
        "BAD_AWARDS_FLAG":(policy,models.replace('model:SetAttribute("NoDropsNoCurrencyNoDamage",true)',
            'model:SetAttribute("NoDropsNoCurrencyNoDamage",false)',1)),
        "BAD_NEUTRAL_COLLISION":(policy,models.replace('p.CanCollide=false','p.CanCollide=true',1)),
        "BAD_PAY_TO_DISCOVER":(policy,models.replace('prompt.ActionText="みつけた！"',
            'prompt.ActionText="Pay Robux"',1)),
        "BAD_MODEL_NOT_MOVING":(policy,models.replace(
            'encounter.model:PivotTo(CFrame.new(destination))',
            'encounter.model:PivotTo(CFrame.new(base))',1)),
    }
    if len(set(changes.values()))!=len(changes):
        raise RuntimeError("Bad mutant didn't actually change exact original source")
    for name,(pol,model) in changes.items():
        combined=(MOCKS+"\nlocal Catalog=(function()\n"+catalog+
            "\nend)()\nlocal Policy=(function()\n"+pol+
            "\nend)()\nlocal Models=(function()\n"+
            model.replace(needle,"local Policy = Policy",1)+
            "\nend)()\n"+CASES)
        f=out/(name+".luau")
        f.write_text(combined,encoding="utf-8")
        print("RARE_NEUTRAL_EXACT_NATIVE_RUNNER_WRITTEN",name,f)
if __name__=="__main__":
    main()
