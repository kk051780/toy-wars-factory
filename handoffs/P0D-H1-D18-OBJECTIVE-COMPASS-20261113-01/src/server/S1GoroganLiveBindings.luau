--!strict
-- TRAP RAIDERS S1: concrete, opt-in SERVER authority binding for the original
-- D07 Gorogan Combined/AI/Rig/Damage/Receipt modules. No new round, event RNG,
-- RemoteEvent, heartbeat, client authority or alternate boss implementation.
local Players = game:GetService("Players")
local Combined = require(script.Parent:WaitForChild("GoroganCombinedRuntime"))
local Driver = require(script.Parent:WaitForChild("GoroganRigDriver"))
local Gate = require(script.Parent:WaitForChild("GoroganDamageBoundary"))
local Window = require(script.Parent:WaitForChild("GoroganAttackReceiptWindow"))

local Binding = {}
Binding.__index = Binding

local function finite(v)
    return type(v) == "number" and v == v
        and v ~= math.huge and v ~= -math.huge
end
local function goodVec(v)
    return typeof(v) == "Vector3" and finite(v.X)
        and finite(v.Y) and finite(v.Z)
end
local function safeId(v)
    return type(v) == "string" and #v >= 1 and #v <= 64
        and v:match("^[%w_%-]+$") ~= nil
end
local function validTeam(v)
    return v == "RED" or v == "BLUE"
end
local function nowFrom(self)
    local ok, n = pcall(self.deps.serverTime)
    if not ok or not finite(n) or n < 0 or n > 1e12 then return nil end
    return n
end
local function liveMatch(self)
    local ok, m = pcall(self.deps.readMatch)
    if not ok or type(m) ~= "table"
        or m.phase ~= "ACTIVE" or m.serial ~= self.serial
        or m.startedAt ~= self.startedAt or m.deadline ~= self.deadline
        or not finite(m.deadline) or not finite(m.startedAt) then
        return false
    end
    local t = nowFrom(self)
    return t ~= nil and t >= self.startedAt and t < self.deadline
end
local function activeEvent(self, roundId, eventId)
    return self.activeEventId ~= nil and roundId == self.roundId
        and eventId == self.activeEventId and liveMatch(self)
end
local function healthy(player)
    if typeof(player) ~= "Instance" or not player:IsA("Player")
        or player.Parent ~= Players then return nil, nil end
    local character = player.Character
    local h = character and character:FindFirstChildOfClass("Humanoid")
    local root = character and character:FindFirstChild("HumanoidRootPart")
    if not h or h.Health <= 0 or not root or not root:IsA("BasePart")
        or not goodVec(root.Position) then return nil, nil end
    return root, h
end
local function teamFor(self, player)
    local ok, team = pcall(self.deps.getPlayerTeam, player)
    return if ok and validTeam(team) then team else "NONE"
end
local function inSpawnSafeZone(self, player)
    local root = healthy(player)
    if not root then return true end
    local team = teamFor(self, player)
    if not validTeam(team) then return true end
    local side = self.deps.map.teams[team]
    if type(side) ~= "table" or typeof(side.spawn) ~= "CFrame" then return true end
    return (root.Position - side.spawn.Position).Magnitude < 14
end
local function protectedByRespawn(self, player)
    local ok, expiration = pcall(self.deps.getInvulnerableUntil, player)
    local now = nowFrom(self)
    if not ok or not finite(expiration) or not now then return true end
    return now < expiration
end
local function playerFromId(playerId)
    -- Original D07 AI and damage gate allow canonical negative Studio-local
    -- test Player.UserId strings. Trusted roster (not client input) provides
    -- these IDs. Exact identity prevents "012" aliasing player "12".
    if not safeId(playerId) or not playerId:match("^%-?%d+$") then return nil end
    local found = nil
    for _, player in ipairs(Players:GetPlayers()) do
        if player.Parent == Players and tostring(player.UserId) == playerId then
            if found ~= nil then return nil end -- fail closed if duplicate ID
            found = player
        end
    end
    return found
end

-- Returns the real Roblox root/humanoid state on each read, never client data.
local function currentRoster(self)
    if not liveMatch(self) then return {} end
    local players = Players:GetPlayers()
    if #players > 24 then return nil end
    local result = {}
    for _, player in ipairs(players) do
        local team = teamFor(self, player)
        local root, hum = healthy(player)
        if validTeam(team) and root and hum then
            local p = root.Position
            if math.abs(p.X) > 2048 or p.Y < -100 or p.Y > 700
                or math.abs(p.Z) > 2048 then return nil end
            table.insert(result, {
                playerId = tostring(player.UserId), team = team,
                alive = true, position = {x = p.X, y = p.Y, z = p.Z},
                inSafeZone = inSpawnSafeZone(self, player)
                    or protectedByRespawn(self, player),
            })
        end
    end
    return result
