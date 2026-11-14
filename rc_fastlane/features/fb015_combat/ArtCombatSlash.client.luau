--!nocheck
-- FB-008 / FB-015 ART-COMBAT: server-CONFIRMED neutral hits -> short
-- original client-local slash arcs. Pure appearance, never hit authority.
-- This private candidate is intentionally Studio-only pending OWNER visual QA.
local RunService = game:GetService("RunService")
if not RunService:IsStudio() then return end

local Players = game:GetService("Players")
local Debris = game:GetService("Debris")
local TweenService = game:GetService("TweenService")
local HttpService = game:GetService("HttpService")
local UserInputService = game:GetService("UserInputService")
local localPlayer = Players.LocalPlayer
if not localPlayer then return end

-- Studio-only private visual cue from server: reliable per-hit deliveries.
local arena = workspace:WaitForChild("TRAP_RAIDERS_S1")
local mobs = arena:WaitForChild("EGG_RUMBLE_NEUTRAL_MUSOU_EXPERIMENT")

local FEATURE = "ART_COMBAT_SLASH_READONLY_V1"
local MAX_LIVE = 8
local MAX_BURSTS_PER_SECOND = 9
local live = 0
local times = {}
local function makeArc(hitPos, toward, isKO)
    if live >= MAX_LIVE then return end
    local dx = Vector3.new(toward.X - hitPos.X, 0, toward.Z - hitPos.Z)
    if dx.Magnitude < .1 then dx = Vector3.new(0, 0, -1) end
    local holder = Instance.new("Part")
    holder.Name = "P0D_ART_COMBAT_SLASH_FX"
    holder.Anchored = true
    holder.Size = Vector3.new(.12, .12, .12)
    holder.Transparency = 1
    holder.CanCollide = false
    holder.CanTouch = false
    holder.CanQuery = false
    holder.CastShadow = false
    holder.CFrame = CFrame.lookAt(hitPos + Vector3.new(0, 1.35, 0), hitPos + dx)
    holder.Parent = workspace
    live += 1
    holder.Destroying:Connect(function() live = math.max(0, live - 1) end)

    local count = if UserInputService.TouchEnabled then 1 else 2
    local extent = if isKO then 3.2 else 2.25
    for i = 1, count do
        local a = Instance.new("Attachment")
        a.Name = "FX_START_" .. i
        a.Position = Vector3.new(-extent, (i - 1) * .24, -.25)
        a.Parent = holder
        local b = Instance.new("Attachment")
        b.Name = "FX_END_" .. i
        b.Position = Vector3.new(extent, .35 + (i - 1) * .3, -.25)
        b.Parent = holder
        local beam = Instance.new("Beam")
        beam.Name = "P0D_SERVER_HIT_CONFIRMED_ARC"
        beam.Attachment0 = a
        beam.Attachment1 = b
        beam.Segments = 10
        beam.CurveSize0 = if i == 1 then 2.7 else -2.1
        beam.CurveSize1 = if i == 1 then -2.0 else 1.8
        beam.Width0 = if isKO then .48 else .32
        beam.Width1 = .11
        beam.FaceCamera = true
        beam.LightEmission = .7
        beam.Color = if isKO
            then ColorSequence.new(Color3.fromRGB(255, 186, 63), Color3.fromRGB(255, 246, 207))
            else ColorSequence.new(Color3.fromRGB(139, 235, 255), Color3.fromRGB(255, 250, 210))
        beam.Transparency = NumberSequence.new({
            NumberSequenceKeypoint.new(0, .12),
            NumberSequenceKeypoint.new(.55, .04),
            NumberSequenceKeypoint.new(1, 1),
        })
        beam.Parent = holder
    end
    -- Sparks are authored locally: server ParticleEmitter:Emit is not
    -- reliable visual replication across Roblox clients.
    local sparks=Instance.new("ParticleEmitter")
    sparks.Name="P0D_CLIENT_CONFIRMED_HIT_SPARKS"
    sparks.Rate=0
    sparks.Lifetime=NumberRange.new(.16,.32)
    sparks.Speed=NumberRange.new(3,7)
    sparks.Size=NumberSequence.new(.34)
    sparks.LightEmission=.8
    sparks.SpreadAngle=Vector2.new(65,65)
    sparks.Color=ColorSequence.new(
        if isKO then Color3.fromRGB(255,192,70)
        else Color3.fromRGB(116,231,255))
    sparks.Parent=holder
    sparks:Emit(if isKO then 10 else 4)
    TweenService:Create(holder, TweenInfo.new(.16, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
        CFrame = holder.CFrame * CFrame.Angles(0, 0, math.rad(if isKO then 52 else 32))
    }):Play()
    Debris:AddItem(holder, .22)
