--!strict
-- Optional V3 client-only visual LOD; NEVER changes attacks, castle/egg, collision or server state.
-- Only seven named secondary skill silhouettes may be hidden at >=125 studs.
-- FLASH/RING/ULTIMATE, boss warnings, hit confirmations and objective HUD remain untouched.
local Players=game:GetService("Players")
local RunService=game:GetService("RunService")
local Workspace=game:GetService("Workspace")
if not RunService:IsStudio() then return end
local player=Players.LocalPlayer
local Rules=require(script.Parent:WaitForChild("EGGRUMBLE_FXBudgetRules"))
local ARENA="EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW"
local MAX_TRACKED=144
local state=Rules.newState()
local tracked={}:: {[BasePart]:boolean}
local originals={}:: {[BasePart]:number}
local count=0
local root:Instance?=nil
local rootConnection:RBXScriptConnection?=nil
local frames=0
local frameSeconds=0
local visibilitySeconds=0
local active=true
local function restore(part:BasePart)
 local original=originals[part]
 if original~=nil and part.Parent then part.LocalTransparencyModifier=original end
 originals[part]=nil
end
local function reset()
 for part in pairs(tracked) do restore(part) end
 table.clear(tracked);table.clear(originals);count=0
 if rootConnection then rootConnection:Disconnect();rootConnection=nil end
 root=nil
end
local function watch(inst:Instance)
 if not inst:IsA("BasePart") or not Rules.isDecorative(inst.Name) then return end
 local part=inst::BasePart
 if tracked[part] or count>=MAX_TRACKED then return end
 tracked[part]=true
 count+=1
end
local function attach(folder:Instance)
 if root==folder then return end
 reset()
 root=folder
 for _,inst in ipairs(folder:GetDescendants()) do watch(inst) end
 rootConnection=folder.DescendantAdded:Connect(watch)
end
local current=Workspace:FindFirstChild(ARENA)
if current then attach(current) end
local childConnection=Workspace.ChildAdded:Connect(function(child)
 if child.Name==ARENA then attach(child) end
end)
local tickConnection=RunService.Heartbeat:Connect(function(dt)
 if not active or dt<=0 then return end
 frames+=1;frameSeconds+=dt;visibilitySeconds+=dt
 if frameSeconds>=1 then
  Rules.sample(state,frames/frameSeconds)
  frames=0;frameSeconds=0
 end
 if visibilitySeconds<.35 then return end
 visibilitySeconds=0
 if root and not root.Parent then reset() end
 if not root then return end
 local camera=Workspace.CurrentCamera
 if not camera then return end
 local eye=camera.CFrame.Position
 local forced=player:GetAttribute("EGGRUMBLE_ReducedEffects")==true
 for part in pairs(tracked) do
  if not part:IsDescendantOf(root) then
   restore(part)
   tracked[part]=nil;count-=1
  else
   local hide=Rules.shouldCull(part.Name,(part.Position-eye).Magnitude,state.low,forced)
   if hide and originals[part]==nil then
    originals[part]=part.LocalTransparencyModifier
    part.LocalTransparencyModifier=1
   elseif not hide then
    restore(part)
   end
  end
 end
end)
script.Destroying:Connect(function()
 active=false;tickConnection:Disconnect();childConnection:Disconnect();reset()
end)
