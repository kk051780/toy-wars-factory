"""Execute the EXACT FULL original Studio.server Luau, full original 4-realm
Scene, 4 moving creature Models, Book/HUD/Plan under native Luau.
Only external Roblox Instance/Players/RunService/events/Vector3 are doubles.
The test-only opt-in and module-import redirection are explicit, never committed
into the original source files. No Roblox Studio game is launched by this QA.
"""
from pathlib import Path
import argparse

ROOT=Path(__file__).resolve().parents[1]
WORLD=ROOT.parent/"P0D-WORLD-RARE-4REALMS-3D-20261112-01/src"
CREATURE=ROOT.parent/"P0D-WORLD-RARE-NEUTRAL-ENCOUNTERS-20261112-01/src"
BOOK=ROOT.parent/"P0D-RARE-DISCOVERY-BOOK-20261112-01/src"
FILES=[
 ("Catalog",WORLD/"RareRealmCatalog.luau","return Catalog"),
 ("Scene",WORLD/"RareRealmScene.luau","return Scene"),
 ("Policy",CREATURE/"RareEncounterPolicy.luau","return P"),
 ("Models",CREATURE/"RareEncounterModels.luau","return M"),
 ("Book",BOOK/"RareDiscoveryBook.luau","return Book"),
 ("HUD",BOOK/"RareDiscoveryHUD.luau","return HUD"),
 ("Plan",BOOK/"RareDiscoveryQAPlan.luau","return Plan")
]
SERVER=BOOK/"RareDiscoveryStudio.server.luau"