end

-- No local damage claims and NO creation of a client-to-server command.
-- A real single outbound RemoteEvent lives under the existing Musou folder.
-- Wait without an expiry: a slow Studio scene must not disable visual cues
-- forever when the server creates Horde after an artificial timeout.
local cue=mobs:WaitForChild("P0D_ART_COMBAT_SIGNAL_V1")
if not cue:IsA("RemoteEvent") then
    warn("ART_COMBAT_INVALID_CUE_VISUAL_OFF")
    return
end
local lastRound=nil
local lastEpoch=nil
local lastByMob={}
local destroyed=false
local visualConnection
local historyConnection
local epochConnection
local characterConnection
local rootConnection
local pending={}
local MAX_PENDING_CUES=16
local highestPacketEpoch=nil

-- BEGIN_ACTUAL_CUE_DEDUPE_POLICY (extracted and executed by native Luau)
local function acceptVisualCue(id,serial,round,epoch)
    if type(id)~="number" or id<1 or id>9 or id%1~=0
        or type(serial)~="number" or serial<1 or serial%1~=0
        or type(round)~="number" or round%1~=0
        or type(epoch)~="number" or epoch<1 or epoch%1~=0 then return false end
    if lastEpoch~=epoch then
        if lastEpoch~=nil and epoch<lastEpoch then return false end
        lastEpoch=epoch
        lastRound=round
        table.clear(lastByMob)
    elseif lastRound==nil then
        -- First hit after observing a new server epoch: accept its round.
        lastRound=round
    elseif lastRound~=round then
        return false
    end
    -- A live hit can overtake older snapshot cues. Keep a bounded set,
    -- not a single high-water mark that discards earlier unseen hits.
    local state=lastByMob[id]
    if not state then
        state={max=0,seen={}}
        lastByMob[id]=state
    end
    if state.seen[serial] or serial<=state.max-16 then return false end
    state.seen[serial]=true
    state.max=math.max(state.max,serial)
    -- Never forget a serial still inside the 16-serial acceptance window.
    -- Arrival-order eviction would let a delayed snapshot redraw it.
    for previous in pairs(state.seen) do
        if previous<=state.max-16 then state.seen[previous]=nil end
    end
    return true
end
local function isEpochStale(authoritativeEpoch,packetEpoch)
    -- Server RemoteEvent can arrive before its replicated epoch Attribute.
    -- Reject only OLD packets, never newer confirmed server-owned hits.
    return type(authoritativeEpoch)=="number"
        and type(packetEpoch)=="number"
        and packetEpoch<authoritativeEpoch
end
-- END_ACTUAL_CUE_DEDUPE_POLICY
-- BEGIN_ACTUAL_PENDING_EPOCH_POLICY
-- Pure epoch admission shared by live/queued/respawn processing.
local function admitPacketEpoch(epoch)
    if type(epoch)~="number" or epoch%1~=0 or epoch<1 then return false end
    if highestPacketEpoch~=nil and epoch<highestPacketEpoch then return false end
    if highestPacketEpoch==nil or epoch>highestPacketEpoch then
        highestPacketEpoch=epoch
        -- New match wins immediately. Never render old-round cues after a
        -- root arrives, even before its replicated epoch Attribute arrives.
        for i=#pending,1,-1 do
            if pending[i][7]<epoch then table.remove(pending,i) end
        end
    end
    return true
end
-- END_ACTUAL_PENDING_EPOCH_POLICY


local function onConfirmedHit(id,hitPos,fromPos,isKO,serial,round,epoch)
    if destroyed or typeof(hitPos)~="Vector3" or typeof(fromPos)~="Vector3"
        or type(isKO)~="boolean" then return end
    local authoritativeEpoch=cue:GetAttribute("P0D_ART_EPOCH_V1")
    if isEpochStale(authoritativeEpoch,epoch) then return end
    if not admitPacketEpoch(epoch) then return end
    local root=localPlayer.Character and localPlayer.Character:FindFirstChild("HumanoidRootPart")
    if not root then
        -- Preserve actual live packets while the character is respawning.
        -- Cap memory; server snapshots cover the newest 2.5 seconds as well.
        if #pending>=MAX_PENDING_CUES then
            table.remove(pending,1)
            warn("P0D_ART_PENDING_OVERFLOW_DROPPED_OLDEST_VISUAL_ONLY")
        end
        table.insert(pending,{id,hitPos,fromPos,isKO,serial,round,epoch,os.clock()})
        return
    end
    if (root.Position-hitPos).Magnitude>64 then return end
    local now=os.clock()
    while #times>0 and now-times[1]>=1 do table.remove(times,1) end
    if #times>=MAX_BURSTS_PER_SECOND or live>=MAX_LIVE then return end
    -- Commit dedupe only AFTER there is a root and render budget.
    if not acceptVisualCue(id,serial,round,epoch) then return end
    table.insert(times,now)
    makeArc(hitPos,fromPos,isKO)
