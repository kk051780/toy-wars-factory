-- Known limits: unrotated boxes/ellipsoids only, synchronous fake signals,
-- no actual Humanoid, ProximityPrompt rendering, navmesh, physics, or replication.
local vec = {}
local function vector(x, y, z)
    return setmetatable({X = x, Y = y, Z = z}, vec)
end
vec.__add = function(a, b) return vector(a.X + b.X, a.Y + b.Y, a.Z + b.Z) end
vec.__sub = function(a, b) return vector(a.X - b.X, a.Y - b.Y, a.Z - b.Z) end
vec.__mul = function(a, n) return vector(a.X * n, a.Y * n, a.Z * n) end
vec.__index = function(v, key)
    local size = math.sqrt(v.X ^ 2 + v.Y ^ 2 + v.Z ^ 2)
    if key == "Magnitude" then return size end
    if key == "Unit" then return v * (1 / size) end
end
local Vector3 = {new = vector}
local Color3 = {fromRGB = function(...) return {...} end}
local Enum = {
    Material = {SmoothPlastic = "SmoothPlastic", Glass = "Glass"},
    PartType = {Ball = "Ball"},
    RaycastFilterType = {Exclude = "Exclude"},
}
local CFrame = {lookAt = function(at, _look) return {Position = at} end}
local function signal()
    local listener
    return {
        Connect = function(_, fn) listener = fn end,
        Fire = function(_, ...) assert(listener, "missing connection"); listener(...) end,
    }
end

local nodes = {}
local methods = {}
function methods:GetChildren()
    local found = {}
    for _, node in ipairs(nodes) do
        if node.Parent == self then table.insert(found, node) end
    end
    return found
end
function methods:FindFirstChild(name)
    for _, child in ipairs(self:GetChildren()) do
        if child.Name == name then return child end
    end
end
function methods:FindFirstChildOfClass(class)
    for _, child in ipairs(self:GetChildren()) do
        if child:IsA(class) then return child end
    end
end
function methods:IsA(class)
    return self.class == class or (class == "BasePart" and self.class == "Part")
end
function methods:Destroy()
    for _, child in ipairs(self:GetChildren()) do child:Destroy() end
    self.Parent = nil
end
function methods:GetClosestPointOnSurface(at)
    local center, size = self.Position, self.Size
    local offset = at - center
    if self.Shape == Enum.PartType.Ball then
        -- Project along the center-to-point line. This approximates the
        -- engine nearest surface for a non-uniform egg without hard-coding a blocker.
        local radius = math.sqrt((offset.X * 2 / size.X) ^ 2 + (offset.Y * 2 / size.Y) ^ 2 + (offset.Z * 2 / size.Z) ^ 2)
        return if radius > 1 then center + offset * (1 / radius) else at
    end
    return center + vector(math.clamp(offset.X, -size.X / 2, size.X / 2),
        math.clamp(offset.Y, -size.Y / 2, size.Y / 2), math.clamp(offset.Z, -size.Z / 2, size.Z / 2))
end
function methods:GetPivot() return {Position = self.PrimaryPart.Position} end
function methods:PivotTo(cf) self.PrimaryPart.Position = cf.Position end
local Instance = {new = function(class)
    local node = setmetatable({class = class, Name = class}, {__index = methods})
    if class == "Part" then
        node.CanCollide, node.CanTouch, node.CanQuery = true, true, true
        node.Shape, node.Position, node.Size = "Block", vector(0, 0, 0), vector(1, 1, 1)
    elseif class == "ProximityPrompt" then
        node.Enabled, node.Triggered = true, signal()
    end
    table.insert(nodes, node)
    return node
end}

local function excluded(node, list)
    while node do
        if table.find(list or {}, node) then return true end
        node = node.Parent
    end
    return false
