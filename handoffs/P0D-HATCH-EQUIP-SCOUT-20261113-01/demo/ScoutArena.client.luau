-- Studio-only 2-client mobile-friendly controls for private scout proof.
-- Real player-facing hatch/save/trading UI requires subsequent sole #220 integration.
local RunService=game:GetService("RunService")
if not RunService:IsStudio() then return end
local Players=game:GetService("Players")
local ReplicatedStorage=game:GetService("ReplicatedStorage")
local localPlayer=Players.LocalPlayer
local event=ReplicatedStorage:WaitForChild("EggRumbleScoutDemo",20)
if not event then return end
local gui=Instance.new("ScreenGui")
gui.Name="EggRumbleScoutDemoHUD"
gui.ResetOnSpawn=false
gui.IgnoreGuiInset=false
gui.Parent=localPlayer:WaitForChild("PlayerGui")
local function label(text, pos, sz, color)
    local l=Instance.new("TextLabel")
    l.Size=sz
    l.Position=pos
    l.BackgroundColor3=color or Color3.fromRGB(28,35,58)
    l.BackgroundTransparency=0.13
    l.BorderSizePixel=0
    l.TextColor3=Color3.fromRGB(250,250,255)
    l.TextStrokeTransparency=0.65
    l.TextScaled=true
    l.Font=Enum.Font.GothamBold
    l.Text=text
    l.Parent=gui
    return l
end
local status=label("魔獣の装備・召喚 実験 | 2人待機",UDim2.fromScale(.18,.035),
    UDim2.fromScale(.64,.07))
local inventory=label("図鑑：スターター偵察魔獣",UDim2.fromScale(.2,.115),
    UDim2.fromScale(.6,.075))
local message=label("孵化→装備→次戦で召喚してみよう",UDim2.fromScale(.16,.82),
    UDim2.fromScale(.68,.08))
local function button(text, pos, color)
    local b=Instance.new("TextButton")
    b.Position=pos
    b.Size=UDim2.fromScale(.24,.11)
    b.BackgroundColor3=color
    b.TextColor3=Color3.fromRGB(255,255,255)
    b.Text=text
    b.TextScaled=true
    b.Font=Enum.Font.GothamBold
    b.Parent=gui
    local corner=Instance.new("UICorner")
    corner.CornerRadius=UDim.new(0,9)
    corner.Parent=b
    return b
end
local summon=button("魔獣を召喚",UDim2.fromScale(.02,.62),Color3.fromRGB(41,111,189))
local equip=button("孵化魔獣を装備",UDim2.fromScale(.74,.62),Color3.fromRGB(93,154,80))
local lastState={equipped="starter_scout",ownsForest=false,ownsStar=false,phase="LOBBY"}
summon.MouseButton1Click:Connect(function()
    event:FireServer("SCOUT")
end)
equip.MouseButton1Click:Connect(function()
    local target=lastState.ownsStar and "star_scout" or
        (lastState.ownsForest and "forest_scout" or "starter_scout")
    event:FireServer("EQUIP",target)
end)
event.OnClientEvent:Connect(function(kind,payload)
    if kind=="STATE" and type(payload)=="table" then
        lastState=payload
        local equipped=tostring(payload.equipped or "starter_scout")
        local phase=tostring(payload.phase or "LOBBY")
        local team=tostring(payload.team or "?")
        status.Text="EGG RAID RUMBLE | "..team.." | "..phase.." | 第"..tostring(payload.epoch or 0).."試合"
        inventory.Text="装備："..equipped.." | 星空レア："..(payload.ownsStar and "所持" or "未入手")
    elseif kind=="HATCH" then
        message.Text="無料孵化で "..tostring(payload).." をゲット！ロビーで装備"
    elseif kind=="INFO" or kind=="ERROR" or kind=="SCOUT_FOUND" then
        message.Text=tostring(payload)
    end
end)
