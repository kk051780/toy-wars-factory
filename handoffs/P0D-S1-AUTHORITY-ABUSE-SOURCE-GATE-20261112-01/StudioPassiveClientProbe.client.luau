--!strict
-- P0D PASSIVE STUDIO QA PROBE: LOCAL CLONE ONLY, never a shipping asset.
-- Reads authentic server RemoteEvent + existing GUI. NO FireServer, NO mutations.
local RunService = game:GetService("RunService")
if not RunService:IsStudio() then return end

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local UserInputService = game:GetService("UserInputService")
local player = Players.LocalPlayer
if not player then return end

local remote = ReplicatedStorage:WaitForChild("TrapRaidersS1Remote", 20)
if not remote or not remote:IsA("RemoteEvent") then
    warn("P0D_STUDIO_PROBE_V1 CLIENT FAIL reason=REMOTE_MISSING")
    return
end

local gui = player:WaitForChild("PlayerGui", 20)
if not gui then
    warn("P0D_STUDIO_PROBE_V1 CLIENT FAIL reason=PLAYER_GUI_MISSING")
    return
end

local state = {
    serial = -1, phase = "", side = "NONE", lastScores = {RED = 0, BLUE = 0},
    lastHp = {RED = 0, BLUE = 0}, lastCarry = "",
    activeAt = nil :: number?, firstActiveSerial = -1,
    previousResultsSerial = -1, sawCapture = false,
    milestones = {} :: {[string]: boolean},
    observed = {} :: {[string]: boolean},
    lastView = "", missingUiAt = time(),
    logs = 0, invalidPackets = 0,
}
local function token(v: any): string
    return string.sub(string.gsub(tostring(v), "[^%w_-]", "_"), 1, 42)
end
local function record(tag: string, info: string)
    state.logs += 1
    print("P0D_STUDIO_PROBE_V1 CLIENT kind=" .. tag .. " " .. info)
end
local function reject(reason: string)
    state.invalidPackets += 1
    warn("P0D_STUDIO_PROBE_V1 CLIENT BLOCK reason=" .. reason)
end
record("START", "studio_only=1 readonly=1 platform=" ..
    (if UserInputService.TouchEnabled then "TOUCH_ENABLED_NOT_PROOF_OF_PHONE" else "DESKTOP"))

local function viewSample(snapshot: any)
    local hud = gui:FindFirstChild("TrapRaidersS1HUD")
    local coach = gui:FindFirstChild("TR_S1_FirstMinuteCoach")
    if not (hud and coach and hud:IsA("ScreenGui") and coach:IsA("ScreenGui")) then
        if time() - state.missingUiAt > 15 then
            record("UI_NOT_READY", "hud=" .. tostring(hud ~= nil) ..
                " coach=" .. tostring(coach ~= nil))
            state.missingUiAt = time()
        end
        return
    end
    local score = hud:FindFirstChild("Score")
    local status = hud:FindFirstChild("Status")
    local attack = hud:FindFirstChild("Attack")
    local role = hud:FindFirstChild("RaiderRole")
    local panel = coach:FindFirstChild("CoachPanel")
    if not (score and status and attack and role and panel
            and score:IsA("TextLabel") and status:IsA("TextLabel")
            and attack:IsA("GuiButton") and role:IsA("GuiButton")
            and panel:IsA("GuiObject")) then
        record("UI_INCOMPLETE", "expected=Score_Status_Attack_RaiderRole_CoachPanel")
        return
    end
    local title = panel:FindFirstChild("CoachTitle")
    local titleText = if title and title:IsA("TextLabel") then title.Text else "MISSING"
    local phase = snapshot.phase
    local viewport = if workspace.CurrentCamera then workspace.CurrentCamera.ViewportSize
        else Vector2.new(0, 0)
    local stateString = phase .. "/" .. titleText .. "/" .. tostring(panel.Visible)
    if stateString ~= state.lastView then
        state.lastView = stateString
        record("UI_VIEW", "phase=" .. token(phase) ..
            " coach_visible=" .. tostring(panel.Visible) ..
            " coach_title=" .. token(titleText) ..
            " attack_visible=" .. tostring(attack.Visible) ..
            " role_visible=" .. tostring(role.Visible) ..
            " viewport=" .. tostring(math.floor(viewport.X)) .. "x" ..
                tostring(math.floor(viewport.Y)) ..
            " status=" .. token(status.Text))
    end
    if phase == "ACTIVE" and not attack.Visible then
        record("UI_WARNING", "reason=ATTACK_HIDDEN_DURING_ACTIVE")
    end
    if phase == "RESULTS" and attack.Visible then
        record("UI_WARNING", "reason=ATTACK_VISIBLE_DURING_RESULTS")
    end
    if phase == "ACTIVE" and role.Visible then
        record("UI_WARNING", "reason=ROLE_SELECT_VISIBLE_DURING_COMBAT")
    end
    if phase == "RESULTS" then
        local winner = snapshot.winner
        local should = if winner == "DRAW" then "引き分け！"
            elseif winner == snapshot.team then "勝利！"
            else "敗北！"
        if string.find(status.Text, should, 1, true) == nil then
            record("UI_WARNING", "reason=JAPANESE_RESULT_NOT_VISIBLE")
        end
    end
    -- Screenspace check: only logs. Never modifies any UI object.
    if viewport.X > 0 and viewport.Y > 0 then
        local p = panel.AbsolutePosition
        local s = panel.AbsoluteSize
        if panel.Visible and (p.X < -1 or p.Y < -1
            or p.X + s.X > viewport.X + 2 or p.Y + s.Y > viewport.Y + 2) then
            record("UI_WARNING", "reason=COACH_PANEL_OUT_OF_VIEWPORT")
        end
    end
