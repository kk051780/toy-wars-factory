local function empty() end
local vector={}
vector.__index=function(v,k)
 if k=="Magnitude" then return math.sqrt(v.X*v.X+v.Y*v.Y+v.Z*v.Z) end
end
local Vector3={new=function(x,y,z) return setmetatable({X=x,Y=y,Z=z},vector) end}
function vector.__add(a,b) return Vector3.new(a.X+b.X,a.Y+b.Y,a.Z+b.Z) end
function vector.__sub(a,b) return Vector3.new(a.X-b.X,a.Y-b.Y,a.Z-b.Z) end
function vector.__mul(a,b) return Vector3.new(a.X*b,a.Y*b,a.Z*b) end
local Color3={fromRGB=function(...) return {...} end}
local UDim2={fromScale=function(...) return {...} end}
local atk={Position=Vector3.new(0,3,0),CFrame={LookVector=Vector3.new(1,0,0)}}
local targetRoot={Position=Vector3.new(20,3,0)}
local attrs={EGGRUMBLE_QueuedMode="TEAM",EGGRUMBLE_Role="MAGE",EGGRUMBLE_Attribute="WATER"}
local attacker={UserId=1,GetAttribute=function(_,key) if key=="EGGRUMBLE_Role" then return "WARRIOR" end end}
local player={UserId=2,GetAttribute=function(_,key) return attrs[key] end}
local Players={GetPlayers=function() return {attacker,player} end}
local game={GetService=function(_,service) assert(service=="Players"); return Players end}
local phase="LOBBY"
local permittedArena="TEAM_Arena"
local arena={IsA=function(_,class) return class=="Folder" end,
 GetAttribute=function(_,key) assert(key=="EGGRUMBLE_MatchPhase");return phase end}
local world={FindFirstChild=function(_,key) if key==permittedArena then return arena end end}
local workspace={FindFirstChild=function(_,key) assert(key=="EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW");return world end}
local mounted=false
local realmPanel={Visible=true,IsA=function(_,type) return type=="Frame" end}
local realmGui={Enabled=true,IsA=function(_,type) return type=="ScreenGui" end,
 FindFirstChild=function(_,name) if name=="Controls" then return realmPanel end end}
local playerGui={FindFirstChild=function(_,name)
 if name=="GQ8_RealmBattleControls" and mounted then return realmGui end
end}
local mapSnapshot
local frame
local RunService={RenderStepped={Connect=function(_,callback) frame=callback end}}
local hp,buffs,fill,skillUse={},{},{},{}
local actions={MUSOU={},INVUL={},ATTACK={},ITEM={},DODGE={},SKILL={}}
local gui={Enabled=false,FindFirstChild=function() return nil end}
local mapBox,drawer,growthFooter={},{Visible=false},{}
local selectedSlot,mapExpanded,growthRoles="A",false,{MAGE=true}
local musouTool,counterTool,slotTool,dodgeTool=empty,empty,empty,empty
local basicTool=function() return true end
local closeDrawer,updateLayout=empty,empty
local function toolWith() return {} end
local function avatar(maxHP)
 local hum={Health=maxHP,MaxHealth=maxHP,GetAttribute=function() return nil end}
 function hum:TakeDamage(amount) self.Health=math.max(0,self.Health-amount) end
 local model={FindFirstChildOfClass=function(_,class) if class=="Humanoid" then return hum end end}
 return model,hum
end
local function characterOf(p)
 if p==player and p.Character then
  return p.Character,targetRoot,p.Character:FindFirstChildOfClass("Humanoid")
 end
end
local function currentHumanMember() return true end
local function humanCombatTargetable() return true end
local function lineClear() return true end
local InvulRuntime={filterDamage=function(_,amount) return amount end}
local ImpactFeedback={hit=empty}
__SELECTED_FUNCTIONS__

local function observe(label,expected,visible)
 frame(.16)
 assert(hp.Text==expected,label..": "..tostring(hp.Text).." expected "..expected)
 assert(gui.Enabled==visible,label.." visibility")
end
local h
player.Character,h=avatar(HealthPolicy.initialMaxHP("MAGE"))
observe("lobby", "HP 195/195",false)
phase="COUNTDOWN"
mapSnapshot={mode="TEAM"}
observe("configured countdown", "HP 195/195",false)
phase="ACTIVE"
mapSnapshot=nil
observe("await map", "HP 195/195",false)
mapSnapshot={mode="TEAM",statuses={}}
observe("initial deployed", "HP 195/195",true)

local combatSession={mode="TEAM",rules={phase="ACTIVE",castles={["1"]={alive=true,team="RED"},["2"]={alive=true,team="BLUE"}}}}
local a=Balance.skill("WARRIOR","A")
local b=Balance.skill("WARRIOR","B")
local _,_,basic=Mobility.authorize({},"WARRIOR","BASIC",20,{serverVerified=true,roleVerified=true,ownsTool=true,
 phase="ACTIVE",mode="TEAM",alive=true,castleAlive=true,matchEpoch="actual-hit-hud-mock"})
-- The authored pure policy exposes BASIC stats via an authorized real context.
assert(a.damage==44 and b.damage==26)
local function hit(spec,reach)
 local hits=hitHumanHeroes(combatSession,attacker,atk,{},rootAdvance(atk,reach or spec.reach),
  spec.radius,spec.damage,spec.shape)
 assert(hits==1)
end
for _=1,3 do hit(a) end
observe("far A actual damage", "HP 63/195",true)
targetRoot.Position=Vector3.new(10,3,0)
hit(b,b.reach-6)
observe("close lance actual damage", "HP 30/195",true)
local spec=assert(basic,"BASIC_SPEC")
assert(spec.damage==12)
for _=1,2 do hit(spec) end
assert(h.Health==0.5 and actions.ATTACK.Visible and gui.Enabled)
observe("alive fractional remainder",if fixed then "HP <1/195" else "HP 0/195",true)
if requireFixed then assert(hp.Text=="HP <1/195","LIVING_HP_DISPLAYED_AS_KO") end
h.Health=.99
observe("fraction under one",if fixed then "HP <1/195" else "HP 0/195",true)
h.Health=1
observe("exactly one","HP 1/195",true)
h.Health=194.75
observe("almost full does not claim full","HP 194/195",true)
mounted=true
observe("realm mount keeps numeric HP","HP 194/195",true)
assert(actions.ATTACK.Visible==false)
mounted=false
h.Health=0
observe("true KO","HP 0/195",false)
player.Character=nil
observe("old avatar detached","HP --/--",false)
player.Character,h=avatar(HealthPolicy.initialMaxHP("NINJA"))
attrs.EGGRUMBLE_Role="NINJA"
observe("new avatar health", "HP 185/185",true)
attrs.EGGRUMBLE_Eliminated=true
observe("eliminated", "HP 185/185",false)
attrs.EGGRUMBLE_Eliminated=false
attrs.EGGRUMBLE_QueuedMode="BATTLE_ROYALE"
observe("stale TEAM map after switch", "HP 185/185",false)
mapSnapshot={mode="BATTLE_ROYALE"}
permittedArena="BATTLE_ROYALE_Arena"
observe("active BR", "HP 185/185",true)
phase="FINISHED"
observe("results", "HP 185/185",false)