MOCKS=r'''
local NOW=1000
local REFERENCE_CLOCK=1000
local logs={}
local originalPrint=print
local function saveLog(...)
    local joined=""
    for _,x in ipairs({...}) do
        if #joined>0 then joined..=" " end
        joined..=tostring(x)
    end
    table.insert(logs,joined)
end
local function contains(fragment)
    for _,line in ipairs(logs) do
        if string.find(line,fragment,1,true) then return true end
    end
    return false
end
local function countLines(fragment)
    local n=0
    for _,line in ipairs(logs) do
        if string.find(line,fragment,1,true) then n+=1 end
    end
    return n
end
local function Event()
    local links={}
    return {
        Connect=function(self,fn)
            local state={callback=fn,active=true}
            table.insert(links,state)
            return {Disconnect=function(self)state.active=false end}
        end,
        Fire=function(self,...)
            local copy={}
            for _,v in ipairs(links) do table.insert(copy,v) end
            for _,v in ipairs(copy) do
                if v.active then v.callback(...) end
            end
        end
    }
end
local V={}
V.__add=function(a,b)return setmetatable({X=a.X+b.X,Y=a.Y+b.Y,Z=a.Z+b.Z},V) end
V.__sub=function(a,b)return setmetatable({X=a.X-b.X,Y=a.Y-b.Y,Z=a.Z-b.Z},V) end
V.__mul=function(a,b)
    if type(a)=="number" then return setmetatable({X=a*b.X,Y=a*b.Y,Z=a*b.Z},V) end
    return setmetatable({X=a.X*b,Y=a.Y*b,Z=a.Z*b},V)
end
V.__index=function(v,k)
    if k=="Magnitude" then return math.sqrt(v.X*v.X+v.Y*v.Y+v.Z*v.Z) end
end
local function vec(x,y,z)return setmetatable({X=x,Y=y,Z=z},V) end
Vector3={new=vec}
Vector2={new=function(x,y)return {X=x,Y=y} end}
Color3={fromRGB=function(r,g,b)return {R=r,G=g,B=b} end}
CFrame={new=function(pos)return {Position=pos} end,
        lookAt=function(mid,finish)return {Position=mid,Target=finish} end}
UDim={new=function(a,b)return {Scale=a,Offset=b} end}
UDim2={fromOffset=function(x,y)return {X=x,Y=y} end,
       fromScale=function(x,y)return {X=x,Y=y} end,
       new=function(a,b,c,d)return {xScale=a,xOffset=b,yScale=c,yOffset=d} end}
Enum={
 Material={SmoothPlastic="SmoothPlastic",Neon="Neon",Grass="Grass"},
 PartType={Ball="Ball"},Font={GothamBold="GothamBold",Gotham="Gotham"},
 TextXAlignment={Left="Left"},TextYAlignment={Center="Center"}
}
local function InstanceObj(class)
    local data={ClassName=class,Name=class,_children={},attrs={}}
    local obj
    obj=setmetatable({},{
        __index=function(_,key)
            if key=="IsA" then
                return function(self,other)
                    if other=="Instance" then return true end
                    if other=="BasePart" then
                        return class=="Part" or class=="SpawnLocation"
                    end
                    return class==other
                end
            elseif key=="FindFirstChild" then
                return function(self,name)
                    for _,v in ipairs(data._children) do
                        if v.Name==name then return v end
                    end
                    return nil
                end
            elseif key=="FindFirstChildOfClass" then
                return function(self,other)
                    for _,v in ipairs(data._children) do
                        if v.ClassName==other then return v end
                    end
                    return nil
                end
            elseif key=="WaitForChild" then
                return function(self,name)
                    return self:FindFirstChild(name)
                end
            elseif key=="IsDescendantOf" then
                return function(self,other)
                    local current=data.Parent
                    while current do
                        if current==other then return true end
                        current=current.Parent
                    end
                    return false
                end
            elseif key=="GetChildren" then
                return function(self)return data._children end
            elseif key=="SetAttribute" then
                return function(self,name,value)data.attrs[name]=value end
            elseif key=="GetAttribute" then
                return function(self,name)return data.attrs[name] end
            elseif key=="PivotTo" then
                return function(self,cf)
                    assert(class=="Model","only Model pivots")
                    local primary=self.PrimaryPart
                    assert(primary,"missing model PrimaryPart")
                    local shift=cf.Position-primary.Position
                    for _,v in ipairs(self:GetChildren()) do
                        if v:IsA("BasePart") then v.Position=v.Position+shift end
                    end
                end
            elseif key=="Destroy" then
                return function(self)
                    self.Parent=nil
                    data.Destroyed=true
                end
            else
                return data[key]
            end
        end,
        __newindex=function(_,key,value)
            if key=="Parent" then
                if data.Parent then
                    local kids=data.Parent._children
                    for i,v in ipairs(kids) do
                        if v==obj then table.remove(kids,i);break end
                    end
                end
                data.Parent=value
                if value then table.insert(value._children,obj) end
            else data[key]=value end
        end
    })
    if class=="ProximityPrompt" then obj.Triggered=Event() end
    if class=="Player" then obj.CharacterRemoving=Event() end
    return obj
end
Instance={new=InstanceObj}
task={spawn=function(fn)fn() end}
local run={
    Heartbeat=Event(),
    IsStudio=function(self)return true end,
    IsServer=function(self)return true end
}
local players=Instance.new("Players")
players.PlayerAdded=Event()
players.PlayerRemoving=Event()
players.GetPlayers=function(self)
    local out={}
    for _,c in ipairs(self:GetChildren()) do
        if c.ClassName=="Player" then table.insert(out,c) end
    end
    return out
end
local closeHandler=nil
game={
    GetService=function(self,key)
        if key=="RunService" then return run end
        if key=="Players" then return players end
        error("unexpected game service request: "..key)
    end,
    BindToClose=function(self,fn) closeHandler=fn end
}
workspace=Instance.new("Workspace")
local function newPlayer()
    local player=Instance.new("Player")
    local ui=Instance.new("PlayerGui")
    ui.Name="PlayerGui";ui.Parent=player
    local character=Instance.new("Model")
    character.Name="Character";character.Parent=workspace
    local human=Instance.new("Humanoid")
    human.Name="Humanoid";human.Health=100;human.Parent=character
    local root=Instance.new("Part")
    root.Name="HumanoidRootPart"
    root.Position=Vector3.new(0,3,0)
    root.Anchored=false
    root.Parent=character
    player.Character=character
    player.Parent=players
    return player,root,human,ui
end
local userA,rootA,humanA,uiA=newPlayer()
local userB,rootB,humanB,uiB=newPlayer()
local function tick(seconds)
    assert(seconds>=0 and seconds<=125,"invalid simulation time")
    NOW=REFERENCE_CLOCK+seconds
    run.Heartbeat:Fire(0.22)
end
local function notebookTitle(player)
    local gui=player:FindFirstChildOfClass("PlayerGui")
    local screen=gui and gui:FindFirstChild("RareDiscoverySessionBook")
    local panel=screen and screen:FindFirstChild("NotebookPanel")
    local title=panel and panel:FindFirstChild("Title")
    return title and title.Text or "MISSING"
end
local function nowEncounter(id)
    local scene=workspace:FindFirstChild("P0D_FourRareRealms")
    local layer=scene and scene:FindFirstChild("RARE_DISCOVERY_BENCH_ONLY")
    local model=layer and layer:FindFirstChild("RARE_NEUTRAL_"..id)
    local body=model and model.PrimaryPart
    local prompt=body and body:FindFirstChild("RareDiscoveryPrompt")
    return model,body,prompt,layer
end
'''
TESTS=r'''
local assertCount=0
local function ok(cond,description)
    assertCount+=1
    assert(cond,"RARE_BOOK_FULL_SERVER_NATIVE_FAIL assertion="..tostring(assertCount)..
        " "..description)
end
ok(contains("event=BOOT"),"actual Studio source was invoked under isolated test opt-in")
ok(contains("not_real_rarity=true"),"test only encounter schedule")
ok(not contains("event=TWO_CLIENT_INDEPENDENT_BOOK_4_OF_4"),"no false initial full success")
ok(notebookTitle(userA)=="発見ずかん 0/4","player A actual server source GUI")
ok(notebookTitle(userB)=="発見ずかん 0/4","player B actual server source GUI")
local beforeScene=workspace:FindFirstChild("P0D_FourRareRealms")
ok(beforeScene~=nil and beforeScene:GetAttribute("RealStudioQA")=="NOT_TESTED",
    "actual original scene built, but does not fake real Roblox Studio QA")
local schedule={"SPACE","CELESTIAL","EMBER","ECLIPSE"}
local lastPrompt=nil
for i,id in ipairs(schedule) do
    local start=(i-1)*26
    tick(start+0.2)
    local model,body,prompt,layer=nowEncounter(id)
    ok(model~=nil and body~=nil and prompt~=nil,
       "original full server spawned the correct original moving model")
    ok(model.ClassName=="Model" and model:GetAttribute("NoDropsNoCurrencyNoDamage")==true,
       "actual model factory has no combat/rewards")
    ok(prompt.Enabled==false,"prompt must show visual cue before interaction")
    local firstTitle=notebookTitle(userA)
    local secondTitle=notebookTitle(userB)
    rootA.Position=body.Position
    prompt.Triggered:Fire(userA)
    ok(notebookTitle(userA)==firstTitle,"early prompt even from valid nearby character rejected")
    rootA.Position=Vector3.new(0,3,0)
    tick(start+2.7)
    ok(prompt.Enabled==true,"2sec cue elapsed, actual prompt enabled")
    prompt.Triggered:Fire(userA)
    ok(notebookTitle(userA)==firstTitle,"faraway prompt manipulation rejected")
    rootA.Position=body.Position
    rootB.Position=body.Position
    tick(start+5.1)
    humanA.Health=0
    prompt.Triggered:Fire(userA)
    ok(notebookTitle(userA)==firstTitle,"dead character cannot claim discovery")
    humanA.Health=100
    rootA.Anchored=true
    prompt.Triggered:Fire(userA)
    ok(notebookTitle(userA)==firstTitle,"anchored character cannot claim discovery")
    rootA.Anchored=false
    prompt.Triggered:Fire(userA)
    ok(notebookTitle(userA)=="発見ずかん "..tostring(i).."/4",
       "actual original server prompt accepted A at realm "..id)
    prompt.Triggered:Fire(userA)
    ok(notebookTitle(userA)=="発見ずかん "..tostring(i).."/4",
       "same client repeating creature does not inflate count")
    if i==4 then
        ok(notebookTitle(userB)=="発見ずかん 3/4",
            "cannot log 2client final pass just from player A")
        ok(not contains("event=TWO_CLIENT_INDEPENDENT_BOOK_4_OF_4"),
            "server full PASS must not be logged until both done")
    end
    prompt.Triggered:Fire(userB)
    ok(notebookTitle(userB)=="発見ずかん "..tostring(i).."/4",
       "actual original server prompt independently accepted B at realm "..id)
    ok(countLines("event=TWO_REAL_CLIENT_SAME_CREATURE")>=i,
       "server recorded two DISTINCT real service Players for this event")
    local previous=body.Position
    tick(start+7)
    ok((body.Position-previous).Magnitude>0.4,
       "actual original Models.update makes displayed creature body really move")
    tick(start+23.2)
    ok(nowEncounter(id)==nil,"expired/hidden creature is not interactable")
    prompt.Triggered:Fire(userA)
    ok(notebookTitle(userA)=="発見ずかん "..tostring(i).."/4",
       "disconnected old prompt may not grant stale discovery")
end
ok(notebookTitle(userA)=="発見ずかん 4/4","A full book")
ok(notebookTitle(userB)=="発見ずかん 4/4","B independent full book")
ok(contains("event=TWO_CLIENT_INDEPENDENT_BOOK_4_OF_4"),
    "full original Studio server code can print intended actual two-client gate")
ok(countLines("event=TWO_CLIENT_INDEPENDENT_BOOK_4_OF_4")==1,
    "two-client 4/4 gate emitted exactly once")
ok(countLines("event=NEW_DISCOVERY")==8,"eight actual server-proximity unique events")
local truthfulDiscoveryReceipts=0
for _,entry in ipairs(logs) do
    if string.find(entry,"event=NEW_DISCOVERY",1,true) and
       string.find(entry,"no_inventory=true",1,true) then
        truthfulDiscoveryReceipts+=1
    end
end
ok(truthfulDiscoveryReceipts==8,
    "all eight actual discoveries must state no real inventory or currency")
ok(not contains("reward_coins="),
    "never claim unearned coins, gameplay rewards or monetization from a scene-only preview")
ok(countLines("event=CREATURE_VISIBLE")==4,"exactly four original model spawn events")
ok(countLines("event=CREATURE_EXPIRED")==4,"exactly four original model cleanup events")
tick(104.5)
ok(nowEncounter("SPACE")==nil and nowEncounter("CELESTIAL")==nil,
   "deterministic only four slots, does not respawn forever")
local beforeJoin=notebookTitle(userB)
players.PlayerRemoving:Fire(userA)
userA.Parent=nil
ok(notebookTitle(userB)==beforeJoin,"departure of A does not alter surviving B")
ok(notebookTitle(userA)=="発見ずかん 4/4",
    "removed client GUI visually stale but not an authority; data must be discarded internally")
local newlyJoined,rootNew,humanNew,uiNew=newPlayer()
players.PlayerAdded:Fire(newlyJoined)
ok(notebookTitle(newlyJoined)=="発見ずかん 0/4",
    "disconnected/new user never inherits prior persisted account book")
local char=userB.Character
userB.CharacterRemoving:Fire(char)
ok(notebookTitle(userB)=="発見ずかん 4/4",
    "surviving user's session book unchanged on respawn")
ok(closeHandler~=nil,"source registered true BindToClose cleanup")
closeHandler()
ok(workspace:FindFirstChild("P0D_FourRareRealms")==nil,
    "actual original server test scene torn down on close")
ok(contains("event=STOP"),"actual server emitted truthful stop evidence")
originalPrint("RARE_BOOK_FULL_SERVER_NATIVE_PASS assertions="..tostring(assertCount)..
    " original_scene=true original_models=4 clients=2 discovered=8 original_server=true")
'''
def read_exact(path,ending):
    src=path.read_text(encoding="utf-8")
    if not src.startswith("--!strict\n") or not src.rstrip().endswith(ending):
        raise RuntimeError("unexpected source body "+str(path))
    return src.removeprefix("--!strict\n")