end

local function validSnapshot(s: any): boolean
    if type(s) ~= "table" or s.kind ~= "SNAPSHOT" then return false end
    if type(s.serial) ~= "number" or s.serial ~= s.serial or s.serial < 0
        or s.serial % 1 ~= 0 or s.serial > 1000000000 then return false end
    if s.phase ~= "LOBBY" and s.phase ~= "COUNTDOWN"
        and s.phase ~= "ACTIVE" and s.phase ~= "RESULTS" then return false end
    if s.team ~= "RED" and s.team ~= "BLUE" and s.team ~= "NONE" then return false end
    if type(s.scores) ~= "table" or type(s.hp) ~= "table" then return false end
    for _, side in ipairs({"RED", "BLUE"}) do
        local score, hp = s.scores[side], s.hp[side]
        if type(score) ~= "number" or score ~= score or score < 0 or score > 1000000
            or type(hp) ~= "number" or hp ~= hp or hp < 0 or hp > 1000000 then
            return false
        end
    end
    if type(s.redPlayers) ~= "number" or type(s.bluePlayers) ~= "number"
        or type(s.time) ~= "number" or s.time ~= s.time then return false end
    if s.carrying ~= "" and s.carrying ~= "RED" and s.carrying ~= "BLUE" then
        return false
    end
    return true
end

local function milestone(label: string, snapshot: any, seconds: number)
    local key = tostring(snapshot.serial) .. "_" .. label
    if state.milestones[key] then return end
    state.milestones[key] = true
    record("FIRST_MINUTE", "phase=ACTIVE serial=" .. tostring(snapshot.serial) ..
        " elapsed_threshold=" .. label .. " observed_after=" ..
        tostring(math.floor(seconds)) .. "s")
    task.defer(function() viewSample(snapshot) end)
end

