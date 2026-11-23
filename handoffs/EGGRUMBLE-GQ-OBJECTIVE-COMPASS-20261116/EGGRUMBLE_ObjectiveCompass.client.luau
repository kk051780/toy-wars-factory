--!strict
-- EGGRUMBLE GQ independent objective compass; preview-only client presentation.
-- No remotes, reward authority, damage, item effects, or changes to gameplay ownership.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")
if not RunService:IsStudio() then return end -- Private preview. Official enablement belongs to #220.
local player = Players.LocalPlayer
local playerGui = player:WaitForChild("PlayerGui")
local SOURCE_ROOT = "EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW"
local UPDATE_SECONDS = 0.8
local INITIAL_SECONDS = 18
local arrows = {"↑","↗","→","↘","↓","↙","←","↖"}
local roles = {
 WARRIOR="武神", MAGE="魔法使い", NINJA="暗殺者",
 TRAPPER="超能力者", BUILDER="マッドサイエンティスト",
 BEAST="魔獣使い", ZOMBIE="呪術師",
}
if playerGui:FindFirstChild("EGGRUMBLE_GQ_ObjectiveCompass") then return end
local gui = Instance.new("ScreenGui")
gui.Name="EGGRUMBLE_GQ_ObjectiveCompass"
gui.ResetOnSpawn=false
gui.IgnoreGuiInset=false
gui.DisplayOrder=8
gui.Parent=playerGui
local toggle=Instance.new("TextButton")
toggle.Name="ObjectiveToggle"
toggle.Size=UDim2.fromOffset(52,30)
toggle.Position=UDim2.new(0.5,154,0,10)
toggle.BackgroundColor3=Color3.fromRGB(33,39,51)
toggle.BackgroundTransparency=0.15
toggle.Text="目標"
toggle.TextColor3=Color3.fromRGB(240,244,248)
toggle.TextSize=13
toggle.Font=Enum.Font.GothamMedium
toggle.Visible=false
toggle.Parent=gui
Instance.new("UICorner",toggle).CornerRadius=UDim.new(0,8)
-- Manual home guidance only. Server-side carried-egg state is deliberately not inferred.
local returnHome=Instance.new("TextButton")
returnHome.Name="ManualReturnHome"
returnHome.Size=UDim2.fromOffset(48,30)
returnHome.BackgroundColor3=Color3.fromRGB(51,63,78)
returnHome.BackgroundTransparency=.12
returnHome.Text="帰城"
returnHome.TextColor3=Color3.fromRGB(245,238,197)
returnHome.TextSize=12
returnHome.Font=Enum.Font.GothamMedium
returnHome.Visible=false
returnHome.Parent=gui
Instance.new("UICorner",returnHome).CornerRadius=UDim.new(0,8)
local bar=Instance.new("TextLabel")
bar.Name="OneLineObjective"
bar.AnchorPoint=Vector2.new(0.5,0)
bar.Position=UDim2.new(0.5,-29,0,10)
bar.Size=UDim2.fromOffset(294,30)
bar.BackgroundColor3=Color3.fromRGB(22,29,41)
bar.BackgroundTransparency=0.12
bar.TextColor3=Color3.fromRGB(248,250,255)
bar.TextSize=13
bar.Font=Enum.Font.GothamMedium
bar.TextTruncate=Enum.TextTruncate.AtEnd
bar.Text="目的地を確認中"
bar.Visible=false
bar.Parent=gui
Instance.new("UICorner",bar).CornerRadius=UDim.new(0,8)
local marker=Instance.new("BillboardGui")
marker.Name="ObjectiveWorldMarker"
marker.Size=UDim2.fromOffset(124,31)
marker.StudsOffsetWorldSpace=Vector3.new(0,8,0)
marker.AlwaysOnTop=false -- Respect walls and level geometry.
marker.MaxDistance=380
marker.Enabled=false
marker.Parent=playerGui
local markText=Instance.new("TextLabel")
markText.Size=UDim2.fromScale(1,1)
markText.BackgroundColor3=Color3.fromRGB(28,35,49)
markText.BackgroundTransparency=0.2
markText.TextColor3=Color3.fromRGB(255,236,167)
markText.Font=Enum.Font.GothamBold
markText.TextSize=12
markText.Text="目的地"
markText.Parent=marker
Instance.new("UICorner",markText).CornerRadius=UDim.new(0,9)
local expanded=true
local visibleSince=os.clock()
local lastMode=""
local manuallyReturning=false
local currentTarget:BasePart?=nil