end
local function intersect(part, origin, direction)
    local localOrigin = origin - part.Position
    if part.Shape == Enum.PartType.Ball then
        local half = part.Size * .5
        local p = vector(localOrigin.X / half.X, localOrigin.Y / half.Y, localOrigin.Z / half.Z)
        local d = vector(direction.X / half.X, direction.Y / half.Y, direction.Z / half.Z)
        local a = d.X ^ 2 + d.Y ^ 2 + d.Z ^ 2
        local b = p.X * d.X + p.Y * d.Y + p.Z * d.Z
        local c = p.X ^ 2 + p.Y ^ 2 + p.Z ^ 2 - 1
        local disc = b ^ 2 - a * c
        if a == 0 or disc < 0 then return nil end
        for _, t in ipairs({(-b - math.sqrt(disc)) / a, (-b + math.sqrt(disc)) / a}) do
            if t >= 0 and t <= 1 then return t end
        end
        return nil
    end
    local low, high = 0, 1
    for _, axis in ipairs({"X", "Y", "Z"}) do
        local p, d, half = localOrigin[axis], direction[axis], part.Size[axis] * .5
        if math.abs(d) < 1e-9 then
            if math.abs(p) > half then return nil end
        else
            local a, b = (-half - p) / d, (half - p) / d
            low, high = math.max(low, math.min(a, b)), math.min(high, math.max(a, b))
            if low > high then return nil end
        end
    end
    return low
end
local workspace = Instance.new("Workspace")
local RaycastParams = {new = function() return {} end}
function workspace:Raycast(origin, direction, params)
    local nearest, distance = nil, math.huge
    for _, part in ipairs(nodes) do
        local queryable = if params.RespectCanCollide then part.CanCollide else part.CanQuery
        if part:IsA("BasePart") and part.Parent and queryable and not excluded(part, params.FilterDescendantsInstances) then
            local t = intersect(part, origin, direction)
            if t and t < distance then nearest, distance = part, t end
        end
    end
    if nearest then
        -- Only used to recognize the top surface of the fixture floor.
        local normal = if nearest.Name == "StandardFoundation" then vector(0, 1, 0) else vector(1, 0, 0)
        return {Instance = nearest, Position = origin + direction * distance, Normal = normal}
    end
end
local fakeRunService = {IsStudio = function() return true end}
local fakePathfinding = {CreatePath = function() error("Navmesh intentionally unavailable") end}
local game = {GetService = function(_, name)
    local service = ({RunService = fakeRunService, PathfindingService = fakePathfinding})[name]
    return assert(service, name)
end}
local task = {spawn = function(fn) fn() end}

local function newPlayer(id)
    local player, character = Instance.new("Player"), Instance.new("Model")
    local humanoid, HRP = Instance.new("Humanoid"), Instance.new("Part")
    player.Parent, player.Character, player.UserId = workspace, character, id
    humanoid.Health, humanoid.Parent = 100, character
    HRP.Name, HRP.CanCollide, HRP.Parent = "HumanoidRootPart", false, character
    return player, HRP, humanoid
end

local Rules = (function()
__FIELD_RULES__
end)()
local Deadline = (function()
__FIELD_DEADLINE__
return Deadline
end)()
local IS_CONTROL = __FIELD_IS_CONTROL__
local root = Vector3.new(0,4,0)
local joined = {}
local InvulRuntime = {allowObjectiveAction = function() return true end}
local InteractionGuard = {allow = function() return true end}
__FIELD_BLOCK__
__FIELD_PROMPT__
local function attachFieldAndRefresh(session, mode)
__FIELD_DECLARATION__
__FIELD_REFRESH__
end
__FIELD_LOOP__
return session.refresh
end
local function frozenValue(value)
    if type(value) ~= "table" then
        return type(value) .. ":" .. tostring(value)
    end
    local fields = {}
    for key, item in value do
        table.insert(fields, frozenValue(key) .. "=" .. frozenValue(item))
    end
    table.sort(fields)
    return "{" .. table.concat(fields, ",") .. "}"
