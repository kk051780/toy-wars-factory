--!strict
-- EGGRUMBLE / ART-A01 / private Studio-only CLIENT visual LOD (2026-11-16).
-- One camera-distance pass every 1.2s: no RenderStepped/Heartbeat work,
-- no CombatFeel, animation, gameplay/physics, character, Humanoid or HUD changes.
-- Only A01-owned ART_ parts inside the exact A01 folder namespaces are eligible.
-- Genuine short KO feedback stays visible; author weapons/skill FX NEVER touched.
local RunService=game:GetService("RunService")
if not RunService:IsStudio() then return end
local UserInputService=game:GetService("UserInputService")

local MAX_TRACKED_PARTS=1800
local UPDATE_INTERVAL_SECONDS=1.2
local MOBILE=UserInputService.TouchEnabled

-- Distances (studs) are design caps, not measured device-FPS thresholds.
-- Near personal hero and mode gates stay readable. Far flora/neutral pieces
-- disappear on lower-end touchscreen clients without server replication writes.
local DISPLAY_DISTANCES:{[string]:number}={
 EGGRUMBLE_RoleVisuals=160,
 EGGRUMBLE_BotVisuals=130,
 EGGRUMBLE_LobbyRoleMiniatures_VisualOnly=165,
 EGGRUMBLE_FlagshipLandscape_VisualOnly=135,
 EGGRUMBLE_CastleArt_VisualOnly=195,
 EGGRUMBLE_NeutralArt_VisualOnly=95,
 EGGRUMBLE_EggVisual_VisualOnly=145,
 EGGRUMBLE_FieldItemVisual_VisualOnly=145,
 EGGRUMBLE_CastleEggStationArt_VisualOnly=155,
 EGGRUMBLE_ModeGateFrame_VisualOnly=180,
 EGGRUMBLE_DefenseModuleVisualOnly=150,
 EGGRUMBLE_StoneGiantVisual_VisualOnly=190,
 EGGRUMBLE_InteriorHeraldry_VisualOnly=170,
}
local DESKTOP_DISTANCE_MULTIPLIER=1.75
local MAX_ANCESTOR_STEPS=7
local records:{[BasePart]:number}={}
local hidden:{[BasePart]:boolean}={}
local trackedCount=0
local limit=if MOBILE then 1 else DESKTOP_DISTANCE_MULTIPLIER

local function originalA01Distance(part:BasePart):number?
 -- Server output is always named ART_* and parented into an A01-exclusive
 -- folder; limiting by BOTH prevents culling original author weapons and FX.
 if part.Name:sub(1,4)~="ART_" then return nil end
 local ancestor:Instance?=part.Parent
 for _=1,MAX_ANCESTOR_STEPS do
  if not ancestor then return nil end
  local dist=DISPLAY_DISTANCES[ancestor.Name]
  if dist then return dist end
  ancestor=ancestor.Parent
 end
 return nil
end

local function register(instance:Instance)
 if not instance:IsA("BasePart") then return end
 if records[instance]~=nil or trackedCount>=MAX_TRACKED_PARTS then return end
 local maxDist=originalA01Distance(instance)
 if maxDist==nil then return end
 records[instance]=maxDist
 trackedCount+=1
end

local function remove(instance:Instance)
 if not instance:IsA("BasePart") then return end
 if records[instance]==nil then return end
 -- The part may be reparented while still live. Restore original client
 -- visibility before removing our local, reversible LOD ownership.
 if instance.Parent then instance.LocalTransparencyModifier=0 end
 records[instance]=nil
 hidden[instance]=nil
 trackedCount=math.max(0,trackedCount-1)
end

for _,instance in ipairs(workspace:GetDescendants()) do register(instance) end
workspace.DescendantAdded:Connect(register)
workspace.DescendantRemoving:Connect(remove)

task.spawn(function()
 while script.Parent do
  task.wait(UPDATE_INTERVAL_SECONDS)
  local camera=workspace.CurrentCamera
  if not camera then continue end -- Never hide art while camera is uninitialized.
  local viewpoint=camera.CFrame.Position
  for part,distance in pairs(records) do
   if not part:IsDescendantOf(workspace) then
    remove(part)
   else
    local delta=part.Position-viewpoint
    -- 12% distance hysteresis: stop visible armor, eggs and distant gates
    -- flickering when the camera moves across a threshold during a dash.
    -- Nearward return deliberately happens earlier than outward hiding.
    local wasFar=hidden[part] or false
    local margin=if wasFar then .88 else 1.12
    local maxDist=distance*limit*margin
    local isFar=delta:Dot(delta)>maxDist*maxDist
    if isFar~=wasFar then
     hidden[part]=isFar
     part.LocalTransparencyModifier=if isFar then 1 else 0
    end
   end
  end
 end
end)

print("[EGGRUMBLE A01 CLIENT LOD] A01 visual-only distance LOD ready;",
 if MOBILE then "touch" else "desktop", "part cap",MAX_TRACKED_PARTS)
