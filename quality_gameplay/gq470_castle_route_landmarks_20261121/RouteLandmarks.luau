--!strict
-- GQ470_ROUTE_LANDMARKS_REAL69_20261121
-- FB-015/016: three distinguishable in-world castle approach silhouettes.
-- A PREP ONLY: standalone optional module, NOT included in the 69 selected sources.
-- The existing FieldArt/Host owner must supply verified route anchors at intake.
-- No HUD, prompts, collisions, damage, Remotes, reward, or gameplay ownership.
local RouteLandmarks = {}
local ROOT_NAME = "GQ470_RouteLandmarks"
local EXPECTED_ROUTES = 3
local PARTS_PER_ROUTE = 4
local SIDE_OFFSET = 20 -- outside the 23-stud route corridor
local MIN_ANCHOR_SEPARATION = 24

local STONE = Color3.fromRGB(72, 83, 104)
local EDGE = Color3.fromRGB(161, 173, 184)
local PROFILE: {{size: Vector3, yaw: number}} = {
 {size=Vector3.new(2.6, 3.2, 1.6), yaw=-19}, -- pointed northern approach
 {size=Vector3.new(4.6, 1.6, 1.4), yaw=0},   -- broad central approach
 {size=Vector3.new(2.3, 4.2, 1.5), yaw=22}, -- high southern approach
}

local function makePart(parent: Model, name: string, dimensions: Vector3,
 frame: CFrame, tint: Color3, wedge: boolean): BasePart
 local p: BasePart
 if wedge then
  p = Instance.new("WedgePart")
 else
  p = Instance.new("Part")
 end
 p.Name = name
 p.Size = dimensions
 p.CFrame = frame
 p.Color = tint
 p.Material = if wedge then Enum.Material.Metal else Enum.Material.Slate
 p.Transparency = 0
 p.Anchored = true
 p.CanCollide = false
 p.CanTouch = false
 p.CanQuery = false
 p.CastShadow = false
 p.Parent = parent
 return p
end

local function validAnchors(root: Instance, anchors: {BasePart}, color: Color3): boolean
 if typeof(root) ~= "Instance" or not root:IsDescendantOf(workspace) then return false end
 if typeof(color) ~= "Color3" or type(anchors) ~= "table" then return false end
 if #anchors ~= EXPECTED_ROUTES then return false end
 for i = 1, EXPECTED_ROUTES do
  local current = anchors[i]
  if typeof(current) ~= "Instance" or not current:IsA("BasePart") then return false end
  if not current:IsDescendantOf(workspace) then return false end
  for j = 1, i - 1 do
   if current == anchors[j] or (current.Position - anchors[j].Position).Magnitude < MIN_ANCHOR_SEPARATION then
    return false
   end
  end
 end
 return true
end

-- Only remove a container this module previously created; no shared arena cleanup.
function RouteLandmarks.clear(root: Instance): boolean
 if typeof(root) ~= "Instance" then return false end
 local prior = root:FindFirstChild(ROOT_NAME)
 if not prior then return true end
 if not prior:IsA("Model") or prior:GetAttribute("GQ470RouteVisual") ~= true then
  return false
 end
 prior:Destroy()
 return true
end

-- Reversible, visual-only. Caller owns arena lifetime and existing field art.
function RouteLandmarks.attach(root: Instance, anchors: {BasePart}, teamTint: Color3): boolean
 if not validAnchors(root, anchors, teamTint) then return false end
 -- Reject unexpected same-name instances rather than deleting another owner.
 if not RouteLandmarks.clear(root) then return false end
 local decoration = Instance.new("Model")
 decoration.Name = ROOT_NAME
 decoration:SetAttribute("GQ470RouteVisual", true)
 decoration:SetAttribute("SourceOnly", true)
 decoration:SetAttribute("RouteCount", EXPECTED_ROUTES)
 decoration:SetAttribute("DecorativeParts", EXPECTED_ROUTES * PARTS_PER_ROUTE)
 for index = 1, EXPECTED_ROUTES do
  local anchor = anchors[index]
  local frame = anchor.CFrame * CFrame.new(SIDE_OFFSET, 0, 0)
  local profile = PROFILE[index]
  local motif = "Approach" .. tostring(index)
  makePart(decoration, motif .. "_LeftPillar", Vector3.new(1.3, 6, 1.4),
   frame * CFrame.new(-5, 3, 0), STONE, false)
  makePart(decoration, motif .. "_RightPillar", Vector3.new(1.3, 6, 1.4),
   frame * CFrame.new(5, 3, 0), STONE, false)
  makePart(decoration, motif .. "_Lintel", Vector3.new(11.2, 1.2, 1.7),
   frame * CFrame.new(0, 6.7, 0), EDGE, false)
  makePart(decoration, motif .. "_Crest", profile.size,
   frame * CFrame.new(0, 8.8, 0) * CFrame.Angles(0, math.rad(profile.yaw), 0),
   teamTint, true)
 end
 decoration.Parent = root
 return true
end
return RouteLandmarks