end

local function raycastParams(self)
    local params = RaycastParams.new()
    params.FilterType = Enum.RaycastFilterType.Exclude
    local ignore = {}
    if self.driver and self.driver.model then table.insert(ignore, self.driver.model) end
    for _, player in ipairs(Players:GetPlayers()) do
        if player.Character then table.insert(ignore, player.Character) end
    end
    params.FilterDescendantsInstances = ignore
    return params
end
local function groundAllowed(self, p)
    if not liveMatch(self) or not goodVec(p)
        or math.abs(p.X) > 52 or math.abs(p.Z) > 40
        or p.Y < -3 or p.Y > 14 then return false end
    local origin = p + Vector3.new(0, 7, 0)
    local hit = workspace:Raycast(origin, Vector3.new(0, -18, 0), raycastParams(self))
    return hit ~= nil and hit.Instance:IsDescendantOf(self.deps.map.model)
        and hit.Normal.Y >= 0.5
end
local function getPhysicalBoss(self)
    local d = self.driver
    local p = d and d:getPosition() or nil
    if type(p) ~= "table" or not finite(p.x) or not finite(p.y) or not finite(p.z)
        then return nil end
    return Vector3.new(p.x, p.y, p.z)
end
local function clearEvent(self)
    self.activeEventId = nil
    self.pendingActivation = nil
end

function Binding.new(deps)
    assert(type(deps) == "table" and deps.approvedByOwner == true,
        "OWNER_APPROVED_ACTUAL_D07_CALLBACKS_REQUIRED")
    for _, field in ipairs({
        "readMatch", "serverTime", "getPlayerTeam",
        "getInvulnerableUntil", "sendBossVisual",
    }) do assert(type(deps[field]) == "function", "S1_MISSING_" .. field) end
    local m = deps.readMatch()
    assert(type(m) == "table" and m.phase == "ACTIVE"
        and finite(m.serial) and m.serial >= 1 and m.serial < 1024
        and m.serial % 1 == 0 and finite(m.startedAt) and finite(m.deadline)
        and m.deadline > m.startedAt, "FRESH_S1_ROUND_REQUIRED")
    assert(type(deps.map) == "table"
        and typeof(deps.map.model) == "Instance"
        and deps.map.model:IsA("Folder")
        and deps.map.model.Name == "TRAP_RAIDERS_S1"
        and deps.map.model:IsDescendantOf(workspace)
        and type(deps.map.teams) == "table"
        and deps.map.teams.RED and deps.map.teams.BLUE,
        "EXACT_S1_MAP_REQUIRED")
    return setmetatable({
        deps = deps, serial = m.serial, startedAt = m.startedAt,
        deadline = m.deadline, roundId = "S1_" .. tostring(m.serial),
        driver = nil, gate = nil, window = nil, combined = nil,
        activeEventId = nil, pendingActivation = nil, attempted = false,
        closed = false, ignoredModel = {},
    }, Binding)
end

