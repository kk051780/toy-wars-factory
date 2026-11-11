--!strict
-- TRAP RAIDERS D18: optional decorative display only; no gameplay authority.
-- No automatic instantiation or D01-D17 overrides. Parent must be explicit.
local Catalog = require(script.Parent:WaitForChild("ShowcaseCatalog"))
local Factory = {}
local registry: {[Model]: any} = setmetatable({}, {__mode = "k"})
local POSES = {
    idle = CFrame.new(),
    tap = CFrame.Angles(0, math.rad(12), math.rad(3)),
    win = CFrame.Angles(0, math.rad(-9), math.rad(5)),
    loss = CFrame.Angles(0, math.rad(5), math.rad(-6)),
}
local MAX_PARTS = 24
local MAX_MODELS = 12

local function owned(inst: Instance?): any
    if inst == nil or not inst:IsA("Model") then return nil end
    local model = inst :: Model
    local record = registry[model]
    if record == nil or model.Parent == nil then return nil end
    if model:GetAttribute("D18_SHOWCASE_ID") ~= record.id then return nil end
    if model:GetAttribute("D18_DISPLAY_ONLY") ~= true then return nil end
    return record
end

local function countModels(): number
    local n = 0
    for model, _ in pairs(registry) do
        if model.Parent ~= nil then
            n += 1
        else
            registry[model] = nil
        end
    end
    return n
end

function Factory.Build(parent: Instance, characterId: string, origin: CFrame?): Model?
    if parent == nil or not (parent:IsA("Workspace") or parent:IsA("Folder") or parent:IsA("Model")) then return nil end
    if typeof(characterId) ~= "string" then return nil end
    local data = Catalog[characterId]
    if data == nil or #data.parts < 1 or #data.parts > MAX_PARTS then return nil end
    local base = origin or CFrame.new()
    if typeof(base) ~= "CFrame" or countModels() >= MAX_MODELS then return nil end
    local model = Instance.new("Model")
    model.Name = "D18_Showcase_" .. characterId
    model.WorldPivot = CFrame.new()
    model:SetAttribute("D18_SHOWCASE_ID", characterId)
    model:SetAttribute("D18_DISPLAY_ONLY", true)
    for _, spec in ipairs(data.parts) do
        local p: BasePart
        if spec.shape == "Wedge" then
            p = Instance.new("WedgePart")
        else
            local q = Instance.new("Part")
            q.Shape = if spec.shape == "Ball" then Enum.PartType.Ball else Enum.PartType.Block
            p = q
        end
        p.Name = spec.name
        p.Size = Vector3.new(spec.size[1], spec.size[2], spec.size[3])
        p.CFrame = CFrame.new(spec.pos[1], spec.pos[2], spec.pos[3]) * CFrame.Angles(0, 0, math.rad(spec.zrot))
        p.Color = Color3.fromRGB(spec.rgb[1], spec.rgb[2], spec.rgb[3])
        p.Material = Enum.Material.SmoothPlastic
        p.Anchored = true
        p.CanCollide = false
        p.CanTouch = false
        p.CanQuery = false
        p.CastShadow = false
        p:SetAttribute("D18_FAR_DETAIL", spec.far)
        p.Parent = model
    end
    model.Parent = parent
    registry[model] = {id=characterId, origin=base, pose="idle", far=false}
    model:PivotTo(base)
    return model
end

function Factory.SetPose(instance: Instance, pose: string): boolean
    local state = owned(instance)
    if state == nil or typeof(pose) ~= "string" or POSES[pose] == nil then return false end
    state.pose = pose
    (instance :: Model):PivotTo(state.origin * POSES[pose])
    return true
end

function Factory.SetLod(instance: Instance, far: boolean): boolean
    local state = owned(instance)
    if state == nil or typeof(far) ~= "boolean" then return false end
    for _, child in ipairs(instance:GetChildren()) do
        if child:IsA("BasePart") then
            child.Transparency = if far and child:GetAttribute("D18_FAR_DETAIL") == true then 1 else 0
        end
    end
    state.far = far
    return true
end

function Factory.GetStatus(instance: Instance): {[string]: any}?
    local state = owned(instance)
    if state == nil then return nil end
    local data = Catalog[state.id]
    local farCount = 0
    for _, item in ipairs(data.parts) do
        if not item.far then farCount += 1 end
    end
    return {id=state.id, displayOnly=true, partsNear=#data.parts, partsFar=farCount,
        pose=state.pose, far=state.far}
end

function Factory.Destroy(instance: Instance): boolean
    if owned(instance) == nil then return false end
    local model = instance :: Model
    registry[model] = nil
    model:Destroy()
    return true
end

return Factory
