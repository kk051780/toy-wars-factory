-- Standalone private Studio preview ONLY. Not installed in the game.
local RunService=game:GetService("RunService")
if not RunService:IsStudio() then return end
local Players=game:GetService("Players")
local ReplicatedStorage=game:GetService("ReplicatedStorage")
local Rules=require(ReplicatedStorage:WaitForChild("RumbleLinkCueRules"))
local player=Players.LocalPlayer
local gui=Instance.new("ScreenGui")
gui.Name="RumbleLinkStudioOnly"
gui.ResetOnSpawn=false
gui.DisplayOrder=8
gui.Parent=player:WaitForChild("PlayerGui")
local box=Instance.new("Frame")
box.Name="Cue"
box.Size=UDim2.new(0.58,0,0,70)
box.Position=UDim2.new(0.21,0,0.075,0)
box.BackgroundColor3=Color3.fromRGB(23,36,56)
box.BackgroundTransparency=0.12
box.BorderSizePixel=0
box.Visible=false
box.Parent=gui
local corner=Instance.new("UICorner")
corner.CornerRadius=UDim.new(0,10)
corner.Parent=box
local function line(y,h,maxsize,font,color)
 local t=Instance.new("TextLabel")
 t.Size=UDim2.new(1,-16,0,h)
 t.Position=UDim2.new(0,8,0,y)
 t.BackgroundTransparency=1
 t.TextScaled=true
 t.Font=font
 t.TextColor3=color
 t.Parent=box
 local c=Instance.new("UITextSizeConstraint")
 c.MaxTextSize=maxsize
 c.Parent=t
 return t
end
local title=line(3,32,21,Enum.Font.GothamBold,Color3.fromRGB(255,245,178))
local detail=line(37,23,15,Enum.Font.Gotham,Color3.fromRGB(255,255,255))
local state=Rules.new()
local token=0
local kinds={"SCOUT_ASSIST","SEA_ESCORT","TRAP_GUARD","CASTLE_RECAPTURE"}
for i,kind in ipairs(kinds) do
 if not gui.Parent then break end
 task.wait(2.6)
 local now=workspace:GetServerTimeNow()
 -- Synthetic demo packets are never routed to game Remote/rewards.
 local c=Rules.accept(state,{roundId="PREVIEW_STUDIO_ONLY",roundSerial=1,seq=i,
  kind=kind,team="BLUE",expiresAt=now+2},now,"BLUE")
 if c then
  token+=1
  local current=token
  title.Text=c.icon.." "..c.title
  detail.Text=c.detail
  box.Visible=true
  task.delay(c.duration,function()
   if token==current and box.Parent then box.Visible=false end
  end)
 end
end
