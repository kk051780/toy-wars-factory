--!nocheck
-- #388 / #372 FB-015 ART-MOTION: first client-only cosmetic motion slice.
-- This is SOURCE_WIP, not PREP_READY, not official RC and not Studio accepted.
-- Parent candidate #387 supplies the original #374 ART_* silhouettes. No new
-- damage, AI, hitbox, score, XP, Remote, store, or authoritative animation.
local RunService = game:GetService("RunService")
if not RunService:IsStudio() then return end
local Players = game:GetService("Players")
local HttpService = game:GetService("HttpService")
local Workspace = game:GetService("Workspace")

local localPlayer = Players.LocalPlayer
if not localPlayer then return end
-- Avoid permanent timeout when Roblox streaming delays the original world.
local arena = Workspace:WaitForChild("TRAP_RAIDERS_S1")
local horde = arena:WaitForChild("EGG_RUMBLE_NEUTRAL_MUSOU_EXPERIMENT")

local FEATURE = "P0D_ART_MOTION_CLIENT_V1"
local MAX_MODELS = 16
-- Full existing art: 3 knights×10 + 3 wraiths×10 + 2 brutes×11
-- + 1 elite×10 = 92 client-only mirrors, bounded at 104 for headroom.
local MAX_ACTIVE_COSMETIC_PARTS = 104
local VIEW_RANGE_STUDS = 105
local ANIM_STEP = 1 / 25
local connected = {}
local records = {}
local isRunning = true
local elapsed = 0
local activeParts = 0
local lastRound = nil
local lastEpoch = nil
local lastHitSerial = {}
-- Bounded 9-NPC short-lived cues can arrive before an art model replicates.
-- Replaying them at their original time avoids inventing later damage events.
local pendingHits = {}
-- Server-created anchored art is never locally re-positioned. We animate only
-- client-owned clones and reveal server originals when outside the view range.
local localArt = Instance.new("Folder")
localArt.Name = "P0D_FB015_MOTION_COSMETIC_CLIENT_ONLY"
localArt.Parent = Workspace

-- These names refer to the original #374 generated art. We DO NOT recreate
-- geometry or overlap #379/#381 slash particles or #374's hit sparks.
local watchedParts = {
    KNIGHT = {
        "ART_KNIGHT_CHEST", "ART_KNIGHT_HELMET", "ART_KNIGHT_CREST",
        "ART_KNIGHT_PAULDRON_-1", "ART_KNIGHT_PAULDRON_1",
        "ART_KNIGHT_SHIELD", "ART_KNIGHT_SHIELD_MARK",
        "ART_KNIGHT_SPEAR_SHAFT", "ART_KNIGHT_SPEAR_TIP", "ART_KNIGHT_CAPE",
    },
    WRAITH = {
        "ART_WRAITH_HOOD", "ART_WRAITH_COWL", "ART_WRAITH_FACE_VEIL",
        "ART_WRAITH_CRYSTAL_EYE_-1", "ART_WRAITH_CRYSTAL_EYE_1",
        "ART_WRAITH_SHOULDER_FIN_-1", "ART_WRAITH_SHOULDER_FIN_1",
        "ART_WRAITH_CHEST_SIGIL", "ART_WRAITH_ORB", "ART_WRAITH_SHROUD",
    },
    BRUTE = {
        "ART_BRUTE_CHEST_PLATE", "ART_BRUTE_JAW",
        "ART_BRUTE_TUSK_-1", "ART_BRUTE_TUSK_1",
        "ART_BRUTE_HORN_-1", "ART_BRUTE_HORN_1",
        "ART_BRUTE_SHOULDER_-1", "ART_BRUTE_SHOULDER_1",
        "ART_BRUTE_MAUL_HANDLE", "ART_BRUTE_MAUL_HEAD", "ART_BRUTE_BACK_FUR",
    },
    ELITE = {
        "ART_ELITE_CHEST_ARMOUR", "ART_ELITE_MASK",
        "ART_ELITE_CURVED_HORN_-1", "ART_ELITE_CURVED_HORN_1",
        "ART_ELITE_SHOULDER_SPIKE_-1", "ART_ELITE_SHOULDER_SPIKE_1",
        "ART_ELITE_GAUNTLET_-1", "ART_ELITE_GAUNTLET_1",
        "ART_ELITE_BACK_BANNER", "ART_ELITE_WAR_CORE",
    },
}

local function isMinion(model)
    return model:IsA("Model") and (
        model.Name:match("^MUSOU_MINION_%d+$") ~= nil
        or model.Name == "MUSOU_ELITE_TELEGRAPH")
end

local function typeOf(model)
    if model.Name == "MUSOU_ELITE_TELEGRAPH" then return "ELITE" end
    local id = tonumber(model.Name:match("(%d+)$"))
    if not id then return nil end
    return ({"KNIGHT","WRAITH","BRUTE"})[((id - 1) % 3) + 1]
