"""Execute EXACT original G5 3D Scene.build and Routes source with native Luau.
Only Roblox Engine service objects are mocked, never original scene functions.
Negative mutation runners mutate the actual source text (NOT an invented geometry toy).
"""
from pathlib import Path
import argparse

BASE = Path(__file__).resolve().parents[2] / "P0D-WORLD-LINK-G5-20261112-01"
SCENE = BASE / "src/WorldLinkScene.luau"
ROUTES = BASE / "src/WorldLinkRoutes.luau"

MOCKS = r'''
local function vec(x,y,z) return {X=x,Y=y,Z=z} end
Vector3={new=vec}
Color3={fromRGB=function(r,g,b) return {R=r,G=g,B=b} end}
Enum={Material={Grass="Grass",SmoothPlastic="SmoothPlastic",Glass="Glass",
    Neon="Neon",WoodPlanks="WoodPlanks"},PartType={Ball="Ball"},
    Font={GothamBold="GothamBold"}}
UDim2={fromOffset=function(x,y) return {kind="offset",X=x,Y=y} end,
    fromScale=function(x,y) return {kind="scale",X=x,Y=y} end}
local CF={}
CF.__mul=function(a,b) return setmetatable({Position=a.Position,angle=b.angle},CF) end
CFrame={
    new=function(pos) return setmetatable({Position=pos,angle=0},CF) end,
    Angles=function(x,y,z) return setmetatable({angle=z},CF) end
}
local function RobloxObject(class)
    local data={ClassName=class,Name=class,_children={},attributes={}}
    local obj
    obj=setmetatable({},{
        __index=function(_,key)
            if key=="IsA" then
                return function(self,name) return data.ClassName==name end
            elseif key=="FindFirstChild" then
                return function(self,name)
                    for _,c in ipairs(data._children) do
                        if c.Name==name then return c end
                    end
                    return nil
                end
            elseif key=="SetAttribute" then
                return function(self,name,value) data.attributes[name]=value end
            elseif key=="GetAttribute" then
                return function(self,name) return data.attributes[name] end
            elseif key=="Destroy" then
                return function(self)
                    self.Parent=nil
                    data.destroyed=true
                end
            else
                return data[key]
            end
        end,
        __newindex=function(_,key,value)
            if key=="Parent" then
                local prior=data.Parent
                if prior then
                    for i,c in ipairs(prior._children) do
                        if c==obj then table.remove(prior._children,i);break end
                    end
                end
                data.Parent=value
                if value then table.insert(value._children,obj) end
            else
                data[key]=value
            end
        end
    })
    return obj
end
Instance={new=RobloxObject}
'''

