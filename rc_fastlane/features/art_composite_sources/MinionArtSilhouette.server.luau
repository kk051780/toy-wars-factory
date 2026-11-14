--!nocheck
-- #372 ART-MINION / FB-008+012+015: 3 recognizable neutral enemy silhouettes
-- and one elite plus restrained hit/death reactions, attached to ORIGINAL Horde.
-- No new Game, spawn, damage, score, XP, Remote, AI or hitbox authority.
local RunService = game:GetService("RunService")
if not RunService:IsStudio() then return end

local arena = workspace:WaitForChild("TRAP_RAIDERS_S1", 45)
if not arena then warn("ART_MINION_NO_ARENA"); return end
local mobsFolder = arena:WaitForChild("EGG_RUMBLE_NEUTRAL_MUSOU_EXPERIMENT", 45)
if not mobsFolder then warn("ART_MINION_NO_ORIGINAL_HORDE"); return end

local equipped = {}
local function rgb(r,g,b) return Color3.fromRGB(r,g,b) end
local function piece(model, core, name, size, offset, color, material, shape, alpha, yaw)
    local item = if shape == "wedge" then Instance.new("WedgePart") else Instance.new("Part")
    item.Name = "ART_" .. name
    item.Size = size
    item.CFrame = core.CFrame * CFrame.new(offset)
        * CFrame.Angles(0, math.rad(yaw or 0), 0)
    item.Color = color
    item.Material = material
    item.Transparency = alpha or 0
    -- Original server Horde moves the entire model via Model:PivotTo.
    -- Keep this decorative Part anchored and in the same Model, so its
    -- original silhouette follows PivotTo with NO welded physics assembly.
    item.Anchored = true
    item.CanCollide = false
    item.CanTouch = false
    item.CanQuery = false
    item.CastShadow = false
    if item:IsA("Part") then
        if shape == "ball" then item.Shape = Enum.PartType.Ball
        elseif shape == "cylinder" then item.Shape = Enum.PartType.Cylinder end
    end
    item.Parent = model
    return item
end

local function knight(model, core)
    local blue=rgb(72,132,182)
    local steel=rgb(188,211,222)
    local gold=rgb(241,197,101)
    piece(model,core,"KNIGHT_CHEST",Vector3.new(2.8,2.2,2.25),
        Vector3.new(0,.15,0),blue,Enum.Material.Metal)
    piece(model,core,"KNIGHT_HELMET",Vector3.new(2.35,1.28,2.4),
        Vector3.new(0,4.05,0),steel,Enum.Material.Metal)
    piece(model,core,"KNIGHT_CREST",Vector3.new(.55,1.35,2.0),
        Vector3.new(0,4.85,0),gold,Enum.Material.SmoothPlastic,"wedge")
    for _,side in ipairs({-1,1}) do
        piece(model,core,"KNIGHT_PAULDRON_"..side,Vector3.new(1.24,1.1,1.5),
            Vector3.new(side*1.72,1.14,0),steel,Enum.Material.Metal)
    end
    piece(model,core,"KNIGHT_SHIELD",Vector3.new(.32,1.85,1.52),
        Vector3.new(-2.05,-.10,-.9),blue,Enum.Material.Metal)
    piece(model,core,"KNIGHT_SHIELD_MARK",Vector3.new(.38,.64,.65),
        Vector3.new(-2.26,-.1,-.9),gold,Enum.Material.Neon)
    piece(model,core,"KNIGHT_SPEAR_SHAFT",Vector3.new(.22,4.3,.22),
        Vector3.new(2.19,.6,-.9),gold,Enum.Material.Wood)
    piece(model,core,"KNIGHT_SPEAR_TIP",Vector3.new(.65,1.55,.65),
        Vector3.new(2.19,3.10,-.9),steel,Enum.Material.Metal,"wedge")
    return piece(model,core,"KNIGHT_CAPE",Vector3.new(1.7,2.7,.26),
        Vector3.new(0,-.15,1.25),blue,Enum.Material.Fabric,nil,.07)
end