local function isEnemy(mode:string, own:Model, other:Model, arena:Instance):boolean
 if own==other then return false end
 if mode=="BATTLE_ROYALE" then return true end
 if mode~="TEAM" then return false end
 local battlefield=arena:FindFirstChild("TacticalBattlefield")
 local ownVault=own:FindFirstChild("EggVault",true)
 local otherVault=other:FindFirstChild("EggVault",true)
 if not battlefield or not battlefield:IsA("BasePart")
    or not ownVault or not ownVault:IsA("BasePart")
    or not otherVault or not otherVault:IsA("BasePart") then return false end
 -- Opposing castle districts lie on different sides of the existing center road.
 -- Fail closed if the scene layout changes; never mark an unverified ally as enemy.
 return (ownVault.Position.X-battlefield.Position.X)
       *(otherVault.Position.X-battlefield.Position.X)<0
end

local function nearestActiveItem(arena:Instance, at:Vector3):(BasePart?,number)
 local items=arena:FindFirstChild("EGGRUMBLE_FieldItems")
 if not items then return nil,math.huge end
 local nearest:BasePart?=nil
 local best=math.huge
 for _,child in ipairs(items:GetChildren()) do
  if child:IsA("BasePart") and child.CanQuery and child.Transparency<0.5 then
   local distance=(child.Position-at).Magnitude
   if distance<best then best=distance;nearest=child end
  end
 end
 return nearest,best
end

local liveCoreColor=Color3.fromRGB(172,166,147)
local function hasRaidableEgg(castle:Model):boolean
 local core=castle:FindFirstChild("StandardCore")
 if not core or not core:IsA("BasePart") or core.Color~=liveCoreColor then return false end
 local board=core:FindFirstChildOfClass("BillboardGui")
 local label=board and board:FindFirstChildOfClass("TextLabel")
 if not label then return false end
 -- The Host uses different stock labels at spawn and on subsequent updates.
 local status=label.Text
 return string.match(status,"\nHP%d+ / 卵[1-9]%d*$")~=nil
     or string.match(status,"\n卵×[1-9]%d* / HP%d+$")~=nil
end

local function pickObjective(mode:string,arena:Instance,own:Model,at:Vector3,homeSelected:boolean):(BasePart?,string)
 if homeSelected then
  local home=own:FindFirstChild("OwnEggDeposit",true)
  if home and home:IsA("BasePart") then return home,"自城へ帰還（手動）" end
  return nil,"自城へ帰還（手動）"
 end
 local item,itemDistance=nearestActiveItem(arena,at)
 if item and itemDistance<=32 then return item,"近くの物資を取る" end
 local boss=arena:FindFirstChild("NEUTRAL_BOSS_STONE_GIANT",true)
 if boss and boss:IsA("Model") then
  local core=boss:FindFirstChild("WeakCore",true) or boss:FindFirstChildWhichIsA("BasePart",true)
  if core and core:IsA("BasePart") and (core.Position-at).Magnitude<=65 then
   return core,"巨人の弱点を狙う"
  end
 end
 local closest:BasePart?=nil
 local best=math.huge
 for _,model in ipairs(arena:GetChildren()) do
  if model:IsA("Model") and model.Name:sub(1,7)=="Castle_"
      and isEnemy(mode,own,model,arena) then
   local vault=model:FindFirstChild("EggVault",true)
   if vault and vault:IsA("BasePart") and hasRaidableEgg(model) then
    local dist=(vault.Position-at).Magnitude
    if dist<best then best=dist;closest=vault end
   end
  end
 end
 if closest then return closest,"敵城の卵を奪う → 自城へ納入" end
 local deposit=own:FindFirstChild("OwnEggDeposit",true)
 if deposit and deposit:IsA("BasePart") then return deposit,"自城を防衛・卵を納入" end
 return nil,"自城を防衛"
end

local function directionTo(from:Vector3,to:Vector3):string
 local camera=workspace.CurrentCamera
 if not camera then return "•" end
 local delta=Vector3.new(to.X-from.X,0,to.Z-from.Z)
 if delta.Magnitude<0.1 then return "•" end
 local unit=delta.Unit
 local look=camera.CFrame.LookVector
 local right=camera.CFrame.RightVector
 local angle=math.atan2(right:Dot(unit),look:Dot(unit))
 local octant=(math.floor(angle/(math.pi/4)+0.5)%8+8)%8+1
 return arrows[octant]
