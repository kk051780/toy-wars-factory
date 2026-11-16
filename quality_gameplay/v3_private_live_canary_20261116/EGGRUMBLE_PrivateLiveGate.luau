--!strict
-- Isolated EGGRUMBLE V3 private-place canary gate. NOT an official RC enable flag.
-- This module is installed only in a separately composed 21-source test Place.
local RunService=game:GetService("RunService")
local ReplicatedStorage=game:GetService("ReplicatedStorage")
local Gate={}
Gate.OPT_IN_ATTRIBUTE="EGGRUMBLE_V3_EXPLICIT_PRIVATE_CANARY"
Gate.READY_ATTRIBUTE="EGGRUMBLE_V3_PRIVATE_SERVER_READY"

function Gate.serverAllowed():boolean
 if RunService:IsStudio() then return true end
 if not RunService:IsServer() then return false end
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
 ReplicatedStorage:SetAttribute(Gate.READY_ATTRIBUTE,true)
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