end


local warrior = {UserId = 11}

local function newRound(mode)
    local team = mode == Rules.MODE_TEAM
    local roster = if team then {{id = "11", team = "RED"}, {id = "21", team = "BLUE", isAI = true}}
        else {{id = "11"}, {id = "21", isAI = true}}
    local session = {rules = Rules.new(mode, roster, 24), world = Instance.new("Folder")}
    Rules.start(session.rules)
    joined[warrior.UserId] = mode
    local refresh = attachFieldAndRefresh(session, mode)
    assert(#session.world:GetChildren() == 24)
    return session, refresh
end

local function pickup(session, i)
    local egg = assert(session.world:FindFirstChild("FieldEgg_" .. i))
    return egg, assert(egg:FindFirstChildOfClass("ProximityPrompt"))
end

for _, mode in {Rules.MODE_TEAM, Rules.MODE_ROYALE} do
    for _, finish in {"CASTLE", "DEADLINE"} do
        local otherMode = if mode == Rules.MODE_TEAM then Rules.MODE_ROYALE else Rules.MODE_TEAM
        local other = newRound(otherMode)
        local _, otherPrompt = pickup(other, 1)
        local session, refresh = newRound(mode)
        local egg, first = pickup(session, 1)
        local remaining, witness = pickup(session, 2)
        prompt(remaining, "Other action", "Out of scope", function() end)
        local unrelated
        for _, child in remaining:GetChildren() do
            if child.ActionText == "Other action" then unrelated = child end
        end
        assert(unrelated, "Expected the unrelated prompt")
        assert(first.Enabled and witness.Enabled and unrelated.Enabled and otherPrompt.Enabled)
        first.Triggered:Fire(warrior)
        assert(egg.Parent == nil and first.Parent == nil and not session.rules.fieldEggTokens.FIELD_1)
        assert(session.rules.castles["11"].heldEggs == 1)
        assert(Rules.depositEggs(session.rules, "11", 1) == 1)
        assert(Rules.auditEggConservation(session.rules).valid)
        refresh()
        assert(witness.Enabled)

        if finish == "CASTLE" then
            local last
            for _ = 1, 5 do
                last = Rules.damageCastle(session.rules, "21", "11", 250)
                if last.fallen then break end
            end
            assert(last.fallen and last.winner ~= nil)
        else
            local lease = Deadline.new(100, "test")
            assert(not Deadline.expire(session.rules, lease, 999.99, "test"))
            refresh()
            assert(witness.Enabled)
            assert(Deadline.expire(session.rules, lease, 1000, "test"))
        end
        assert(session.rules.phase == "FINISHED" and witness.Enabled)
        local before = frozenValue(session.rules)
        refresh()
        refresh()
        assert(witness.Enabled == IS_CONTROL and unrelated.Enabled and otherPrompt.Enabled)
        for i = 2, 24 do
            local existing, instance = pickup(session, i)
            assert(existing.Parent == session.world and instance.Enabled == IS_CONTROL)
        end
        witness.Triggered:Fire(warrior)
        assert(remaining.Parent == session.world and Rules.auditEggConservation(session.rules).valid)
        assert(frozenValue(session.rules) == before, "terminal state changed")

        local replay, replayRefresh = newRound(mode)
        replayRefresh()
        local newEgg, newPrompt = pickup(replay, 2)
        assert(newPrompt.Enabled and newPrompt ~= witness and replay.rules.fieldEggTokens.FIELD_2)
        newPrompt.Triggered:Fire(warrior)
        assert(newEgg.Parent == nil and replay.rules.castles["11"].heldEggs == 1)
        assert(Rules.auditEggConservation(replay.rules).valid)
        print("PASS", mode, finish, if IS_CONTROL then "REPRODUCED_CONTROL" else "FIELD_PROMPTS_DISABLED", "fresh replay and other mode unchanged")
    end
end