local function wraith(model, core)
    local lavender=rgb(147,117,211)
    local dark=rgb(47,43,92)
    local glow=rgb(116,233,235)
    piece(model,core,"WRAITH_HOOD",Vector3.new(2.7,2.35,2.5),
        Vector3.new(0,3.66,0),dark,Enum.Material.Fabric)
    piece(model,core,"WRAITH_COWL",Vector3.new(2.45,1.0,2.55),
        Vector3.new(0,4.77,0),lavender,Enum.Material.Fabric,"wedge")
    piece(model,core,"WRAITH_FACE_VEIL",Vector3.new(1.54,1.42,.22),
        Vector3.new(0,3.30,-1.30),rgb(31,45,80),Enum.Material.SmoothPlastic,nil,.06)
    for _,side in ipairs({-1,1}) do
        piece(model,core,"WRAITH_CRYSTAL_EYE_"..side,Vector3.new(.4,.45,.19),
            Vector3.new(side*.5,3.54,-1.44),glow,Enum.Material.Neon)
        piece(model,core,"WRAITH_SHOULDER_FIN_"..side,Vector3.new(.8,2.2,1.3),
            Vector3.new(side*1.52,1.45,.25),lavender,Enum.Material.Glass,"wedge",.15)
    end
    piece(model,core,"WRAITH_CHEST_SIGIL",Vector3.new(.9,1.15,.15),
        Vector3.new(0,.40,-1.3),glow,Enum.Material.Neon,nil,.12)
    piece(model,core,"WRAITH_ORB",Vector3.new(1.1,1.1,1.1),
        Vector3.new(2.0,.75,-1.3),glow,Enum.Material.Glass,"ball",.22)
    return piece(model,core,"WRAITH_SHROUD",Vector3.new(2.4,3.2,.3),
        Vector3.new(0,-.45,1.36),dark,Enum.Material.Fabric,nil,.22)
end

local function brute(model, core)
    local rust=rgb(162,90,57)
    local ochre=rgb(197,141,74)
    local bone=rgb(239,224,183)
    piece(model,core,"BRUTE_CHEST_PLATE",Vector3.new(3.0,2.15,2.2),
        Vector3.new(0,.30,0),rust,Enum.Material.Slate)
    piece(model,core,"BRUTE_JAW",Vector3.new(1.65,.68,1.05),
        Vector3.new(0,2.35,-1.13),ochre,Enum.Material.Slate)
    for _,side in ipairs({-1,1}) do
        piece(model,core,"BRUTE_TUSK_"..side,Vector3.new(.4,1.25,.45),
            Vector3.new(side*.94,2.85,-1.23),bone,Enum.Material.SmoothPlastic,"wedge")
        piece(model,core,"BRUTE_HORN_"..side,Vector3.new(1.02,1.45,.9),
            Vector3.new(side*1.16,4.13,.35),bone,Enum.Material.SmoothPlastic,"wedge",0,side*26)
        piece(model,core,"BRUTE_SHOULDER_"..side,Vector3.new(1.58,1.7,1.4),
            Vector3.new(side*1.62,1.0,.32),ochre,Enum.Material.Rock)
    end
    piece(model,core,"BRUTE_MAUL_HANDLE",Vector3.new(.25,3.2,.25),
        Vector3.new(2.2,.25,-.8),bone,Enum.Material.Wood)
    piece(model,core,"BRUTE_MAUL_HEAD",Vector3.new(1.65,1.0,1.3),
        Vector3.new(2.2,2.0,-.8),rust,Enum.Material.Metal)
    return piece(model,core,"BRUTE_BACK_FUR",Vector3.new(2.7,2.3,.55),
        Vector3.new(0,.1,1.35),ochre,Enum.Material.Fabric,nil,.18)
end

