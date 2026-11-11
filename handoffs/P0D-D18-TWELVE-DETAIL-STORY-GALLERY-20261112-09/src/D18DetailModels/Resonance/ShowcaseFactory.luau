--!strict
-- TRAP RAIDERS D18: 2 optional cosmetic-only models, never auto-installed.
local Catalog = require(script.Parent:WaitForChild("ShowcaseCatalog"))
local Factory = {}
local registry: {[Model]: any} = setmetatable({}, {__mode = "k"})
local VALID_POSES = {idle = true, tap = true, win = true, loss = true}
local poseOffsets = {
    idle = CFrame.new(),
    tap = CFrame.Angles(0, math.rad(12), math.rad(3)),
    win = CFrame.Angles(0, math.rad(-8), math.rad(6)),
    loss = CFrame.Angles(0, math.rad(5), math.rad(-5)),
}
local MAX_INSTANCES = 16
local live = 0

local function getRecord(model: Instance?): any
    if model == nil or not model:IsA("Model") then return nil end
    local rec = registry[model]
    if not rec or model:GetAttribute("ShowcaseOnly") ~= true or model:GetAttribute("TRCA_ID") ~= rec.id then
        return nil
    end
    return rec
end

local function getParentValid(parent: Instance): boolean
    return parent:IsA("Workspace") or parent:IsA("Folder") or parent:IsA("Model")
end

function Factory.Build(parent: Instance, characterId: string, origin: CFrame?): Model
    assert(parent ~= nil and getParentValid(parent), "showroom parent must be Workspace/Folder/Model")
    assert(type(characterId)=="string" and Catalog[characterId] ~= nil, "unknown D18 showcase ID")
    assert(live < MAX_INSTANCES, "D18 sample instance budget")
    local base = origin or CFrame.new()
    assert(typeof(base) == "CFrame", "expected CFrame origin")
    local data = Catalog[characterId]
    local model = Instance.new("Model")
    model.Name = "D18_Showcase_" .. characterId
    model.WorldPivot = CFrame.new()
    model:SetAttribute("ShowcaseOnly", true)
    model:SetAttribute("TRCA_ID", characterId)
    model:SetAttribute("DisplayNameJP", data.displayName)
    for _, source in ipairs(data.parts) do
        local newPart: BasePart
        if source.shape == "Wedge" then
            newPart = Instance.new("WedgePart")
        else
            local normalPart = Instance.new("Part")
            if source.shape == "Ball" then normalPart.Shape = Enum.PartType.Ball end
            if source.shape == "Cylinder" then normalPart.Shape = Enum.PartType.Cylinder end
            newPart = normalPart
        end
        newPart.Name = source.name
        newPart.Size = Vector3.new(source.size[1],source.size[2],source.size[3])
        newPart.CFrame = CFrame.new(source.position[1],source.position[2],source.position[3]) *
            CFrame.Angles(math.rad(source.rotation[1]),math.rad(source.rotation[2]),math.rad(source.rotation[3]))
        newPart.Color = Color3.fromRGB(source.rgb[1],source.rgb[2],source.rgb[3])
        newPart.Material = Enum.Material.SmoothPlastic
        newPart.Anchored = true
        newPart.CanCollide = false
        newPart.CanTouch = false
        newPart.CanQuery = false
        newPart.CastShadow = false
        newPart:SetAttribute("FarDetail", source.farDetail)
        newPart.Parent = model
    end
    model.Parent = parent
    registry[model] = {origin=base, id=characterId, pose="idle", far=false}
    live += 1
    model:PivotTo(base)
    return model
end

function Factory.SetPose(model: Model, pose: string): boolean
    local rec = getRecord(model)
    if not rec or VALID_POSES[pose] ~= true then return false end
    rec.pose = pose
    model:PivotTo(rec.origin * poseOffsets[pose])
    return true
end

function Factory.SetLod(model: Model, far: boolean): boolean
    local rec = getRecord(model)
    if not rec or type(far)~="boolean" then return false end
    for _, obj in ipairs(model:GetChildren()) do
        if obj:IsA("BasePart") then
            obj.Transparency = if far and obj:GetAttribute("FarDetail") == true then 1 else 0
        end
    end
    rec.far = far
    return true
end

function Factory.GetStatus(model: Model): any
    local rec = getRecord(model)
    if not rec then return nil end
    local data = Catalog[rec.id]
    local farCount = 0
    for _, p in ipairs(data.parts) do
        if not p.farDetail then farCount += 1 end
    end
    return {id=rec.id, displayName=data.displayName, partCount=#data.parts,
        nearCount=#data.parts, farCount=farCount, far=rec.far,
        pose=rec.pose, displayOnly=true}
end

function Factory.Destroy(model: Model): boolean
    local rec = getRecord(model)
    if not rec then return false end
    registry[model] = nil
    live = math.max(0, live-1)
    model:Destroy()
    return true
end

return Factory
