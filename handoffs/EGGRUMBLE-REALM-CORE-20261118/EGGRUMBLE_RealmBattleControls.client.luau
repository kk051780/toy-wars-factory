--!nonstrict
-- GQ8 REALM CORE client: keyboard and touch flight/mounted combat controls.
-- Input is untrusted; server verifies live pilot, current match and rate limits.
local Players=game:GetService("Players")
local ReplicatedStorage=game:GetService("ReplicatedStorage")
local UIS=game:GetService("UserInputService")
local RunService=game:GetService("RunService")
local player=Players.LocalPlayer
local remote=ReplicatedStorage:WaitForChild("EGGRUMBLE_RealmBattleIntent_V1",20)
if not remote then return end
local gui=Instance.new("ScreenGui")
gui.Name="GQ8_RealmBattleControls"
gui.ResetOnSpawn=false
gui.DisplayOrder=28
gui.Parent=player:WaitForChild("PlayerGui")
local frame=Instance.new("Frame")
frame.Name="Controls"
frame.Size=UDim2.fromOffset(218,290)
frame.Position=UDim2.new(1,-230,1,-330)
frame.BackgroundColor3=Color3.fromRGB(22,30,43)
frame.BackgroundTransparency=.20
frame.Visible=false
frame.Parent=gui
local heading=Instance.new("TextLabel")
heading.Size=UDim2.new(1,0,0,28)
heading.BackgroundTransparency=1
heading.TextColor3=Color3.fromRGB(240,242,255)
heading.TextScaled=true
heading.Font=Enum.Font.GothamBold
heading.Text="陸海空・搭乗戦"
heading.Parent=frame
local currentKind="NONE"
local held={UP=false,DOWN=false,LEFT=false,RIGHT=false}
local function action(id)
 if currentKind=="NONE" then return end
 remote:FireServer("FIRE",id)
end
local function button(name,label,x,y,callback,hold)
 local b=Instance.new("TextButton")
 b.Name=name;b.Text=label
 b.Size=UDim2.fromOffset(100,39)
 b.Position=UDim2.fromOffset(x,y)
 b.Font=Enum.Font.GothamBold;b.TextSize=14
 b.BackgroundColor3=Color3.fromRGB(58,104,154)
 b.TextColor3=Color3.fromRGB(255,255,255)
 b.Parent=frame
 if hold then
  b.InputBegan:Connect(function(input)
   if input.UserInputType==Enum.UserInputType.Touch
    or input.UserInputType==Enum.UserInputType.MouseButton1 then held[hold]=true end
  end)
  b.InputEnded:Connect(function(input)
   if input.UserInputType==Enum.UserInputType.Touch
    or input.UserInputType==Enum.UserInputType.MouseButton1 then held[hold]=false end
  end)
 else b.Activated:Connect(callback) end
 return b
end
local up=button("PitchUp","機首 上昇",5,34,nil,"UP")
local down=button("PitchDown","機首 下降",111,34,nil,"DOWN")
local left=button("BankLeft","左ロール",5,78,nil,"LEFT")
local right=button("BankRight","右ロール",111,78,nil,"RIGHT")
local gun=button("Gun","機銃 G",5,122,function()action("GUN")end)
local bomb=button("Bomb","爆撃 B",111,122,function()action("BOMB")end)
local cannon=button("Cannon","艦砲 C",5,166,function()action("CANNON")end)
local breath=button("Breath","魔獣 V",111,166,function()action("BREATH")end)
local hydro=button("Hydro","水中波 H",5,210,function()action("HYDRO")end)
local notice=Instance.new("TextLabel")
notice.Size=UDim2.fromOffset(100,40)
notice.Position=UDim2.fromOffset(111,210)
notice.BackgroundTransparency=1
notice.TextColor3=Color3.fromRGB(252,210,95)
notice.TextScaled=true
notice.TextWrapped=true
notice.Text="矢印/操縦桿で旋回"
notice.Parent=frame
local keys={
 [Enum.KeyCode.R]="UP",[Enum.KeyCode.F]="DOWN",
 [Enum.KeyCode.Q]="LEFT",[Enum.KeyCode.E]="RIGHT"}
