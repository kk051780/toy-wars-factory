--!strict
-- TRAP RAIDERS D18 / TRCA-BE-072 / 月冠キリン
-- Standalone, noncombat showroom primitive art. Never auto-executes; no remotes/rewards.
local Factory = {}
local ID = "TRCA-BE-072"
local NAME = "月冠キリン"

-- Positions are studs from the optional display origin. One bright sock and
-- a floating five-piece crescent are deliberately legible in silhouette.
local PLAN = {
    {"Body", "Block", {0, 1.66, 0}, {2.35, 1.16, 1.10}, {170, 145, 210}, false, 0},
    {"RearLeftLeg", "Block", {-0.78, 0.72, -0.40}, {0.34, 1.44, 0.36}, {140, 112, 185}, false, 0},
    {"RearRightLeg", "Block", {-0.78, 0.72, 0.40}, {0.34, 1.44, 0.36}, {140, 112, 185}, false, 0},
    {"FrontLeftLeg", "Block", {0.84, 0.72, -0.40}, {0.34, 1.44, 0.36}, {140, 112, 185}, false, 0},
    {"FrontRightLeg", "Block", {0.84, 0.72, 0.40}, {0.34, 1.44, 0.36}, {140, 112, 185}, false, 0},
    {"SingleWhiteSock", "Block", {0.84, 0.27, 0.40}, {0.38, 0.54, 0.40}, {244, 246, 253}, false, 0},
    {"NeckLower", "Block", {0.89, 2.73, 0}, {0.52, 1.58, 0.53}, {192, 170, 227}, false, -8},
    {"NeckUpper", "Block", {1.08, 3.76, 0}, {0.45, 1.38, 0.48}, {192, 170, 227}, false, 8},
    {"Head", "Block", {1.17, 4.56, 0}, {0.80, 0.57, 0.68}, {205, 188, 232}, false, 0},
    {"EyeLeft", "Ball", {1.54, 4.61, -0.23}, {0.13, 0.13, 0.13}, {41, 35, 63}, true, 0},
    {"EyeRight", "Ball", {1.54, 4.61, 0.23}, {0.13, 0.13, 0.13}, {41, 35, 63}, true, 0},
    {"StitchedCape", "Block", {-0.28, 2.31, 0.00}, {1.18, 0.16, 1.12}, {112, 94, 164}, false, -17},
    {"CapeStitch", "Block", {-0.78, 2.38, 0.00}, {0.10, 0.11, 0.97}, {234, 231, 250}, true, -17},
    {"MoonArcTop", "Ball", {1.35, 5.42, 0}, {0.28, 0.22, 0.19}, {239, 241, 252}, false, 0},
    {"MoonArcLeftHigh", "Ball", {1.04, 5.33, 0}, {0.29, 0.26, 0.19}, {239, 241, 252}, false, 0},
    {"MoonArcLeftMid", "Ball", {0.91, 5.06, 0}, {0.28, 0.28, 0.19}, {239, 241, 252}, false, 0},
    {"MoonArcLeftLow", "Ball", {1.03, 4.84, 0}, {0.26, 0.23, 0.19}, {239, 241, 252}, false, 0},
    {"MoonArcTip", "Ball", {1.32, 4.76, 0}, {0.25, 0.18, 0.19}, {239, 241, 252}, false, 0},
}

local poses = {
    idle = {yaw = 0, lean = 0},
    tap = {yaw = 12, lean = 0},
    win = {yaw = -9, lean = 5},
    loss = {yaw = 4, lean = -6},
}

local registry: {[Model]: {origin: CFrame, pose: string, far: boolean}} = setmetatable({}, {__mode = "k"})

local function valid(model: Instance): boolean
    return model:IsA("Model") and model:GetAttribute("TRCA_ID") == ID and registry[model :: Model] ~= nil
end

local function pivot(model: Model, state: {origin: CFrame, pose: string, far: boolean})
    local p = poses[state.pose]
    model:PivotTo(state.origin * CFrame.Angles(0, math.rad(p.yaw), math.rad(p.lean)))
end

function Factory.Build(parent: Instance, origin: CFrame?): Model
    assert(parent ~= nil and (parent:IsA("Workspace") or parent:IsA("Folder") or parent:IsA("Model")), "display parent required")
    local where = origin or CFrame.new()
    assert(typeof(where) == "CFrame", "origin must be CFrame")
    local model = Instance.new("Model")
    model.WorldPivot = CFrame.new() -- preserve floor-relative authored offsets for PivotTo
    model.Name = "D18_MoonGiraffe_BE072_Showcase"
    model:SetAttribute("TRCA_ID", ID)
    model:SetAttribute("DisplayNameJP", NAME)
    model:SetAttribute("DisplayOnly", true)
    for _, entry in ipairs(PLAN) do
        local part = Instance.new("Part")
        part.Name = entry[1] :: string
        part.Shape = if entry[2] == "Ball" then Enum.PartType.Ball else Enum.PartType.Block
        local xyz = entry[3] :: {number}
        local size = entry[4] :: {number}
        local rgb = entry[5] :: {number}
        part.Size = Vector3.new(size[1], size[2], size[3])
        part.CFrame = CFrame.new(xyz[1], xyz[2], xyz[3]) * CFrame.Angles(0, 0, math.rad(entry[7] :: number))
        part.Color = Color3.fromRGB(rgb[1], rgb[2], rgb[3])
        part.Material = Enum.Material.SmoothPlastic
        part.Anchored = true
        part.CanCollide = false
        part.CanTouch = false
        part.CanQuery = false
        part.CastShadow = false
        part:SetAttribute("FarDetail", entry[6] :: boolean)
        part.Parent = model
    end
    model.Parent = parent
    registry[model] = {origin = where, pose = "idle", far = false}
    pivot(model, registry[model])
    return model
end

function Factory.SetPose(model: Model, name: string): boolean
    if not valid(model) or poses[name] == nil then
        return false
    end
    local state = registry[model]
    state.pose = name
    pivot(model, state)
    return true
end

function Factory.SetLod(model: Model, far: boolean): boolean
    if not valid(model) or typeof(far) ~= "boolean" then
        return false
    end
    for _, child in ipairs(model:GetChildren()) do
        if child:IsA("BasePart") then
            child.Transparency = if far and child:GetAttribute("FarDetail") == true then 1 else 0
        end
    end
    registry[model].far = far
    return true
end

function Factory.GetStatus(model: Model): {[string]: any}?
    if not valid(model) then
        return nil
    end
    local state = registry[model]
    return {id = ID, name = NAME, partCount = #PLAN, nearCount = #PLAN, farCount = #PLAN - 3, pose = state.pose, far = state.far, displayOnly = true}
end

function Factory.Destroy(model: Model): boolean
    if not valid(model) then
        return false
    end
    registry[model] = nil
    model:Destroy()
    return true
end

return Factory
