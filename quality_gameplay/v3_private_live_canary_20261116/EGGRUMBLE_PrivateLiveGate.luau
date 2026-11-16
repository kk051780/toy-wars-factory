--!strict
-- Isolated EGGRUMBLE V3 private-place canary gate. NOT an official RC enable flag.
-- This module is installed only in a separately composed 21-source test Place.
local RunService=game:GetService("RunService")
local ReplicatedStorage=game:GetService("ReplicatedStorage")
local Gate={}
Gate.OPT_IN_ATTRIBUTE="EGGRUMBLE_V3_EXPLICIT_PRIVATE_CANARY"
Gate.READY_ATTRIBUTE="EGGRUMBLE_V3_PRIVATE_SERVER_READY"
-- This is a one-shot test-server lease, never a production authority.
local activeWorld:Instance?=nil
local permanentlyRevoked=false

function Gate.serverAllowed():boolean
 if RunService:IsStudio() then return true end
 if not RunService:IsServer() or permanentlyRevoked then return false end
 -- No public/live-server opt-in. Only a dedicated Roblox private server whose
 -- ServerStorage attribute was explicitly configured can run this test Place.
 if type(game.PrivateServerId)~="string" or game.PrivateServerId=="" then return false end
 return game:GetService("ServerStorage"):GetAttribute(Gate.OPT_IN_ATTRIBUTE)==true
end

function Gate.allowed():boolean
 if RunService:IsStudio() then return true end
 if RunService:IsServer() then return Gate.serverAllowed() end
 -- A client can only see the server-published readiness acknowledgement.
 return ReplicatedStorage:GetAttribute(Gate.READY_ATTRIBUTE)==true
end

function Gate.advertiseServerReady():boolean
 if not RunService:IsServer() or not Gate.serverAllowed() then return false end
 -- Only a registered, still mounted private arena can advertise readiness.
 -- The host calls this once all original TEAM/BR portals are initialized.
 if not RunService:IsStudio() and (not activeWorld or not activeWorld.Parent) then
  return false
 end
 ReplicatedStorage:SetAttribute(Gate.READY_ATTRIBUTE,true)
 return true
end


-- When an isolated private test session has started, clearing the server-owned
-- opt-in must also withdraw the client READY signal and remove the test arena.
-- Never touches the production Game, Store, Remote, HP or scoring services.
-- Source-only QA: Roblox live runtime lifecycle still requires Studio/Android tests.
function Gate.watchWorld(world:Instance):boolean
 if not RunService:IsServer() then return false end
 if RunService:IsStudio() then return true end
 -- Never let two copies of the host create a second castle/egg/horde arena.
 -- Duplicate registration cannot withdraw the valid world's READY.
 if activeWorld then
  if activeWorld~=world and world.Parent then world:Destroy() end
  return activeWorld==world
 end
 if not Gate.serverAllowed() then
  permanentlyRevoked=true
  ReplicatedStorage:SetAttribute(Gate.READY_ATTRIBUTE,false)
  if world.Parent then world:Destroy() end
  return false
 end
 activeWorld=world
 local function retire()
  if activeWorld~=world then return end
  -- Fail closed for the remainder of this server instance, even if opt-in
  -- flips false->true between polling intervals. Restart to test again.
  permanentlyRevoked=true
  activeWorld=nil
  ReplicatedStorage:SetAttribute(Gate.READY_ATTRIBUTE,false)
  if world.Parent then world:Destroy() end
 end
 local serverStorage=game:GetService("ServerStorage")
 local changed=serverStorage:GetAttributeChangedSignal(Gate.OPT_IN_ATTRIBUTE):Connect(function()
  if not Gate.serverAllowed() then retire() end
 end)
 -- Close the permission-check/registration race without allowing a re-enable.
 if not Gate.serverAllowed() then
  retire()
  changed:Disconnect()
  return false
 end
 task.spawn(function()
  while activeWorld==world and world.Parent and Gate.serverAllowed() do
   task.wait(0.25)
  end
  retire()
  changed:Disconnect()
 end)
 return true
end

function Gate.waitAllowed(seconds:number?):boolean
 if RunService:IsStudio() then return true end
 if RunService:IsServer() then return Gate.allowed() end
 local timeout=math.clamp(seconds or 8,0,10)
 local deadline=os.clock()+timeout
 repeat
  if Gate.allowed() then return true end
  task.wait(0.1)
 until os.clock()>=deadline
 return Gate.allowed()
end
return Gate
