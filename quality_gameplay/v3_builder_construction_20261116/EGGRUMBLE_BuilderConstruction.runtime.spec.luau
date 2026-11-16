--!nocheck
-- Native Luau executable server-module boundary harness; not Roblox Studio evidence.
-- Replaces only Roblox runtime primitives with deterministic fake objects, without
-- modifying author-owned Game/Remote/client code.
local assertions=0
local function check(b,tag)
 assertions+=1
 assert(b,"BUILDER_RUNTIME_"..tostring(assertions).."_"..(tag or "NO_TAG"))
end

local mt={}
Vector3={}
function Vector3.new(x,y,z) return setmetatable({X=x,Y=y,Z=z},mt) end
mt.__index=function(v,key)
 if key=="Magnitude" then return math.sqrt(v.X*v.X+v.Y*v.Y+v.Z*v.Z) end
 if key=="Unit" then
  local m=math.sqrt(v.X*v.X+v.Y*v.Y+v.Z*v.Z)
  return Vector3.new(v.X/m,v.Y/m,v.Z/m)
 end
 return nil
end
mt.__add=function(a,b) return Vector3.new(a.X+b.X,a.Y+b.Y,a.Z+b.Z) end
mt.__sub=function(a,b) return Vector3.new(a.X-b.X,a.Y-b.Y,a.Z-b.Z) end
mt.__mul=function(a,b)
 if type(a)=="number" then return Vector3.new(a*b.X,a*b.Y,a*b.Z) end
 return Vector3.new(a.X*b,a.Y*b,a.Z*b)
end
CFrame={}
function CFrame.lookAt(pos,look) return {Position=pos,LookVector=look-pos} end
Color3={fromRGB=function(r,g,b) return {r,g,b} end}
Enum={RaycastFilterType={Include="INCLUDE"},Material={Slate="SLATE",WoodPlanks="WOOD"}}
RaycastParams={new=function() return {} end}
OverlapParams={new=function() return {} end}
local pending={}
task={delay=function(seconds,callback)
 table.insert(pending,{seconds=seconds,callback=callback})
end}
local currentPlayer
local players={}
function players:GetPlayerByUserId(id)
 if currentPlayer and currentPlayer.UserId==id then return currentPlayer end
 return nil
end
game={GetService=function(_,kind)
 check(kind=="Players","EXPECTED_PLAYERS_SERVICE")
 return players
end}
local created={}
local createdTools={}
local backpack={}
function backpack:GetChildren()
 local found={}
 for _,tool in ipairs(createdTools) do
  if tool.Parent==self then table.insert(found,tool) end
 end
 return found
end
Instance={new=function(kind)
 if kind=="Tool" then
  local signal={}
  function signal:Connect(callback) self.callback=callback;return {} end
  function signal:Fire() if self.callback then self.callback() end end
  local tool={Parent=nil,Activated=signal,wasDestroyed=false}
  function tool:IsA(class) return class=="Tool" end
  function tool:Destroy() self.wasDestroyed=true;self.Parent=nil end
  table.insert(createdTools,tool)
  return tool
 end
 check(kind=="Part","PART_ONLY")
 local p={Name="",Parent=nil,attributes={}}
 function p:SetAttribute(k,v) self.attributes[k]=v end
 function p:Destroy() self.destroyed=true;self.Parent=nil end
 table.insert(created,p)
 return p
end}
local hitRadius={}
local hitBox={}
local missingFloor=false
local actualBridgeGap=false
local loweredRiverbed=false
local floor={
 Name="TacticalBattlefield",CanCollide=true,Parent=nil,
 Size=Vector3.new(500,2,500),
 CFrame={PointToObjectSpace=function(_,p) return p end},
 IsA=function(_,kind) return kind=="BasePart" end,
 IsDescendantOf=function(_,obj) return true end,
 FindFirstAncestorOfClass=function() return nil end,
}
workspace={}
function workspace:Raycast(at,delta,params)
 if missingFloor then return nil end
 check(params.FilterType=="INCLUDE","GROUND_INCLUDE")
 local midSpan=at.Z>14 and at.Z<18
 if actualBridgeGap and midSpan then return nil end
 if loweredRiverbed and midSpan then
  return {Instance=floor,Position=Vector3.new(at.X,-6,at.Z)}
 end
 return {Instance=floor,Position=Vector3.new(at.X,0,at.Z)}
