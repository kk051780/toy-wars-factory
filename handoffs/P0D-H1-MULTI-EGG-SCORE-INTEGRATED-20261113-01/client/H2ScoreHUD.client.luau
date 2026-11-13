--!strict
-- Original H2 five-egg child-friendly scoreboard, READ-ONLY.
-- Existing S1 HUD and EggJoy remain untouched; no client scoring authority.
local RunService=game:GetService("RunService")
if not RunService:IsStudio() then return end
local Players=game:GetService("Players")
local ReplicatedStorage=game:GetService("ReplicatedStorage")
local player=Players.LocalPlayer
local remote=ReplicatedStorage:WaitForChild("TrapRaidersS1Remote")
local gui=Instance.new("ScreenGui")
gui.Name="H2FiveEggScoreOverlay"
gui.ResetOnSpawn=false
gui.IgnoreGuiInset=true
gui.Enabled=false
gui.DisplayOrder=25
gui.Parent=player:WaitForChild("PlayerGui")
local panel=Instance.new("Frame")
panel.Name="H2FiveEggScorePanel"
panel.Size=UDim2.fromOffset(332,108)
panel.Position=UDim2.new(.5,-166,0,14)
panel.BackgroundColor3=Color3.fromRGB(19,28,51)
panel.BackgroundTransparency=.1
panel.Parent=gui
local corner=Instance.new("UICorner")
corner.CornerRadius=UDim.new(0,12)
corner.Parent=panel
local border=Instance.new("UIStroke")
border.Color=Color3.fromRGB(225,210,108)
border.Thickness=2
border.Parent=panel
local function textLabel(name,y,size)
    local label=Instance.new("TextLabel")
    label.Name=name
    label.Size=UDim2.new(1,-12,0,size)
    label.Position=UDim2.fromOffset(6,y)
    label.BackgroundTransparency=1
    label.TextColor3=Color3.fromRGB(255,247,214)
    label.Font=Enum.Font.GothamBold
    label.TextScaled=true
    label.Parent=panel
    return label
end
local title=textLabel("ModeName",4,22)
local scoreboard=textLabel("ScoreBoard",28,39)
local notice=textLabel("NextObjective",72,28)
-- Avoid two stacked scoreboards in the same mobile viewport.
-- Existing HUD stays active for buttons; only its old H0 score/status labels
-- become hidden while a trusted server SCORE_MODE snapshot is active.
local previousInstructions: string? = nil
local function syncOriginalHud(scoreEnabled: boolean)
    local old=player:FindFirstChild("PlayerGui")
    local hud=old and old:FindFirstChild("TrapRaidersS1HUD")
    if not hud then return end
    local score=hud:FindFirstChild("Score")
    local status=hud:FindFirstChild("Status")
    if score and score:IsA("GuiObject") then score.Visible=not scoreEnabled end
    if status and status:IsA("GuiObject") then status.Visible=not scoreEnabled end
    local instructions=hud:FindFirstChild("Instructions")
    if instructions and instructions:IsA("TextLabel") then
        if previousInstructions==nil then previousInstructions=instructions.Text end
        instructions.Text=if scoreEnabled then
            "🥚 5個の卵を守って、敵の卵を持ち帰ろう！4分で高得点が勝ち"
            else previousInstructions
    end
end
title.Text="🥚 エッグ・スコアバトル"
scoreboard.Text="🔴 0 : 0 🔵   4:00"
notice.Text="卵をぬすむ・守る・城に届ける！"
local lastUpdate=-1
local lastSerial=-1
remote.OnClientEvent:Connect(function(data)
    if type(data)~="table" or data.kind~="SNAPSHOT" then return end
    if type(data.serial)~="number" or type(data.updateId)~="number" then return end
    if data.serial<lastSerial or (data.serial==lastSerial and data.updateId<=lastUpdate) then return end
    lastSerial=data.serial;lastUpdate=data.updateId
    if data.scoreMode~=true then gui.Enabled=false; syncOriginalHud(false); return end
    gui.Enabled=true
    syncOriginalHud(true)
    local scores=if type(data.scores)=="table" then data.scores else {}
    local red=if type(scores.RED)=="number" then math.floor(scores.RED) else 0
    local blue=if type(scores.BLUE)=="number" then math.floor(scores.BLUE) else 0
    local seconds=if type(data.scoreTime)=="number" then math.clamp(math.floor(data.scoreTime),0,270) else 0
    local minute=math.floor(seconds/60)
    local second=seconds%60
    local mode=if data.scorePhase=="OVERTIME" then "⚡ 延長！中央の卵が決勝点"
      elseif data.phase=="RESULTS" then "🏆 けっか発表！"
      else "🥚 5こを奪い合う得点戦"
    title.Text=mode
    scoreboard.Text=string.format("🔴 %d : %d 🔵     %d:%02d",red,blue,minute,second)
    local side=data.team
    local held=data.carrying
    if data.phase=="RESULTS" then
        notice.Text=if data.winner==side then "やった！ チームの勝ち！"
            elseif data.winner=="DRAW" then "ひきわけ！ また遊ぼう！"
            else "もういっかい！ つぎこそ勝とう"
    elseif type(held)=="string" and held~="" then
        notice.Text="🥚 卵をもってる！ 自分の城にとどけよう"
    else
        notice.Text="🥚 卵をさがして！ まもって！ とどけよう！"
    end
end)
