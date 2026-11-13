--!strict
-- P0D PASSIVE STUDIO SERVER OBSERVER (only on an unpublished local QA clone).
-- Does not mutate match, Players, remote, map or score.
local RunService = game:GetService("RunService")
if not RunService:IsStudio() then return end

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local workspaceFolder = workspace:WaitForChild("TRAP_RAIDERS_S1", 20)
local remote = ReplicatedStorage:WaitForChild("TrapRaidersS1Remote", 20)
if not workspaceFolder or not remote or not remote:IsA("RemoteEvent") then
    warn("P0D_STUDIO_PROBE_V1 SERVER FAIL reason=REAL_GAME_INSTANCE_MISSING")
    return
end

local function teamName(player: Player): string
    return if player.Team and (player.Team.Name == "RED" or player.Team.Name == "BLUE")
        then player.Team.Name else "NONE"
end
local function observeCharacter(player: Player, character: Model)
    local h = character:WaitForChild("Humanoid", 10)
    if not h or not h:IsA("Humanoid") then
        warn("P0D_STUDIO_PROBE_V1 SERVER WARN reason=HUMANOID_MISSING team=" ..
            teamName(player))
        return
    end
    local last = h.Health
    print("P0D_STUDIO_PROBE_V1 SERVER kind=CHARACTER team=" ..
        teamName(player) .. " hp=" .. tostring(h.Health))
    h.HealthChanged:Connect(function(hp: number)
        if hp < last then
            print("P0D_STUDIO_PROBE_V1 SERVER kind=REAL_HUMANOID_DAMAGE team=" ..
                teamName(player) .. " before=" .. tostring(last) ..
                " after=" .. tostring(hp))
        end
        last = hp
    end)
end
local function observePlayer(p: Player)
    print("P0D_STUDIO_PROBE_V1 SERVER kind=PLAYER_ADDED team=" .. teamName(p))
    p.CharacterAdded:Connect(function(ch) observeCharacter(p, ch) end)
    if p.Character then observeCharacter(p, p.Character) end
end
Players.PlayerAdded:Connect(observePlayer)
Players.PlayerRemoving:Connect(function(p)
    print("P0D_STUDIO_PROBE_V1 SERVER kind=PLAYER_REMOVED team=" .. teamName(p))
end)
for _, p in ipairs(Players:GetPlayers()) do observePlayer(p) end

local valid = 0
for _, side in ipairs({"RED", "BLUE"}) do
    local castle = workspaceFolder:FindFirstChild(side .. "_CASTLE")
    if castle then
        local egg = castle:FindFirstChild(side .. "_EGG")
        local pad = castle:FindFirstChild(side .. "_SCORE_PAD")
        local core = castle:FindFirstChild(side .. "_CASTLE_CORE")
        local eggPrompt = if egg then egg:FindFirstChildOfClass("ProximityPrompt")
            else nil
        local scorePrompt = if pad then pad:FindFirstChildOfClass("ProximityPrompt")
            else nil
        if egg and pad and core and eggPrompt and scorePrompt then
            valid += 1
            eggPrompt.Triggered:Connect(function(p)
                print("P0D_STUDIO_PROBE_V1 SERVER kind=REAL_EGG_PROMPT actor=" ..
                    teamName(p) .. " egg=" .. side)
            end)
            scorePrompt.Triggered:Connect(function(p)
                print("P0D_STUDIO_PROBE_V1 SERVER kind=REAL_SCORE_PROMPT actor=" ..
                    teamName(p) .. " pad=" .. side)
            end)
        else
            warn("P0D_STUDIO_PROBE_V1 SERVER WARN reason=MAP_PROMPT_MISSING side=" ..
                side)
        end
    else
        warn("P0D_STUDIO_PROBE_V1 SERVER WARN reason=CASTLE_MISSING side=" .. side)
    end
end
print("P0D_STUDIO_PROBE_V1 SERVER kind=MAP_CHECK valid_sides=" ..
    tostring(valid) .. " expected=2")
task.spawn(function()
    while RunService:IsStudio() do
        task.wait(15)
        local red, blue = 0, 0
        for _, p in ipairs(Players:GetPlayers()) do
            if teamName(p) == "RED" then red += 1 end
            if teamName(p) == "BLUE" then blue += 1 end
        end
        print("P0D_STUDIO_PROBE_V1 SERVER kind=SERVER_ROSTER red=" .. tostring(red) ..
            " blue=" .. tostring(blue) ..
            " no_gameplay_mutation=1 status=OBSERVED_NOT_ENGINE_PASS")
    end
end)
