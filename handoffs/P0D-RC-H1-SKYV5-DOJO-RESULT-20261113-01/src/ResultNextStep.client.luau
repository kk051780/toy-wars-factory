--!strict
-- P0D-FUN-H1-001: only the OWNER'S unpublished Studio reads existing server
-- snapshots, giving one truthful next step after the real result. NO gameplay
-- Remote sends, score/XP/save authoring, timer changes, or forced prompts.
local RunService = game:GetService("RunService")
if not RunService:IsStudio() then return end
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")
local player = Players.LocalPlayer
if not player then return end
local shared = ReplicatedStorage:WaitForChild("TrapRaidersShared", 25)
if not shared then return end
local policy = shared:WaitForChild("NextStepAdvisor", 25)
if not policy or not policy:IsA("ModuleScript") then return end
local Advisor = require(policy)
local remote = ReplicatedStorage:WaitForChild("TrapRaidersS1Remote", 25)
if not remote or not remote:IsA("RemoteEvent") then return end
local playerGui = player:WaitForChild("PlayerGui", 25)
if not playerGui then return end

local gui = Instance.new("ScreenGui")
gui.Name = "P0D_PrivateResultNextStep"
gui.ResetOnSpawn = false
gui.DisplayOrder = 115
gui.IgnoreGuiInset = false
gui.Parent = playerGui
local box = Instance.new("TextLabel")
box.Name = "SevenSecondSummary"
box.BackgroundColor3 = Color3.fromRGB(22, 36, 55)
box.BackgroundTransparency = 0.09
box.BorderSizePixel = 0
box.AnchorPoint = Vector2.new(0.5, 0)
box.Position = UDim2.new(0.5, 0, 0, 10)
box.Size = UDim2.new(0.62, 0, 0, 90)
box.Font = Enum.Font.GothamBold
box.TextSize = 14
box.TextColor3 = Color3.fromRGB(248, 251, 255)
box.TextWrapped = true
box.TextXAlignment = Enum.TextXAlignment.Center
box.TextYAlignment = Enum.TextYAlignment.Center
box.Active = false
box.Visible = false
box.Parent = gui
local close = Instance.new("TextButton")
close.Name = "Dismiss"
close.Text = "×"
close.TextColor3 = Color3.fromRGB(255, 255, 255)
close.Font = Enum.Font.GothamBold
close.TextSize = 20
close.Size = UDim2.fromOffset(28, 28)
close.AnchorPoint = Vector2.new(1, 0)
close.Position = UDim2.new(1, -2, 0, 2)
close.BackgroundColor3 = Color3.fromRGB(56, 78, 101)
close.AutoButtonColor = true
close.Visible = false
close.Parent = box

local shownSerial = -1
local lastPhase = ""
local showTicket = 0
-- ONE local navigation cue for a REAL server-built home-team dojo pad.
-- Source is the existing Game's PRIVATE_AUTO_DOJO_<TEAM>_<SKILL> station, not
-- a made-up position or a fake stat. Never sends gameplay remotes.
local marker: BillboardGui? = nil
local markerTicket = 0
local function clearTrainingMarker()
    markerTicket += 1
    if marker then
        marker:Destroy()
        marker = nil
    end
end
local function pointToInstalledPad(team: string, skill: string?)
    clearTrainingMarker()
    if (team ~= "RED" and team ~= "BLUE")
        or (skill ~= "BEAST" and skill ~= "WEAPON") then return end
    local arena = workspace:FindFirstChild("TRAP_RAIDERS_S1")
    if not arena then return end
    local expected = "PRIVATE_AUTO_DOJO_"..team.."_"..skill
    local pad = arena:FindFirstChild(expected)
    -- Refuse any approximate position, opponent pad or unrelated local part.
    if not pad or not pad:IsA("BasePart")
        or pad:GetAttribute("P0DTrainingSkill") ~= skill
        or pad:GetAttribute("FreeTraining") ~= true
        or pad:GetAttribute("StudioSessionOnly") ~= true then
        print("[P0D_STUDIO_RESULT_ADVISOR] PAD_NOT_FOUND "..expected)
        return
    end
    local worldCue = Instance.new("BillboardGui")
    worldCue.Name = "P0D_PrivateDojoNextStep"
    worldCue.Adornee = pad
    worldCue.Size = UDim2.fromOffset(180, 58)
    worldCue.StudsOffsetWorldSpace = Vector3.new(0, 8, 0)
    worldCue.AlwaysOnTop = true
    worldCue.MaxDistance = 240
    local nameLabel = Instance.new("TextLabel")
    nameLabel.Name = "ActualInstalledPadOnly"
    nameLabel.Size = UDim2.fromScale(1, 1)
    nameLabel.BackgroundColor3 = Color3.fromRGB(33, 86, 101)
    nameLabel.BackgroundTransparency = 0.18
    nameLabel.TextColor3 = Color3.fromRGB(255, 247, 199)
    nameLabel.Font = Enum.Font.GothamBold
    nameLabel.TextScaled = true
    nameLabel.TextWrapped = true
    nameLabel.Text = if skill == "BEAST" then "🐉 次はここで魔獣修行！"
        else "⚔ 次はここで武器修行！"
    nameLabel.Parent = worldCue
    worldCue.Parent = playerGui
    marker = worldCue
    local ticket = markerTicket
    -- Do not leave old suggested destinations floating over a NEW battle.
    task.delay(20, function()
        if ticket == markerTicket then clearTrainingMarker() end
    end)
