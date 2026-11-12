--!strict
-- P0-D S1: read-only headless ENGINE smoke test. NOT a two-player/mobile test.
-- Install nothing, change nothing, and never call SavePlaceAsync.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")
local Teams = game:GetService("Teams")
local Players = game:GetService("Players")
local HttpService = game:GetService("HttpService")

local checks = {}
local problems = {}
local function verify(label: string, ok: boolean)
    checks[label] = ok
    if not ok then table.insert(problems, label) end
end
local function child(parent: Instance?, name: string): Instance?
    return if parent then parent:FindFirstChild(name) else nil
end
local function hasClass(parent: Instance?, name: string, class: string): boolean
    local item = child(parent, name)
    return item ~= nil and item:IsA(class)
end

local shared = ReplicatedStorage:WaitForChild("TrapRaidersShared", 15)
local serverRoot = ServerScriptService:WaitForChild("TrapRaidersS1", 15)
local world = workspace:WaitForChild("TRAP_RAIDERS_S1", 15)
local remote = ReplicatedStorage:WaitForChild("TrapRaidersS1Remote", 15)
verify("shared_config", hasClass(shared, "Config", "ModuleScript"))
verify("server_game", hasClass(serverRoot, "Game", "Script"))
verify("server_mapbuilder", hasClass(serverRoot, "MapBuilder", "ModuleScript"))
verify("server_rules", hasClass(serverRoot, "S1Rules", "ModuleScript"))
verify("server_traps", hasClass(serverRoot, "S1TrapRules", "ModuleScript"))
verify("server_lobby", hasClass(serverRoot, "LobbyTeamRecovery", "ModuleScript"))
verify("single_named_remote", remote ~= nil and remote:IsA("RemoteEvent"))
local count = 0
for _, desc in ipairs(ReplicatedStorage:GetDescendants()) do
    if desc.Name == "TrapRaidersS1Remote" then count += 1 end
end
verify("one_remote_total", count == 1)

local red = child(world, "RED_CASTLE")
local blue = child(world, "BLUE_CASTLE")
verify("arena_exists", hasClass(world, "GrassArena", "Part"))
verify("red_castle", red ~= nil and red:IsA("Folder"))
verify("blue_castle", blue ~= nil and blue:IsA("Folder"))
for _, team in ipairs({"RED", "BLUE"}) do
    local folder = if team == "RED" then red else blue
    local egg = child(folder, team .. "_EGG")
    local pad = child(folder, team .. "_SCORE_PAD")
    verify(team .. "_core", hasClass(folder, team .. "_CASTLE_CORE", "Part"))
    verify(team .. "_egg", egg ~= nil and egg:IsA("Part"))
    verify(team .. "_scorepad", pad ~= nil and pad:IsA("Part"))
    verify(team .. "_spawn", hasClass(folder, team .. "_SPAWN", "Part"))
    verify(team .. "_egg_prompt", egg ~= nil and egg:FindFirstChildOfClass("ProximityPrompt") ~= nil)
    verify(team .. "_score_prompt", pad ~= nil and pad:FindFirstChildOfClass("ProximityPrompt") ~= nil)
    local teamObj = Teams:FindFirstChild(team)
    verify(team .. "_registered", teamObj ~= nil and teamObj:IsA("Team") and not teamObj.AutoAssignable)
end
verify("guardian_trap_folder", hasClass(world, "S1_GUARDIAN_TRAPS", "Folder"))

local passed = 0
for _, ok in pairs(checks) do if ok then passed += 1 end end
local report = {
    probe = "P0D_S1_V6_CLOUD_PASSIVE_V1",
    placeId = game.PlaceId,
    universeId = game.GameId,
    checked = passed + #problems,
    passed = passed,
    failures = problems,
    observedPlayers = #Players:GetPlayers(),
    provesTwoClientOrMobile = false,
}
print("P0D_CLOUD_GATE_JSON=" .. HttpService:JSONEncode(report))
if #problems > 0 then
    error("P0D_CLOUD_GATE_FAIL " .. table.concat(problems, ","))
end
print("P0D_CLOUD_GATE_PASS checked=" .. tostring(report.checked))
return report