local function elite(model, core)
    local iron=rgb(72,61,91)
    local gold=rgb(247,189,86)
    piece(model,core,"ELITE_CHEST_ARMOUR",Vector3.new(4.7,3.5,3.55),
        Vector3.new(0,.55,0),iron,Enum.Material.Metal)
    piece(model,core,"ELITE_MASK",Vector3.new(3.3,2.0,2.9),
        Vector3.new(0,4.5,0),gold,Enum.Material.Metal)
    for _,side in ipairs({-1,1}) do
        piece(model,core,"ELITE_CURVED_HORN_"..side,Vector3.new(1.2,2.65,1.1),
            Vector3.new(side*1.58,6.05,.35),iron,Enum.Material.Slate,"wedge",0,side*33)
        piece(model,core,"ELITE_SHOULDER_SPIKE_"..side,Vector3.new(1.8,2.8,1.3),
            Vector3.new(side*3.1,2.15,.25),gold,Enum.Material.Metal,"wedge")
        piece(model,core,"ELITE_GAUNTLET_"..side,Vector3.new(1.25,2.3,1.1),
            Vector3.new(side*3.25,-.4,-.25),iron,Enum.Material.Metal)
    end
    piece(model,core,"ELITE_BACK_BANNER",Vector3.new(2.1,4.8,.35),
        Vector3.new(0,-.25,1.95),rgb(152,64,150),Enum.Material.Fabric)
    return piece(model,core,"ELITE_WAR_CORE",Vector3.new(1.25,1.45,.3),
        Vector3.new(0,1.02,-1.96),gold,Enum.Material.Neon)
end

-- Shared, reusable slash geometry. The original Horde is the only damage
-- authority: these 2 Beams per NPC never create hitboxes, Remotes or KO.
-- Build once per NPC (8 normal and 1 elite); just enable briefly on a real
-- server-owned yellow hit flash. Crossed curves read as an impact slash at
-- third-person camera distance without large overhead labels.
local function makeSlashArcs(core, accent, isElite)
    local scale = if isElite then 1.42 else 1
    local arcs = {}
    for i = 1, 2 do
        local a = Instance.new("Attachment")
        a.Name = "ART_SLASH_START_" .. i
        a.Position = Vector3.new(-2.0*scale, if i==1 then 1.2 else -.45, -1.85*scale)
        a.Parent = core
        local z = Instance.new("Attachment")
        z.Name = "ART_SLASH_END_" .. i
        z.Position = Vector3.new(2.0*scale, if i==1 then -.55 else 1.5, -1.85*scale)
        z.Parent = core
        local beam = Instance.new("Beam")
        beam.Name = "ART_SERVER_HIT_SLASH_" .. i
        beam.Attachment0 = a
        beam.Attachment1 = z
        beam.Segments = 12
        beam.CurveSize0 = if i==1 then 1.4*scale else -1.3*scale
        beam.CurveSize1 = if i==1 then -1.4*scale else 1.3*scale
        beam.Width0 = 0.62*scale
        beam.Width1 = 0.11*scale
        beam.Color = ColorSequence.new(accent)
        beam.Transparency = NumberSequence.new({
            NumberSequenceKeypoint.new(0,.88),
            NumberSequenceKeypoint.new(.23,.08),
            NumberSequenceKeypoint.new(.74,.25),
            NumberSequenceKeypoint.new(1,1),
        })
        beam.LightEmission = .7
        beam.FaceCamera = true
        beam.Enabled = false
        beam.Parent = core
        table.insert(arcs,beam)
    end
    return arcs
end

-- Directly observe the original Horde's replicated damage cues. Polling
-- only every .14s can miss its .18s flash, or combine consecutive hits into
-- one flash. CombatCue HP text is updated by the server for EVERY true hit;
-- exact yellow Core is an independent fallback, not a damage authority.
local function isOriginalGold(c)
    return c.R > .96 and c.G > .85 and c.B > .35 and c.B < .58
end
local function fireHitVisual(item)
    local now = os.clock()
    if now-item.lastImpactAt < .06 then return end
    local previousGap = now-item.lastImpactAt
    item.streak = if previousGap < 1.25 then math.min(item.streak+1,5) else 1
    item.lastImpactAt = now
    item.recoilUntil = now+.19
    item.sparks:Emit(7+item.streak)
    item.slashStart = now
    item.slashWidth = item.baseSlashWidth*(1+.055*(item.streak-1))
    for _,arc in ipairs(item.slashes) do
        arc.Color = ColorSequence.new(item.slashColor)
        arc.Enabled = true
    end
