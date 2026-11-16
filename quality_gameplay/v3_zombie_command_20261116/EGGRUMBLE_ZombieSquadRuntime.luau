--!strict
-- PRIVATE CANDIDATE ONLY: opt-in server adapter for the existing ZOMBIE role Skill C.
-- Never installs another Game, Combat, Damage, Remote, Store, or SCORE authority.
-- The existing Combat author must call begin() and provide its authoritative hit().
local RunService = game:GetService("RunService")
local Policy = require(script.Parent.EGGRUMBLE_ZombieOrderPolicy)
local Runtime = {}
local active = setmetatable({}, { __mode = "k" })

local function buildMinion(parent: Instance, position: Vector3, name: string): (Model, Humanoid, BasePart)
    local model = Instance.new("Model")
    model.Name = name
    local root = Instance.new("Part")
    root.Name = "HumanoidRootPart"
    root.Size = Vector3.new(2.4, 3.4, 2)
    root.Color = Color3.fromRGB(106, 165, 133)
    root.Material = Enum.Material.SmoothPlastic
    root.CanCollide = true
    root.CFrame = CFrame.new(position + Vector3.new(0, 2, 0))
    root.Parent = model
    local head = Instance.new("Part")
    head.Name = "Head"
    head.Shape = Enum.PartType.Ball
    head.Size = Vector3.new(2, 2, 2)
    head.Color = Color3.fromRGB(174, 194, 151)
    head.CanCollide = false
    head.CFrame = root.CFrame * CFrame.new(0, 2.5, 0)
    head.Parent = model
    local weld = Instance.new("WeldConstraint")
    weld.Part0 = root
    weld.Part1 = head
    weld.Parent = root
    local humanoid = Instance.new("Humanoid")
    humanoid.WalkSpeed = 14
    humanoid.MaxHealth = 20
    humanoid.Health = 20
    humanoid.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
    humanoid.Parent = model
    model.PrimaryPart = root
    model.Parent = parent
    -- Server owns movement; never grant client network ownership.
    pcall(function() root:SetNetworkOwner(nil) end)
    return model, humanoid, root
end

-- opts: matchToken, ownerId, world, snapshot(player), hit(player,targetId,damage,token)
-- The hit callback MUST revalidate current-mode membership, LOS, HP and reward owner.
function Runtime.begin(player: Player, opts: any): (boolean, string?)
    assert(RunService:IsServer(), "zombie commander is server-only")
    assert(type(opts) == "table" and type(opts.matchToken) == "string")
    assert(type(opts.snapshot) == "function" and type(opts.hit) == "function")
    if active[player] then Runtime.stop(player) end
    local character = player.Character
    local root = character and character:FindFirstChild("HumanoidRootPart") :: BasePart?
    if not root or not opts.world or not opts.world.Parent then return false, "NO_WORLD_OR_AVATAR" end
    local epoch = tostring(opts.matchToken)
    local ownerId = tostring(opts.ownerId or player.UserId)
    local policy = Policy.new(epoch, ownerId, os.clock())
    local units: {[string]: {model:Model, humanoid:Humanoid, root:BasePart}} = {}
    local folder = Instance.new("Folder")
    folder.Name = "EGGRUMBLE_ZombieServants_" .. tostring(player.UserId)
    folder.Parent = opts.world
    local connection: RBXScriptConnection? = nil
    local ended = false
    local function stop()
        if ended then return end
        ended = true
        Policy.retire(policy)
        if connection then connection:Disconnect() end
        folder:Destroy()
        if active[player] and active[player].stop == stop then active[player] = nil end
    end
    for i = 1, Policy.MAX_UNITS do
        local position = root.Position + Vector3.new((i-2)*3.2, 0, -4)
        local id = tostring(player.UserId) .. "-z" .. tostring(i)
        local model, hum, part = buildMinion(folder, position, "SummonedZombie_" .. tostring(i))
        units[id] = { model = model, humanoid = hum, root = part }
        assert(Policy.enlist(policy, id, os.clock(), { x=part.Position.X, z=part.Position.Z }))
    end
    active[player] = { stop = stop, policy = policy }
    local elapsed = 0
    connection = RunService.Heartbeat:Connect(function(dt)
        elapsed += dt
        if elapsed < 0.25 then return end
        elapsed = 0
        if ended or player.Character ~= character or not player.Parent then stop(); return end
        local ok, snapshot = pcall(opts.snapshot, player)
        if not ok or type(snapshot) ~= "table" then stop(); return end
        for id, data in pairs(units) do
            if data.model.Parent and data.root.Parent and data.humanoid.Health > 0 then
                Policy.locate(policy, id, { x=data.root.Position.X, z=data.root.Position.Z })
            else
                stop(); return
            end
        end
        local actions = Policy.step(policy, os.clock(), snapshot)
        if not policy.active then stop(); return end
        for _, action in ipairs(actions) do
            local data = units[action.unitId]
            if data and data.model.Parent then
                if action.kind == "MOVE" then
                    -- MoveTo uses Roblox collision/path blockers; no wall teleport.
                    data.humanoid:MoveTo(Vector3.new(action.x, data.root.Position.Y, action.z))
                elseif action.kind == "ATTACK" then
                    -- The single original server Combat authority decides actual damage/credit.
                    local authorized = pcall(opts.hit, player, action.targetId, action.damage, epoch, data.root)
                    if not authorized then stop(); return end
                elseif action.kind == "DESPAWN" then
                    data.model:Destroy()
                    units[action.unitId] = nil
                end
            end
        end
    end)
    return true, nil
end

function Runtime.order(player: Player, order: string, focusId: string?): boolean
    local state = active[player]
    if not state then return false end
    -- Caller must be the server authority, not a raw client Remote argument.
    return Policy.issue(state.policy, order, focusId)
end

function Runtime.stop(player: Player)
    local state = active[player]
    if state then state.stop() end
end

return Runtime
