--!strict
-- EGG RAID RUMBLE - standalone read-only mobile level-journey preview HUD.
-- Private Studio only. Future production must reuse original ONE Game Remote.
local RunService=game:GetService("RunService")
if not RunService:IsStudio() then return end
local Players=game:GetService("Players")
local ReplicatedStorage=game:GetService("ReplicatedStorage")
local TweenService=game:GetService("TweenService")
local remote=ReplicatedStorage:WaitForChild("EggRumbleLevelJourneyPreviewRemote",15)
if not remote then return end
local player=Players.LocalPlayer
local gui=Instance.new("ScreenGui")
gui.Name="EggRumbleLevelJourneyPreview"
gui.ResetOnSpawn=false
gui.IgnoreGuiInset=false
gui.DisplayOrder=5
gui.Parent=player:WaitForChild("PlayerGui")

local function rounded(frame)
    local c=Instance.new("UICorner")
    c.CornerRadius=UDim.new(0,10)
    c.Parent=frame
end
local function makeFrame(name,pos,size,color)
    local frame=Instance.new("Frame")
    frame.Name=name;frame.Position=pos;frame.Size=size
    frame.BackgroundColor3=color;frame.BorderSizePixel=0
    frame.Parent=gui;rounded(frame)
    return frame
end
local bg=makeFrame("Progress",UDim2.fromScale(.025,.045),UDim2.fromScale(.45,.28),Color3.fromRGB(24,31,51))
bg.BackgroundTransparency=.10
local function label(parent,name,pos,size,content)
    local text=Instance.new("TextLabel")
    text.Name=name;text.Position=pos;text.Size=size
    text.BackgroundTransparency=1;text.Font=Enum.Font.GothamBold
    text.TextColor3=Color3.fromRGB(247,249,255);text.TextScaled=true
    text.TextXAlignment=Enum.TextXAlignment.Left
    text.Text=content;text.Parent=parent
    return text
end
local headline=label(bg,"Level",UDim2.fromScale(.04,.07),UDim2.fromScale(.92,.23),"PLAYER Lv1")
local nextReward=label(bg,"NextReward",UDim2.fromScale(.04,.33),UDim2.fromScale(.92,.16),"次の報酬：卵バナー")
local function makeBar(name,y,tint)
    local track=Instance.new("Frame")
    track.Name=name;track.Position=UDim2.fromScale(.04,y)
    track.Size=UDim2.fromScale(.92,.12)
    track.BackgroundColor3=Color3.fromRGB(66,77,97);track.BorderSizePixel=0
    track.Parent=bg;rounded(track)
    local fill=Instance.new("Frame")
    fill.Name="Fill";fill.BackgroundColor3=tint;fill.BorderSizePixel=0
    fill.Size=UDim2.fromScale(0,1);fill.Parent=track;rounded(fill)
    return fill
end
local accountBar=makeBar("AccountXP",.52,Color3.fromRGB(77,208,253))
local accountText=label(bg,"XP",UDim2.fromScale(.04,.66),UDim2.fromScale(.92,.13),"0 / 60 XP")
local focusText=label(bg,"Focus",UDim2.fromScale(.04,.83),UDim2.fromScale(.92,.13),"試合内成長 Lv1")

local masteryBg=makeFrame("Mastery",UDim2.fromScale(.025,.35),UDim2.fromScale(.45,.12),Color3.fromRGB(37,50,73))
local masteryText=label(masteryBg,"Content",UDim2.fromScale(.04,.12),UDim2.fromScale(.92,.75),"装備熟練度 Lv1")
local banner=makeFrame("LevelUp",UDim2.fromScale(.18,.70),UDim2.fromScale(.64,.18),Color3.fromRGB(95,59,160))
banner.Visible=false;banner.BackgroundTransparency=.08
local bannerText=label(banner,"Celebrate",UDim2.fromScale(.04,.12),UDim2.fromScale(.92,.76),"レベルアップ！")
bannerText.TextXAlignment=Enum.TextXAlignment.Center
local demo=label(gui,"PrivateCaption",UDim2.fromScale(.02,.93),UDim2.fromScale(.93,.04),
    "STUDIO専用デモ：試合イベント・報酬は演出サンプル（実アカウントには保存されません）")
demo.TextColor3=Color3.fromRGB(255,215,142)
local lastRevision=0
local bannerRevision=0
local function animate(fill,value)
    local pct=math.clamp(tonumber(value) or 0,0,100)/100
    TweenService:Create(fill,TweenInfo.new(.35,Enum.EasingStyle.Quad,Enum.EasingDirection.Out),
        {Size=UDim2.fromScale(pct,1)}):Play()
end
local function announce(value,rev)
    bannerRevision=rev
    banner.Visible=true
    bannerText.Text=value
    task.delay(3,function()
        if bannerRevision==rev then banner.Visible=false end
    end)
end
remote.OnClientEvent:Connect(function(payload)
    if type(payload)~="table" or payload.schema~="P0D_LEVEL_VIEW_V1" or
        type(payload.revision)~="number" or payload.revision<=lastRevision then return end
    if payload.kind=="SNAPSHOT" then
        if type(payload.account)~="table" or type(payload.focus)~="table" then return end
        lastRevision=payload.revision
        local a=payload.account
        headline.Text="PLAYER Lv"..tostring(a.level or 1)
        accountText.Text=if a.max then "最高レベル達成！"
            else tostring(a.xp or 0).." / "..tostring(a.needed or 0).." XP"
        animate(accountBar,a.percent)
        local nextItem=a.nextReward
        nextReward.Text=nextItem and ("次の報酬 Lv"..tostring(nextItem.level).."："..tostring(nextItem.label))
            or "すべてのレベル報酬を確認！"
        local focus=payload.focus
        focusText.Text="試合内フォーカス Lv"..tostring(focus.level or 1)..
            " | "..tostring(focus.nextGoal or "")
        local mastery=payload.mastery
        masteryText.Text=mastery and
            ("魔獣熟練 Lv"..tostring(mastery.level).." | "..tostring(mastery.xp)..
            "/"..tostring(mastery.needed).." XP") or "装備して魔獣の熟練度を上げよう"
    elseif payload.kind=="SETTLEMENT" then
        lastRevision=payload.revision
        local text="試合おつかれ！ + "..tostring(payload.gainedXp or 0).." XP"
        if payload.playerLeveled then
            text="LEVEL UP! Lv"..tostring(payload.accountLevelAfter)
        elseif payload.itemLeveled then
            text="魔獣の熟練度UP！"
        end
        local ms=payload.accountMilestones
        if type(ms)=="table" and #ms>0 then
            text=text.." | 次の解放候補："..tostring(ms[1].label)
        end
        -- IMPORTANT: view only; cosmetic entitlement is NOT granted here.
        announce(text,lastRevision)
    end
end)
