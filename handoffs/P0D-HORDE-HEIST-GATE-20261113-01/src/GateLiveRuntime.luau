--!strict
-- Isolated unpublished B42+V7 preview adapter; never a second Game/Remote.
-- Requires existing original authoritative Game round, Horde, and H1 sea.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local GateRules = require(script.Parent:WaitForChild("GateRules"))
local EliteKOBridge = require(script.Parent:WaitForChild("EliteKOBridge"))
local GateVisual = require(script.Parent:WaitForChild("GateVisual"))
local GateRouteOverlay = require(script.Parent:WaitForChild("GateRouteOverlay"))
local GateLiveRuntime = {}
GateLiveRuntime.__index = GateLiveRuntime

function GateLiveRuntime.new(arena: Instance)
    return setmetatable({arena=arena,round=nil,rules=nil,route=nil},GateLiveRuntime)
end

function GateLiveRuntime:startRound(epoch: number, now: number)
    -- The old barriers disappear before the new round respawn settles.
    if self.route then
        GateRouteOverlay.render(self.route,GateVisual,{phase="OPEN",passable=true})
        self.route.model:Destroy()
    end
    self.route=nil
    self.round=epoch
    self.rules=GateRules.new(tostring(epoch))
end

function GateLiveRuntime:beforeHit(horde)
    if not RunService:IsStudio() or self.rules==nil or self.round~=horde.round then
        return nil
    end
    return EliteKOBridge.capture(horde)
end

function GateLiveRuntime:afterHit(horde,receipt,now: number)
    if receipt==nil or self.rules==nil or self.round~=horde.round then return false end
    if EliteKOBridge.didConfirmEliteKO(horde,receipt) then
        return self.rules:onEliteKO(tostring(self.round),true,now)
    end
    return false
end

local function livingCharacters()
    local result = {}
    for _,player in ipairs(Players:GetPlayers()) do
        local char=player.Character
        local hum=char and char:FindFirstChildOfClass("Humanoid")
        if hum and hum.Health>0 and char then table.insert(result,char) end
    end
    return result
end

local function countsWithinBox(cf: CFrame,size: Vector3,characters)
    if #characters==0 then return 0 end
    local overlap=OverlapParams.new()
    overlap.FilterType=Enum.RaycastFilterType.Include
    overlap.FilterDescendantsInstances=characters
    overlap.MaxParts=0 -- no truncation of character parts
    local hits=workspace:GetPartBoundsInBox(cf,size,overlap)
    local found={}
    for _,part in ipairs(hits) do
        for _,char in ipairs(characters) do
            if part:IsDescendantOf(char) then found[char]=true end
        end
    end
    local count=0
    for _ in pairs(found) do count+=1 end
    return count
end

local function doorOccupancy(route)
    local chars=livingCharacters()
    if #chars==0 then return 0 end
    local visited={}
    for _,model in ipairs(route.doors) do
        local part=model.PrimaryPart
        if not part then return 128 end -- fail open if geometry corrupted
        local overlap=OverlapParams.new()
        overlap.FilterType=Enum.RaycastFilterType.Include
        overlap.FilterDescendantsInstances=chars
        overlap.MaxParts=0
        for _,p in ipairs(workspace:GetPartBoundsInBox(part.CFrame,
                part.Size+Vector3.new(4,4,4),overlap)) do
            for _,char in ipairs(chars) do
                if p:IsDescendantOf(char) then visited[char]=true end
            end
        end
    end
    local count=0
    for _ in pairs(visited) do count+=1 end
    return math.min(count,128)
end

-- Before constructing opaque stone arms, do not place walls through any living avatar.
local function safeToMount()
    local chars=livingCharacters()
    if #chars==0 then return true end
    for _,side in ipairs({-1,1}) do
        local x=side*36
        if countsWithinBox(CFrame.new(x,6,-16),
                Vector3.new(7,16,72),chars)>0 then return false end
    end
    return true
end

function GateLiveRuntime:tick(now: number,epoch: number,phase: string)
    if not RunService:IsStudio() or self.rules==nil or self.round~=epoch then return end
    if phase~="ACTIVE" then
        if self.route then
            GateRouteOverlay.render(self.route,GateVisual,{phase="OPEN",passable=true})
        end
        return
    end
    if self.route==nil and safeToMount() then
        local route,err=GateRouteOverlay.create(self.arena,GateVisual)
        if route then self.route=route end
        -- A missing/changed H1 route never creates a cosmetic gate.
    end
    if self.route then
        local count=doorOccupancy(self.route)
        if self.rules:step(tostring(epoch),now,count) then
            GateRouteOverlay.render(self.route,GateVisual,self.rules:snapshot())
        else
            -- Reject malformed sensor input by leaving the existing state.
        end
    else
        self.rules:step(tostring(epoch),now,0)
    end
end

return GateLiveRuntime