end
close.MouseButton1Click:Connect(function()
    showTicket += 1
    box.Visible = false
    close.Visible = false
    clearTrainingMarker()
end)

local function dojoView(snapshot: any): ({beast:number, weapon:number, friendBonus:boolean}?)
    if type(snapshot.dojo) ~= "table" then return nil end
    local d = snapshot.dojo
    local beast, weapon = d.beast, d.weapon
    if type(beast) ~= "number" or type(weapon) ~= "number"
        or beast ~= beast or weapon ~= weapon
        or beast % 1 ~= 0 or weapon % 1 ~= 0
        or beast < 1 or beast > 5 or weapon < 1 or weapon > 5 then
        return nil
    end
    return {beast=beast, weapon=weapon, friendBonus=d.friendBonus == true}
end

local function serverTeamScore(msg: any): number?
    if msg.team ~= "RED" and msg.team ~= "BLUE" then return nil end
    if type(msg.scores) ~= "table" then return nil end
    local n = msg.scores[msg.team]
    if type(n) ~= "number" or n ~= n or n < 0 or n > 100 then return nil end
    return math.floor(n)
end

local function summarize(msg: any): string
    local won: boolean? = nil
    local resultText = "試合結果を確認"
    if msg.winner == "DRAW" then
        resultText = "引き分け"
    elseif msg.winner == "RED" or msg.winner == "BLUE" then
        if msg.team == "RED" or msg.team == "BLUE" then
            won = msg.winner == msg.team
            resultText = if won then "勝利！" else "惜しい！"
        end
    end

    local score = serverTeamScore(msg)
    -- The original snapshot has team score, NOT individual egg deposits.
    -- Never label this as a player's own egg or the match's neutral KOs.
    local scoreText = if score ~= nil
        then "チーム得点: "..tostring(score)
        else "チーム得点: 未確認"
    local dojo = dojoView(msg)
    local adviceText = "もう一度、卵を奪いに行こう！"
    local suggestedPad: string? = nil
    local bonusText = ""
    if dojo then
        -- Only verified H1 BEAST and WEAPON; no six-skill V4 claim.
        -- Hatch readiness is not in the current server snapshot: false
        -- prevents claiming a free hatch item was earned.
        local advice = Advisor.build({won=won, eggsScored=score or 0},
            {canEvolve=msg.evoCanUpgrade == true, canHatch=false,
             skillLevels={beast=dojo.beast, weapon=dojo.weapon}},
            {availableSkills={"beast", "weapon"},
             sameServerFriendBonus=dojo.friendBonus})
        if advice.action == "VIEW_EVOLUTION" then
            adviceText = "つぎは進化をチェック！"
        elseif advice.action == "VIEW_TRAINING" then
            if advice.suggestedSkill == "beast" then
                suggestedPad = "BEAST"
                adviceText = "つぎは魔獣道場で放置修行！"
            elseif advice.suggestedSkill == "weapon" then
                suggestedPad = "WEAPON"
                adviceText = "つぎは武器道場で放置修行！"
            end
        else
            adviceText = "もう一度、卵を奪いに行こう！"
        end
        if advice.friendBonusVisible then
            bonusText = "  フレンド育成ボーナスあり"
        end
    end
    local summary = resultText.."  |  "..scoreText.."\n"..adviceText..bonusText..
        "\n7秒で消えます・戦績はサーバー情報のみ"
    return summary, suggestedPad
end

remote.OnClientEvent:Connect(function(msg: any)
    if type(msg) ~= "table" or msg.kind ~= "SNAPSHOT" then return end
    local phase = if type(msg.phase) == "string" then msg.phase else ""
    local serial = if type(msg.serial) == "number" then msg.serial else -1
    if phase ~= "RESULTS" then
        if box.Visible then
            showTicket += 1
            box.Visible = false
            close.Visible = false
        end
        -- Keep the temporary waypoint while waiting in LOBBY/COUNTDOWN,
        -- remove it as soon as the next ACTIVE round actually starts.
        if phase == "ACTIVE" and marker then clearTrainingMarker() end
        lastPhase = phase
        return
    end
    if serial < 0 or (lastPhase == "RESULTS" and shownSerial == serial) then return end
    lastPhase = "RESULTS"
    shownSerial = serial
    showTicket += 1
    local ticket = showTicket
    local summary, suggestedPad = summarize(msg)
    box.Text = summary
    pointToInstalledPad(if type(msg.team) == "string" then msg.team else "", suggestedPad)
    box.Visible = true
    close.Visible = true
    print("[P0D_STUDIO_RESULT_ADVISOR] RESULTS serial="..tostring(serial)..
        " next-action-only; OWNER_FUN_NOT_TESTED")
    task.delay(7, function()
        if ticket == showTicket then
            box.Visible = false
            close.Visible = false
        end
    end)
end)