local fires={
 [Enum.KeyCode.G]="GUN",[Enum.KeyCode.B]="BOMB",
 [Enum.KeyCode.C]="CANNON",[Enum.KeyCode.V]="BREATH",
 [Enum.KeyCode.H]="HYDRO"}
UIS.InputBegan:Connect(function(input,processed)
 if processed then return end
 if keys[input.KeyCode] then held[keys[input.KeyCode]]=true end
 if fires[input.KeyCode] then action(fires[input.KeyCode]) end
end)
UIS.InputEnded:Connect(function(input)
 if keys[input.KeyCode] then held[keys[input.KeyCode]]=false end
end)
local function pilotKind()
 if player:GetAttribute("EGGRUMBLE_RealmDepth")=="SUBSEA" then return "SUBSEA" end
 local character=player.Character
 local hum=character and character:FindFirstChildOfClass("Humanoid")
 local seat=hum and hum.SeatPart
 if not seat or seat.Name~="PilotSeat" then return "NONE" end
 local m=seat.Parent
 if not m or not m:IsA("Model") then return "NONE" end
 local kind=m:GetAttribute("RealmKind")
 if kind=="FIGHTER" and m:GetAttribute("RealmPilot")==player.UserId then return "FIGHTER" end
 if m.Name:match("_(%d+)$")~=tostring(player.UserId) then return "NONE" end
 if m.Name:find("_SEA_BOAT_") then return "SHIP" end
 if m.Name:find("_SEA_BEAST_") then return "SEA_BEAST" end
 if m.Name:find("_SKY_BEAST_") then return "SKY_BEAST" end
 if m.Name:find("_AIRSHIP_") then return "AIRSHIP" end
 return "NONE"
end
local elapsed=0
RunService.RenderStepped:Connect(function(dt)
 elapsed+=dt
 if elapsed<.13 then return end
 elapsed=0
 local previous=currentKind
 currentKind=pilotKind()
 local active=currentKind~="NONE"
 frame.Visible=active
 local isFlight=currentKind=="FIGHTER"
 local isAir=currentKind=="AIRSHIP"
 local isBeast=currentKind=="SEA_BEAST" or currentKind=="SKY_BEAST"
 local isShip=currentKind=="SHIP"
 local isDiver=currentKind=="SUBSEA"
 for _,b in ipairs({up,down,left,right}) do b.Visible=isFlight end
 gun.Visible=isFlight or isAir
 bomb.Visible=isFlight
 cannon.Visible=isShip
 breath.Visible=isBeast
 hydro.Visible=isDiver
 notice.Visible=isFlight
 if isFlight then
  local character=player.Character
  local hum=character and character:FindFirstChildOfClass("Humanoid")
  local seat=hum and hum.SeatPart
  local core=seat and seat.Parent and seat.Parent.Parent
  local weather=core and core:GetAttribute("RealmWeather") or "CLEAR"
  local warning=core and core:GetAttribute("LightningWarning")==true
  notice.Text=warning and "雷接近！高度を下げよう"
   or weather=="THUNDER" and "雷雨：高度注意"
   or weather=="WIND" and "強風：速度低下"
   or "操縦：R/F/Q/E"
 end
 heading.Text=currentKind=="FIGHTER" and "戦闘機・空中戦"
  or currentKind=="SHIP" and "軍艦・海上戦"
  or currentKind=="SUBSEA" and "海中戦・水中波"
  or currentKind=="AIRSHIP" and "飛行艇・機銃"
  or isBeast and "騎乗魔獣戦" or "陸海空・搭乗戦"
 if isFlight then
  local pitch=(held.UP or UIS:IsKeyDown(Enum.KeyCode.R)) and 1
   or (held.DOWN or UIS:IsKeyDown(Enum.KeyCode.F)) and -1 or 0
  local roll=(held.LEFT or UIS:IsKeyDown(Enum.KeyCode.Q)) and -1
   or (held.RIGHT or UIS:IsKeyDown(Enum.KeyCode.E)) and 1 or 0
  remote:FireServer("FLIGHT",{pitch=pitch,roll=roll})
 elseif previous=="FIGHTER" then
  for k in pairs(held) do held[k]=false end
 end
end)
