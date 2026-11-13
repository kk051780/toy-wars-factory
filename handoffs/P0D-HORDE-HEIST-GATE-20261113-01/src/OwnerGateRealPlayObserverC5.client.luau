--!strict
-- PRIVATE Roblox Studio read-only movement evidence for C5.
-- Never FireServer, mutate a Player, award XP, move an egg, or create a Remote.
-- Distinguishes source existence, real physics properties, and avatar crossing.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
if not RunService:IsStudio() then return end

local player = Players.LocalPlayer
if player == nil then return end
local originalRemote = ReplicatedStorage:WaitForChild("TrapRaidersS1Remote", 25)
if originalRemote == nil or not originalRemote:IsA("RemoteEvent") then
    warn("[P0D_GATE_ENGINE_QA] ORIGINAL_REMOTE_NOT_FOUND")
    return
end

local epoch: number? = nil
local phase = "LOBBY"
local carrying = ""
local eggId = ""
local lastServerSnapshotAt = 0
local activeStarted = 0
local missingReported = false
local mountReported = false
local openingReported = false
local crossingReported: {[string]: boolean} = {}
local visits: {[string]: {side: number, startAt: number}} = {}
local previous: Vector3? = nil
local previousAt = 0
local previousCharacter: Model? = nil

local function resetObservations()
    missingReported = false
    mountReported = false
    openingReported = false
    crossingReported = {}
    visits = {}
    previous = nil
    previousAt = 0
    previousCharacter = nil
end

originalRemote.OnClientEvent:Connect(function(packet)
    if type(packet) ~= "table" or packet.kind ~= "SNAPSHOT" then return end
    if type(packet.serial) ~= "number" or packet.serial ~= math.floor(packet.serial)
        or packet.serial < 0 then return end
    if type(packet.phase) ~= "string" then return end
    if epoch ~= packet.serial then
        epoch = packet.serial
        resetObservations()
        print("[P0D_GATE_ENGINE_QA] SNAPSHOT_EPOCH serial="..tostring(epoch))
    end
    if phase ~= packet.phase then
        phase = packet.phase
        if phase == "ACTIVE" then
            activeStarted = os.clock()
        else
            visits = {}
        end
        print("[P0D_GATE_ENGINE_QA] SERVER_PHASE "..phase)
    end
    carrying = type(packet.carrying) == "string" and packet.carrying or ""
    eggId = type(packet.eggId) == "string" and packet.eggId or ""
    lastServerSnapshotAt = os.clock()
end)

local function getDoorModels()
    local arena = workspace:FindFirstChild("TRAP_RAIDERS_S1")
    local overlay = arena and arena:FindFirstChild("P0D_S2_NeutralShortcut_ReviewOnly")
    if overlay == nil then return nil end
    local red = overlay:FindFirstChild("RED_SHARED_SEA_GATE")
    local blue = overlay:FindFirstChild("BLUE_SHARED_SEA_GATE")
    if red == nil or blue == nil or not red:IsA("Model")
        or not blue:IsA("Model") then return nil end
    local redDoor = red:FindFirstChild("PhysicalDoor")
    local blueDoor = blue:FindFirstChild("PhysicalDoor")
    if not redDoor or not blueDoor or not redDoor:IsA("BasePart")
        or not blueDoor:IsA("BasePart") then return nil end
    return {RED = redDoor, BLUE = blueDoor}
end

local function physicalDoorOpen(part: BasePart): boolean
    return part.CanCollide == false and part.CanQuery == false
end

local function actuallyInsideLane(part: BasePart, location: Vector3): (number?, number?)
    local localPos = part.CFrame:PointToObjectSpace(location)
    -- A 10-stud actual opening. Do NOT accept outside-of-gate detours,
    -- ramps above it, jumps over it, or standing on a nearby wall.
    if math.abs(localPos.X) > part.Size.X/2 - 0.65 then return nil,nil end
    if math.abs(localPos.Y) > part.Size.Y/2 - 0.15 then return nil,nil end
    if math.abs(localPos.Z) > 7.0 then return nil,nil end
    return localPos.Z,localPos.X
end

local lastPoll = 0
RunService.Heartbeat:Connect(function()
    local now = os.clock()
    if now-lastPoll < 0.055 then return end
    lastPoll = now
    if phase ~= "ACTIVE" or epoch == nil then return end

    local doors = getDoorModels()
    if doors == nil then
        if not missingReported and now-activeStarted >= 12 then
            missingReported = true
            warn("[P0D_GATE_ENGINE_QA] ACTIVE_12S_NO_PHYSICAL_SEA_GATES")
        end
        visits = {}
        previous = nil
        return
    end
    if not mountReported then
        mountReported = true
        print("[P0D_GATE_ENGINE_QA] BOTH_PHYSICAL_GATE_PARTS_FOUND")
    end
    if physicalDoorOpen(doors.RED) and physicalDoorOpen(doors.BLUE)
        and not openingReported then
        openingReported = true
        print("[P0D_GATE_ENGINE_QA] BOTH_DOORS_ACTUALLY_NONCOLLIDING_NONQUERYING")
    end

    local character = player.Character
    local humanoid = character and character:FindFirstChildOfClass("Humanoid")
    local root = character and character:FindFirstChild("HumanoidRootPart")
    if humanoid == nil or humanoid.Health <= 0
        or root == nil or not root:IsA("BasePart") then
        visits = {}; previous = nil; previousCharacter = nil
        return
    end
    if previousCharacter ~= character then
        visits = {}; previous = nil; previousCharacter = character
    end
    local position = root.Position
    local movementOK = previous ~= nil and now-previousAt > 0
        and now-previousAt <= 0.35
        and (position-previous).Magnitude <= 5.0
    if not movementOK then visits = {} end

    for name,part in pairs(doors) do
        if crossingReported[name] then continue end
        if not physicalDoorOpen(part) or not movementOK then
            visits[name] = nil
            continue
        end
        local z = actuallyInsideLane(part,position)
        if z == nil then
            visits[name]=nil
            continue
        end
        local currentSide = if z <= -1.5 then -1
            elseif z >= 1.5 then 1 else 0
        local started = visits[name]
        if started ~= nil and currentSide ~= 0
            and started.side ~= currentSide
            and now - started.startAt <= 2.0 then
            crossingReported[name] = true
            visits[name]=nil
            -- A real observed local HumanoidRootPart crossing, not a claim
            -- that egg score or server PvP logic has passed.
            local freshServerEgg = now-lastServerSnapshotAt <= 2.0
                and (carrying ~= "" or eggId ~= "")
            print("[P0D_GATE_ENGINE_QA] REAL_AVATAR_CROSSED_OPEN_"..name
                .." epoch="..tostring(epoch)
                .." serverEggSnapshotRecent="..tostring(freshServerEgg))
        elseif currentSide ~= 0 and started == nil then
            visits[name] = {side=currentSide,startAt=now}
        elseif started ~= nil and now-started.startAt > 2.0 then
            visits[name] = nil
        end
    end
    previous = position
    previousAt = now
end)
