--!strict
-- GQ8_RC85_FIRST90_REAL69_STUDIO_GUIDE_20261120
-- Actual first-session 90-second on-character guide adapted to V3.
-- One LOCAL guide only; never a second server Game/Store/HUD/Remote or game authority.
-- Unlike original S1 First90 HUD, this provides a small nonblocking 3D bubble.
-- Functional semantic equality with every old S1 First90 step is NOT claimed.
local RunService=game:GetService("RunService")
if not RunService:IsStudio() then return end
local Players=game:GetService("Players")
local player=Players.LocalPlayer
if not player then return end
local DURATION=90
local STEP1=22
local STEP2=48
local POLL=.5
local UI_NAME="EGGRUMBLE_First90WorldHint_Real69"
local sourceId="GQ8_RC85_FIRST90_REAL69_STUDIO_GUIDE_20261120"
local playerGui=player:WaitForChild("PlayerGui",12)
if not playerGui or not playerGui:IsA("PlayerGui") then return end
if playerGui:FindFirstChild(UI_NAME) then return end

local billboard=Instance.new("BillboardGui")
billboard.Name=UI_NAME
billboard.AlwaysOnTop=false
billboard.MaxDistance=32
billboard.Size=UDim2.fromOffset(210,43)
billboard.StudsOffsetWorldSpace=Vector3.new(0,4.3,0)
billboard.Enabled=false
billboard:SetAttribute("FeatureId",sourceId)
billboard:SetAttribute("SessionOnly",true)
billboard.Parent=playerGui

local label=Instance.new("TextLabel")
label.Name="Cue"
label.Size=UDim2.fromScale(1,1)
label.BorderSizePixel=0
label.BackgroundColor3=Color3.fromRGB(25,40,64)
label.BackgroundTransparency=.26
label.TextColor3=Color3.fromRGB(246,251,255)
label.TextStrokeTransparency=.55
label.Font=Enum.Font.GothamBold
label.TextScaled=false
label.TextSize=12
label.TextWrapped=true
label.Text=""
label.Parent=billboard
local corner=Instance.new("UICorner")
corner.CornerRadius=UDim.new(0,8)
corner.Parent=label

local started=os.clock()
local alive=true
local currentCharacter:Model?=nil
local respawnConnection:RBXScriptConnection?=nil
local ancestryConnection:RBXScriptConnection?=nil
local function attach(character:Model?)
 currentCharacter=character
 if respawnConnection then
  respawnConnection:Disconnect()
  respawnConnection=nil
 end
 billboard.Adornee=nil
 billboard.Enabled=false
 if not character then return end
 local head=character:FindFirstChild("Head")
 if head and head:IsA("BasePart") then
  billboard.Adornee=head
 else
  -- Only wait on the current avatar. Old callbacks cannot re-attach after respawn.
  respawnConnection=character.ChildAdded:Connect(function(child)
   if alive and currentCharacter==character and child.Name=="Head"
    and child:IsA("BasePart") then
    billboard.Adornee=child
   end
  end)
 end
end
local characterConnection=player.CharacterAdded:Connect(attach)
attach(player.Character)
ancestryConnection=player.AncestryChanged:Connect(function(_,parent)
 if not parent then alive=false end
end)
-- GQ8_FB014_CANONICAL_ROLE_MODE_V3_20261120
-- Use the server's actual role stand acknowledgement during lobby and its
-- canonical BATTLE_ROYALE mode. Combat role is a fallback after deployment.
local function cue(now:number):string
 local role=player:GetAttribute("EGGRUMBLE_SelectedRole")
 if type(role)~="string" or role=="" then
  role=player:GetAttribute("EGGRUMBLE_Role")
 end
 local mode=player:GetAttribute("EGGRUMBLE_QueuedMode")
 if player:GetAttribute("EGGRUMBLE_Eliminated")==true then
  return ""
 end
 if type(mode)~="string" or (mode~="TEAM" and mode~="BATTLE_ROYALE") then
  return "1/3  役職と対戦モードを選ぼう"
 end
 if type(role)~="string" or role=="" then
  return "1/3  好きな役職を選んで出撃！"
 end
 local elapsed=now-started
 if elapsed<STEP1 then
  return "1/3  " .. (mode=="TEAM" and "チーム戦に参加しよう" or "全員対戦に参加しよう")
 end
 if elapsed<STEP2 then
  return "2/3  卵を奪う／敵の城を攻める"
 end
 return "3/3  卵を運び帰る・仲間と連携！"
end

task.spawn(function()
 while alive and player.Parent==Players do
  local now=os.clock()
  if now-started>=DURATION then break end
  local message=cue(now)
  local head=billboard.Adornee
  billboard.Enabled=message~="" and head~=nil and head.Parent~=nil
   and player.Character==currentCharacter
  if billboard.Enabled and label.Text~=message then
   label.Text=message
  end
  task.wait(POLL)
 end
 alive=false
 if respawnConnection then respawnConnection:Disconnect() end
 if ancestryConnection then ancestryConnection:Disconnect() end
 characterConnection:Disconnect()
 billboard:Destroy()
end)