end
function workspace:GetPartBoundsInRadius(center,radius,params)
 check(params.FilterDescendantsInstances[1]~=workspace,"OBJECTIVE_REGION_SESSION_SCOPED")
 return hitRadius
end
function workspace:GetPartBoundsInBox(cf,size,params)
 check(params.FilterDescendantsInstances[1]==workspace,"ALL_WORKSPACE_COLLISION")
 return hitBox
end
local folder={Parent=workspace}
function folder:FindFirstChild(name)
 return if name=="TacticalBattlefield" then floor else nil
end
local avatar={}
function avatar:GetChildren()
 local found={}
 for _,tool in ipairs(createdTools) do
  if tool.Parent==self then table.insert(found,tool) end
 end
 return found
end
local torso={Position=Vector3.new(0,3,0),CFrame={LookVector=Vector3.new(0,0,1)},Parent=avatar}
function torso:IsA(kind) return kind=="BasePart" end
function avatar:FindFirstChildOfClass(kind)
 return if kind=="Humanoid" then {Health=100} else nil
end
function avatar:FindFirstChild(kind)
 return if kind=="HumanoidRootPart" then torso else nil
end
local attributes={EGGRUMBLE_Role="BUILDER",EGGRUMBLE_QueuedMode="TEAM"}
local p={Parent=players,UserId=1337,Character=avatar}
function p:GetAttribute(key) return attributes[key] end
function p:FindFirstChildOfClass(class)
 return if class=="Backpack" then backpack else nil
end
currentPlayer=p
local owner={id="1337",isAI=false,alive=true,heldEggs=0}
local session={
 mode="TEAM",rules={phase="ACTIVE",winner=nil,castles={["1337"]=owner}},
 world=folder,roster={{id="1337",isAI=false}},castleLocations={}
}
local activeSession=session
session.isCurrentHuman=function(candidate)
 return activeSession==session and candidate==p
end
script={Parent={WaitForChild=function(_,name)
 check(name=="EGGRUMBLE_BuilderPlacementPolicy","POLICY_DEPENDENCY")
 return "./EGGRUMBLE_BuilderPlacementPolicy"
end}}
local Build=require("./EGGRUMBLE_BuilderConstruction")

