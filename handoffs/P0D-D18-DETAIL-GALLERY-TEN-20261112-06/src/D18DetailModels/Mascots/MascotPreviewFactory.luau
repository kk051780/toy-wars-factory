-- TRAP RAIDERS / D18 editorial mascots, disabled-by-default isolated preview.
-- DISPLAY ONLY. No Humanoid, networking, events, damage, purchases, or DataStore.
-- Input: caller-supplied Instance parent + CFrame, two fixed original mascot IDs.
local Catalog = require(script.Parent.MascotPreviewCatalog)

local Factory = {}
local ACTIVE = setmetatable({}, { __mode = "k" })
local ALLOWED_POSES = { idle = true, tap = true, win = true, loss = true }
local WORLD_LIMIT = 100000

local function validOrigin(origin)
    if typeof(origin) ~= "CFrame" then
        return false
    end
    local p = origin.Position
    return p.X == p.X and p.Y == p.Y and p.Z == p.Z
        and math.abs(p.X) <= WORLD_LIMIT
        and math.abs(p.Y) <= WORLD_LIMIT
        and math.abs(p.Z) <= WORLD_LIMIT
end

local function transform(origin, partSpec)
    local p = partSpec.position
    local r = partSpec.rotation
    return origin * CFrame.new(p[1], p[2], p[3])
        * CFrame.Angles(math.rad(r[1]), math.rad(r[2]), math.rad(r[3]))
end

local function makePart(partSpec, palette, origin)
    local part = Instance.new("Part")
    part.Name = partSpec.name
    part.Shape = Enum.PartType[partSpec.shape]
    local dimensions = partSpec.size
    part.Size = Vector3.new(dimensions[1], dimensions[2], dimensions[3])
    local rgb = palette[partSpec.color]
    part.Color = Color3.fromRGB(rgb[1], rgb[2], rgb[3])
    part.Material = Enum.Material.SmoothPlastic
    part.Anchored = true
    part.CanCollide = false
    part.CanTouch = false
    part.CanQuery = false
    part.CastShadow = false
    part.Transparency = 0
    part.CFrame = transform(origin, partSpec)
    part:SetAttribute("P0DDisplayOnly", true)
    return part
end

-- Build ONLY in an isolated, OWNER-approved lobby preview. Never attach to battle actors.
function Factory.Build(parent, characterId, origin)
    if typeof(parent) ~= "Instance" or not validOrigin(origin) then
        return nil, "INVALID_PREVIEW_CONTEXT"
    end
    if type(characterId) ~= "string" then
        return nil, "UNKNOWN_CHARACTER"
    end
    local definition = Catalog.get(characterId)
    if not definition then
        return nil, "UNKNOWN_CHARACTER"
    end

    local model = Instance.new("Model")
    model.Name = "D18Preview_" .. characterId
    model:SetAttribute("P0DDisplayOnly", true)
    model:SetAttribute("P0DCharacterId", characterId)
    model:SetAttribute("P0DGameId", "TRAP_RAIDERS")
    local slots = {}
    for _, spec in ipairs(definition.parts) do
        local part = makePart(spec, definition.palette, origin)
        part.Parent = model
        table.insert(slots, { instance = part, base = part.CFrame, spec = spec })
    end
    ACTIVE[model] = {
        slots = slots,
        definition = definition,
        pose = "idle",
        far = false,
    }
    model.Parent = parent
    return model, nil
end

-- Caller-triggered static reaction; no timers or hidden animation loops.
-- Future animation may interpolate between these poses only after Studio QA.
function Factory.SetPose(model, pose)
    local state = ACTIVE[model]
    if not state or not ALLOWED_POSES[pose] then
        return false
    end
    local adjustments = state.definition.pose_offsets[pose] or {}
    for _, slot in ipairs(state.slots) do
        local offsets = adjustments[slot.spec.group] or {}
        slot.instance.CFrame = slot.base
            * CFrame.new(offsets.dx or 0, offsets.dy or 0, offsets.dz or 0)
            * CFrame.Angles(0, 0, math.rad(offsets.rz or 0))
    end
    state.pose = pose
    return true
end

-- Always retains all Parts and all noninteractive safety flags; only hides details.
function Factory.SetLod(model, far)
    local state = ACTIVE[model]
    if not state or type(far) ~= "boolean" then
        return false
    end
    for _, slot in ipairs(state.slots) do
        slot.instance.Transparency = (far and slot.spec.detail) and 1 or 0
    end
    state.far = far
    return true
end

function Factory.GetStatus(model)
    local state = ACTIVE[model]
    if not state then
        return nil
    end
    return {
        characterId = model:GetAttribute("P0DCharacterId"),
        partCount = #state.slots,
        pose = state.pose,
        far = state.far,
        displayOnly = true,
    }
end

function Factory.Destroy(model)
    if not ACTIVE[model] then
        return false
    end
    ACTIVE[model] = nil
    model:Destroy()
    return true
end

return Factory
