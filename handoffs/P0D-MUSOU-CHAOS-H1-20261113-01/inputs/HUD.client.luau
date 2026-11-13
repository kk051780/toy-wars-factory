--!strict
-- Client HUD only. It submits intent, never chosen target, damage, score or server position.
-- Roblox native thumbstick/jump remain enabled for touch players.
local Players = game:GetService("Players")
local UserInputService = game:GetService("UserInputService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local player = Players.LocalPlayer
local remote = ReplicatedStorage:WaitForChild("TrapRaidersS1Remote") :: RemoteEvent

local gui = Instance.new("ScreenGui")
gui.Name = "TrapRaidersS1HUD"
gui.ResetOnSpawn = false
gui.IgnoreGuiInset = false
gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
gui.Parent = player:WaitForChild("PlayerGui")

local function label(parent: Instance, name: string, size: UDim2, pos: UDim2,
    color: Color3, fontSize: number): TextLabel
    local l = Instance.new("TextLabel")
    l.Name = name
    l.Size = size
    l.Position = pos
    l.BackgroundColor3 = Color3.fromRGB(17, 25, 37)
    l.BackgroundTransparency = .12
    l.BorderSizePixel = 0
    l.TextColor3 = color
    l.TextWrapped = true
    l.TextScaled = false
    l.TextSize = fontSize
    l.Font = Enum.Font.GothamBold
    l.Parent = parent
    local corner = Instance.new("UICorner")
    corner.CornerRadius = UDim.new(0, 10)
    corner.Parent = l
    return l
end
local function button(parent: Instance, name: string, text: string,
    size: UDim2, pos: UDim2, color: Color3): TextButton
    local b = Instance.new("TextButton")
    b.Name = name
    b.Size = size
    b.Position = pos
    b.AnchorPoint = Vector2.new(0, 1)
    b.BackgroundColor3 = color
    b.TextColor3 = Color3.new(1, 1, 1)
    b.TextScaled = true
    b.TextWrapped = true
    b.Font = Enum.Font.GothamBold
    b.BorderSizePixel = 0
    b.Parent = parent
    local corner = Instance.new("UICorner")
    corner.CornerRadius = UDim.new(0, 12)
    corner.Parent = b
    local pad = Instance.new("UIPadding")
    pad.PaddingBottom = UDim.new(0, 7)
    pad.PaddingTop = UDim.new(0, 7)
    pad.PaddingLeft = UDim.new(0, 6)
    pad.PaddingRight = UDim.new(0, 6)
    pad.Parent = b
    return b
end

local top = label(gui, "Score", UDim2.new(.76, 0, 0, 58), UDim2.new(.12, 0, 0, 4),
    Color3.new(1, 1, 1), 17)
top.Text = "EGG RAID RUMBLE · 接続中..."
local status = label(gui, "Status", UDim2.new(.76, 0, 0, 34), UDim2.new(.12, 0, 0, 65),
    Color3.fromRGB(255, 232, 135), 14)
status.Text = "2人そろうと開始。卵を奪って自陣の納品台へ！"
-- Source-only #284 owns optional full level-journey view; this is the actual
-- ORIGINAL H1 read-only mini XP feedback (no second GUI authority or Remote).
local progressBadge=label(gui,"RealH1ServerLevel",UDim2.new(.76,0,0,35),
    UDim2.new(.12,0,0,105),Color3.fromRGB(196,249,227),13)
progressBadge.Visible=false
progressBadge.Text="Lv1 | 0/60 XP | 🎯 フォーカス1 | 🐉 熟練1"
local instructions = label(gui, "Instructions", UDim2.new(.55, 0, 0, 42),
    UDim2.new(.2, 0, 1, -58), Color3.fromRGB(231, 240, 255), 13)
instructions.Text = "敵の卵に近づいてE／タップで奪取 → 自陣の台へ。城を攻撃しても勝てる！"
local attack = button(gui, "Attack", "⚔ 攻撃\nFキー", UDim2.fromOffset(126, 88),
    UDim2.new(1, -140, 1, -16), Color3.fromRGB(211, 75, 72))
local trapButton = button(gui, "GuardianTrap", "🪤 罠設置\nTキー",
    UDim2.fromOffset(110, 74), UDim2.new(1, -140, 1, -110), Color3.fromRGB(168, 105, 56))
trapButton.Visible = false
-- The same mobile slot is shared by Guardian trap and Raider wind burst.
local windButton = button(gui, "RaiderWind", "🌪 風走り\nRキー",
    UDim2.fromOffset(110, 74), UDim2.new(1, -140, 1, -110),
    Color3.fromRGB(55, 139, 192))
windButton.Visible = false
-- Studio H1-only: readable extra controls in free right-middle space.
local netButton = button(gui,"ShortCaptureNet","🕸 網で捕獲\\nNキー",
    UDim2.fromOffset(110,62),UDim2.new(1,-140,1,-185),Color3.fromRGB(112,83,173))
netButton.Visible=false
local rescueButton=button(gui,"BreakOrRescue","⛓ 仲間を救助\\nBキー",
    UDim2.fromOffset(115,62),UDim2.new(1,-265,1,-185),Color3.fromRGB(66,154,151))
rescueButton.Visible=false
local mobCue=label(gui,"MusouHordeCue",UDim2.new(.56,0,0,27),
    UDim2.new(.22,0,0,142),Color3.fromRGB(255,221,132),14)
mobCue.Text="⚔ 中立兵の群れ！"
mobCue.Visible=false
local roleRaider = button(gui, "RaiderRole", "🏃 速攻", UDim2.fromOffset(92, 53),
    UDim2.new(.02, 0, 1, -64), Color3.fromRGB(59, 128, 208))
local roleGuardian = button(gui, "GuardianRole", "🛡 守護", UDim2.fromOffset(92, 53),
    UDim2.new(.02, 98, 1, -64), Color3.fromRGB(46, 152, 125))

-- Two modes in ONE original H1 game, only a single HUD owns Remote sequence numbers.
local modePanel = Instance.new("Frame")
modePanel.Name = "TwoModeLobby"
modePanel.AnchorPoint = Vector2.new(.5, 0)
modePanel.Position = UDim2.new(.5, 0, 0, 108)
modePanel.Size = UDim2.new(.86, 0, 0, 108)
modePanel.BackgroundColor3 = Color3.fromRGB(12, 28, 47)
modePanel.BackgroundTransparency = .06
modePanel.BorderSizePixel = 0
modePanel.Visible = false
modePanel.Parent = gui
local modeSize=Instance.new("UISizeConstraint")
modeSize.MaxSize=Vector2.new(700,108)
modeSize.MinSize=Vector2.new(245,108)
modeSize.Parent=modePanel
local modeCorner=Instance.new("UICorner")
modeCorner.CornerRadius=UDim.new(0,13)
modeCorner.Parent=modePanel
local modeHint = label(modePanel,"ModeVoteCount",UDim2.new(1,-10,0,39),
    UDim2.new(0,5,0,4),Color3.fromRGB(240,244,255),13)
modeHint.BackgroundTransparency=1
modeHint.Text="次の試合を選ぼう！ 未投票なら卵どろぼう戦"
local classicMode = button(modePanel,"ClassicEggMode","🥚 卵どろぼう戦\n卵1こ",
    UDim2.new(.5,-8,0,53),UDim2.new(0,5,1,-5),Color3.fromRGB(58,126,208))
local scoreMode = button(modePanel,"FiveEggScoreMode","🏆 得点バトル\n卵5こ",
    UDim2.new(.5,-8,0,53),UDim2.new(.5,3,1,-5),Color3.fromRGB(165,101,52))

-- Real FREE hatch / OWNED collectible / EQUIP / NEXT ROUND 3D ability HUD.
-- Both old CLASSIC and five egg SCORE modes share the SAME original HUD/Remote/seq.
local equipPanel=Instance.new("Frame")
equipPanel.Name="BEAST_HATCH_EQUIP"
equipPanel.AnchorPoint=Vector2.new(.5,0)
equipPanel.Position=UDim2.new(.5,0,0,219)
equipPanel.Size=UDim2.new(.88,0,0,84)
equipPanel.BackgroundColor3=Color3.fromRGB(20,40,58)
equipPanel.BackgroundTransparency=.08
equipPanel.BorderSizePixel=0
equipPanel.Visible=false
equipPanel.Parent=gui
local equipConstraint=Instance.new("UISizeConstraint")
equipConstraint.MinSize=Vector2.new(245,84)
equipConstraint.MaxSize=Vector2.new(710,84)
equipConstraint.Parent=equipPanel
local equipCorner=Instance.new("UICorner")
equipCorner.CornerRadius=UDim.new(0,12)
equipCorner.Parent=equipPanel
local equipTitle=label(equipPanel,"OwnedScoutsTitle",UDim2.new(1,-8,0,25),
    UDim2.new(0,4,0,2),Color3.fromRGB(241,237,188),13)
equipTitle.BackgroundTransparency=1
equipTitle.Text="🥚 魔獣を装備して次の試合で使用"
local starterEquip=button(equipPanel,"EquipStarter","最初の魔獣",
    UDim2.new(.333,-6,0,48),UDim2.new(0,4,1,-3),Color3.fromRGB(52,110,161))
local forestEquip=button(equipPanel,"EquipForest","森の魔獣",
    UDim2.new(.333,-6,0,48),UDim2.new(.333,2,1,-3),Color3.fromRGB(48,134,99))
local starEquip=button(equipPanel,"EquipStar","星の魔獣",
    UDim2.new(.333,-6,0,48),UDim2.new(.666,2,1,-3),Color3.fromRGB(157,126,47))
local scoutButton=button(gui,"SummonRealScout","🐉 魔獣を呼ぶ\\nGキー",
    UDim2.fromOffset(126,79),UDim2.new(0,15,1,-16),Color3.fromRGB(59,143,124))
scoutButton.Visible=false
local hatchBanner=label(gui,"FreeHatchEarned",UDim2.new(.8,0,0,74),
    UDim2.new(.1,0,0,118),Color3.fromRGB(255,221,118),18)
hatchBanner.Visible=false
hatchBanner.Text="🥚 無料の卵が孵化！\\n次のロビーで装備できるよ"
-- No false persistent save indicator when Studio has API access disabled.
local saveLabel=label(gui,"ActualSaveStatus",UDim2.new(.86,0,0,32),
    UDim2.new(.07,0,0,308),Color3.fromRGB(245,224,155),14)
saveLabel.Visible=false
saveLabel.Text="🔄 所有魔獣の保存を確認中"
local equipButtons={
    {button=starterEquip,item="starter_scout",label="最初の魔獣"},
    {button=forestEquip,item="forest_scout",label="森の魔獣"},
    {button=starEquip,item="star_scout",label="星の魔獣"}
}

local seq = 0
local currentNetBound=false -- display state ONLY; server independently validates
local lastSerial = -1
local lastUpdateId = -1 -- never reset between rounds; view-only HUD ordering
local bossVisual: {serial: number, eventId: string, lastSeq: number, cueUntil: number}? = nil
local function action(kind: string, role: string?)
    seq += 1
    -- No target, position, score, damage or client-side server timestamps in payload.
    if kind == "MODE_VOTE" then
        remote:FireServer({action = kind, mode = role, seq = seq})
    elseif kind == "EQUIP_SCOUT" then
        remote:FireServer({action = kind, itemId = role, seq = seq})
    else
        remote:FireServer({action = kind, role = role, seq = seq})
    end
end
attack.MouseButton1Click:Connect(function() action("ATTACK", nil) end)
trapButton.MouseButton1Click:Connect(function() action("PLACE_TRAP", nil) end)
windButton.MouseButton1Click:Connect(function() action("WIND_BURST", nil) end)
netButton.MouseButton1Click:Connect(function() action("NET_THROW",nil) end)
rescueButton.MouseButton1Click:Connect(function()
    action(if currentNetBound then "BREAK_FREE" else "RESCUE",nil)
end)
roleRaider.MouseButton1Click:Connect(function() action("ROLE", "RAIDER") end)
roleGuardian.MouseButton1Click:Connect(function() action("ROLE", "GUARDIAN") end)
classicMode.MouseButton1Click:Connect(function() action("MODE_VOTE","CLASSIC") end)
scoreMode.MouseButton1Click:Connect(function() action("MODE_VOTE","SCORE_5") end)
scoutButton.MouseButton1Click:Connect(function() action("ACTIVATE_SCOUT",nil) end)
for _,entry in ipairs(equipButtons) do
    entry.button.MouseButton1Click:Connect(function()
        action("EQUIP_SCOUT",entry.item)
    end)
end
UserInputService.InputBegan:Connect(function(input, processed)
    if processed then return end
    if input.KeyCode == Enum.KeyCode.F then action("ATTACK", nil)
    elseif input.KeyCode == Enum.KeyCode.T then action("PLACE_TRAP", nil)
    elseif input.KeyCode == Enum.KeyCode.R then action("WIND_BURST", nil)
    elseif input.KeyCode == Enum.KeyCode.N then action("NET_THROW",nil)
    elseif input.KeyCode == Enum.KeyCode.B then
        action(if currentNetBound then "BREAK_FREE" else "RESCUE",nil)
    elseif input.KeyCode == Enum.KeyCode.G then action("ACTIVATE_SCOUT", nil) end
end)

local function displayRole(role: string): string
    return if role == "GUARDIAN" then "守護" else "速攻"
end
-- RESULT_COPY_BEGIN: results copy only; no new Remote or game authority.
local RESULT_REASONS = {
    EGG_CAPTURE = "卵を運んで得点",
    CASTLE_DESTROYED = "城が破壊された",
    OPPONENT_LEFT = "相手が退出した",
    TEAM_EMPTY = "相手チームの人数が不足",
    TIME_LIMIT = "制限時間が終了",
    FIVE_EGG_TIME_LIMIT = "卵5こ得点戦の時間切れ",
    FIVE_EGG_SCORE_240S = "卵5こ得点戦・4分決着",
}
local function resultLine(s): string
    local outcome = "試合終了"
    if s.winner == "DRAW" then
        outcome = "引き分け！"
    elseif s.winner == "RED" or s.winner == "BLUE" then
        if s.team == "RED" or s.team == "BLUE" then
            outcome = if s.winner == s.team then "勝利！" else "敗北！"
        end
    end
    local reason = if type(s.reason) == "string"
        then (RESULT_REASONS[s.reason] or "勝敗が確定しました")
        else "勝敗が確定しました"
    local seconds = 0
    if type(s.time) == "number" and s.time == s.time and s.time >= 0
        and s.time <= 3600 then
        seconds = math.floor(s.time)
    end
    -- RESULTS ends at the lobby. A new round still needs enough players.
    return outcome .. "　" .. reason .. "｜次の準備まで " .. tostring(seconds) .. " 秒"
end
-- RESULT_COPY_END

local function phaseText(s): string
    if s.phase == "LOBBY" then return "準備中：役職と次の試合モードを選ぼう！" end
    if s.phase == "COUNTDOWN" then return "開始まで " .. tostring(s.time) .. " 秒！" end
    if s.phase == "RESULTS" then return resultLine(s) end
    local carrying = if s.carrying ~= "" then
        (if s.scoreMode=="FIVE_EGG_SCORE" then " 🥚卵を持っている！金庫へ！"
            else " 🥚敵の卵を持っている！自陣へ！")
        else (if s.scoreMode=="FIVE_EGG_SCORE" then " 🏆卵を奪って・守って得点！" else "")
    local warning = if s.alarm == "WARNING" then " ⚠ 襲撃の予兆 " .. tostring(s.alarmTime) .. "秒"
        else (if s.alarm == "SIGNAL" then " ⚡警報発動中！" else "")
    return "対戦中｜残り " .. tostring(s.time) .. "秒" .. carrying .. warning
end
remote.OnClientEvent:Connect(function(s)
    if type(s) ~= "table" then return end
    if s.kind == "BOSS_VISUAL" then
        -- Display only; no boss choice, physics, HP or Remote FireServer.
        if type(s.serial) ~= "number" or s.serial ~= lastSerial
            or s.bossId ~= "GOROGAN"
            or s.eventId ~= "G07_" .. tostring(lastSerial)
            or type(s.seq) ~= "number" or s.seq % 1 ~= 0
            or s.seq < 1 or s.seq > 10000
            or type(s.serverSentAt) ~= "number"
            or s.serverSentAt ~= s.serverSentAt then return end
        if bossVisual and s.seq <= bossVisual.lastSeq then return end
        if s.visualKind == "START" then
            bossVisual = {serial = lastSerial, eventId = s.eventId,
                lastSeq = s.seq, cueUntil = 0}
        elseif bossVisual and bossVisual.eventId == s.eventId then
            bossVisual.lastSeq = s.seq
            if s.visualKind == "STOMP" then
                bossVisual.cueUntil = s.serverSentAt + 2
                local seconds = math.max(0, bossVisual.cueUntil - workspace:GetServerTimeNow())
                if seconds > 0 then
                    status.Text = "⚠ 巨獣の踏みつけ！あと " .. string.format("%.1f", seconds) .. "秒"
                end
            elseif s.visualKind == "END" then
                bossVisual = nil
            end
        end
        return
    end
    if s.kind ~= "SNAPSHOT" then return end
    if type(s.serial) ~= "number" or s.serial < lastSerial then return end
    -- Same-round stale SNAPSHOTs must never roll back score, phase or buttons.
    -- Use the same numeric and legacy-upgrade policy as FirstMinuteModel.
    local id = s.updateId
    if id ~= nil then
        if type(id) ~= "number" or id ~= id or id < 0
            or id > 1000000000 or id % 1 ~= 0
            or id <= lastUpdateId then return end
    elseif lastUpdateId >= 0 then
        return
    end
    if type(s.scores) ~= "table" or type(s.hp) ~= "table" then return end
    if s.serial > lastSerial or s.phase ~= "ACTIVE" then bossVisual = nil end
    lastSerial = s.serial
    if id ~= nil then lastUpdateId = id end
    top.Text = string.format("🔴 %d / 🏰 %d       🔵 %d / 🏰 %d\n自分:%s・%s  |  %d対%d人",
        s.scores.RED or 0, s.hp.RED or 0, s.scores.BLUE or 0,
        s.hp.BLUE or 0, s.team or "?", displayRole(s.role),
        s.redPlayers or 0, s.bluePlayers or 0)
    status.Text = phaseText(s)
    local level=if type(s.progressLevel)=="number"
        and s.progressLevel%1==0 and s.progressLevel>=1 and s.progressLevel<=50
        then s.progressLevel else 1
    local xp=if type(s.progressXp)=="number" and s.progressXp>=0
        and s.progressXp<=20000 then math.floor(s.progressXp) else 0
    local need=if type(s.progressNextXp)=="number" and s.progressNextXp>=0
        and s.progressNextXp<=10000 then math.floor(s.progressNextXp) else 60
    local focus=if type(s.progressFocus)=="number" and s.progressFocus>=1
        and s.progressFocus<=3 then math.floor(s.progressFocus) else 1
    local mastery=if type(s.progressMastery)=="number" and s.progressMastery>=1
        and s.progressMastery<=10 then math.floor(s.progressMastery) else 1
    local progressStatus=if type(s.progressSaveStatus)=="string"
        then s.progressSaveStatus else "LOCAL_ONLY"
    progressBadge.Visible=s.phase=="ACTIVE"
    progressBadge.Text="⭐ Lv"..tostring(level).."  "..tostring(xp).."/"..tostring(need)
        .." XP   🎯"..tostring(focus).."   🐉熟練"..tostring(mastery)
    if s.phase=="RESULTS" then
        local granted=if type(s.progressLastAward)=="number"
            and s.progressLastAward>=0 and s.progressLastAward<=150
            then math.floor(s.progressLastAward) else 0
        if granted>0 then
            status.Text..="　+"..tostring(granted).."XP"
                ..(if progressStatus=="SAVED" then " ✅XP保存応答"
                    elseif progressStatus=="SAVING" then " 🔄XP保存中"
                    else " ⚠XP保存未確認")
        end
    end
    if s.scoreMode=="FIVE_EGG_SCORE" then
        top.Text=string.format("🏆 🔴 %d 点    🔵 %d 点\n自分:%s・%s　|　卵5こ得点戦",
            s.scores.RED or 0,s.scores.BLUE or 0,s.team or "?",displayRole(s.role))
    end
    instructions.Text=if s.scoreMode=="FIVE_EGG_SCORE" and s.phase=="ACTIVE"
        then "卵は5こ！ E／タップでひろう→自陣の金庫へ。持って逃げても得点！"
        else "敵の卵に近づいてE／タップで奪取 → 自陣の台へ。城を攻撃しても勝てる！"
    local canChoose=(s.phase=="LOBBY" or s.phase=="COUNTDOWN")
        and s.modeScoreAvailable==true
    modePanel.Visible=canChoose
    local c=if type(s.voteClassic)=="number" and s.voteClassic>=0 then s.voteClassic else 0
    local v=if type(s.voteFive)=="number" and s.voteFive>=0 then s.voteFive else 0
    local nextMode=if s.modeVote=="SCORE_5" then "🏆 得点バトル" else "🥚 卵どろぼう戦"
    modeHint.Text="次の試合："..nextMode.."　🥚"..tostring(c).." vs 🏆"..tostring(v)
        .."　Lv"..tostring(level)
    classicMode.Text=if s.myModeVote=="CLASSIC" then "✓ 🥚 卵どろぼう戦\n卵1こ"
        else "🥚 卵どろぼう戦\n卵1こ"
    scoreMode.Text=if s.myModeVote=="SCORE_5" then "✓ 🏆 得点バトル\n卵5こ"
        else "🏆 得点バトル\n卵5こ"
    local hatchAvailable=s.hatchEnabled==true
    local lobby=(s.phase=="LOBBY" or s.phase=="COUNTDOWN")
    local owned=if type(s.hatchOwned)=="table" then s.hatchOwned else {}
    local equipped=if type(s.hatchEquipped)=="string" then s.hatchEquipped else ""
    local saveState=if type(s.hatchSaveStatus)=="string" then s.hatchSaveStatus else "LOCAL_ONLY"
    saveLabel.Visible=hatchAvailable and (lobby or s.phase=="RESULTS")
    saveLabel.Text=if saveState=="SAVED" then "✅ 保存サーバー応答あり（再ログイン検証は別）"
        elseif saveState=="LOADING" then "🔄 以前の魔獣を読み込み中"
        elseif saveState=="SAVE_FAILED" then "⚠️ 保存未確認！再ログインで消失の可能性"
        else "⚠️ Studioでは一時保存のみ。再ログインで消えます"
    saveLabel.TextColor3=if saveState=="SAVED" then Color3.fromRGB(153,247,177)
        else Color3.fromRGB(255,207,120)
    equipPanel.Visible=hatchAvailable and lobby
    for _,entry in ipairs(equipButtons) do
        local count=if type(owned[entry.item])=="number" and owned[entry.item]>=0
            then math.floor(owned[entry.item]) else 0
        entry.button.Active=hatchAvailable and s.phase=="LOBBY"
            and saveState~="LOADING" and count>0
        entry.button.AutoButtonColor=entry.button.Active
        entry.button.Text=(if equipped==entry.item then "✓ " else "")
            ..entry.label..(if count>0 then " ×"..tostring(count) else " 🔒")
    end
    instructions.Visible=s.phase=="ACTIVE"
    local eggItem=if type(s.hatchLast)=="string" and #s.hatchLast<=32
        then s.hatchLast else ""
    hatchBanner.Visible=hatchAvailable and s.phase=="RESULTS" and eggItem~=""
    hatchBanner.Text=if eggItem=="star_scout" then "✨ レア卵が孵化！星の魔獣をGET！\n次の試合で装備して呼び出そう"
        elseif eggItem=="forest_scout" then "🥚 無料の卵が孵化！森の魔獣をGET！\n次の試合で装備して呼び出そう"
        else "🥚 無料孵化で魔獣をGET！\n次のロビーで装備しよう"
    if hatchBanner.Visible and saveState~="SAVED" then
        hatchBanner.Text=hatchBanner.Text.."（保存未確認）"
    end
    scoutButton.Visible=hatchAvailable and s.phase=="ACTIVE"
    local cooldown=if type(s.scoutCooldown)=="number" and s.scoutCooldown>=0
        and s.scoutCooldown<=60 then math.ceil(s.scoutCooldown) else 0
    local carry=type(s.carrying)=="string" and s.carrying~=""
    local active=s.scoutActive==true
    scoutButton.Active=scoutButton.Visible and not carry and cooldown==0 and not active
    scoutButton.AutoButtonColor=scoutButton.Active
    scoutButton.Text=if carry then "🥚 卵運び中\n召喚はできない"
        elseif active then "🐉 魔獣が偵察中！"
        elseif cooldown>0 then "🐉 あと"..tostring(cooldown).."秒"
        else "🐉 魔獣を呼ぶ\nGキー"
    if bossVisual and bossVisual.serial == s.serial
        and bossVisual.cueUntil > workspace:GetServerTimeNow() then
        local remain = bossVisual.cueUntil - workspace:GetServerTimeNow()
        status.Text ..= " ⚠ 巨獣の踏みつけ " .. string.format("%.1f", remain) .. "秒"
    end
    roleRaider.Visible = s.phase ~= "ACTIVE"
    roleGuardian.Visible = s.phase ~= "ACTIVE"
    attack.Visible = s.phase == "ACTIVE"
    -- A single actual horde is driven by the existing ATTACK. Combo is view-only.
    mobCue.Visible=s.musouActive==true
    if mobCue.Visible then
        local alive=if type(s.musouMobCount)=="number"
            then math.clamp(math.floor(s.musouMobCount),0,9) else 0
        local combo=if type(s.musouCombo)=="number"
            then math.clamp(math.floor(s.musouCombo),0,99) else 0
        mobCue.Text="⚔ 中立兵 "..tostring(alive).."体  |  "
            ..(if combo>1 then tostring(combo).."連撃！" else "斬って進もう！")
    end
    currentNetBound=s.netBound==true
    local netCd=if type(s.netCooldown)=="number" and s.netCooldown>=0
        and s.netCooldown<=3600 then math.ceil(s.netCooldown) else 0
    netButton.Visible=s.musouActive==true and s.role=="GUARDIAN"
    netButton.Active=netButton.Visible and netCd==0
        and not currentNetBound and (type(s.carrying)~="string" or s.carrying=="")
    netButton.AutoButtonColor=netButton.Active
    netButton.Text=if netCd>0 then "🕸 あと"..tostring(netCd).."秒"
        else "🕸 網で捕獲\\nNキー"
    rescueButton.Visible=s.musouActive==true
        and (currentNetBound or s.netRescueNearby==true)
    rescueButton.Active=rescueButton.Visible
    rescueButton.AutoButtonColor=rescueButton.Active
    rescueButton.Text=if currentNetBound then "⛓ 自力で脱出\\nBキー"
        else "🤝 仲間を救助\\nBキー"
    trapButton.Visible = s.phase == "ACTIVE" and s.role == "GUARDIAN"
    windButton.Visible = s.phase == "ACTIVE" and s.role == "RAIDER"
    local trapCooldown = if type(s.trapCooldown) == "number" and s.trapCooldown > 0
        then math.ceil(s.trapCooldown) else 0
    -- Children should not tap a button that the server will definitely reject.
    -- These are display-only affordances; the server remains the authority.
    local carryingEgg = type(s.carrying) == "string" and s.carrying ~= ""
    trapButton.Active = s.phase == "ACTIVE" and s.role == "GUARDIAN"
        and not carryingEgg and trapCooldown == 0
    trapButton.AutoButtonColor = trapButton.Active
    trapButton.Text = if carryingEgg then "🥚 卵運搬中\n罠は使えない"
        elseif trapCooldown > 0 then ("🪤 あと " .. tostring(trapCooldown) .. "秒")
        else "🪤 罠設置\nTキー"
    local windCooldown = if type(s.windCooldown) == "number" and s.windCooldown >= 0
        and s.windCooldown <= 3600 then math.ceil(s.windCooldown) else 0
    windButton.Active = s.phase == "ACTIVE" and s.role == "RAIDER"
        and not carryingEgg and windCooldown == 0 and s.windActive ~= true
    windButton.AutoButtonColor = windButton.Active
    windButton.Text = if carryingEgg then "🥚 卵運搬中\n風走り不可"
        elseif s.windActive == true then "🌪 風走り中！"
        elseif windCooldown > 0 then ("🌪 あと " .. tostring(windCooldown) .. "秒")
        else "🌪 風走り\nRキー"
end)