local ok,reason=Build.place(session,p,"WALL",nil)
check(not ok and reason=="FEATURE_OFF","DEFAULT_OFF")
ok,reason=Build.place(session,p,"UNKNOWN",true)
check(not ok and reason=="INVALID_KIND","INVALID_KIND")
ok,reason=Build.place(session,p,"WALL",true)
check(ok and reason=="WALL","PHYSICAL_WALL")
check(#created==1 and created[1].Size.X==13 and created[1].Size.Y==10,"WALL_PHYSICS")
check(created[1].CanCollide==true and created[1].Parent==folder,"WALL_MATCH_PARENT")
check(created[1].attributes.EGGRUMBLE_ConstructOwner==1337,"AUTHORITATIVE_OWNER")
check(#pending==2 and pending[1].seconds==9 and pending[2].seconds==0.25,"BOUNDED_LIFETIME_AND_WATCHDOG")
ok,reason=Build.place(session,p,"WALL",true)
check(not ok and reason=="COOLDOWN","SPAM_BLOCK")
Build.clear(session)
check(created[1].destroyed and created[1].Parent==nil,"ROUND_CLEAN")
pending[1].callback()
check(created[1].Parent==nil,"EXPIRED_CALLBACK_IDEMPOTENT")
pending[2].callback()
check(created[1].Parent==nil,"STALE_WATCHDOG_NO_RECREATE")

-- Same mode is not proof of the current session: original #531 Host owns
-- session.isCurrentHuman and rejects an old arena even if role and roster match.
activeSession=nil
ok,reason=Build.place(session,p,"WALL",true)
check(not ok and reason=="NOT_AUTHORIZED","STALE_SAME_MODE_SESSION")
activeSession=session
session.isCurrentHuman=nil
ok,reason=Build.place(session,p,"WALL",true)
check(not ok and reason=="NOT_AUTHORIZED","MISSING_LIVE_MEMBERSHIP_CALLBACK")
session.isCurrentHuman=function(_) error("retired session") end
ok,reason=Build.place(session,p,"WALL",true)
check(not ok and reason=="NOT_AUTHORIZED","MEMBERSHIP_CALLBACK_ERROR_FAIL_CLOSED")
session.isCurrentHuman=function(candidate)
 return activeSession==session and candidate==p
end

-- Non-collidable body parts MUST still block an actual new wall.
local humModel={FindFirstChildOfClass=function(_,kind)
 return if kind=="Humanoid" then {Health=100} else nil
end}
local body={
 Name="LeftUpperArm",CanCollide=false,
 FindFirstAncestorOfClass=function(_,kind)
  return if kind=="Model" then humModel else nil
 end,
 IsDescendantOf=function() return false end
}
hitBox={body}
ok,reason=Build.place(session,p,"WALL",true)
check(not ok and reason=="HUMANOID_OVERLAP","AVATAR_NONCOLLIDABLE_BODY")
hitBox={}

-- A foreign floor name must not bypass collision policy.
local foreign={
 Name="TacticalBattlefield",CanCollide=true,
 FindFirstAncestorOfClass=function() return nil end,
 IsDescendantOf=function() return false end
}
hitBox={foreign}
ok,reason=Build.place(session,p,"WALL",true)
check(not ok and reason=="OBSTACLE_OR_CONSTRUCT","FOREIGN_FLOOR_UNTRUSTED")
hitBox={}

local egg={Name="ReleasedEgg_CARRIER_DROP",CanCollide=false}
hitRadius={egg}
ok,reason=Build.place(session,p,"WALL",true)
check(not ok and reason=="OBJECTIVE_BLOCK","NEAR_EGG_REJECT")
hitRadius={}

-- Unauthorised player/round/carrier; no actor source modification.
owner.heldEggs=1
ok,reason=Build.place(session,p,"WALL",true)
check(not ok and reason=="NOT_AUTHORIZED","CARRYING_EGG")
owner.heldEggs=0
attributes.EGGRUMBLE_Role="MAGE"
ok,reason=Build.place(session,p,"WALL",true)
check(not ok and reason=="NOT_AUTHORIZED","WRONG_ROLE")
attributes.EGGRUMBLE_Role="BUILDER"
missingFloor=true
ok,reason=Build.place(session,p,"WALL",true)
check(not ok and reason=="NO_SUPPORT","GAP_UNSUPPORTED")
missingFloor=false
session.rules.phase="FINISHED"
ok,reason=Build.place(session,p,"WALL",true)
check(not ok and reason=="NOT_AUTHORIZED","FINISHED_MATCH")
session.rules.phase="ACTIVE"

ok,reason=Build.place(session,p,"BRIDGE",true)
check(not ok and reason=="NO_GAP","SOLID_GRASS_IS_NOT_BRIDGE")
actualBridgeGap=true
ok,reason=Build.place(session,p,"BRIDGE",true)
check(ok and reason=="BRIDGE","TRUE_MIDSPAN_GAP_BRIDGE")
check(created[#created].Size.Z==20 and created[#created].CanCollide,"GAP_BRIDGE_PHYSICS")
Build.clear(session)
check(created[#created].destroyed,"GAP_BRIDGE_CLEAR")
actualBridgeGap=false
loweredRiverbed=true
ok,reason=Build.place(session,p,"BRIDGE",true)
check(ok and reason=="BRIDGE","LOWERED_RIVERBED_BRIDGE")
Build.clear(session)
check(created[#created].destroyed,"RIVER_BRIDGE_CLEAR")
loweredRiverbed=false

-- Different mode: ownership attribute must not leak across TEAM/BR.
session.mode="BATTLE_ROYALE"
ok,reason=Build.place(session,p,"WALL",true)
check(not ok and reason=="NOT_AUTHORIZED","CROSS_MODE_DENIED")
attributes.EGGRUMBLE_QueuedMode="BATTLE_ROYALE"
ok,reason=Build.place(session,p,"WALL",true)
check(ok and reason=="WALL","BR_MODE_VALID")
-- The author closeRound hook is not yet wired; the module must self-clean
-- in <= 0.25 second after a real match ends, independently of tool expiry.
check(pending[#pending].seconds==0.25,"BR_MODE_SINGLE_WATCHDOG")
session.rules.phase="FINISHED"
pending[#pending].callback()
check(created[#created].destroyed,"AUTO_MATCH_FINISH_CLEAR")
session.rules.phase="ACTIVE"
Build.clear(session)
check(created[#created].destroyed,"FINISH_CLEAR_IDEMPOTENT")

-- A winner is also terminal even before an external round close callback.
ok,reason=Build.place(session,p,"WALL",true)
check(ok and reason=="WALL","NEW_SESSION_CONSTRUCT_BEFORE_WIN")
session.rules.winner="RED"
pending[#pending].callback()
check(created[#created].destroyed,"AUTO_WIN_CLEAR")
session.rules.winner=nil

-- Destroying the arena Folder must revoke collision objects immediately,
-- even if the game never invoked its optional cleanup integration hook.
ok,reason=Build.place(session,p,"WALL",true)
check(ok and reason=="WALL","NEW_CONSTRUCT_BEFORE_WORLD_LOST")
folder.Parent=nil
pending[#pending].callback()
check(created[#created].destroyed,"AUTO_DESTROYED_WORLD_CLEAR")
folder.Parent=workspace
Build.clear(session)

-- Real additional Builder Tool input, preserving original A/B/C tools.
session.mode="TEAM"
attributes.EGGRUMBLE_QueuedMode="TEAM"
local toolOff,toolReason=Build.equip(session,p,false)
check(not toolOff and toolReason=="FEATURE_OFF","BUILDER_TOOL_OFF")
check(#createdTools==0,"BUILDER_TOOL_OFF_NO_ITEMS")
local toolOK,toolReady=Build.equip(session,p,true)
check(toolOK and toolReady=="TOOLS_READY","BUILDER_TOOLS_SERVER_GRANTED")
check(#createdTools==2,"BUILDER_TWO_TOOLS_NO_REMOTE")
check(createdTools[1].Name=="EGGRUMBLE_SKILL_CONSTRUCT_WALL","BUILDER_WALL_TOOL_NAMED")
check(createdTools[2].Name=="EGGRUMBLE_SKILL_CONSTRUCT_BRIDGE","BUILDER_BRIDGE_TOOL_NAMED")
check(createdTools[1].Parent==backpack and createdTools[2].Parent==backpack,"BUILDER_TOOLS_IN_BACKPACK")
local firstWall=createdTools[1]
local n=#created
firstWall.Activated:Fire()
check(#created==n,"UNEQUIPPED_TOOL_DENIED")
firstWall.Parent=avatar
firstWall.Activated:Fire()
check(#created==n+1,"EQUIPPED_SERVER_TOOL_CREATES_WALL")
Build.clear(session)
local old=firstWall
toolOK,toolReady=Build.equip(session,p,true)
check(toolOK and toolReady=="TOOLS_READY","BUILDER_RESYNC_OK")
check(old.wasDestroyed and old.Parent==nil,"BUILDER_OLD_TOOL_REMOVED")
check(#createdTools==4,"BUILDER_TOOLS_REGENERATED")
local staleN=#created
old.Activated:Fire()
check(#created==staleN,"BUILDER_STALE_UNEQUIPPED_TOOL_NOOP")
local currentTool=createdTools[3]
currentTool.Parent=avatar
session.isCurrentHuman=function(_) return false end
currentTool.Activated:Fire()
check(#created==staleN,"BUILDER_TOOL_LIVE_MATCH_GUARD")
session.isCurrentHuman=function(candidate) return activeSession==session and candidate==p end
session.rules.phase="FINISHED"
currentTool.Activated:Fire()
check(#created==staleN,"BUILDER_TOOL_TERMINAL_PHASE_GUARD")
session.rules.phase="ACTIVE"
Build.clear(session)

print("GQ_BUILDER_RUNTIME_MOCK_PASS assertions="..tostring(assertions))
