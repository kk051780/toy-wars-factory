--!strict
-- TOY WARS FACTORY v1.2: lightweight touch + keyboard UI.
local Players=game:GetService("Players")
local ReplicatedStorage=game:GetService("ReplicatedStorage")
local player=Players.LocalPlayer
-- Show a useful queue state before waiting for a workshop slot (max four plots).
local gui=Instance.new("ScreenGui")
gui.Name="ToyWarsHUD"
gui.ResetOnSpawn=false
gui.DisplayOrder=10
gui.Parent=player:WaitForChild("PlayerGui")
local waiting=Instance.new("TextLabel")
waiting.Name="WorkshopQueueNotice"
waiting.Size=UDim2.new(0.76,0,0,54)
waiting.Position=UDim2.new(0.12,0,0.4,0)
waiting.BackgroundColor3=Color3.fromRGB(23,35,54)
waiting.TextColor3=Color3.fromRGB(248,251,255)
waiting.Font=Enum.Font.GothamBold
waiting.TextScaled=true
waiting.TextWrapped=true
waiting.Text="Waiting for a free workshop slot..."
waiting.Parent=gui
-- Show queue feedback before replicated assets can delay this LocalScript.
local stats=player:WaitForChild("leaderstats")
-- Allocation is known; keep feedback accurate while status values replicate.
waiting.Text="Preparing your workshop..."
local event=ReplicatedStorage:WaitForChild("ToyWarsSelectUnit")
local B=require(ReplicatedStorage:WaitForChild("ToyWarsBalance"))
local status=player:WaitForChild("ToyWarsStatus")
local coins=stats:WaitForChild("Coins")
local wave=stats:WaitForChild("Wave")
local kills=stats:WaitForChild("Defeated")
local hp=status:WaitForChild("BaseHP")
local lv=status:WaitForChild("FactoryLevel")
local allies=status:WaitForChild("Allies")
local enemies=status:WaitForChild("Enemies")
local selected=status:WaitForChild("SelectedToy")
-- The server result may arrive after normal workshop values; never block UI startup.
local found=status.FindFirstChild and status:FindFirstChild("RoundOutcome")
local outcome=found and found.ClassName=="StringValue" and found or nil
waiting.Visible=false
local function round(parent,r)
    local c=Instance.new("UICorner")
    c.CornerRadius=UDim.new(0,r)
    c.Parent=parent
end
local function addText(parent,sz,pos,txt,col)
    local l=Instance.new("TextLabel")
    l.Size=sz
    l.Position=pos
    l.BackgroundTransparency=1
    l.Text=txt
    l.TextColor3=col or Color3.fromRGB(248,251,255)
    l.Font=Enum.Font.GothamBold
    l.TextScaled=true
    l.TextWrapped=true
    l.Parent=parent
    return l
end
local panel=Instance.new("Frame")
panel.Name="StatusPanel"
panel.Size=UDim2.new(0.55,0,0,106)
panel.Position=UDim2.new(0.025,0,0.035,0)
panel.BackgroundColor3=Color3.fromRGB(23,35,54)
panel.BackgroundTransparency=0.12
panel.Parent=gui
round(panel,13)
local title=addText(panel,UDim2.new(1,-20,0,28),UDim2.new(0,10,0,5),"TOY WARS FACTORY",Color3.fromRGB(255,216,115))
local summary=addText(panel,UDim2.new(1,-20,0,29),UDim2.new(0,10,0,39),"Loading...",Color3.fromRGB(251,251,255))
local subt=addText(panel,UDim2.new(1,-20,0,27),UDim2.new(0,10,0,69),"",Color3.fromRGB(169,226,231))
local pane=Instance.new("Frame")
pane.Name="SelectToy"
pane.Size=UDim2.new(0.88,0,0,90)
pane.Position=UDim2.new(0.06,0,1,-112)
pane.BackgroundColor3=Color3.fromRGB(20,33,53)
pane.BackgroundTransparency=0.12
pane.Parent=gui
round(pane,14)
local buttons={}
local choices={{"pon","PON",Color3.fromRGB(44,175,179)},{"guardon","GUARDON",Color3.fromRGB(64,113,205)},{"tankuru","TANKURU",Color3.fromRGB(218,135,72)}}
for i,spec in ipairs(choices) do
    local button=Instance.new("TextButton")
    button.Name=spec[1]
    -- Display authoritative prices from the shared balance module, never hard-code HUD prices.
    button.Text=string.format("%s | %d",spec[2],B.UNITS[spec[1]].cost)
    button.Size=UDim2.new(1/3,-12,0,62)
    button.Position=UDim2.new((i-1)/3,7,0,14)
    button.BackgroundColor3=spec[3]
    button.TextColor3=Color3.fromRGB(255,255,255)
    button.Font=Enum.Font.GothamBold
    button.TextScaled=true
    button.Parent=pane
    round(button,10)
    button.Activated:Connect(function()event:FireServer(spec[1])end)
    buttons[spec[1]]=button