end

-- Subscribe to the reliable live stream FIRST, then catch up from the
-- server's bounded history. A hit arriving in between is deduped by
-- (monotonic match epoch, mob id, per-mob serial).
local function replayRecent()
    if destroyed then return end
    local encoded=cue:GetAttribute("P0D_ART_RECENT_V1")
    if type(encoded)~="string" or #encoded>4096 then return end
    local ok,records=pcall(function() return HttpService:JSONDecode(encoded) end)
    if not ok or type(records)~="table" or #records>12 then return end
    local now=workspace:GetServerTimeNow()
    for _,v in ipairs(records) do
        if type(v)=="table" and #v==12 then
            local id,x,y,z,fx,fy,fz,isKO,serial,round,epoch,stamp=
                v[1],v[2],v[3],v[4],v[5],v[6],v[7],v[8],v[9],v[10],v[11],v[12]
            if type(x)=="number" and type(y)=="number" and type(z)=="number"
                and type(fx)=="number" and type(fy)=="number"
                and type(fz)=="number" and type(stamp)=="number"
                and stamp==stamp and now-stamp>=-1 and now-stamp<=2.5 then
                onConfirmedHit(id,Vector3.new(x,y,z),
                    Vector3.new(fx,fy,fz),isKO,serial,round,epoch)
            end
        end
    end
end

local function syncServerEpoch()
    local current=cue:GetAttribute("P0D_ART_EPOCH_V1")
    if type(current)~="number" or current<1 then return end
    if lastEpoch~=nil and current<=lastEpoch then return end
    lastEpoch=current
    lastRound=nil
    table.clear(lastByMob)
    -- Preserve queued cues for this epoch, discarding only stale matches.
    if highestPacketEpoch==nil or current>highestPacketEpoch then
        highestPacketEpoch=current
    end
    for i=#pending,1,-1 do
        if pending[i][7]<highestPacketEpoch then table.remove(pending,i) end
    end
    -- Attribute replication may deliver history before the new epoch.
    -- Retry it NOW even if the history Attribute never changes again.
    replayRecent()
end

local function drainPending()
    if destroyed then return end
    local queued=pending
    pending={}
    local now=os.clock()
    for _,hit in ipairs(queued) do
        if now-hit[8]<=2.5 then
            onConfirmedHit(hit[1],hit[2],hit[3],hit[4],hit[5],hit[6],hit[7])
        end
    end
    replayRecent()
end

-- Listener first, then current epoch and replay. Live/snapshot overlap
-- dedupes by exact per-mob event identity, including out-of-order arrivals.
visualConnection=cue.OnClientEvent:Connect(onConfirmedHit)
historyConnection=cue:GetAttributeChangedSignal("P0D_ART_RECENT_V1")
    :Connect(replayRecent)
epochConnection=cue:GetAttributeChangedSignal("P0D_ART_EPOCH_V1")
    :Connect(syncServerEpoch)
syncServerEpoch()
replayRecent()
local function watchCharacter(character)
    if rootConnection then rootConnection:Disconnect(); rootConnection=nil end
    local function onRoot(child)
        if child.Name~="HumanoidRootPart" then return end
        if rootConnection then rootConnection:Disconnect(); rootConnection=nil end
        if localPlayer.Character==character then drainPending() end
    end
    -- Listen FIRST then check, so a root inserted between operations is
    -- seen exactly once for both fresh and already-existing characters.
    rootConnection=character.ChildAdded:Connect(onRoot)
    local existing=character:FindFirstChild("HumanoidRootPart")
    if existing then onRoot(existing) end
end
characterConnection=localPlayer.CharacterAdded:Connect(watchCharacter)
if localPlayer.Character then watchCharacter(localPlayer.Character) end
script.Destroying:Connect(function()
    destroyed=true
    if visualConnection then visualConnection:Disconnect() end
    if historyConnection then historyConnection:Disconnect() end
    if epochConnection then epochConnection:Disconnect() end
    if characterConnection then characterConnection:Disconnect() end
    if rootConnection then rootConnection:Disconnect() end
    table.clear(lastByMob)
    table.clear(times)
    table.clear(pending)
    highestPacketEpoch=nil
end)
print(FEATURE.." _STUDIO_ONLY_CLIENT_SPARKS_EPOCH_PENDING_REPLAY")
