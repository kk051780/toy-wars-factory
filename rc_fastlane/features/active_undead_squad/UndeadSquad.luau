--!strict
-- FB026: three real moving, attacking undead companions; original Game keeps authority.
-- Must be invoked only after original Game's authorized NECROMANCER JOB_SKILL validation.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local M = {}
local squads: {[Player]: any} = {}
local COUNT = 3
local MAX_TICKS = 240 -- 48s @0.20s, strictly bounded
local MAX_DURATION = 48
local ATTACK_INTERVAL = 1.45
local LEASH = 15
local RANGE = 8.5

local function body(model: Model, name: string, size: Vector3, offset: Vector3,
        color: Color3, shape: Enum.PartType): BasePart
    local p = Instance.new("Part")
    p.Name = name
    p.Shape = shape
    p.Size = size
    p.CFrame = CFrame.new(offset)
    p.Color = color
    p.Material = Enum.Material.SmoothPlastic
    p.Anchored = true
    p.CanCollide = false
    p.CanTouch = false
    p.CanQuery = false
    p.CastShadow = false
    p.Parent = model
    return p
end

local function buildZombie(index: number, origin: Vector3, parent: Instance): Model
    local zombie = Instance.new("Model")
    zombie.Name = "P0D_UNDEAD_SOLDIER_" .. index
    local skin = Color3.fromRGB(117, 191, 120)
    local armor = Color3.fromRGB(60, 75, 77)
    local torso = body(zombie, "Body", Vector3.new(1.25, 1.7, .80),
        Vector3.new(0, 1.5, 0), armor, Enum.PartType.Block)
    zombie.PrimaryPart = torso
    body(zombie, "Head", Vector3.new(1.08, 1.0, 1.05),
        Vector3.new(0, 2.78, 0), skin, Enum.PartType.Ball)
    for _, sign in ipairs({-1, 1}) do
        body(zombie, "Eye" .. sign, Vector3.new(.17, .19, .1),
            Vector3.new(sign * .27, 2.85, -.51), Color3.fromRGB(241, 230, 110), Enum.PartType.Ball)
        body(zombie, "Arm" .. sign, Vector3.new(.43, 1.7, .43),
            Vector3.new(sign * .87, 1.55, -.16), skin, Enum.PartType.Block)
        body(zombie, "Leg" .. sign, Vector3.new(.46, 1.0, .56),
            Vector3.new(sign * .30, .31, 0), armor, Enum.PartType.Block)
    end
    zombie.Parent = parent
    zombie:PivotTo(CFrame.new(origin))
    return zombie
end

function M.clear(player: Player)
    local squad = squads[player]
    if squad == nil then return end
    squads[player] = nil -- revoke before Destroy; running loop sees revocation
    if player.Parent then player:SetAttribute("P0D_UndeadCommand", nil) end
    if squad.container and squad.container.Parent then squad.container:Destroy() end
end

