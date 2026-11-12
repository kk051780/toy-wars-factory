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
top.Text = "TRAP RAIDERS · 接続中..."
local status = label(gui, "Status", UDim2.new(.76, 0, 0, 34), UDim2.new(.12, 0, 0, 65),
    Color3.fromRGB(255, 232, 135), 14)
status.Text = "2人そろうと開始。卵を奪って自陣の納品台へ！"
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
local roleRaider = button(gui, "RaiderRole", "🏃 速攻", UDim2.fromOffset(92, 53),
    UDim2.new(.02, 0, 1, -64), Color3.fromRGB(59, 128, 208))
local roleGuardian = button(gui, "GuardianRole", "🛡 守護", UDim2.fromOffset(92, 53),
    UDim2.new(.02, 98, 1, -64), Color3.fromRGB(46, 152, 125))

local seq = 0
local lastSerial = -1
local lastUpdateId = -1 -- never reset between rounds; view-only HUD ordering
local bossVisual: {serial: number, eventId: string, lastSeq: number, cueUntil: number}? = nil
local function action(kind: string, role: string?)
    seq += 1
    -- No target, position, score, damage or client-side server timestamps in payload.
    remote:FireServer({action = kind, role = role, seq = seq})
end
attack.MouseButton1Click:Connect(function() action("ATTACK", nil) end)
trapButton.MouseButton1Click:Connect(function() action("PLACE_TRAP", nil) end)
windButton.MouseButton1Click:Connect(function() action("WIND_BURST", nil) end)
roleRaider.MouseButton1Click:Connect(function() action("ROLE", "RAIDER") end)
roleGuardian.MouseButton1Click:Connect(function() action("ROLE", "GUARDIAN") end)
UserInputService.InputBegan:Connect(function(input, processed)
    if processed then return end
    if input.KeyCode == Enum.KeyCode.F then action("ATTACK", nil)
    elseif input.KeyCode == Enum.KeyCode.T then action("PLACE_TRAP", nil)
    elseif input.KeyCode == Enum.KeyCode.R then action("WIND_BURST", nil) end
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
    if s.phase == "LOBBY" then return "準備中：2人集まると開始。役職を選ぼう！" end
    if s.phase == "COUNTDOWN" then return "開始まで " .. tostring(s.time) .. " 秒！" end
    if s.phase == "RESULTS" then return resultLine(s) end
    local carrying = if s.carrying ~= "" then " 🥚敵の卵を持っている！自陣へ！" else ""
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
    if bossVisual and bossVisual.serial == s.serial
        and bossVisual.cueUntil > workspace:GetServerTimeNow() then
        local remain = bossVisual.cueUntil - workspace:GetServerTimeNow()
        status.Text ..= " ⚠ 巨獣の踏みつけ " .. string.format("%.1f", remain) .. "秒"
    end
    roleRaider.Visible = s.phase ~= "ACTIVE"
    roleGuardian.Visible = s.phase ~= "ACTIVE"
    attack.Visible = s.phase == "ACTIVE"
    trapButton.Visible = s.phase == "ACTIVE" and s.role == "GUARDIAN"
    windButton.Visible = s.phase == "ACTIVE" and s.role == "RAIDER"
    local trapCooldown = if type(s.trapCooldown) == "number" and s.trapCooldown > 0
        then math.ceil(s.trapCooldown) else 0
    trapButton.Text = if trapCooldown > 0 then ("🪤 あと " .. tostring(trapCooldown) .. "秒")
        else "🪤 罠設置\nTキー"
    local windCooldown = if type(s.windCooldown) == "number" and s.windCooldown >= 0
        and s.windCooldown <= 3600 then math.ceil(s.windCooldown) else 0
    windButton.Text = if s.windActive == true then "🌪 風走り中！"
        elseif windCooldown > 0 then ("🌪 あと " .. tostring(windCooldown) .. "秒")
        else "🌪 風走り\nRキー"
end)
