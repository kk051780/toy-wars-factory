--!strict
-- Child-readable view of server-owned H2 lab state. NO client actions or Remote.
local Players=game:GetService("Players")
local ReplicatedStorage=game:GetService("ReplicatedStorage")
local RunService=game:GetService("RunService")
if not RunService:IsStudio() then return end
local player=Players.LocalPlayer
local state=ReplicatedStorage:WaitForChild("P0D_H2_MultiEggScoreState",20)
if state==nil then return end
local gui=Instance.new("ScreenGui")
gui.Name="H2FiveEggScore_StudioOnly"
gui.ResetOnSpawn=false;gui.IgnoreGuiInset=false
gui.DisplayOrder=5;gui.Parent=player:WaitForChild("PlayerGui")
local root=Instance.new("Frame")
root.Name="ScoreAndObjective"
root.AnchorPoint=Vector2.new(.5,0)
root.Position=UDim2.new(.5,0,0,8)
root.Size=UDim2.new(.76,0,0,117)
root.BackgroundColor3=Color3.fromRGB(18,31,51)
root.BackgroundTransparency=.14
root.Parent=gui
local limit=Instance.new("UISizeConstraint")
limit.MinSize=Vector2.new(250,107)
limit.MaxSize=Vector2.new(650,117);limit.Parent=root
local corner=Instance.new("UICorner")
corner.CornerRadius=UDim.new(0,11);corner.Parent=root
local function txt(name,y,size,color):TextLabel
    local t=Instance.new("TextLabel")
    t.Name=name;t.Position=UDim2.new(0,7,0,y)
    t.Size=UDim2.new(1,-14,0,size)
    t.BackgroundTransparency=1
    t.TextColor3=color;t.Font=Enum.Font.GothamBold
    t.TextSize=if name=="TeamScores" then 20 else 14
    t.TextXAlignment=Enum.TextXAlignment.Center
    t.TextTruncate=Enum.TextTruncate.AtEnd
    t.Parent=root;return t
end
local title=txt("TeamScores",4,32,Color3.fromRGB(255,245,182))
local sub=txt("ClockStatus",37,24,Color3.fromRGB(240,240,245))
local guide=txt("Objective",67,41,Color3.fromRGB(182,233,248))
guide.TextWrapped=true
local function repaint()
    local red=state:GetAttribute("RED")
    local blue=state:GetAttribute("BLUE")
    local remaining=state:GetAttribute("SECONDS")
    local active=state:GetAttribute("ACTIVE")
    local winner=state:GetAttribute("WINNER")
    local side=player:GetAttribute("H2LabTeam")
    title.Text="🔴 "..tostring(red or 0).."  :  "..tostring(blue or 0).." 🔵"
    if winner and winner~="" then
        sub.Text=if winner=="DRAW" then "引き分け！" else winner.." の勝利！"
    elseif active then
        sub.Text="残り "..tostring(remaining or 0).." 秒｜あなた："..tostring(side or "?")
    else
        sub.Text="準備中｜赤・青の2人が来ると4分ゲーム開始"
    end
    guide.Text="🥚 卵は5個！ E／タップで拾う → 自陣の黄色い台に納める\n持っているだけでも点数が入る！自分の卵も守って運べる"
end
for _,a in ipairs({"RED","BLUE","SECONDS","ACTIVE","WINNER"}) do
    state:GetAttributeChangedSignal(a):Connect(repaint)
end
player:GetAttributeChangedSignal("H2LabTeam"):Connect(repaint)
repaint()
