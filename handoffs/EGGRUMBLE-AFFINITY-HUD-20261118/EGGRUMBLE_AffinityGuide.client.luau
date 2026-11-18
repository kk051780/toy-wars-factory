-- BATTLE-765 LANE3: tiny opt-in affinity tutorial; no second combat/HUD authority.
-- Existing #778 owns geometry/VFX. We only show information, not hit/weakness outcomes.
local Players=game:GetService("Players")
local ReplicatedStorage=game:GetService("ReplicatedStorage")
local player=Players.LocalPlayer
if not player then return end
local module=ReplicatedStorage:WaitForChild("EGGRUMBLE_AffinityGuidePolicy",10)
if not module or not module:IsA("ModuleScript") then return end
local ok,Guide=pcall(require,module)
if not ok or type(Guide)~="table" then return end
local guiParent=player:WaitForChild("PlayerGui",10)
if not guiParent then return end
if guiParent:FindFirstChild("EGGRUMBLE_AffinityGuideUI") then return end
local ui=Instance.new("ScreenGui")
ui.Name="EGGRUMBLE_AffinityGuideUI"
ui.IgnoreGuiInset=false
ui.ResetOnSpawn=false
ui.DisplayOrder=6
ui.Parent=guiParent

local button=Instance.new("TextButton")
button.Name="AffinityHelp"
button.AnchorPoint=Vector2.new(1,0)
button.Position=UDim2.new(1,-8,0.38,0)
button.Size=UDim2.fromOffset(52,44)
button.BackgroundColor3=Color3.fromRGB(36,45,64)
button.BorderSizePixel=0
button.TextColor3=Color3.fromRGB(255,255,255)
button.Font=Enum.Font.GothamBold
button.TextSize=14
button.Text="属性 ?"
button.Parent=ui
local curve=Instance.new("UICorner")
curve.CornerRadius=UDim.new(0,10)
curve.Parent=button

local panel=Instance.new("TextLabel")
panel.Name="AffinityInfo"
panel.AnchorPoint=Vector2.new(1,0)
panel.Position=UDim2.new(1,-66,0.38,0)
panel.Size=UDim2.fromOffset(212,92)
panel.BackgroundColor3=Color3.fromRGB(27,34,47)
panel.BackgroundTransparency=0.05
panel.BorderSizePixel=0
panel.TextColor3=Color3.fromRGB(255,255,255)
panel.Font=Enum.Font.GothamMedium
panel.TextSize=13
panel.TextWrapped=true
panel.TextXAlignment=Enum.TextXAlignment.Left
panel.TextYAlignment=Enum.TextYAlignment.Center
panel.Text="属性相性（無料の基本技）\n"..Guide.help().."\n攻撃結果はサーバー判定"
panel.Visible=false
panel.Parent=ui
local padding=Instance.new("UIPadding")
padding.PaddingLeft=UDim.new(0,8)
padding.PaddingRight=UDim.new(0,8)
padding.Parent=panel
local panelCurve=Instance.new("UICorner")
panelCurve.CornerRadius=UDim.new(0,10)
panelCurve.Parent=panel

local lastSequence=0
local generation=0
local currentLabel=nil
local function renderGuide()
 if not currentLabel then
  panel.Text="属性相性（無料の基本技）\n"..Guide.help().."\n実際の命中・倍率はサーバー判定"
 else
  panel.Text="直近の技属性: "..currentLabel.shortLabel.."\n"..currentLabel.matchup.."\n"..(currentLabel.special or "攻撃の実命中・倍率は未表示")
 end
end
local function showToggle()
 panel.Visible=not panel.Visible
 if not panel.Visible then return end
 generation+=1
 local current=generation
 task.delay(7,function()
  if ui.Parent and generation==current then panel.Visible=false end
 end)
end
button.Activated:Connect(showToggle)
local function confirmedServerCast()
 local sig=player:GetAttribute("EGGRUMBLE_SkillCastSignature")
 local role=player:GetAttribute("EGGRUMBLE_Role")
 local view,seq=Guide.fromVerifiedServerCast(sig,role)
 if not view or not seq or seq<=lastSequence then return end
 if player:GetAttribute("EGGRUMBLE_Eliminated")==true then return end
 local avatar=player.Character
 local hum=avatar and avatar:FindFirstChildOfClass("Humanoid")
 if not hum or hum.Health<=0 then return end
 lastSequence=seq
 currentLabel=view
 if panel.Visible then renderGuide() end
end
-- Observe only future server-written cast signatures. Never replay on initial GUI attachment.
player:GetAttributeChangedSignal("EGGRUMBLE_SkillCastSignature"):Connect(confirmedServerCast)
player:GetAttributeChangedSignal("EGGRUMBLE_Role"):Connect(function()
 currentLabel=nil
 renderGuide()
end)
player.CharacterAdded:Connect(function()
 currentLabel=nil
 panel.Visible=false
end)
button.Activated:Connect(renderGuide)