end

local function drop(model)
    local entry = records[model]
    if not entry then return end
    for _,visual in ipairs(entry.attachments) do
        if visual.original and visual.original.Parent then
            visual.original.LocalTransparencyModifier = visual.initialModifier
        end
        if visual.copy and visual.copy.Parent then visual.copy:Destroy() end
    end
    activeParts = math.max(0, activeParts - #entry.attachments)
    records[model] = nil
end

-- BEGIN_NATIVE_MOTION_PENDING_REPLAY (test exact lines in native Luau)
local function replayPendingHit(entry, id, now)
    local pending = id and pendingHits[id]
    if not pending then return false end
    pendingHits[id] = nil
    -- The authentic hit timestamp determines the remaining pose lifetime.
    if now - pending.at >= .7 then return false end
    entry.hitAt = pending.at
    if pending.ko then entry.koAt = pending.at end
    return true
end
-- END_NATIVE_MOTION_PENDING_REPLAY

local function tryEquip(model)
    if not isRunning or records[model] or not isMinion(model) then return false end
    if model:GetAttribute("P0D_ART_MINION_V1") ~= true then return false end
    local kind = typeOf(model)
    local core = model:FindFirstChild("Core")
    if not kind or not core or not core:IsA("BasePart") then return false end
    local count = 0
    for _ in pairs(records) do count += 1 end
    if count >= MAX_MODELS then return false end

    local originals = {}
    for _,name in ipairs(watchedParts[kind]) do
        local art = model:FindFirstChild(name)
        if art and art:IsA("BasePart") and art:GetAttribute(FEATURE) ~= true then
            table.insert(originals, {original=art, name=name})
        end
    end
    -- The author marks a model before all accessories are fully replicated.
    if #originals ~= #watchedParts[kind]
        or activeParts + #originals > MAX_ACTIVE_COSMETIC_PARTS then return false end
    local attachments = {}
    for _,visual in ipairs(originals) do
        local source = visual.original
        local copy = source:Clone()
        copy.Name = "LOCAL_" .. source.Name
        copy.Anchored = true
        copy.CanCollide = false
        copy.CanTouch = false
        copy.CanQuery = false
        copy.Massless = true
        copy.LocalTransparencyModifier = 0
        copy.Parent = localArt
        table.insert(attachments, {
            original=source, copy=copy, name=visual.name,
            initialModifier=source.LocalTransparencyModifier,
            offset=core.CFrame:ToObjectSpace(source.CFrame),
        })
    end
    records[model] = {
        core=core, model=model, kind=kind, attachments=attachments,
        prevPos=core.Position, speed=0, hitAt=-100, koAt=-100,
        phase=(count * 1.19) + (#model.Name * .17),
    }
    local id = if kind == "ELITE" then 9 else tonumber(model.Name:match("(%d+)$"))
    replayPendingHit(records[model], id, os.clock())
    activeParts += #attachments
    -- IMPORTANT: each anchored server ART_ piece remains at spawn while its
    -- Core moves. Hide ALL original body pieces immediately on full equip;
    -- re-showing any of them draws a frozen ghost / armour in midair.
    for _,visual in ipairs(attachments) do
        if visual.original.Parent then
            visual.original.LocalTransparencyModifier = 1
        end
    end
    return true
end

local function watch(model)
    -- task.defer(watch, model) may run AFTER script.Destroying. Never lease
    -- new listeners once teardown begins.
    if not isRunning or not isMinion(model) or connected[model] then return end
    local leases = {}
    connected[model] = leases
    -- #374 marks the model BEFORE creating art children. ChildAdded retries
    -- ensure this observer does not race the visual model's construction.
    local function attempt()
        if not isRunning or not model.Parent then return end
        if tryEquip(model) then
            for _,c in ipairs(leases) do c:Disconnect() end
            connected[model] = nil
        end
    end
    table.insert(leases,model:GetAttributeChangedSignal("P0D_ART_MINION_V1"):Connect(attempt))
    table.insert(leases,model.ChildAdded:Connect(function(child)
        if child.Name:sub(1,4) == "ART_" then task.defer(attempt) end
    end))
    table.insert(leases,model.Destroying:Connect(function()
        for _,c in ipairs(leases) do c:Disconnect() end
        connected[model] = nil
        drop(model)
    end))
    task.defer(attempt)
end

local function movementFor(kind, name, speed, t, hitAge, koAge)
    local walking = math.clamp(speed / 12, 0, 1)
    local step = math.sin(t * (3.0 + walking * 6.0))
    local breathe = math.sin(t * 2.3) * (1 - walking * .45)
    local hit = if hitAge >= 0 and hitAge < .27 then (1 - hitAge / .27) else 0
    local dying = if koAge >= 0 and koAge < .7 then (koAge / .7) else 0
    local sway = .04 * breathe + .12 * walking * step
    local tilt = -.26 * hit + .45 * dying
    if kind == "KNIGHT" then
        if name:find("SPEAR",1,true) then
            return CFrame.new(0,.06*step,0)*CFrame.Angles(sway+tilt,0,-.08*walking*step)
        elseif name:find("SHIELD",1,true) then
            return CFrame.Angles(.06*walking*step - .16*hit,0,.06*breathe)
        end
        return CFrame.Angles(-.1*walking*step+tilt,0,.08*step)
    elseif kind == "WRAITH" then
        if name:find("ORB",1,true) then
            return CFrame.new(0,.19*math.sin(t*2.7),-.12*walking*step)
        end
        return CFrame.new(0,.11*math.sin(t*2.7),0)*CFrame.Angles(.06*step+tilt,0,.1*breathe)
    elseif kind == "BRUTE" then
        if name:find("MAUL",1,true) then
            return CFrame.Angles(.16*walking*step - .22*hit + tilt,0,.05*step)
        end
        return CFrame.Angles(.04*breathe+tilt,0,.08*step)
    else
        if name:find("GAUNTLET",1,true) then
            return CFrame.new(0,.04*walking*step,0)*CFrame.Angles(.08*step + tilt,0,0)
        end
        return CFrame.Angles(-.08*walking*step+tilt,0,.07*step)
    end
end

-- ChildAdded is registered before the first snapshot (no replication gap).
local added = horde.ChildAdded:Connect(function(child) task.defer(watch,child) end)
for _,child in ipairs(horde:GetChildren()) do task.defer(watch,child) end

-- Reuse the same original server-confirmed hit event as #381's slash.
-- It sends one delivery per actual attack, even during an active damage popup.
-- BEGIN_NATIVE_MOTION_CONFIRMED_HIT (exact runtime policy under native QA)
local function applyConfirmedHit(id, isKO, serial, round, epoch, now, findEntry)
    if type(id) ~= "number" or id%1 ~= 0 or id < 1 or id > 9
        or type(serial) ~= "number" or serial%1 ~= 0 or serial < 1
        or type(round) ~= "number" or round%1 ~= 0
        or type(epoch) ~= "number" or epoch%1 ~= 0 or epoch < 1
        or type(isKO) ~= "boolean" then return false end
    if lastEpoch ~= epoch then
        -- New match epoch is strictly monotonic; round numbers may reset.
        if lastEpoch ~= nil and epoch < lastEpoch then return false end
        lastEpoch = epoch
        lastRound = round
        table.clear(lastHitSerial)
        table.clear(pendingHits)
    elseif lastRound ~= round then
        return false
    end
    if serial <= (lastHitSerial[id] or 0) then return false end
    lastHitSerial[id] = serial
    local entry = findEntry(id)
    if not entry then
        -- Queued actual server hit, never locally predicted damage.
        pendingHits[id] = {at=now, ko=isKO}
        return true
    end
    pendingHits[id] = nil
    entry.hitAt = now
    if isKO then entry.koAt = now end
    return true
end
-- END_NATIVE_MOTION_CONFIRMED_HIT

local cue = horde:WaitForChild("P0D_ART_COMBAT_SIGNAL_V1")
local cueConnection
local historyConnection
local epochConnection

local function findEntryById(targetId)
    local targetName = if targetId == 9 then "MUSOU_ELITE_TELEGRAPH"
        else "MUSOU_MINION_" .. tostring(targetId)
    local model = horde:FindFirstChild(targetName)
    return model and records[model]
end

local function onConfirmedHit(id, isKO, serial, round, epoch, hitAt)
    if not isRunning or not cue:IsA("RemoteEvent") then return end
    local serverEpoch = cue:GetAttribute("P0D_ART_EPOCH_V1")
    if type(serverEpoch) == "number" and epoch < serverEpoch then return end
    applyConfirmedHit(id, isKO, serial, round, epoch, hitAt, findEntryById)
end

-- #387's ORIGINAL Horde stores its most recent 12 server-confirmed events
-- for up to 2.5 seconds. Use those snapshots to bridge startup gaps before
-- this LocalScript's OnClientEvent listener was attached. Replayed poses use
-- the original hit time, never a new/delayed fictitious damage event.
local function replayRecent()
    if not isRunning then return end
    local encoded = cue:GetAttribute("P0D_ART_RECENT_V1")
    if type(encoded) ~= "string" or #encoded > 4096 then return end
    local ok, list = pcall(function() return HttpService:JSONDecode(encoded) end)
    if not ok or type(list) ~= "table" or #list > 12 then return end
    local serverNow = Workspace:GetServerTimeNow()
    local localNow = os.clock()
    for _,hit in ipairs(list) do
        if type(hit) == "table" and #hit == 12 then
            local id, isKO, serial, round, epoch, stamp =
                hit[1], hit[8], hit[9], hit[10], hit[11], hit[12]
            if type(stamp) == "number" and stamp == stamp
                and type(epoch) == "number" and epoch%1 == 0 then
                local age = serverNow - stamp
                if age >= -.25 and age <= .7 then
                    onConfirmedHit(id, isKO, serial, round, epoch,
                        localNow - math.max(0,age))
                end
            end
        end
    end
end

local function syncServerEpoch()
    if not isRunning then return end
    local epoch = cue:GetAttribute("P0D_ART_EPOCH_V1")
    if type(epoch) ~= "number" or epoch%1 ~= 0 or epoch < 1 then return end
    if lastEpoch == nil or epoch > lastEpoch then
        lastEpoch = epoch
        lastRound = nil
        table.clear(lastHitSerial)
        table.clear(pendingHits)
    end
    replayRecent()
end

if cue:IsA("RemoteEvent") then
    -- Register live first. Concurrent snapshot updates are deduped by
    -- (epoch,mob,serial) under the actual native-tested motion policy.
    cueConnection = cue.OnClientEvent:Connect(
        function(id, hitPos, fromPos, isKO, serial, round, epoch)
            onConfirmedHit(id, isKO, serial, round, epoch, os.clock())
        end)
    historyConnection = cue:GetAttributeChangedSignal("P0D_ART_RECENT_V1")
        :Connect(replayRecent)
    epochConnection = cue:GetAttributeChangedSignal("P0D_ART_EPOCH_V1")
        :Connect(syncServerEpoch)
    syncServerEpoch()
end

local pulse
pulse = RunService.Heartbeat:Connect(function(dt)
    if not isRunning then return end
    if not horde.Parent then
        -- Match the original Horde's teardown semantics. Do not leave a
        -- live client animation loop running after world destruction.
        isRunning = false
        added:Disconnect()
        if pulse then pulse:Disconnect() end
        for _,leases in pairs(connected) do
            for _,connection in ipairs(leases) do connection:Disconnect() end
        end
        table.clear(connected)
        table.clear(lastHitSerial)
        table.clear(pendingHits)
        for model in pairs(records) do drop(model) end
        if cueConnection then cueConnection:Disconnect() end
        if historyConnection then historyConnection:Disconnect() end
        if epochConnection then epochConnection:Disconnect() end
        if localArt.Parent then localArt:Destroy() end
        return
    end
    if dt <= 0 or dt > .5 then return end
    elapsed += dt
    if elapsed < ANIM_STEP then return end
    local stepDt = elapsed
    elapsed = 0
    local character = localPlayer.Character
    local root = character and character:FindFirstChild("HumanoidRootPart")
    local now = os.clock()
    for model,entry in pairs(records) do
        local core = entry.core
        if not model.Parent or not core.Parent then
            drop(model)
        else
            local delta = core.Position - entry.prevPos
            entry.prevPos = core.Position
            entry.speed = (entry.speed * .7) + (.3 * (delta.Magnitude / stepDt))
            if root and root:IsA("BasePart")
                and (root.Position-core.Position).Magnitude <= VIEW_RANGE_STUDS then
                local t = now + entry.phase
                for _,visual in ipairs(entry.attachments) do
                    if visual.copy.Parent and visual.original.Parent then
                        visual.original.LocalTransparencyModifier = 1
                        local localMotion = movementFor(entry.kind, visual.name,
                            entry.speed, t, now-entry.hitAt, now-entry.koAt)
                        visual.copy.Transparency = visual.original.Transparency
                        -- Never move a replicated server part on the client.
                        visual.copy.CFrame = core.CFrame * visual.offset * localMotion
                    end
                end
            else
                -- LOD: never redisplay anchored originals at their old spawn
                -- position; only hide cosmetic copies when off-screen.
                for _,visual in ipairs(entry.attachments) do
                    if visual.original.Parent then
                        visual.original.LocalTransparencyModifier = 1
                    end
                    if visual.copy.Parent then visual.copy.Transparency = 1 end
                end
            end
        end
    end
end)

script.Destroying:Connect(function()
    isRunning = false
    added:Disconnect()
    pulse:Disconnect()
    for _,leases in pairs(connected) do
        for _,c in ipairs(leases) do c:Disconnect() end
    end
    table.clear(connected)
    table.clear(lastHitSerial)
    table.clear(pendingHits)
    for model in pairs(records) do drop(model) end
    if cueConnection then cueConnection:Disconnect() end
    if historyConnection then historyConnection:Disconnect() end
    if epochConnection then epochConnection:Disconnect() end
    if localArt.Parent then localArt:Destroy() end
end)
print("ART_MOTION_SOURCE_WIP_CLIENT_COSMETIC_ONLY_NOT_STUDIO_VERIFIED")