CASES = r'''
local count=0
local function ok(value,reason)
    count+=1
    assert(value,"G5_NATIVE_REAL_SCENE_FAIL assertion="..tostring(count).." "..reason)
end
local function close(a,b)
    return math.abs(a-b)<0.03
end
local world=Instance.new("Workspace")
local valid,reason=Routes.validate()
ok(valid,"graph valid")
local scene=Scene.build(world)
ok(scene~=nil,"original Scene.build returned")
ok(scene.folder.Parent==world,"scene attached to the right Workspace")
ok(scene.folder.Name=="WF_G5_LandSeaSky","scene unique name")
ok(world:FindFirstChild("WF_G5_LandSeaSky")==scene.folder,"findable by exact name")
ok(scene.spawn.Parent==scene.folder,"spawn under new standalone folder")
ok(scene.spawn.Neutral==true,"spawn neutral all roles")
ok(scene.spawn.Anchored==true,"spawn anchored")
ok(scene.folder:GetAttribute("WF_SourceMode")=="SOURCE_ONLY_NO_STUDIO_QA","truthful source status")
ok(scene.folder:GetAttribute("WF_NpcSpawnProbability")=="NOT_SET","rare NPC odds explicitly unset")
ok(scene.folder:GetAttribute("WF_EggAndCombatOwnedBy")=="S1_ONLY_NO_WF_CHANGE","no new egg/combat authority")
ok(scene.spawn.ClassName=="SpawnLocation","physical start is an actual class")
ok(close(scene.spawn.Position.X,0) and close(scene.spawn.Position.Y,2),"start at hub")

local children=scene.folder._children
local byname={}
local partCount=0
local cloudCount=0
local glassRoof=0
for _,item in ipairs(children) do
    ok(byname[item.Name]==nil or (item.Name=="SEA_CASTLE_Tower" or
        item.Name=="SKY_CASTLE_Tower" or item.Name=="SEA_CASTLE_Crown" or item.Name=="SKY_CASTLE_Crown"),
        "only intentional duplicate castle tower/crown decorative part names")
    byname[item.Name]=item
    if item.ClassName=="Part" then
        partCount+=1
        ok(item.Anchored==true,"every part anchored")
        ok(item.CanTouch==false,"no hidden Touch event")
        ok(item.CanQuery==item.CanCollide,"walkable query matches collision")
        ok(item.Transparency>=0 and item.Transparency<=1,"transparent part bounded")
        if string.sub(item.Name,1,10)=="SKY_Cloud_" then cloudCount+=1 end
        if string.sub(item.Name,1,23)=="SEA_BUBBLE_B_GlassRoof_" then glassRoof+=1 end
    end
end
ok(partCount>=45 and partCount<=60,"bounded geometric part budget")
ok(cloudCount==18,"actual floating sky cloud models")
ok(glassRoof==5,"five sea glass roof details")
ok(byname.LAND_FreeHub~=nil,"grass home hub")
ok(byname.SEA_FreeDock~=nil,"wooden port")
ok(byname.SEA_CASTLE_Deck~=nil,"actual submerged castle")
ok(byname.SKY_CASTLE_Deck~=nil,"actual sky castle")
ok(byname.SEA_VisualWaterOnly~=nil,"transparent water sea")
ok(byname.SEA_VisualWaterOnly.CanCollide==false,"decorative sea cannot trap players")
ok(close(byname.SEA_VisualWaterOnly.Transparency,0.79),"sea visual is translucent")
ok(close(byname.SEA_CASTLE_Deck.Position.Y,-23),"sea castle is below hub")
ok(close(byname.SKY_CASTLE_Deck.Position.Y,48),"sky castle elevated")
ok(byname.LAND_FreeHub.CanCollide,"land solid")
ok(byname.SEA_FreeDock.CanCollide,"dock solid")
ok(byname.SEA_CASTLE_Deck.CanCollide,"sea castle deck solid")
ok(byname.SKY_CASTLE_Deck.CanCollide,"sky deck solid")
ok(byname.LAND_DestinationBeacon.CanCollide==false,"beacon only visual")

local function ramp(name,x0,y0,x1,y1,z)
    local item=byname[name]
    ok(item~=nil,name.." exists")
    ok(item.ClassName=="Part" and item.CanCollide and item.Anchored,name.." is physical")
    ok(item:GetAttribute("WF_WALKABLE")==true,name.." walkable metadata")
    ok(item.Size.Z>=13,name.." wide enough for route source")
    ok(math.abs((y1-y0)/(x1-x0))<0.32,name.." slope angle acceptable")
    local theta=item.CFrame.angle
    ok(theta~=nil,name.." has actual rotated CFrame")
    local half=item.Size.X*0.5
    local ex0=item.Position.X - half*math.cos(theta)
    local ey0=item.Position.Y - half*math.sin(theta)
    local ex1=item.Position.X + half*math.cos(theta)
    local ey1=item.Position.Y + half*math.sin(theta)
    ok(close(ex0,x0) and close(ey0,y0),name.." start connects exactly")
    ok(close(ex1,x1) and close(ey1,y1),name.." end connects exactly")
    ok(close(item.Position.Z,z),name.." lives on expected accessible lateral lane")
end
ramp("SEA_BRIDGE_FreePortWalk",-28,2,-108,2,-15)
ramp("SEA_BUBBLE_A_DryRamp",-108,2,-205,-22,-15)
ramp("SEA_BUBBLE_B_DryRamp",-4,2,-205,-22,30)
ramp("SKY_RAINBOW_A_Lower",20,2,95,25,-33)
ramp("SKY_RAINBOW_A_Upper",95,25,175,49,-33)
ramp("SKY_RAINBOW_B_Lower",20,2,95,25,33)
ramp("SKY_RAINBOW_B_Upper",95,25,175,49,33)
ok(close(byname.SEA_BRIDGE_FreePortWalk.Position.X,-68),"sea bridge spans LAND to dock")
ok(close(byname.SEA_BUBBLE_B_DryRamp.Position.Z,30),"independent green sea route")
ok(close(byname.SKY_RAINBOW_A_Upper.Position.Z,-33),"yellow sky route distinct")
ok(close(byname.SKY_RAINBOW_B_Upper.Position.Z,33),"purple sky route distinct")
ok(close(byname.SEA_BUBBLE_B_LastTurn.Position.X,-205) and byname.SEA_BUBBLE_B_LastTurn.CanCollide,"secret turn at castle landing")

-- Child signs: original source actually builds Part+BillboardGui+TextLabel.
local signNames={"SEA_PORT_Sign","SEA_SECRET_Sign","SEA_CASTLE_Sign",
    "SKY_FIRST_Sign","SKY_SECOND_Sign","SKY_CASTLE_Sign","LAND_Guidance"}
for _,name in ipairs(signNames) do
    local sign=byname[name]
    ok(sign~=nil and sign.CanCollide==false,name.." harmless cue post")
    local gui=sign:FindFirstChild("WFChildCue")
    ok(gui~=nil and gui.ClassName=="BillboardGui",name.." has actual Roblox UI source")
    local label=gui:FindFirstChild("TextLabel")
    -- In original source TextLabel's Name property is default TextLabel (mock Instance.new must emulate it).
    ok(label~=nil and label.ClassName=="TextLabel",name.." displays label")
    ok(type(label.Text)=="string" and #label.Text>8,name.." has readable text")
    ok(label.TextScaled==true,name.." mobile-scaled source")
end
local twoSign=byname.SEA_SECRET_Sign:FindFirstChild("WFChildCue"):FindFirstChild("TextLabel").Text
ok(string.find(twoSign,"みどり")~=nil,"green route visible")
local skySign=byname.SKY_SECOND_Sign:FindFirstChild("WFChildCue"):FindFirstChild("TextLabel").Text
ok(string.find(skySign,"むらさき")~=nil,"purple route visible")

local again,err=pcall(function() Scene.build(world) end)
ok(not again and string.find(tostring(err),"NO_DUPLICATE_WORLD")~=nil,
    "actual original scene source denies duplicate world")
local protected=Instance.new("Workspace")
local official=Instance.new("Folder")
official.Name="TRAP_RAIDERS_S1"
official.Parent=protected
local allowed,blocked=pcall(function() Scene.build(protected) end)
ok(not allowed and string.find(tostring(blocked),"NO_S1_MAP_OVERLAP")~=nil,
    "actual original source rejects official S1 map collision")
ok(protected:FindFirstChild("WF_G5_LandSeaSky")==nil,
    "collision abort creates no new world")
local notAWorkspace=Instance.new("Folder")
local validContext=pcall(function() Scene.build(notAWorkspace) end)
ok(not validContext,"rejects non-Workspace root")

print("WORLD_G5_ACTUAL_NATIVE_SCENE_PASS assertions="..tostring(count)..
    " parts="..tostring(partCount).." labels="..tostring(#signNames)..
    " routes=5")
'''

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output-dir",required=True)
    args=parser.parse_args()
    target=Path(args.output_dir)
    target.mkdir(parents=True,exist_ok=True)
    s=SCENE.read_text(encoding="utf-8")
    r=ROUTES.read_text(encoding="utf-8")
    redirect="local Routes = require(script.Parent.WorldLinkRoutes)"
    if s.count(redirect)!=1 or not s.rstrip().endswith("return Scene"):
        raise RuntimeError("Unexpected original Scene source. Fail closed.")
    if not r.startswith("--!strict\n") or not r.rstrip().endswith("return Routes"):
        raise RuntimeError("Unexpected original Routes source. Fail closed.")

    mutations={
        "positive":s,
        "BAD_ROUTES_NONCOLLIDABLE":s.replace('p.CanCollide=solid','p.CanCollide=false',1),
        "BAD_SEA_SECRET_DISCONNECTED":s.replace(
            'walkRamp(folder,"SEA_BUBBLE_B_DryRamp",-4,2,-205,-22,30,13,green)',
            'walkRamp(folder,"SEA_BUBBLE_B_DryRamp",-4,2,-105,-22,30,13,green)',1),
        "BAD_SKY_CASTLE_UNREACHABLE":s.replace(
            'walkRamp(folder,"SKY_RAINBOW_A_Upper",95,25,175,49,-33,15,yellow)',
            'walkRamp(folder,"SKY_RAINBOW_A_Upper",95,25,175,35,-33,15,yellow)',1),
        "BAD_CHILD_SECRET_SIGN":s.replace(
            '"🐠 ひみつの みち\\nみどりの さか"',
            '"🐠 ひみつの みち\\nみちが ない"',1),
        "BAD_NONEXCLUSIVE_WORLD":s.replace(
            'assert(world:FindFirstChild("WF_G5_LandSeaSky")==nil,"NO_DUPLICATE_WORLD")',
            'assert(true,"NO_DUPLICATE_WORLD")',1),
    }
    if len(set(mutations.values()))!=len(mutations):
        raise RuntimeError("Mutation targets invalid/missing, refuse fake tests")
    print("G5_NATIVE_ACTUAL_ORIGINAL_SCENE_BYTES",len(s.encode("utf-8")),
          "ROUTES",len(r.encode("utf-8")))
    for name,m in mutations.items():
        compiled=(
            MOCKS+"\nlocal Routes=(function()\n"
            +r.replace("--!strict\n","",1)+"\nend)()\n"
            +"local Scene=(function()\n"
            +m.replace("--!strict\n","",1).replace(redirect,"local Routes = Routes",1)
            +"\nend)()\n"+CASES
        )
        f=target/(name+".luau")
        f.write_text(compiled,encoding="utf-8")
        print("G5_NATIVE_REAL_SCENE_RUNNER_WRITTEN",name,f)

if __name__=="__main__":
    main()
