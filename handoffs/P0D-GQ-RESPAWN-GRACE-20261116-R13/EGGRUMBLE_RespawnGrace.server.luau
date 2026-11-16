--!strict
-- Optional EGGRUMBLE V3, private-Studio-only respawn fairness.
-- One isolated ServerScript. It does NOT touch original combat/egg/lobby modules.
-- The original 21-source #482 server remains the ONLY game/session authority.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ProximityPromptService = game:GetService("ProximityPromptService")
local Workspace = game:GetService("Workspace")
if not RunService:IsStudio() then return end

local WORLD_NAME = "EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW"
local GRACE_SECONDS = 2.25
local SPAWN_BIND_DELAY = 0.95
local MAX_HOME_DISTANCE = 85
local FALLEN_CORE_COLOR = Color3.fromRGB(59, 54, 55)
type ShieldState = {
    character: Model,
    shield: ForceField,
    connections: {RBXScriptConnection},
}
local live: {[Player]: ShieldState} = {}

local function clear(player: Player)
    local state = live[player]
    if not state then return end
    live[player] = nil
    for _, connection in ipairs(state.connections) do
        connection:Disconnect()
    end
    if state.shield.Parent then state.shield:Destroy() end
end

local function originArena(player: Player, character: Model): Instance?
    -- Both mode and elimination are written by #482 SERVER.
    if player.Parent ~= Players or player.Character ~= character then return nil end
    if player:GetAttribute("EGGRUMBLE_Eliminated") == true then return nil end
    local mode = player:GetAttribute("EGGRUMBLE_QueuedMode")
    if mode ~= "TEAM" and mode ~= "BATTLE_ROYALE" then return nil end
    local scenes = Workspace:FindFirstChild(WORLD_NAME)
    local arena = scenes and scenes:FindFirstChild(mode .. "_Arena")
    if not arena then return nil end
    local castle = arena:FindFirstChild("Castle_" .. tostring(player.UserId))
    if not castle or not castle:IsA("Model") then return nil end
    local core = castle:FindFirstChild("StandardCore")
    if not core or not core:IsA("BasePart") or core.Color == FALLEN_CORE_COLOR then return nil end
    local human = character:FindFirstChildOfClass("Humanoid")
    local root = character:FindFirstChild("HumanoidRootPart")
    if not human or human.Health <= 0 or not root or not root:IsA("BasePart") then return nil end
    -- No grace in a lobby or remote battlefield: actual #482 respawn returns
    -- near its own home at +/-45 studs, before this delay.
    if (root.Position - core.Position).Magnitude > MAX_HOME_DISTANCE then return nil end
    return arena
end

local function install(player: Player, character: Model)
    clear(player)
    local arena = originArena(player, character)
    if not arena then return end
    if character:FindFirstChildOfClass("ForceField") then
        -- Respect Roblox/other author-owned ForceFields, never steal or extend them.
        return
    end
    local shield = Instance.new("ForceField")
    shield.Name = "EGGRUMBLE_GQ_RespawnGrace"
    shield.Visible = false -- no extra glow in #485's high-quality field art
    shield.Parent = character
    local state: ShieldState = {character = character, shield = shield, connections = {}}
    live[player] = state
    local function revoke()
        if live[player] == state then clear(player) end
    end
    -- Equipping any combat tool ends protection BEFORE the next attack;
    -- do not allow protected aggressive duels or carrying eggs into a siege.
    table.insert(state.connections, character.ChildAdded:Connect(function(instance: Instance)
        if instance:IsA("Tool") then revoke() end
    end))
    for _, instance in ipairs(character:GetChildren()) do
        if instance:IsA("Tool") then
            revoke()
            return
        end
    end
    local humanoid = character:FindFirstChildOfClass("Humanoid")
    if humanoid then
        table.insert(state.connections, humanoid.Died:Connect(revoke))
    end
    table.insert(state.connections, player:GetAttributeChangedSignal("EGGRUMBLE_Eliminated"):Connect(function()
        if player:GetAttribute("EGGRUMBLE_Eliminated") == true then revoke() end
    end))
    table.insert(state.connections, player:GetAttributeChangedSignal("EGGRUMBLE_QueuedMode"):Connect(function()
        if originArena(player, character) ~= arena then revoke() end
    end))
    task.delay(GRACE_SECONDS, revoke)
    task.spawn(function()
        -- Bounded 0.1s checks; no persistent loop across a round or another life.
        local deadline = os.clock() + GRACE_SECONDS
        while live[player] == state and os.clock() < deadline do
            task.wait(0.1)
            if live[player] ~= state then return end
            if originArena(player, character) ~= arena then
                revoke()
                return
            end
        end
        revoke()
    end)
end

local function watch(player: Player)
    player.CharacterAdded:Connect(function(character: Model)
        -- #482's original CharacterAdded returns the avatar to its home after
        -- ~0.8s. The grace is never granted to a pre-match lobby spawn.
        task.delay(SPAWN_BIND_DELAY, function()
            if player.Character == character then install(player, character) end
        end)
    end)
    player.CharacterRemoving:Connect(function()
        clear(player)
    end)
end

ProximityPromptService.PromptTriggered:Connect(function(_prompt: ProximityPrompt, player: Player)
    -- Egg theft, items, castle siege, ability stands: first world interaction
    -- ends the respawn defense without modifying any original prompt callback.
    clear(player)
end)
Players.PlayerRemoving:Connect(clear)
for _, player in ipairs(Players:GetPlayers()) do
    watch(player)
end
Players.PlayerAdded:Connect(watch)
print("[EGGRUMBLE_GQ_RESPAWN] optional short anti-camp grace: no server rule override")