end
local tip=addText(gui,UDim2.new(0.8,0,0,34),UDim2.new(0.1,0,1,-160),"SELECT A TOY TO AUTO-PRODUCE • UPGRADE AT THE GOLD PLATFORM",Color3.fromRGB(255,255,255))
tip.TextStrokeTransparency=0.4
-- Session-local first-play guide: touch-friendly, dismissible; never sends gameplay commands.
-- Created only after workshop assignment; no cross-session completion persistence.
-- ImageButtons keep the three toy-selection TextButtons unambiguous.
local quickStart=Instance.new("Frame")
quickStart.Name="QuickStart"
quickStart.Visible=true
quickStart.Size=UDim2.new(0.78,0,0,182)
quickStart.Position=UDim2.new(0.11,0,0.12,0)
quickStart.BackgroundColor3=Color3.fromRGB(24,38,63)
quickStart.BackgroundTransparency=0.04
quickStart.ZIndex=20
quickStart.Parent=gui
round(quickStart,15)
local guideTitle=addText(quickStart,UDim2.new(1,-24,0,28),UDim2.new(0,12,0,10),
    "WELCOME, FACTORY MASTER!",Color3.fromRGB(255,216,115))
guideTitle.Name="GuideTitle"
guideTitle.ZIndex=21
local guideSteps={
    "1/3  PICK A TOY\nPON fast • GUARDON tough • TANKURU ranged. Tap below.",
    "2/3  PRODUCE & DEFEND\nYour factory auto-produces toys; defend the vault from JUNK.",
    "3/3  EARN & UPGRADE\nDefeat JUNK for coins; upgrade at gold. Loss automatically restarts wave 1.",
}
local guidePage=1
local guideText=addText(quickStart,UDim2.new(1,-28,0,74),UDim2.new(0,14,0,43),
    guideSteps[guidePage],Color3.fromRGB(242,248,255))
guideText.Name="GuideStepText"
guideText.ZIndex=21
local function guideButton(name,caption,x,color)
    local button=Instance.new("ImageButton")
    button.Name=name
    button.Image=""
    button.Size=UDim2.new(0.39,0,0,45)
    button.Position=UDim2.new(x,0,1,-56)
    button.BackgroundColor3=color
    button.ZIndex=21
    button.Parent=quickStart
    round(button,10)
    local text=addText(button,UDim2.new(1,0,1,0),UDim2.new(0,0,0,0),
        caption,Color3.fromRGB(255,255,255))
    text.Name=name.."Caption"
    text.ZIndex=22
    return button,text
end
local skipButton=guideButton("GuideSkip","SKIP",0.07,Color3.fromRGB(79,92,111))
local nextButton,nextCaption=guideButton("GuideNext","NEXT",0.54,Color3.fromRGB(44,175,179))
skipButton.Activated:Connect(function()
    quickStart.Visible=false
end)
nextButton.Activated:Connect(function()
    if not quickStart.Visible then return end
    if guidePage==#guideSteps then
        quickStart.Visible=false
        return
    end
    guidePage=guidePage+1
    guideText.Text=guideSteps[guidePage]
    if guidePage==#guideSteps then nextCaption.Text="PLAY" end
end)
local function refresh()
    summary.Text=string.format("COINS %d  |  WAVE %d  |  VAULT %d%%",coins.Value,wave.Value,hp.Value)
    subt.Text=string.format("LV %d  •  TOYS %d  •  JUNK %d  •  KILLS %d",lv.Value,allies.Value,enemies.Value,kills.Value)
    local upgradeCost=B.upgradePrice(lv.Value)
    local chosenId=type(selected.Value)=="string" and string.lower(selected.Value) or nil
    local unit=chosenId and B.isUnit(chosenId) and B.UNITS[chosenId] or nil
    if outcome and outcome.Value=="LOSS" then
        tip.Text="BASE LOST • RESTARTING WAVE 1"
    elseif outcome and outcome.Value=="VICTORY" then
        tip.Text="WAVE 50 CLEARED • NEW FACTORY RUN"
    elseif allies.Value>=B.MAX_FIELD_UNITS then
        tip.Text=upgradeCost and string.format("FIELD FULL %d/%d • GOLD %d",allies.Value,B.MAX_FIELD_UNITS,upgradeCost)
            or string.format("FIELD FULL %d/%d • MAX LEVEL",allies.Value,B.MAX_FIELD_UNITS)
    elseif unit and coins.Value<unit.cost then
        tip.Text=upgradeCost and string.format("WAIT %s %d COINS • GOLD %d",unit.name,unit.cost,upgradeCost)
            or string.format("WAIT %s %d COINS • MAX LEVEL",unit.name,unit.cost)
    else
        tip.Text=upgradeCost and string.format("SELECT A TOY • GOLD UPGRADE: %d COINS",upgradeCost)
            or "SELECT A TOY • FACTORY MAX LEVEL"
    end
    for id,button in pairs(buttons) do
        button.BorderSizePixel=(string.upper(id)==selected.Value) and 3 or 0
        button.BorderColor3=Color3.fromRGB(255,255,255)
    end
end
local observed={coins,wave,kills,hp,lv,allies,enemies,selected}
if outcome then observed[#observed+1]=outcome end
for _,v in ipairs(observed) do v.Changed:Connect(refresh) end
-- Attach the optional server-owned outcome as soon as replication provides it.
if status.ChildAdded then
    status.ChildAdded:Connect(function(child)
        if not outcome and child.Name=="RoundOutcome" and child.ClassName=="StringValue" then
            outcome=child
            outcome.Changed:Connect(refresh)
            refresh()
        end
    end)
end
refresh()
print("TWF_HUD_OK v1.2")
