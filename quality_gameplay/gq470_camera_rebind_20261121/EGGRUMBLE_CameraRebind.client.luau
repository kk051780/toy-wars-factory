--!strict
-- P0 #470: Visual recovery for missing local CameraSubject on spawn/respawn.
-- Never touches spawn, world geometry, gameplay authority, CameraType, or CFrame.
local Players = game:GetService("Players")
local Workspace = game:GetService("Workspace")
local player = Players.LocalPlayer
local FEATURE_ID = "GQ470_P0_CAMERA_SUBJECT_REBIND_20261121"
local RECOVERY_WINDOW_SECONDS = 4
local RETRY_SECONDS = {0.10, 0.35, 0.80, 1.70, 3.20}
local previousOwnHumanoid: Humanoid? = nil
local generation = 0

local function lostOwnSubject(subject: Instance?, currentCharacter: Model): boolean
    if subject == nil then return true end
    -- Do not steal spectator/vehicle/cutscene camera control.
    if subject:IsA("Seat") or subject:IsA("VehicleSeat") then return false end
    if subject:IsA("Humanoid") then
        if subject.Parent == currentCharacter then return false end
        if previousOwnHumanoid ~= nil and subject == previousOwnHumanoid then return true end
        return not subject:IsDescendantOf(game)
    end
    return not subject:IsDescendantOf(game)
end

local function rebindIfLost(character: Model, humanoid: Humanoid)
    if player.Character ~= character or character.Parent == nil then return end
    if humanoid.Parent ~= character or humanoid.Health <= 0 then return end
    local camera = Workspace.CurrentCamera
    if camera == nil then return end
    if camera.CameraType ~= Enum.CameraType.Custom then return end
    if not lostOwnSubject(camera.CameraSubject, character) then return end
    camera.CameraSubject = humanoid
end

local function onCharacterAdded(character: Model)
    generation += 1
    local token = generation
    local found = character:FindFirstChildOfClass("Humanoid")
    if found == nil then found = character:WaitForChild("Humanoid", 2) end
    if found == nil or not found:IsA("Humanoid") then return end
    local humanoid: Humanoid = found
    local started = os.clock()
    for _, seconds in RETRY_SECONDS do
        task.delay(seconds, function()
            if generation ~= token or os.clock() - started > RECOVERY_WINDOW_SECONDS then return end
            rebindIfLost(character, humanoid)
        end)
    end
end

player.CharacterRemoving:Connect(function(character: Model)
    generation += 1
    local previous = character:FindFirstChildOfClass("Humanoid")
    previousOwnHumanoid = if previous and previous:IsA("Humanoid") then previous else nil
end)
player.CharacterAdded:Connect(onCharacterAdded)
if player.Character then task.defer(onCharacterAdded, player.Character) end
