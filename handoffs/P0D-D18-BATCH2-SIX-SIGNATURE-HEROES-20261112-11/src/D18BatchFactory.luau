-- TRAP RAIDERS D18 - original 6-class batch preview factory, CLIENT DISPLAY ONLY.
-- No Humanoid, combat, traps, events, sound, commerce or inventory authority.
local Catalog = require(script.Parent.D18BatchCatalog)
local Factory = {}
local ACTIVE = setmetatable({}, {__mode="k"})
local POSES = {idle=true, tap=true, win=true, loss=true}
local MAX_ACTIVE = 12

local function validOrigin(origin)
    if typeof(origin) ~= "CFrame" then return false end
    local v = origin.Position
    return v.X == v.X and v.Y == v.Y and v.Z == v.Z
        and math.abs(v.X) < 10000 and math.abs(v.Y) < 10000 and math.abs(v.Z) < 10000
end

local function activeCount()
    local n = 0
    for model, state in pairs(ACTIVE) do
        if model.Parent == nil then
            ACTIVE[model] = nil
        else
            n += 1
        end
    end
    return n
end

local function safePart(spec, palette)
    local p = Instance.new("Part")
    p.Name = spec.name
    p.Shape = Enum.PartType[spec.shape]
    p.Size = Vector3.new(spec.size[1], spec.size[2], spec.size[3])
    local rgb = palette[spec.color]
    p.Color = Color3.fromRGB(rgb[1],rgb[2],rgb[3])
    p.Material = Enum.Material.SmoothPlastic
    p.Anchored = true
    p.CanCollide = false
    p.CanTouch = false
    p.CanQuery = false
    p.CastShadow = false
    p:SetAttribute("P0DDisplayOnly",true)
    return p
end

local function render(state)
    local pose = state.definition.pose_offsets[state.pose] or {}
    local yaw = CFrame.Angles(0, math.rad(state.yaw), 0)
    for _, slot in ipairs(state.parts) do
        local s = slot.spec
        local o = pose[s.group] or {}
        slot.part.CFrame = state.origin * yaw
            * CFrame.new(s.position[1],s.position[2],s.position[3])
            * CFrame.Angles(math.rad(s.rotation[1]),math.rad(s.rotation[2]),math.rad(s.rotation[3]))
            * CFrame.new(o.dx or 0,o.dy or 0,o.dz or 0)
            * CFrame.Angles(0,0,math.rad(o.rz or 0))
        slot.part.Transparency = (state.far and not s.far) and 1 or 0
    end
end

-- WorldModel-only prevents accidental direct part creation in the battle Workspace.
function Factory.Build(parent, id, origin)
    if typeof(parent) ~= "Instance" or not parent:IsA("WorldModel") then return nil,"INVALID_VIEWPORT_PARENT" end
    if not validOrigin(origin) then return nil,"INVALID_ORIGIN" end
    local data = Catalog.get(id)
    if data == nil then return nil,"UNKNOWN_CHARACTER" end
    if activeCount() >= MAX_ACTIVE then return nil,"PREVIEW_CAP" end
    local model = Instance.new("Model")
    model.Name = "D18Preview_" .. id
    model:SetAttribute("P0DDisplayOnly",true)
    model:SetAttribute("P0DSourceModelId",id)
    local parts = {}
    for _, s in ipairs(data.parts) do
        local part = safePart(s,data.palette)
        part.Parent = model
        table.insert(parts,{part=part,spec=s})
    end
    local state = {origin=origin,pose="idle",far=false,yaw=0,parts=parts,definition=data}
    ACTIVE[model] = state
    model.Parent = parent
    render(state)
    return model,nil
end
function Factory.SetPose(model,pose)
    local state=ACTIVE[model]
    if not state or not POSES[pose] then return false end
    state.pose=pose
    render(state)
    return true
end
function Factory.SetLod(model,far)
    local state=ACTIVE[model]
    if not state or type(far) ~= "boolean" then return false end
    state.far=far
    render(state)
    return true
end
function Factory.SetYaw(model,angle)
    local state=ACTIVE[model]
    if not state or type(angle) ~= "number" or angle ~= angle
        or angle < 0 or angle >= 360 or angle % 45 ~= 0 then return false end
    state.yaw=angle
    render(state)
    return true
end
function Factory.GetStatus(model)
    local state=ACTIVE[model]
    if not state then return nil end
    local visible=0
    for _,slot in ipairs(state.parts) do
        if slot.part.Transparency == 0 then visible += 1 end
    end
    return {id=model:GetAttribute("P0DSourceModelId"),partCount=#state.parts,
        visibleParts=visible,pose=state.pose,far=state.far,yaw=state.yaw,displayOnly=true}
end
function Factory.Destroy(model)
    local state=ACTIVE[model]
    if state == nil then return false end
    ACTIVE[model]=nil
    model:Destroy()
    return true
end
return Factory
