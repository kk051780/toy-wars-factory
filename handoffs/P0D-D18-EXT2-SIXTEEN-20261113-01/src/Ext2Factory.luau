-- 16 studio-only original low-poly prototypes, not gameplay models.
local RunService = game:GetService("RunService")
local Factory = {}
local colors = {"main", "accent", "glow", "shade"}
local function part(parent, label, kind, position, size, rgb, lit)
    local p = Instance.new(kind == "Wedge" and "WedgePart" or "Part")
    p.Name = label
    if kind == "Ball" then p.Shape = Enum.PartType.Ball end
    if kind == "Cylinder" then p.Shape = Enum.PartType.Cylinder end
    p.Size = Vector3.new(size[1], size[2], size[3])
    p.Position = Vector3.new(position[1], position[2], position[3])
    p.Color = Color3.fromRGB(rgb[1], rgb[2], rgb[3])
    p.Material = lit and Enum.Material.Neon or Enum.Material.SmoothPlastic
    p.Anchored = true
    p.CanCollide = false
    p.CanTouch = false
    p.CanQuery = false
    p.CastShadow = false
    p.Parent = parent
    return p
end
local baseByCategory = {
 BEAST = {
  {"Ball",0,1.45,0,2.05,1.6,1.7,1}, {"Ball",0,2.3,-.82,1.33,1.2,1.12,1},
  {"Ball",-.34,2.36,-1.38,.2,.22,.15,4}, {"Ball",.34,2.36,-1.38,.2,.22,.15,4},
  {"Cylinder",-.68,.55,-.42,.5,.88,.5,2}, {"Cylinder",.68,.55,-.42,.5,.88,.5,2},
  {"Wedge",0,1.3,1.1,.67,.7,1.1,2},
 },
 SPELL = {
  {"Ball",0,1.75,0,1.4,1.4,1.4,1}, {"Ball",0,1.75,-.65,.5,.5,.4,3},
  {"Cylinder",0,.55,0,.5,.86,.86,2}, {"Wedge",-1,1.25,.2,.7,.25,1.1,2},
  {"Wedge",1,1.25,.2,.7,.25,1.1,2},
 },
 MOUNT = {
  {"Block",0,1.25,0,2.6,.8,2.15,1}, {"Block",0,1.75,.4,1.5,.3,1.1,2},
  {"Cylinder",-1.05,.52,-.75,.34,1.05,1.05,4}, {"Cylinder",1.05,.52,-.75,.34,1.05,1.05,4},
  {"Cylinder",-1.05,.52,.75,.34,1.05,1.05,4}, {"Cylinder",1.05,.52,.75,.34,1.05,1.05,4},
 },
 ITEM = {
  {"Cylinder",0,1.52,0,.32,3,.32,1}, {"Block",0,.5,0,1.25,.17,.32,2},
  {"Wedge",0,2.6,0,.7,.7,.6,3}, {"Ball",0,3.2,0,.3,.3,.3,3},
 },
 ZOMBIE = {
  {"Block",0,1.53,0,1.45,1.48,.9,1}, {"Ball",0,2.68,-.08,1.1,1.03,.98,1},
  {"Block",-1.03,1.55,0,.42,1.2,.45,2}, {"Block",1.03,1.55,0,.42,1.2,.45,2},
  {"Block",-.43,.48,0,.5,.92,.55,4}, {"Block",.43,.48,0,.5,.92,.55,4},
  {"Ball",0,2.75,-.59,.28,.28,.22,3},
 },
 TRAP = {
  {"Block",0,.55,0,2.5,.25,2.5,1}, {"Wedge",-1.08,.92,-.75,.4,.75,.7,2},
  {"Wedge",1.08,.92,.75,.4,.75,.7,2}, {"Ball",0,1.2,0,.6,.6,.6,3},
 },
}
function Factory.build(item, parent, distant)
    if not RunService:IsStudio() then return nil, "STUDIO_ONLY" end
    if type(item) ~= "table" or type(item.itemId) ~= "string" then return nil, "INVALID_ITEM" end
    if type(parent) ~= "userdata" and typeof(parent) ~= "Instance" then return nil, "INVALID_PARENT" end
    local base = baseByCategory[item.category]
    if not base or not item.palette or type(item.accents) ~= "table" then return nil, "INVALID_RECIPE" end
    local model = Instance.new("Model")
    model.Name = item.itemId .. "_" .. item.name
    local count = 0
    local function add(spec, label)
        local palette = item.palette[colors[spec[8]]]
        if not palette then error("Invalid palette index") end
        local built = part(model, label, spec[1], {spec[2],spec[3],spec[4]}, {spec[5],spec[6],spec[7]}, palette, spec[8] == 3)
        count += 1
        if not model.PrimaryPart then model.PrimaryPart = built end
    end
    for i, spec in ipairs(base) do add(spec, "BASE_" .. i) end
    for i, spec in ipairs(item.accents) do
        if not distant or i <= 3 then add(spec, "SIGN_" .. i) end
    end
    if count > 20 then model:Destroy(); return nil, "OVER_BUDGET" end
    model:SetAttribute("D18SourceOnly", true)
    model:SetAttribute("LivePlayable", false)
    model:SetAttribute("PartCount", count)
    model.Parent = parent
    return model
end
-- Static personality key-poses only, not runtime animation/AI.
function Factory.previewPose(model, pose)
    if not RunService:IsStudio() or not model or not model:GetAttribute("D18SourceOnly") then return false end
    local target = {IDLE={0,0,0},TAP={.2,0,.17},WIN={0,.38,-.12},LOSE={0,-.22,.21}}
    local t = target[pose]
    if not t then return false end
    model:PivotTo(CFrame.new(0,t[2],0)*CFrame.Angles(t[3],t[1],0))
    return true
end
return Factory