end
local function fireKOCosmetic(item)
    if item.lastDeath then return end
    item.lastDeath = true
    item.sparks:Emit(22)
    item.slashStart = os.clock()
    item.koUntil = item.slashStart+.62
    for _,arc in ipairs(item.slashes) do
        arc.Color = ColorSequence.new(rgb(255,192,111))
        arc.Enabled = true
    end
end
local function originalHPText(s)
    return s:match("^中立 %d+/%d+$") ~= nil
        or s:match("^精鋭 %d+/%d+$") ~= nil
end
local function clearVisualSignals(item)
    for _,connection in ipairs(item.connections) do
        connection:Disconnect()
    end
    table.clear(item.connections)
end

local function decorate(model)
    if not model or not model:IsA("Model") or not model.Parent then return end
    if model:GetAttribute("P0D_ART_MINION_V1") == true then return end
    local numeric = tonumber(model.Name:match("^MUSOU_MINION_(%d+)$"))
    local isElite = model.Name == "MUSOU_ELITE_TELEGRAPH"
    if not isElite and not numeric then return end
    local core = model:FindFirstChild("Core")
    local head = model:FindFirstChild("Head")
    if not core or not core:IsA("BasePart") or not head or not head:IsA("BasePart")
        or not model.PrimaryPart then return end
    -- Mark before creating children to avoid duplicate asynchronous callbacks.
    model:SetAttribute("P0D_ART_MINION_V1", true)
    model:SetAttribute("P0D_ART_MINION_SWAY_VISUAL", true)
    local typeId = if isElite then 4 else ((numeric-1)%3)+1
    local accent = if typeId==1 then rgb(84,179,224)
        elseif typeId==2 then rgb(114,226,231)
        elseif typeId==3 then rgb(242,166,91)
        else rgb(255,196,96)
    local moving = if typeId==1 then knight(model,core)
        elseif typeId==2 then wraith(model,core)
        elseif typeId==3 then brute(model,core)
        else elite(model,core)

    -- Existing server Horde remains sole hit/HP/KO authority. One emitter per
    -- original Core is silent until an observed author-owned damage/KO cue.
    local sparks = Instance.new("ParticleEmitter")
    sparks.Name = "ART_HIT_FEEDBACK"
    sparks.Rate = 0
    sparks.Lifetime = NumberRange.new(.22,.42)
    sparks.Speed = NumberRange.new(3,7)
    sparks.SpreadAngle = Vector2.new(48,48)
    sparks.Size = NumberSequence.new({
        NumberSequenceKeypoint.new(0,.56),
        NumberSequenceKeypoint.new(1,0),
    })
    sparks.Drag = 9
    sparks.LightEmission = .75
    sparks.Color = ColorSequence.new(accent)
    sparks.Enabled = true
    sparks.Parent = core
    local slashes = makeSlashArcs(core,accent,isElite)

    for _,item in ipairs(core:GetChildren()) do
        if item:IsA("BillboardGui") and item.Name == "CombatCue" then
            item.Size = UDim2.fromOffset(80,26)
            item.MaxDistance = 27
            item.AlwaysOnTop = false
        elseif item:IsA("BillboardGui") and item.Name == "RealDamagePopup" then
            item.MaxDistance = 44
        end
    end
    local entry={
        model=model, core=core, moving=moving, sparks=sparks,
        slashes=slashes, slashStart=-100, slashColor=accent,
        baseSlashWidth=if isElite then .90 else .64,
        slashWidth=if isElite then .90 else .64,
        -- Cache once in model-space; never drift against server-owned Core.
        movingRelative=core.CFrame:ToObjectSpace(moving.CFrame),
        typeId=typeId, lastHit=false, lastDeath=false, id=numeric or 9,
        lastImpactAt=-100, recoilUntil=-100, koUntil=-100, streak=0,
        connections={},
    }
    -- Server cue updates on every non-lethal hit as HP decreases, even when
    -- two attacks deal equal damage while Color is still gold.
    local cueGui=core:FindFirstChild("CombatCue")
    local cueText=if cueGui and cueGui:IsA("BillboardGui")
        then cueGui:FindFirstChildOfClass("TextLabel") else nil
    if cueText then
        table.insert(entry.connections,cueText:GetPropertyChangedSignal("Text"):Connect(function()
            if not model.Parent then return end
            local value=cueText.Text
            if originalHPText(value) then
                fireHitVisual(entry)
            elseif string.find(value,"撃破",1,true) then
                fireHitVisual(entry)
                fireKOCosmetic(entry)
            end
        end))
    end
    -- Core Color can change at a different moment than cue replication.
    -- 60ms deduplication prevents two visual bursts for one server hit.
    table.insert(entry.connections,core:GetPropertyChangedSignal("Color"):Connect(function()
        if model.Parent and isOriginalGold(core.Color) then
            fireHitVisual(entry)
        end
    end))
    table.insert(equipped,entry)
