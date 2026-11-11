--!strict
-- D18 original noncombat showroom. Manual opt-in only. No server-owned gameplay changes.
local Catalog = require(script.Parent:WaitForChild("ShowcaseCatalog"))
local Factory = {}
local states: {[Model]: {id: string, origin: CFrame, pose: string, far: boolean}} = setmetatable({}, {__mode="k"})
local poses = {
    idle = {yaw = 0, tilt = 0},
    tap = {yaw = 9, tilt = 0},
    win = {yaw = -10, tilt = 5},
    loss = {yaw = 5, tilt = -6},
}
local MAX_PARTS = 24

local function owned(model: Instance): boolean
    if not model:IsA("Model") then return false end
    local state = states[model :: Model]
    return state ~= nil and model:GetAttribute("D18_SHOWCASE_ID") == state.id
end

local function poseModel(model: Model, state: {id: string, origin: CFrame, pose: string, far: boolean})
    local preset = poses[state.pose]
    model:PivotTo(state.origin * CFrame.Angles(0, math.rad(preset.yaw), math.rad(preset.tilt)))
end

function Factory.Build(parent: Instance, characterId: string, origin: CFrame?): Model?
    if parent == nil or not (parent:IsA("Workspace") or parent:IsA("Folder") or parent:IsA("Model")) then return nil end
    if typeof(characterId) ~= "string" then return nil end
    local design = Catalog[characterId]
    if design == nil or #design.parts > MAX_PARTS or #design.parts < 1 then return nil end
    local pivot = origin or CFrame.new()
    if typeof(pivot) ~= "CFrame" then return nil end

    local model = Instance.new("Model")
    model.Name = "D18_Showcase_" .. characterId
    model.WorldPivot = CFrame.new()
    model:SetAttribute("D18_SHOWCASE_ID", characterId)
    model:SetAttribute("D18_DISPLAY_ONLY", true)
    for _, spec in ipairs(design.parts) do
        local p = Instance.new("Part")
        p.Name = spec.name
        p.Shape = if spec.shape == "Ball" then Enum.PartType.Ball else Enum.PartType.Block
        p.Size = Vector3.new(spec.size[1], spec.size[2], spec.size[3])
        p.CFrame = CFrame.new(spec.pos[1], spec.pos[2], spec.pos[3]) * CFrame.Angles(0,0,math.rad(spec.rot))
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
    states[model] = {id=characterId, origin=pivot, pose="idle", far=false}
    poseModel(model, states[model])
    return model
end

function Factory.SetPose(model: Instance, nextPose: string): boolean
    if not owned(model) or typeof(nextPose) ~= "string" or poses[nextPose] == nil then return false end
    local m = model :: Model
    local state = states[m]
    state.pose = nextPose
    poseModel(m,state)
    return true
end

function Factory.SetLod(model: Instance, far: boolean): boolean
    if not owned(model) or typeof(far) ~= "boolean" then return false end
    local m = model :: Model
    for _, item in ipairs(m:GetChildren()) do
        if item:IsA("BasePart") then
            item.Transparency = if far and item:GetAttribute("D18_FAR_DETAIL") == true then 1 else 0
        end
    end
    states[m].far = far
    return true
end

function Factory.GetStatus(model: Instance): {[string]: any}?
    if not owned(model) then return nil end
    local m = model :: Model
    local design = Catalog[states[m].id]
    local countFar = 0
    for _, p in ipairs(design.parts) do
        if not p.far then countFar += 1 end
    end
    return {id=states[m].id, displayOnly=true, partsNear=#design.parts, partsFar=countFar, pose=states[m].pose, far=states[m].far}
end

function Factory.Destroy(model: Instance): boolean
    if not owned(model) then return false end
    local m = model :: Model
    states[m] = nil
    m:Destroy()
    return true
end

return Factory