-- Called ONLY by the already approved S1CanonicalRoundHost.makeCombined(mapper).
-- Original modules are instantiated once for this serial, not globally.
function Binding:makeCombined(mapper)
    assert(not self.closed and not self.combined
        and type(mapper) == "table"
        and type(mapper.isCanonicalActivation) == "function"
        and liveMatch(self), "MAPPER_AND_CURRENT_ROUND_REQUIRED")
    local me = self
    local window = Window.new()
    self.window = window
    local driver = Driver.new({
        integrationApproved = true, serverOnlyFolder = self.deps.map.model,
        currentRound = function() return me.roundId end,
        isEventActive = function(roundId, eventId) return activeEvent(me, roundId, eventId) end,
        isValidStageAnchor = function(stage, p)
            return stage == "S1" and goodVec(p)
                and (p - Vector3.new(0, 0, 0)).Magnitude <= 0.1
        end,
        isSafeTerrain = function(p) return groundAllowed(me, p) end,
    })
    self.driver = driver
    local ignoredModel = self.ignoredModel
    local gate = Gate.new({
        integrationApproved = true,
        isRealRoundEvent = function(roundId, eventId)
            return activeEvent(me, roundId, eventId)
        end,
        resolvePlayerFromTrustedId = playerFromId,
        isSafeZone = function(player) return inSpawnSafeZone(me, player) end,
        isDamageImmune = function(player) return protectedByRespawn(me, player) end,
        isActiveCombatant = function(player, roundId)
            return roundId == me.roundId and liveMatch(me)
                and validTeam(teamFor(me, player)) and healthy(player) ~= nil
        end,
        getBossPosition = function()
            ignoredModel[1] = if me.driver then me.driver.model else nil
            return getPhysicalBoss(me)
        end,
        getAttackCenter = function(roundId, eventId, attackId)
            return window:center(roundId, eventId, attackId)
        end,
        isCanonicalAttackReceipt = function(roundId, eventId, attackId)
            return window:attests(roundId, eventId, attackId)
        end,
        raycastIgnore = ignoredModel,
    })
    self.gate = gate

    local combined = Combined.new({
        integrationApproved = true, driver = driver,
        damageGate = gate, receiptWindow = window,
        isCanonicalActivation = function(a)
            return liveMatch(me) and mapper:isCanonicalActivation(a)
        end,
        isRoundActive = function(roundId, eventId)
            return activeEvent(me, roundId, eventId)
        end,
        getCurrentRoundId = function()
            return if liveMatch(me) then me.roundId else "STALE_S1"
        end,
        getStageId = function(_roundId) return "S1" end,
        getNow = function()
            return nowFrom(me) or -1
        end,
        mintServerEventId = function(activation)
            if me.attempted or not liveMatch(me)
                or not mapper:isCanonicalActivation(activation) then
                return nil
            end
            me.attempted = true
            me.activeEventId = "G07_" .. tostring(me.serial)
            return me.activeEventId
        end,
        getGroundAnchor = function(_stage) return Vector3.new(0, 0, 0) end,
        getRoster = function()
            return currentRoster(me)
        end,
        isLineOfSight = function(center, playerData)
            if type(center) ~= "table" or not finite(center.x)
                or not finite(center.y) or not finite(center.z)
                or type(playerData) ~= "table" then return false end
            local player = playerFromId(playerData.playerId)
            local root = player and healthy(player)
            if not root then return false end
            local source = Vector3.new(center.x, center.y + 2, center.z)
            local target = root.Position + Vector3.new(0, 1, 0)
            local v = target - source
            if v.Magnitude < 0.01 or v.Magnitude > 64 then return false end
            local params = RaycastParams.new()
            params.FilterType = Enum.RaycastFilterType.Exclude
            params.FilterDescendantsInstances = if me.driver and me.driver.model
                then {me.driver.model} else {}
            local hit = workspace:Raycast(source, v, params)
            return hit == nil or hit.Instance:IsDescendantOf(player.Character)
        end,
        broadcastVisual = function(data)
            if not liveMatch(me) or not safeId(data.matchId)
                or data.matchId ~= me.roundId
                or data.eventId ~= me.activeEventId then
                error("STALE_OR_UNTRUSTED_BOSS_VISUAL")
            end
            local ok, result = pcall(me.deps.sendBossVisual, data)
            if not ok or result ~= true then error("S1_BOSS_VISUAL_CALLBACK_FAILED") end
        end,
    })
    self.combined = combined
    return combined
end

-- Idempotent safety cleanup for a partially yielded start and round-stop paths.
-- This is the ONLY callback passed to the original Mapper.abortCombined.
function Binding:abort(roundId)
    if roundId ~= self.roundId then return false end
    local success = true
    if self.combined and self.combined.active then
        local eventId = self.activeEventId
        local ok = pcall(function() self.combined:stop(roundId, eventId) end)
        success = success and ok
    end
    if self.window then self.window:close() end
    if self.gate and self.gate.active then
        local ok, result = pcall(function()
            return self.gate:stop(roundId, self.gate.eventId)
        end)
        success = success and ok and result == true
    end
    if self.driver and not self.driver.closed then
        local ok, result = pcall(function()
            return self.driver:stop(roundId, self.driver.eventId)
        end)
        success = success and ok and result == true
    end
    if self.combined and self.combined.active then success = false end
    if self.driver and self.driver.model then success = false end
    if self.gate and self.gate.active then success = false end
    clearEvent(self)
    self.closed = true
    return success
end

function Binding:status()
    return {
        roundId = self.roundId, eventId = self.activeEventId,
        active = not self.closed and liveMatch(self),
        bossSpawned = self.driver ~= nil and self.driver.model ~= nil,
        verifiedInRobloxStudio = false,
    }
end

return Binding
