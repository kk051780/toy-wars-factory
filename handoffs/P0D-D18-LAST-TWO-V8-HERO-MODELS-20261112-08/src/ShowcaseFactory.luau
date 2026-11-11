-- TRAP RAIDERS D18 original flagship preview: safe DISPLAY-ONLY factory.
-- No Humanoid, Remote, DataStore, damage, jump, trap, horn weapon, sound or purchases.
local Catalog = require(script.Parent.ShowcaseCatalog)
local Factory = {}
local ACTIVE = setmetatable({}, {__mode = "k"})
local VALID_POSE = {idle = true, tap = true, win = true, loss = true}
local MAX_PREVIEWS = 12
local MAX_WORLD = 10000

local function originOK(origin)
    if typeof(origin) ~= "CFrame" then return false end
    local v = origin.Position
    return v.X == v.X and v.Y == v.Y and v.Z == v.Z
        and math.abs(v.X) < MAX_WORLD and math.abs(v.Y) < MAX_WORLD and math.abs(v.Z) < MAX_WORLD
end

local function activeCount()
    local n = 0
    for model, _ in pairs(ACTIVE) do
        if model.Parent ~= nil then
            n += 1
        else
            ACTIVE[model] = nil
        end
    end
    return n
end

local function newPart(spec, palette, origin)
    local p = Instance.new("Part")
    p.Name = spec.name
    p.Shape = Enum.PartType[spec.shape]
    p.Size = Vector3.new(spec.size[1],spec.size[2],spec.size[3])
    local c = palette[spec.color]
    p.Color = Color3.fromRGB(c[1],c[2],c[3])
    p.Material = Enum.Material.SmoothPlastic
    p.Anchored = true
    p.CanCollide = false
    p.CanTouch = false
    p.CanQuery = false
    p.CastShadow = false
    p.CFrame = origin * CFrame.new(spec.position[1],spec.position[2],spec.position[3])
        * CFrame.Angles(math.rad(spec.rotation[1]),math.rad(spec.rotation[2]),math.rad(spec.rotation[3]))
    p:SetAttribute("P0DDisplayOnly",true)
    return p
end

-- Purely local opt-in preview. Caller owns the Folder/WorldModel, never Workspace battle Actors.
function Factory.Build(parent, characterId, origin)
    if typeof(parent) ~= "Instance" or not (parent:IsA("WorldModel") or parent:IsA("Model") or parent:IsA("Folder")) then
        return nil, "INVALID_DISPLAY_PARENT"
    end
    if not originOK(origin) then return nil, "INVALID_ORIGIN" end
    local definition = Catalog.get(characterId)
    if not definition then return nil, "UNKNOWN_CHARACTER" end
    if activeCount() >= MAX_PREVIEWS then return nil, "CAP_REACHED" end

    local model = Instance.new("Model")
    model.Name = "D18Detailed_" .. characterId
    model:SetAttribute("P0DDisplayOnly",true)
    model:SetAttribute("P0DCharacterId",characterId)
    model:SetAttribute("P0DGameId","TRAP_RAIDERS")
    local slots = {}
    for _, spec in ipairs(definition.parts) do
        local part = newPart(spec, definition.palette, origin)
        part.Parent = model
        table.insert(slots,{part=part,base=part.CFrame,spec=spec})
    end
    ACTIVE[model]={slots=slots,definition=definition,pose="idle",far=false}
    model.Parent = parent
    return model,nil
end

function Factory.SetPose(model, pose)
    local state=ACTIVE[model]
    if not state or not VALID_POSE[pose] then return false end
    local offsets=state.definition.pose_offsets[pose] or {}
    for _,slot in ipairs(state.slots) do
        local o=offsets[slot.spec.group] or {}
        slot.part.CFrame=slot.base * CFrame.new(o.dx or 0,o.dy or 0,o.dz or 0)
            * CFrame.Angles(0,0,math.rad(o.rz or 0))
    end
    state.pose=pose
    return true
end

function Factory.SetLod(model, far)
    local state=ACTIVE[model]
    if not state or type(far) ~= "boolean" then return false end
    for _,slot in ipairs(state.slots) do
        slot.part.Transparency=(far and slot.spec.detail) and 1 or 0
    end
    state.far=far
    return true
end

function Factory.GetStatus(model)
    local state=ACTIVE[model]
    if not state then return nil end
    local visible=0
    for _,slot in ipairs(state.slots) do
        if slot.part.Transparency==0 then visible+=1 end
    end
    return {characterId=model:GetAttribute("P0DCharacterId"),partCount=#state.slots,
        visibleParts=visible,pose=state.pose,far=state.far,displayOnly=true}
end

function Factory.Destroy(model)
    if not ACTIVE[model] then return false end
    ACTIVE[model]=nil
    model:Destroy()
    return true
end
return Factory
