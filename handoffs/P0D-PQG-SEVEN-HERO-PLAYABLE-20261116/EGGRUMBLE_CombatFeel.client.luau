--!strict
-- EGGRUMBLE V3 mobile-conservative *local* hit response.
-- Read-only replicated server-confirmed impact attributes: no RemoteEvent,
-- no authority or camera knockback on missed hits, no always-on large GUI.
local Players=game:GetService("Players")
local RunService=game:GetService("RunService")
local TweenService=game:GetService("TweenService")
local player=Players.LocalPlayer
if not RunService:IsStudio() then return end
local IMPACT_WINDOW=.115
local MAX_ANGLE=.006 -- radians; protect mobile players from nausea
local MAX_PUSH=.06 -- studs
local RECENT_CD=.12
local lastPulse=-100
local start=-100
local power=0
local pulse=0
local tones={
 WARRIOR=Color3.fromRGB(255,214,91),
 MAGE=Color3.fromRGB(97,212,255),
 NINJA=Color3.fromRGB(177,117,248),
 TRAPPER=Color3.fromRGB(193,116,255),
 BUILDER=Color3.fromRGB(65,243,205),
 BEAST=Color3.fromRGB(255,176,69),
 ZOMBIE=Color3.fromRGB(146,251,153),
}
-- Small, short-lived hit reticle in the center (nothing persists as a large HUD).
local gui=Instance.new("ScreenGui")
gui.Name="EGGRUMBLE_HitConfirmLocal"
gui.ResetOnSpawn=false;gui.IgnoreGuiInset=true;gui.DisplayOrder=18
gui.Parent=player:WaitForChild("PlayerGui")
local mark=Instance.new("Frame")
mark.Name="HitConfirm"
mark.AnchorPoint=Vector2.new(.5,.5)
mark.Position=UDim2.fromScale(.5,.49)
mark.Size=UDim2.fromOffset(12,12)
mark.BackgroundTransparency=1;mark.Visible=false
mark.Parent=gui
local corners={}
for i=1,4 do
 local v=Instance.new("Frame")
 v.Name="Tick_"..i;v.BorderSizePixel=0
 v.AnchorPoint=Vector2.new(.5,.5)
 v.Size=UDim2.fromOffset(3,10)
 v.BackgroundColor3=tones.WARRIOR
 v.Parent=mark
 v.Rotation=i*90
 local positions={
  UDim2.fromOffset(6,-9),UDim2.fromOffset(21,6),
  UDim2.fromOffset(6,21),UDim2.fromOffset(-9,6),
 }
 v.Position=positions[i]
 table.insert(corners,v)
end
local function reduced():boolean
 return player:GetAttribute("EGGRUMBLE_ReducedEffects")==true
end
player:GetAttributeChangedSignal("EGGRUMBLE_ImpactSequence"):Connect(function()
 if reduced() then return end
 local now=os.clock()
 if now-lastPulse<RECENT_CD then return end
 lastPulse=now;start=now
 power=math.clamp(player:GetAttribute("EGGRUMBLE_ImpactWeight") or 1,1,3)
 pulse+=1
 local thisPulse=pulse
 local role=player:GetAttribute("EGGRUMBLE_ImpactRole") or "WARRIOR"
 local c=tones[role] or tones.WARRIOR
 mark.Visible=true;mark.Size=UDim2.fromOffset(12,12)
 for _,v in ipairs(corners) do
  v.BackgroundColor3=c;v.BackgroundTransparency=0
  TweenService:Create(v,TweenInfo.new(.16,Enum.EasingStyle.Quad,Enum.EasingDirection.Out),
   {BackgroundTransparency=1}):Play()
 end
 TweenService:Create(mark,TweenInfo.new(.16,Enum.EasingStyle.Quad,Enum.EasingDirection.Out),
  {Size=UDim2.fromOffset(26,26)}):Play()
 task.delay(.17,function()
  if thisPulse==pulse and mark.Parent then mark.Visible=false end
 end)
end)
RunService:BindToRenderStep("EGGRUMBLE_RealHitFeedback",Enum.RenderPriority.Camera.Value+1,function()
 if reduced() then return end
 local camera=workspace.CurrentCamera
 if not camera or camera.CameraType~=Enum.CameraType.Custom then return end
 local elapsed=os.clock()-start
 if elapsed<0 or elapsed>IMPACT_WINDOW then return end
 local envelope=(1-elapsed/IMPACT_WINDOW)*power/3
 local tilt=MAX_ANGLE*envelope
 camera.CFrame=camera.CFrame*
  CFrame.Angles(math.sin(elapsed*80)*tilt,math.cos(elapsed*70)*tilt*.6,0)*
  CFrame.new(0,0,-MAX_PUSH*envelope)
end)
player.AncestryChanged:Connect(function(_,parent)
 if not parent then
  RunService:UnbindFromRenderStep("EGGRUMBLE_RealHitFeedback")
 end
end)