function M.cast(player: Player, ctx: any): boolean
    -- ctx is built entirely from the original authoritative Game, not a client packet.
    if type(ctx) ~= "table" or type(ctx.valid) ~= "function"
        or type(ctx.root) ~= "function" or type(ctx.targets) ~= "function"
        or type(ctx.hit) ~= "function" or typeof(ctx.parent) ~= "Instance" then return false end
    if player.Parent ~= Players or not ctx.valid() then return false end
    local avatarRoot = ctx.root()
    if not avatarRoot or not avatarRoot:IsA("BasePart") then return false end
    local old = squads[player]
    if old and old.container and old.container.Parent then
        -- A second authorized cast issues a genuine squad command; no second spawn.
        old.mode = if old.mode == "ATTACK" then "GUARD"
            elseif old.mode == "GUARD" then "FOLLOW" else "ATTACK"
        player:SetAttribute("P0D_UndeadCommand", old.mode)
        return true
    end
    M.clear(player)
    local container = Instance.new("Folder")
    container.Name = "P0D_UNDEAD_SQUAD_" .. tostring(player.UserId)
    container.Parent = ctx.parent
    local sight = RaycastParams.new()
    sight.FilterType = Enum.RaycastFilterType.Exclude
    sight.FilterDescendantsInstances = {player.Character, container}
    sight.IgnoreWater = true
    local now = os.clock()
    local squad = {container = container, mode = "ATTACK", created = now,
        lastHit = {0, 0, 0}, zombies = {} :: {Model}, positions = {} :: {Vector3}}
    squads[player] = squad
    player:SetAttribute("P0D_UndeadCommand", "ATTACK")
    for i = 1, COUNT do
        local angle = 2 * math.pi * (i-1) / COUNT
        local offset = Vector3.new(math.cos(angle) * 3.2, 0, math.sin(angle) * 3.2)
        local start = avatarRoot.Position + offset + Vector3.new(0, -1.6, 0)
        table.insert(squad.zombies, buildZombie(i, start, container))
        table.insert(squad.positions, start)
    end
    task.spawn(function()
        for tick = 1, MAX_TICKS do
            task.wait(.2)
            if squads[player] ~= squad or not container.Parent
                or player.Parent ~= Players or os.clock() - squad.created > MAX_DURATION
                or not ctx.valid() then break end
            local root = ctx.root()
            if not root or not root.Parent then break end
            local mobs = ctx.targets()
            if type(mobs) ~= "table" then break end
            for i, zombie in ipairs(squad.zombies) do
                local position = squad.positions[i]
                local angle = 2 * math.pi * (i-1) / COUNT
                local neutral: any = nil
                local closest = 20.0
                if squad.mode ~= "FOLLOW" then
                    for _, mob in ipairs(mobs) do
                        if type(mob) == "table" and type(mob.hp) == "number"
                            and mob.hp > 0 and typeof(mob.pos) == "Vector3"
                            and mob.model and mob.model.Parent then
                            local dist = (mob.pos - root.Position).Magnitude
                            if dist < closest and (mob.pos-position).Magnitude < 22 then
                                closest = dist
                                neutral = mob
                            end
                        end
                    end
                end
                local guardRadius = if squad.mode == "GUARD" then 5 else LEASH
                local desired = root.Position + Vector3.new(math.cos(angle)*3.4, 0,
                    math.sin(angle)*3.4)
                if neutral then
                    local dx = neutral.pos - root.Position
                    local flat = Vector3.new(dx.X, 0, dx.Z)
                    if flat.Magnitude > .1 then
                        desired = root.Position + flat.Unit * math.min(flat.Magnitude, guardRadius)
                    end
                end
                if (position-root.Position).Magnitude > 29 then
                    -- Catch up only across clear space; never blink through a castle gate.
                    local path = desired - position
                    if workspace:Raycast(position + Vector3.new(0, 1.4, 0),
                        Vector3.new(path.X, 0, path.Z), sight) == nil then
                        position = desired
                    end
                end
                local planar = Vector3.new(desired.X-position.X, 0, desired.Z-position.Z)
                if planar.Magnitude > .06 then
                    local step = planar.Unit * math.min(planar.Magnitude, 1.4)
                    -- Don't step through a closed castle gate or blocking wall.
                    if workspace:Raycast(position + Vector3.new(0, 1.4, 0), step, sight) == nil then
                        position += step
                    end
                end
                -- Character root is around 3 studs above the floor; the model pivot
                -- is near its torso. Preserve the same visible floor-relative height.
                position = Vector3.new(position.X, root.Position.Y-1.6,
                    position.Z)
                squad.positions[i] = position
                local face = if neutral then neutral.pos-position else root.Position-position
                local flatFace = Vector3.new(face.X, 0, face.Z)
                if flatFace.Magnitude < .05 then flatFace = Vector3.new(0,0,-1) end
                local bob = .12 * math.abs(math.sin(tick*.8 + i))
                zombie:PivotTo(CFrame.lookAt(position+Vector3.new(0,bob,0),
                    position+flatFace.Unit+Vector3.new(0,bob,0)))
                if neutral and (neutral.pos-position).Magnitude <= RANGE
                    and os.clock()-squad.lastHit[i] >= ATTACK_INTERVAL then
                    squad.lastHit[i] = os.clock()
                    local aim = Vector3.new(neutral.pos.X-position.X, 0,
                        neutral.pos.Z-position.Z)
                    if aim.Magnitude > .2 and ctx.valid() then
                        local lineHit = workspace:Raycast(position + Vector3.new(0, 1.4, 0),
                            aim, sight)
                        -- The enemy itself is a legitimate hit, not an obstructing wall.
                        -- A closed gate/solid castle wall still blocks the strike.
                        if lineHit == nil or lineHit.Instance:IsDescendantOf(neutral.model) then
                            ctx.hit(position, aim.Unit, 8)
                        end
                    end
                end
            end
        end
        if squads[player] == squad then M.clear(player) end
    end)
    return true
end

return M