def wrap_source(name,source):
    redirect={
      "Scene":{"local Catalog = require(script.Parent.RareRealmCatalog)":"local Catalog = Catalog"},
      "Models":{"local Policy = require(script.Parent.RareEncounterPolicy)":"local Policy = Policy"},
      "HUD":{"local Book = require(script.Parent.RareDiscoveryBook)":"local Book = Book"},
    }
    for original,new in redirect.get(name,{}).items():
        if source.count(original)!=1:raise RuntimeError("unexpected module require "+name)
        source=source.replace(original,new,1)
    return "local "+name+"=(function()\n"+source+"\nend)()\n"

def build(server):
    required=[
       ("Scene","local Scene=require(script.Parent.RareRealmScene)"),
       ("Models","local Models=require(script.Parent.RareEncounterModels)"),
       ("Policy","local Policy=require(script.Parent.RareEncounterPolicy)"),
       ("Book","local Book=require(script.Parent.RareDiscoveryBook)"),
       ("HUD","local HUD=require(script.Parent.RareDiscoveryHUD)"),
       ("Plan","local Plan=require(script.Parent.RareDiscoveryQAPlan)"),
    ]
    source=server
    optin="local ENABLE_RARE_DISCOVERY_STUDIO_BOOK = false"
    if source.count(optin)!=1:raise RuntimeError("not exact default-disabled source")
    source=source.replace(optin,"local ENABLE_RARE_DISCOVERY_STUDIO_BOOK = true",1)
    for name,token in required:
        if source.count(token)!=1:raise RuntimeError("original server require changed "+name)
        source=source.replace(token,"local "+name+"="+name,1)
    pieces=[MOCKS]
    for name,path,ending in FILES:
        pieces.append(wrap_source(name,read_exact(path,ending)))
    pieces.append("local function runActualUnmodifiedServerSource()\n")
    pieces.append("local os={clock=function()return NOW end}\n")
    pieces.append("local print=saveLog\n")
    pieces.append(source.removeprefix("--!strict\n"))
    pieces.append("\nend\nrunActualUnmodifiedServerSource()\n")
    pieces.append(TESTS)
    return "\n".join(pieces)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",required=True)
    args=p.parse_args()
    output=Path(args.output);output.mkdir(parents=True,exist_ok=True)
    original=SERVER.read_text(encoding="utf-8")
    if not original.startswith("--!strict\n"):
        raise RuntimeError("missing original strict server")
    cases={
      "positive":original,
      "BAD_SERVER_ACCEPTS_FAR":original.replace(
          "return (root.Position-body.Position).Magnitude<=Policy.MIN_INTERACTION_DISTANCE",
          "return true",1),
      "BAD_SERVER_ACCEPTS_DEAD":original.replace(
          "humanoid.Health<=0","false",1),
      "BAD_SERVER_ACCEPTS_ANCHORED":original.replace(
          "root.Anchored then return false","false then return false",1),
      "BAD_SERVER_USES_FIRST_PLAYER_UI":original.replace(
          "HUD.update(player,nextBook)","HUD.update(Players:GetPlayers()[1],nextBook)",1),
      "BAD_SERVER_PREMATURE_2CLIENT_PASS":original.replace(
          "if count>=2 then","if count>=1 then",1),
      "BAD_SERVER_EXTRA_REWARD_LOG":original.replace(
          'no_inventory=true")','reward_coins=999")',1),
    }
    if len(set(cases.values()))!=len(cases):raise RuntimeError("no real mutant source changed")
    for key,source in cases.items():
        path=output/(key+".luau")
        path.write_text(build(source),encoding="utf-8")
        print("P0D_ORIGINAL_FULL_SERVER_NATIVE_CASE",key,path)
if __name__=="__main__":
    main()
