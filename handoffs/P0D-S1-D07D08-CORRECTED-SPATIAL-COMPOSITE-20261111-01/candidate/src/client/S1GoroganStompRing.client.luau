--!strict
-- S1 client-only spatial danger cue for the authentic D07 physical Gorogan.
-- No RemoteEvent creation, client attacks, damage, hit authority or NPC spawn.
-- The server-replicated physical boss already exists: render ONLY local ring.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Policy = require(script.Parent:WaitForChild("GoroganVisualPolicy"))
local remote = ReplicatedStorage:WaitForChild("TrapRaidersS1Remote") :: RemoteEvent

local lastSerial = -1
local phase = "LOBBY"
local visual: any = nil
local ringParts: {BasePart} = {}
local ringUntil = 0
local tickBudget = 0
local lastEventId: string? = nil

local function finite(n: any): boolean
    return type(n) == "number" and n == n
        and n ~= math.huge and n ~= -math.huge
end

local function goodPosition(p: any): boolean
    return type(p) == "table" and finite(p.x) and finite(p.y)
        and finite(p.z) and math.abs(p.x) <= 2048
        and math.abs(p.z) <= 2048
        and p.y >= -100 and p.y <= 700
end

local function clearRing()
    for _, part in ipairs(ringParts) do
        part:Destroy()
    end
    table.clear(ringParts)
    ringUntil = 0
end

local function clearRound()
    clearRing()
    visual = nil
    lastEventId = nil
end

local function showRing(position, untilAt: number)
    clearRing()
    if phase ~= "ACTIVE" or not goodPosition(position) then return end
    local now = workspace:GetServerTimeNow()
    -- No false full two-second promise after network delay.
    if not finite(now) or untilAt <= now or untilAt - now > 2 then return end
    ringUntil = untilAt
    local center = Vector3.new(position.x, position.y + 0.3, position.z)
    local radius = 7
    local segments = 8
    for i = 1, segments do
        local angle = (i - 1) * (2 * math.pi / segments)
        local part = Instance.new("Part")
        part.Name = "D07_LocalStompDanger_" .. tostring(i)
        part.Anchored = true
        part.CanCollide = false
        part.CanTouch = false
        part.CanQuery = false
        part.CastShadow = false
        part.Locked = true
        part.Size = Vector3.new(5.1, 0.16, 0.58)
        part.Material = Enum.Material.Neon
        part.Color = Color3.fromRGB(250, 72, 52)
        part.Transparency = 0.28
        local offset = Vector3.new(math.sin(angle) * radius, 0, math.cos(angle) * radius)
        part.CFrame = CFrame.new(center + offset) * CFrame.Angles(0, angle, 0)
        part.Parent = workspace
        table.insert(ringParts, part)
    end
end

local function handleSnapshot(s)
    if not finite(s.serial) or s.serial % 1 ~= 0
        or s.serial < 0 or s.serial < lastSerial
        or type(s.phase) ~= "string" then return end
    if s.serial > lastSerial or s.phase ~= "ACTIVE" then clearRound() end
    lastSerial = s.serial
    phase = s.phase
end

local function handleVisual(s)
    if phase ~= "ACTIVE" or not finite(s.serial)
        or s.serial ~= lastSerial or lastSerial < 1
        or s.bossId ~= "GOROGAN"
        or s.stageId ~= "S1"
        or s.eventId ~= "G07_" .. tostring(lastSerial)
        or not finite(s.seq) or s.seq % 1 ~= 0 or s.seq < 1
        or s.seq > 10000
        or not finite(s.serverSentAt) then return end

    local now = workspace:GetServerTimeNow()
    -- Avoid replaying an old attack or future timestamp. The server is the
    -- only source of these packets; this client filter is defense-in-depth.
    if not finite(now) or s.serverSentAt > now + 0.5
        or now - s.serverSentAt > 2 then return end

    if s.visualKind == "START" then
        if visual ~= nil or lastEventId ~= nil or not goodPosition(s.position) then
            return
        end
        local candidate = Policy.new("S1_" .. tostring(lastSerial), "S1")
        local result = Policy.apply(candidate, {
            kind = "START", matchId = "S1_" .. tostring(lastSerial),
            stageId = "S1", bossId = "GOROGAN", eventId = s.eventId,
            seq = s.seq, position = s.position,
        }, now)
        if result == "STARTED" then
            -- Budget the physical server boss's 14s TTL from the trusted
            -- SERVER emission time, not from delayed client receipt.
            candidate.expiresAt = math.min(candidate.expiresAt, s.serverSentAt + 14)
            visual = candidate
            lastEventId = s.eventId
        end
        return
    end

    if not visual or lastEventId ~= s.eventId then return end
    if s.visualKind == "STOMP" then
        if not goodPosition(s.position) then return end
        local result = Policy.apply(visual, {
            kind = "STOMP", matchId = "S1_" .. tostring(lastSerial),
            stageId = "S1", bossId = "GOROGAN", eventId = s.eventId,
            seq = s.seq, position = s.position,
        }, now)
        if result == "STOMP_STARTED" then
            -- Authoritative damage is resolved by the original server D07
            -- ReceiptWindow after its OWN 2s telegraph. This ring is cosmetic.
            local deadline = math.min(visual.telegraphUntil, s.serverSentAt + 2)
            showRing(s.position, deadline)
        end
    elseif s.visualKind == "END" then
        local result = Policy.apply(visual, {
            kind = "END", matchId = "S1_" .. tostring(lastSerial),
            stageId = "S1", bossId = "GOROGAN", eventId = s.eventId,
            seq = s.seq,
        }, now)
        if result == "ENDED" then clearRound() end
    end
end

local connection = remote.OnClientEvent:Connect(function(s)
    if type(s) ~= "table" then return end
    if s.kind == "SNAPSHOT" then
        handleSnapshot(s)
    elseif s.kind == "BOSS_VISUAL" then
        handleVisual(s)
    end
end)

local heartbeat = RunService.Heartbeat:Connect(function(dt)
    tickBudget += math.max(0, dt)
    if tickBudget < 0.1 then return end
    tickBudget = 0
    local now = workspace:GetServerTimeNow()
    if not finite(now) then clearRound(); return end
    if ringUntil > 0 and now >= ringUntil then clearRing() end
    if visual then
        local result = Policy.expire(visual, now)
        if result == "EXPIRED" then clearRound() end
    end
end)

script.Destroying:Connect(function()
    connection:Disconnect()
    heartbeat:Disconnect()
    clearRound()
end)
