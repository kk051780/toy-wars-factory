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
-- An event-only warning on the right of the status panel; never sends commands.
-- Forecast only two waves ahead, sourced from the shared boss-wave rule.
local bossWarning=addText(gui,UDim2.new(0.34,0,0,52),UDim2.new(0.63,0,0.035,0),"")
bossWarning.Name="BossWaveWarning"
bossWarning.BackgroundColor3=Color3.fromRGB(83,38,47)
bossWarning.BackgroundTransparency=0.12
bossWarning.TextColor3=Color3.fromRGB(255,218,143)
bossWarning.Visible=false
round(bossWarning,10)
local pane=Instance.new("Frame")
pane.Name="SelectToy"
pane.Size=UDim2.new(0.88,0,0,90)
pane.Position=UDim2.new(0.06,0,1,-112)
pane.BackgroundColor3=Color3.fromRGB(20,33,53)
pane.BackgroundTransparency=0.12
pane.Parent=gui
round(pane,14)
local buttons,slots,visibleIds={},{},{}
local refresh
local unitOrder=B.PLAYABLE_IDS or {"pon","guardon","tankuru"}
local colors={pon=Color3.fromRGB(44,175,179),guardon=Color3.fromRGB(64,113,205),tankuru=Color3.fromRGB(218,135,72),curebo=Color3.fromRGB(94,174,146)}
local page,pageCount=1,math.max(1,math.ceil(#unitOrder/3))
for i=1,3 do
    local slot=i
    local button=Instance.new("TextButton")
    button.Name="ToySlot"..i
    -- Labels are filled from the shared module when the visible page changes.
    button.Size=UDim2.new(1/3,-12,0,62)
    button.Position=UDim2.new((i-1)/3,7,0,14)
    button.BackgroundColor3=colors.pon
    button.TextColor3=Color3.fromRGB(255,255,255)
    button.Font=Enum.Font.GothamBold
    button.TextScaled=true
    button.Parent=pane
    round(button,10)
    button.Activated:Connect(function()
        local id=visibleIds[slot]
        if id and B.isUnit(id) then event:FireServer(id) end
    end)
    slots[i]=button
end
local navigation=Instance.new("Frame")
navigation.Name="ToyPageNavigation"
navigation.Size=UDim2.new(0.88,0,0,42)
navigation.Position=UDim2.new(0.06,0,1,-159)
navigation.BackgroundTransparency=1
navigation.Visible=false
navigation.Parent=gui
local pageText=addText(navigation,UDim2.new(0.48,0,1,0),UDim2.new(0.26,0,0,0),"")
pageText.Name="ToyPageCaption"
local function showPage(delta)
    page=(page-1+delta)%pageCount+1
    buttons={}
    for i,button in ipairs(slots) do
        local id=unitOrder[(page-1)*3+i]
        visibleIds[i]=id
        button.Visible=id~=nil
        button.Name=id or ("EmptyToySlot"..i)
        if id then
            local spec={id,B.UNITS[id].name,colors[id] or colors.pon}
            button.Text=string.format("%s | %d",spec[2],B.UNITS[spec[1]].cost)
            if id=="curebo" then button.Text=button.Text.."\nREPAIR ALLIES" end

            button.BackgroundColor3=spec[3]
            buttons[id]=button
        end
    end
    pageText.Text=string.format("TOYS %d / %d",page,pageCount)
    if refresh then refresh() end
end
local function pageButton(name,caption,x,delta)
    local b=Instance.new("ImageButton")
    b.Name=name
    b.Image=""
    b.Size=UDim2.new(0.24,0,1,0)
    b.Position=UDim2.new(x,0,0,0)
    b.BackgroundColor3=Color3.fromRGB(46,75,102)
    b.Parent=navigation
    round(b,10)
    addText(b,UDim2.new(1,0,1,0),UDim2.new(0,0,0,0),caption)
    b.Activated:Connect(function() showPage(delta) end)
end
pageButton("ToyPagePrevious","PREV",0,-1)
pageButton("ToyPageNext","NEXT",0.76,1)
showPage(0)
local tip=addText(gui,UDim2.new(0.8,0,0,34),UDim2.new(0.1,0,1,-202),"SELECT A TOY TO AUTO-PRODUCE • UPGRADE AT THE GOLD PLATFORM",Color3.fromRGB(255,255,255))
tip.TextStrokeTransparency=0.4
-- Present a distinct, high-contrast outcome without taking touch input.
local resultBanner=addText(gui,UDim2.new(0.74,0,0,60),UDim2.new(0.13,0,0.40,0),
    "",Color3.fromRGB(255,255,255))
resultBanner.Name="RoundResultBanner"
resultBanner.BackgroundTransparency=0.08
resultBanner.BackgroundColor3=Color3.fromRGB(23,35,54)
resultBanner.ZIndex=30
resultBanner.Visible=false
round(resultBanner,12)
-- Never mistake temporary local Studio preview coins/upgrades for saved progress.
local previewNotice=addText(gui,UDim2.new(0.84,0,0,36),UDim2.new(0.08,0,0.33,0),
    "STUDIO PREVIEW - PROGRESS NOT SAVED",Color3.fromRGB(255,217,119))
previewNotice.Name="StudioPreviewNotice"
previewNotice.ZIndex=40
-- In Roblox replication the folder may arrive before its StringValue child.
-- Missing or unrecognized progress mode must NEVER silently imply saved progress.
local progressMode=nil
local function refreshPreviewNotice()
    if not progressMode then
        previewNotice.Text="PROGRESS STATUS PENDING - SAVE UNVERIFIED"
        previewNotice.Visible=true
    elseif progressMode.Value=="STUDIO_PREVIEW_UNSAVED" then
        previewNotice.Text="STUDIO PREVIEW - PROGRESS NOT SAVED"
        previewNotice.Visible=true
    elseif progressMode.Value=="SAVED" then
        previewNotice.Visible=false
    else
        previewNotice.Text="PROGRESS STATUS UNVERIFIED - DO NOT EXPECT SAVE"
        previewNotice.Visible=true
    end
end
local function bindProgressMode(child)
    if not child or child.Name~="ProgressMode" or child.ClassName~="StringValue"
        or progressMode==child then return end
    progressMode=child
    if child.Changed then child.Changed:Connect(refreshPreviewNotice) end
    refreshPreviewNotice()
end
-- Register first, then re-read: closes the replication race without yielding.
if status.ChildAdded then status.ChildAdded:Connect(bindProgressMode) end
if status.FindFirstChild then bindProgressMode(status:FindFirstChild("ProgressMode")) end
refreshPreviewNotice()
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
    "1/3  PICK A TOY\nPON fast COURIER +"..B.deliveryReward("pon").." • GUARDON tough • TANKURU ranged.",
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
    navigation.Visible=pageCount>1
end)
nextButton.Activated:Connect(function()
    if not quickStart.Visible then return end
    if guidePage==#guideSteps then
        quickStart.Visible=false
        navigation.Visible=pageCount>1
        return
    end
    guidePage=guidePage+1
    guideText.Text=guideSteps[guidePage]
    if guidePage==#guideSteps then nextCaption.Text="PLAY" end
end)
local function bossWaveHint(current)
    if type(current)~="number" or current~=math.floor(current)
        or current<1 or current>B.MAX_WAVE then return nil end
    if B.junkBoss(current) then
        return string.format("JUNK CAPTAIN\nWAVE %d",current)
    end
    local nextWave=math.floor(current/10)*10+10
    local remaining=nextWave-current
    if nextWave>B.MAX_WAVE or remaining>2 or not B.junkBoss(nextWave) then return nil end
    if remaining==1 then return "CAPTAIN NEXT WAVE" end
    return "CAPTAIN IN 2 WAVES"
end
refresh=function()
    summary.Text=string.format("COINS %d  |  WAVE %d  |  VAULT %d%%",coins.Value,wave.Value,hp.Value)
    subt.Text=string.format("LV %d  •  TOYS %d  •  JUNK %d  •  KILLS %d",lv.Value,allies.Value,enemies.Value,kills.Value)
    local upgradeCost=B.upgradePrice(lv.Value)
    local chosenId=type(selected.Value)=="string" and string.lower(selected.Value) or nil
    local unit=chosenId and B.isUnit(chosenId) and B.UNITS[chosenId] or nil
    -- A bottom instruction line is easy to miss; a temporary, noninteractive
    -- result banner keeps LOSS and final-wave VICTORY legible on small screens.
    local outcomeLabel=outcome and outcome.Value or ""
    if outcomeLabel=="LOSS" then
        resultBanner.Text="BASE LOST\nRESTARTING WAVE 1"
        resultBanner.TextColor3=Color3.fromRGB(255,145,145)
        resultBanner.Visible=true
    elseif outcomeLabel=="VICTORY" then
        resultBanner.Text="WAVE 50 CLEARED\nNEW FACTORY RUN"
        resultBanner.TextColor3=Color3.fromRGB(153,255,185)
        resultBanner.Visible=true
    else
        resultBanner.Text=""
        resultBanner.Visible=false
    end
    -- An authoritative LOSS/VICTORY always takes precedence over a boss forecast.
    bossWarning.Text=bossWaveHint(wave.Value) or ""
    bossWarning.Visible=bossWarning.Text~="" and not resultBanner.Visible
    tip.Visible=not resultBanner.Visible
    if outcome and (outcome.Value=="LOSS" or outcome.Value=="VICTORY") then
        -- Expose the authoritative result instead of leaving onboarding over it.
        quickStart.Visible=false
        navigation.Visible=pageCount>1
    end
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
-- Subscribe before rechecking: replication can land between first lookup
-- and ChildAdded registration. Close that gap without blocking normal HUD startup.
local function bindOutcome(child)
    if not outcome and child and child.Name=="RoundOutcome" and child.ClassName=="StringValue" then
        outcome=child
        outcome.Changed:Connect(refresh)
        refresh()
    end
end
if status.ChildAdded then status.ChildAdded:Connect(bindOutcome) end
if not outcome and status.FindFirstChild then
    bindOutcome(status:FindFirstChild("RoundOutcome"))
end
refresh()
print("TWF_HUD_OK v1.2")