end

-- Horde.reset destroys and recreates its nine Models each round; attaching
-- only once at startup would silently regress after the first match.
for _,model in ipairs(mobsFolder:GetChildren()) do
    task.defer(decorate,model)
end
local added = mobsFolder.ChildAdded:Connect(function(child)
    task.defer(decorate,child)
end)
local heartbeatAcc = 0
local cycle = 0
local alive = true
local heart
heart = RunService.Heartbeat:Connect(function(dt)
    if not alive then return end
    if not mobsFolder.Parent then
        alive = false
        added:Disconnect()
        if heart then heart:Disconnect() end
        return
    end
    if dt<=0 or dt>.5 then return end
    heartbeatAcc += dt
    if heartbeatAcc < .14 then return end
    heartbeatAcc = 0
    cycle += .14
    for i=#equipped,1,-1 do
        local item = equipped[i]
        if not item.model.Parent or not item.moving.Parent then
            clearVisualSignals(item)
            table.remove(equipped,i)
        else
            -- Tiny cosmetic breathing/cloak motion; never touches author arms,
            -- original NPC movement or server hit/score logic.
            local sway = math.sin(cycle * 2.8 + item.id * .73)
            local flutter = math.sin(cycle * 4.2 + item.id * .37)
            -- One subtle cloak/fur/core motion per NPC; not a hitbox or
            -- animation override for Core, server arms, or Head.
            -- Recoil and KO affect only the animated costume, not Core,
            -- the server hitbox, knockback, movement or physics ownership.
            local now=os.clock()
            local recoil=math.clamp((item.recoilUntil-now)/.19,0,1)
            local ko=math.clamp((item.koUntil-now)/.62,0,1)
            item.moving.CFrame = item.core.CFrame * item.movingRelative
                * CFrame.new(0,-.12*ko,.18*recoil)
                * CFrame.Angles(sway*.10+ko*.22,flutter*.055,
                    sway*.085+recoil*.23+ko*.28)
            item.moving.Transparency = .10 + .08*(.5+.5*math.sin(cycle*3+item.id))
            -- Low-rate fallback; source-owned property listeners above give
            -- responsive cues even when a flash ends between Heartbeats.
            local flashing = isOriginalGold(item.core.Color)
            if flashing and not item.lastHit then
                fireHitVisual(item)
            end
            item.lastHit = flashing
            local cue = item.core:FindFirstChild("CombatCue")
            local tag = if cue and cue:IsA("BillboardGui")
                then cue:FindFirstChildOfClass("TextLabel") else nil
            local dead=tag ~= nil and string.find(tag.Text,"撃破",1,true) ~= nil
            if dead then
                fireKOCosmetic(item)
            else
                item.lastDeath = false
            end
            -- Fade without Tweens or per-hit Instances. The same two reusable
            -- arcs and one emitter are the *entire* added effect budget.
            local remain = 1 - (os.clock()-item.slashStart)/.36
            for _,arc in ipairs(item.slashes) do
                if remain <= 0 then
                    arc.Enabled = false
                else
                    arc.Width0 = item.slashWidth * remain
                    arc.Width1 = .11 * remain
                end
            end
        end
    end
end)
script.Destroying:Connect(function()
    alive = false
    added:Disconnect()
    if heart then heart:Disconnect() end
    for _,item in ipairs(equipped) do clearVisualSignals(item) end
end)
print("ART_MINION_V3_DIRECT_ORIGINAL_HIT_CUES_VISUAL_ONLY_STUDIO_FUN_PENDING")
