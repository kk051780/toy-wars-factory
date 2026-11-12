"""Execute EXACT original four-realm Catalog, Cycle and Scene.build code in native Luau.
Only Roblox external Instance/Vector3/Enum/CFrame service objects are test doubles.
"""
from pathlib import Path
import argparse
ROOT=Path(__file__).resolve().parents[1]
SOURCE={k:(ROOT/"src"/v).read_text(encoding="utf-8") for k,v in {
 "CATALOG":"RareRealmCatalog.luau",
 "CYCLE":"RareRealmCycle.luau",
 "SCENE":"RareRealmScene.luau"}.items()}
MOCKS=r'''
local VM={}
VM.__add=function(a,b) return setmetatable({X=a.X+b.X,Y=a.Y+b.Y,Z=a.Z+b.Z},VM) end
VM.__sub=function(a,b) return setmetatable({X=a.X-b.X,Y=a.Y-b.Y,Z=a.Z-b.Z},VM) end
VM.__mul=function(a,b)
    if type(a)=="number" then return setmetatable({X=a*b.X,Y=a*b.Y,Z=a*b.Z},VM) end
    return setmetatable({X=a.X*b,Y=a.Y*b,Z=a.Z*b},VM)
end
VM.__index=function(v,k)
    if k=="Magnitude" then return math.sqrt(v.X*v.X+v.Y*v.Y+v.Z*v.Z) end
end
local function vec(x,y,z) return setmetatable({X=x,Y=y,Z=z},VM) end
Vector3={new=vec}
Color3={fromRGB=function(r,g,b) return {R=r,G=g,B=b} end}
Enum={Material={Grass="Grass",SmoothPlastic="SmoothPlastic",Neon="Neon"},
    PartType={Ball="Ball"},Font={GothamBold="GothamBold"}}
CFrame={lookAt=function(mid,target) return {Position=mid,Target=target} end}
UDim2={fromOffset=function(x,y)return {X=x,Y=y} end,
       fromScale=function(x,y)return {X=x,Y=y} end}
local function makeInstance(class)
    local d={ClassName=class,Name=class,children={},attrs={}}
    local obj
    obj=setmetatable({},{
        __index=function(_,key)
            if key=="IsA" then return function(self,k) return d.ClassName==k end end
            if key=="FindFirstChild" then
                return function(self,name)
                    for _,v in ipairs(d.children) do if v.Name==name then return v end end
                    return nil
                end
            end
            if key=="SetAttribute" then return function(self,k,v)d.attrs[k]=v end end
            if key=="GetAttribute" then return function(self,k)return d.attrs[k] end end
            if key=="Destroy" then return function(self)self.Parent=nil end end
            return d[key]
        end,
        __newindex=function(_,key,value)
            if key=="Parent" then
                if d.Parent then
                    for i,v in ipairs(d.Parent.children) do
                        if v==obj then table.remove(d.Parent.children,i);break end
                    end
                end
                d.Parent=value
                if value then table.insert(value.children,obj) end
            else d[key]=value end
        end
    })
    return obj
end
Instance={new=makeInstance}
'''
TESTS=r'''
local assertions=0
local function ok(v,msg)
    assertions+=1
    assert(v,"RARE4_NATIVE_SCENE_FAIL #"..tostring(assertions).." "..msg)
end
local function near(a,b)
    return math.abs(a-b)<0.08
end
local valid,reason=Catalog.validate()
ok(valid,"exact original source catalog valid "..tostring(reason))
local cycleOk,cycleReason=Cycle.validate()
ok(cycleOk,"eclipse color-only cycle "..tostring(cycleReason))
ok(Cycle.phase(0)=="SUN","phase sun")
ok(Cycle.phase(29.99)=="SUN","phase sun stays")
ok(Cycle.phase(30)=="MOON","phase moon")
ok(Cycle.phase(59.99)=="MOON","phase moon stays")
ok(Cycle.phase(60)=="SUN","phase resets")
ok(Cycle.phase(-1)=="SUN","invalid negative safe")
ok(Cycle.phase(0/0)=="SUN","invalid NaN safe")
ok(#Catalog.ORDER==4 and #Catalog.ALL_ROUTES==8,"four realms and eight roads")
local world=Instance.new("Workspace")
local scene=Scene.build(world)
ok(scene.folder.Parent==world and scene.folder.Name=="P0D_FourRareRealms","actual scene created")
ok(scene.spawn.ClassName=="SpawnLocation" and scene.spawn.Neutral==true,"free player spawn")
ok(scene.folder:GetAttribute("RareNPCSpawnStatus")=="NO_AI_OR_DROP_ONLY_SCULPTURE",
    "no imaginary rare NPCs or drops")
ok(scene.folder:GetAttribute("RealStudioQA")=="NOT_TESTED","honest real QA state")
ok(scene.totalParts<=Catalog.MAX_SCENE_PARTS and scene.totalParts>=100,
    "bounded original art parts")
ok(scene.solidParts>=24 and scene.solidParts<=90,"enough walkable structures")
local children=scene.folder.children
local byname={}
local count=0
for _,item in ipairs(children) do
    if item.ClassName=="Part" then
        count+=1
        ok(item.Anchored==true,"every generated part anchored")
        ok(item.CanTouch==false,"no unintended touch script")
        ok(item.CanQuery==item.CanCollide,"physics query matches physical solidity")
        ok(item.Transparency>=0 and item.Transparency<=1,"visual transparency bounded")
        ok(item.Size.X>0 and item.Size.Y>0 and item.Size.Z>0,"no zero-size part")
        ok(byname[item.Name]==nil,"all part names unique for dependable source audits")
    end
    byname[item.Name]=item
end
ok(count==scene.totalParts,"actual total part count exact")
ok(scene.folder:GetAttribute("ActualPartCount")==count,"source count attribute actual")

local expected={
  SPACE={first=vec(50,2,-22),last=vec(186,2,-22),
      secondFirst=vec(50,2,22),secondLast=vec(186,2,22),center=vec(240,0,0)},
  EMBER={first=vec(-50,2,-22),last=vec(-186,2,-22),
      secondFirst=vec(-50,2,22),secondLast=vec(-186,2,22),center=vec(-240,0,0)},
  CELESTIAL={first=vec(-22,2,50),last=vec(-22,32,186),
      secondFirst=vec(22,2,50),secondLast=vec(22,32,186),center=vec(0,30,240)},
  ECLIPSE={first=vec(-22,2,-50),last=vec(-22,2,-186),
      secondFirst=vec(22,2,-50),secondLast=vec(22,2,-186),center=vec(0,0,-240)},
}
local sculptures=0
local signs=0
for _,id in ipairs(Catalog.ORDER) do
    local data=Catalog.WORLDS[id]
    local e=expected[id]
    ok(data~=nil and e~=nil,"four unique original realms")
    local island=scene.islands[id]
    ok(island==byname[id.."_FREE_REALM_ISLAND"],"actual world island platform")
    ok(island.CanCollide==true and island.Anchored==true,"free island walkable")
    ok(island:GetAttribute("NeverPaidAccess")==true,"no real-life payment gates")
    ok(near(island.Position.X,e.center.X) and near(island.Position.Y,e.center.Y)
       and near(island.Position.Z,e.center.Z),"world placed original distant layout")
    local deck=byname[id.."_CASTLE_DECK"]
    ok(deck~=nil and deck.CanCollide==true,"original castle deck physically walkable")
    ok(byname[id.."_CASTLE_BEACON"].CanCollide==false,"castle visual no collider")
    ok(byname[id.."_RARE_SCULPTURE_BODY"]~=nil,"unique rare neutral silhouette exists")
    ok(byname[id.."_RARE_SCULPTURE_HEAD"]~=nil,"original neutral sculpture head")
    ok(byname[id.."_RARE_SCULPTURE_BODY"].CanCollide==false,
        "rare NPC is noncombat decoration only")
    ok(byname[id.."_RARE_ONLY_SCULPTURE_NOTE"]~=nil,"explicitly marks rare sculpture not NPC")
    ok(byname[id.."_WORLD_NAME"]~=nil,"kids recognize world")
    ok(byname[id.."_TACTIC_GUIDE"]~=nil,"tactic and two routes are visible")
    sculptures+=1
    local roads=scene.roads[id]
    ok(#roads==2,"two combat routes for every rare field")
    local start={e.first,e.secondFirst}
    local finish={e.last,e.secondLast}
    for i,p in ipairs(roads) do
        ok(p.Anchored and p.CanCollide,"free walking physical road")
        ok(p:GetAttribute("FreeToAllJobs")==true,"all classes free")
        ok(p:GetAttribute("BackAndForth")==true,"return trip is allowed")
        ok(p.CFrame~=nil and p.CFrame.Position~=nil,"original rotated CFrame")
        ok(near(p.CFrame.Target.X,finish[i].X)
            and near(p.CFrame.Target.Y,finish[i].Y)
            and near(p.CFrame.Target.Z,finish[i].Z),"road ends at original island")
        local reconstructedStart=p.CFrame.Position*2-p.CFrame.Target
        ok(near(reconstructedStart.X,start[i].X)
            and near(reconstructedStart.Y,start[i].Y)
            and near(reconstructedStart.Z,start[i].Z),"road begins at green hub")
        ok(p.Size.X>=16 and p.Size.Z>=120,"road big enough for child")
    end
end
ok(sculptures==4,"one different visual rare creature per world")
ok(scene.eclipsePanels[1].CanCollide==false and scene.eclipsePanels[2].CanCollide==false,
    "eclipse visual cannot ever trap")
ok(scene.eclipsePanels[1]:GetAttribute("ColorCycleAffectsCollision")==false,
    "sun cycle does not affect physics")
ok(scene.eclipsePanels[2]:GetAttribute("ColorCycleAffectsCollision")==false,
    "moon cycle does not affect physics")
ok(byname.SPACE_WF13_FUTURE_ZERO_G_VISUAL_ONLY~=nil,
    "cosmic future local-g bubble only")
ok(byname.SPACE_WF13_FUTURE_ZERO_G_VISUAL_ONLY:GetAttribute("ActualGravityForce")
   =="NOT_INSTALLED_REQUIRE_WF13_SEPARATE_QA","gravity not falsely enabled")
ok(byname.EMBER_GEAR_RELIC_DECORATIVE.CanCollide==false,"magma safe visual")
ok(byname.CELESTIAL_PRISM_CLOUD_BELL_VISUAL.CanCollide==false,"sky bell safe visual")
ok(byname.FREE_4WORLD_HUB.CanCollide==true,"land hub anchored ground")
local guide=byname.HUB_CHILD_GUIDE:FindFirstChild("RareWorldChildGuide")
ok(guide~=nil and guide.ClassName=="BillboardGui","actual child-readable BillboardGui")
local label=guide:FindFirstChild("ChildReadableLabel")
ok(label~=nil and type(label.Text)=="string" and #label.Text>10,"actual Japanese cue")
local duplicate,why=pcall(function() Scene.build(world) end)
ok(not duplicate and string.find(tostring(why),"REALM_DUPLICATE_DENIED")~=nil,
    "reusing same world forbidden")
local official=Instance.new("Workspace")
local tagged=Instance.new("Folder")
tagged.Name="TRAP_RAIDERS_S1";tagged.Parent=official
local allowed,problem=pcall(function() Scene.build(official) end)
ok(not allowed and string.find(tostring(problem),"REALM_NEVER_OVERLAP_OFFICIAL_S1")~=nil,
    "refuses protected real game world")
ok(official:FindFirstChild("P0D_FourRareRealms")==nil,
    "no source affects official world after rejected build")
local badRoot=Instance.new("Folder")
local good=pcall(function() Scene.build(badRoot) end)
ok(not good,"reject nonworkspace target")
print("RARE4_REAL_ORIGINAL_SCENE_NATIVE_PASS assertions="..tostring(assertions)..
    " parts="..tostring(count).." worlds=4 free_paths=8 rare_sculptures=4")
'''
def strip(s):
    if not s.startswith("--!strict\n") or not s.rstrip().startswith("return ") and not s.rstrip().endswith(("return Catalog","return Scene","return Cycle")):
        raise ValueError("original strict Luau required")
    return s.replace("--!strict\n","",1)
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--dir",required=True)
    a=ap.parse_args()
    d=Path(a.dir);d.mkdir(parents=True,exist_ok=True)
    s=SOURCE["SCENE"]
    redirect="local Catalog = require(script.Parent.RareRealmCatalog)"
    if s.count(redirect)!=1: raise ValueError("exact original require not found")
    variants={
       "positive":s,
       "BAD_PAID_OR_JOB_GATE":s.replace('item:SetAttribute("FreeToAllJobs",true)',
           'item:SetAttribute("FreeToAllJobs",false)',1),
       "BAD_NONSOLID_WALKWAY":s.replace("item.CanCollide=solid","item.CanCollide=false",1),
       "BAD_SKY_ROAD_MISALIGNED":s.replace(
           'Vector3.new(-22,data.center.y+2,z-54)',
           'Vector3.new(-22,data.center.y+2,z-66)',1),
       "BAD_RARE_SCULPTURE_MISSING":s.replace(
           'sculpture(id,base,color,rgb(247,226,156))',
           'local _removedAnimal = true',1),
       "BAD_FALSE_GRAVITY_CLAIM":s.replace(
           '"NOT_INSTALLED_REQUIRE_WF13_SEPARATE_QA"',
           '"ACTIVE_GRAVITY"',1),
       "BAD_ECLIPSE_PHYSICS_RISK":s.replace(
           's:SetAttribute("ColorCycleAffectsCollision",false)',
           's:SetAttribute("ColorCycleAffectsCollision",true)',1),
    }
    if len(set(variants.values()))!=len(variants):
        raise ValueError("real source mutation did not change")
    for name,scene in variants.items():
        result=(MOCKS+"\nlocal Catalog=(function()\n"+strip(SOURCE["CATALOG"])+
            "\nend)()\nlocal Cycle=(function()\n"+strip(SOURCE["CYCLE"])+
            "\nend)()\nlocal Scene=(function()\n"+
            strip(scene).replace(redirect,"local Catalog = Catalog",1)+
            "\nend)()\n"+TESTS)
        f=d/(name+".luau")
        f.write_text(result,encoding="utf-8")
        print("RARE4_ORIGINAL_LUAU_TEST_RUNNER_CREATED",name,f)
if __name__=="__main__":
    main()