remote.OnClientEvent:Connect(function(s)
    if type(s) == "table" and s.kind == "BOSS_VISUAL" then
        record("BOSS_VISUAL_UNEXPECTED", "release_gates=EXPECTED_OFF kind=" ..
            token(s.visualKind))
        return
    end
    if not validSnapshot(s) then
        reject("MALFORMED_OR_NON_SNAPSHOT")
        return
    end
    if s.serial < state.serial then reject("STALE_SERIAL"); return end
    if s.serial > state.serial then
        if state.previousResultsSerial >= 0 and s.serial > state.previousResultsSerial
            and s.phase == "ACTIVE" then
            record("REMATCH_OBSERVED", "new_serial=" .. tostring(s.serial))
            state.observed.rematch = true
        end
        state.serial = s.serial
        state.activeAt = nil
        state.firstActiveSerial = -1
        state.lastScores = {RED = 0, BLUE = 0}
        state.lastHp = {RED = 0, BLUE = 0}
        state.lastCarry = ""
        record("NEW_SERIAL", "serial=" .. tostring(s.serial))
    end
    local side = s.team
    if s.phase ~= state.phase then
        state.phase = s.phase
        record("PHASE", "serial=" .. tostring(s.serial) ..
            " phase=" .. token(s.phase) .. " team=" .. token(side) ..
            " red=" .. tostring(s.redPlayers) ..
            " blue=" .. tostring(s.bluePlayers))
        state.observed[s.phase] = true
    end
    if s.redPlayers >= 1 and s.bluePlayers >= 1 then
        if not state.observed.twoSides then
            state.observed.twoSides = true
            record("TWO_SIDES_ON_SERVER", "red=" .. tostring(s.redPlayers) ..
                " blue=" .. tostring(s.bluePlayers) ..
                " actual_two_Studio_clients_must_be_separately_confirmed=1")
        end
    end
    if s.phase == "ACTIVE" then
        if not state.activeAt then
            state.activeAt = time()
            state.firstActiveSerial = s.serial
        end
        local elapsed = time() - (state.activeAt :: number)
        milestone("0", s, elapsed)
        if elapsed >= 12 then milestone("12", s, elapsed) end
        if elapsed >= 32 then milestone("32", s, elapsed) end
        if elapsed >= 60 then milestone("60", s, elapsed) end
    end
    if s.carrying ~= "" and s.carrying ~= state.lastCarry then
        state.observed.carry = true
        record("EGG_CARRY", "serial=" .. tostring(s.serial) ..
            " carried_team=" .. token(s.carrying) .. " player_team=" .. token(side))
    end
    if s.scores.RED > state.lastScores.RED or s.scores.BLUE > state.lastScores.BLUE then
        state.observed.score = true
        record("SCORE_INCREASE", "red=" .. tostring(s.scores.RED) ..
            " blue=" .. tostring(s.scores.BLUE))
    end
    if s.phase == "ACTIVE" and state.lastHp.RED > 0 and state.lastHp.BLUE > 0
        and (s.hp.RED < state.lastHp.RED or s.hp.BLUE < state.lastHp.BLUE) then
        state.observed.castleDamage = true
        record("CASTLE_HP_CHANGE", "red=" .. tostring(s.hp.RED) ..
            " blue=" .. tostring(s.hp.BLUE))
    end
    if s.phase == "RESULTS" then
        state.previousResultsSerial = s.serial
        if not state.observed.resultSeen then
            record("RESULTS", "serial=" .. tostring(s.serial) ..
                " winner=" .. token(s.winner) ..
                " reason=" .. token(s.reason))
            state.observed.resultSeen = true
        end
    end
    state.lastScores = {RED = s.scores.RED, BLUE = s.scores.BLUE}
    state.lastHp = {RED = s.hp.RED, BLUE = s.hp.BLUE}
    state.lastCarry = s.carrying
    state.side = side
    task.defer(function() viewSample(s) end)
end)

task.spawn(function()
    while RunService:IsStudio() do
        task.wait(15)
        record("STATUS_NOT_PASS", "phase=" .. token(state.phase) ..
            " team=" .. token(state.side) ..
            " serial=" .. tostring(state.serial) ..
            " two_sides=" .. tostring(state.observed.twoSides == true) ..
            " carry=" .. tostring(state.observed.carry == true) ..
            " score=" .. tostring(state.observed.score == true) ..
            " result=" .. tostring(state.observed.resultSeen == true) ..
            " rematch=" .. tostring(state.observed.rematch == true) ..
            " invalid_snapshots=" .. tostring(state.invalidPackets) ..
            " engine_test_requires_manual_evidence=1")
    end
end)