end

-- Keep the single objective row and mobile touch toggle on narrow Android screens.
local function layoutForViewport()
 local camera=workspace.CurrentCamera
 local width=if camera then camera.ViewportSize.X else 360
 -- Two short touch controls fit even a 320-pixel screen.
 local barWidth=math.min(294,math.max(90,width-132))
 local groupWidth=barWidth+116
 local left=math.max(4,(width-groupWidth)/2)
 bar.Size=UDim2.fromOffset(barWidth,30)
 bar.Position=UDim2.fromOffset(left+barWidth/2,10)
 returnHome.Position=UDim2.fromOffset(left+barWidth+6,10)
 toggle.Position=UDim2.fromOffset(left+barWidth+60,10)
end

local function refresh()
 layoutForViewport()
 local mode=player:GetAttribute("EGGRUMBLE_QueuedMode")
 local world=workspace:FindFirstChild(SOURCE_ROOT)
 local arena=if typeof(mode)=="string" and world then world:FindFirstChild(mode.."_Arena") else nil
 local own=if arena then arena:FindFirstChild("Castle_"..tostring(player.UserId)) else nil
 local battlefield=if arena then arena:FindFirstChild("TacticalBattlefield") else nil
 local character=player.Character
 local root=if character then character:FindFirstChild("HumanoidRootPart") else nil
 local h=if character then character:FindFirstChildOfClass("Humanoid") else nil
 local inArena=false
 if battlefield and battlefield:IsA("BasePart") and root and root:IsA("BasePart") then
  local dx=math.abs(root.Position.X-battlefield.Position.X)
  local dz=math.abs(root.Position.Z-battlefield.Position.Z)
  inArena=dx<=battlefield.Size.X/2+25 and dz<=battlefield.Size.Z/2+25
 end
 local phase=arena and arena:GetAttribute("EGGRUMBLE_MatchPhase")
 if not inArena or (phase~=nil and phase~="ACTIVE") or not own or not own:IsA("Model")
   or not h or h.Health<=0 or player:GetAttribute("EGGRUMBLE_Eliminated")==true then
  toggle.Visible=false;bar.Visible=false;returnHome.Visible=false;marker.Enabled=false;marker.Adornee=nil
  currentTarget=nil;lastMode="";manuallyReturning=false
  return
 end
 if mode~=lastMode then
  lastMode=mode;expanded=true;visibleSince=os.clock();manuallyReturning=false
 end
 local target,objective=pickObjective(mode,arena,own,root.Position,manuallyReturning)
 currentTarget=target
 if expanded and os.clock()-visibleSince>INITIAL_SECONDS then expanded=false end
 toggle.Visible=true
 toggle.Text=if expanded then "閉じる" else "目標"
 returnHome.Visible=expanded
 returnHome.Text=if manuallyReturning then "攻略" else "帰城"
 bar.Visible=expanded
 local role=player:GetAttribute("EGGRUMBLE_SelectedRole")
 local roleText=if typeof(role)=="string" then (roles[role] or "") else ""
 local suffix=if roleText~="" then " / "..roleText else ""
 if target then
  local dist=math.floor((target.Position-root.Position).Magnitude+0.5)
  bar.Text=directionTo(root.Position,target.Position).." "..objective.." "..tostring(dist).."stud"..suffix
  marker.Adornee=target
  markText.Text=objective
 else
  bar.Text=objective..suffix
  marker.Adornee=nil
 end
 marker.Enabled=expanded and target~=nil
end

returnHome.Activated:Connect(function()
 if not toggle.Visible then return end
 manuallyReturning=not manuallyReturning
 expanded=true
 visibleSince=os.clock()
 refresh()
end)
toggle.Activated:Connect(function()
 if not toggle.Visible then return end
 expanded=not expanded
 visibleSince=os.clock()
 refresh()
end)
UserInputService.InputBegan:Connect(function(input:InputObject,processed:boolean)
 if processed or not toggle.Visible then return end
 if input.KeyCode==Enum.KeyCode.H then
  manuallyReturning=not manuallyReturning
  expanded=true
 elseif input.KeyCode==Enum.KeyCode.G then
  expanded=not expanded
 else
  return
 end
 visibleSince=os.clock()
 refresh()
end)
local elapsed=UPDATE_SECONDS
RunService.Heartbeat:Connect(function(dt:number)
 elapsed+=dt
 if elapsed<UPDATE_SECONDS then return end
 elapsed=0
 refresh()
end)
