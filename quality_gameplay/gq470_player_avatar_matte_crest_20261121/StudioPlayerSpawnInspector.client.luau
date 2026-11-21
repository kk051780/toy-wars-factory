-- GQ470 P0 owner Studio diagnostic; TEMPORARY LocalScript for PRIVATE Studio only.
-- Do NOT add to normal 69/70 source selection. No gameplay mutation, Remote or GUI.
-- Instrument whether the local player's character is absent, anchored, camera-detached,
-- or locally hidden. In first-person, intentional transparency is excluded.
local RunService = game:GetService("RunService")
if not RunService:IsStudio() then return end
local Players = game:GetService("Players")
local Workspace = game:GetService("Workspace")
local player = Players.LocalPlayer
if not player then return end

local PROBE_SECONDS = 1
local MAX_PROBES = 30
local MARK = "[GQ470_P0_STUDIO_PLAYER_APPEARANCE]"
local startedAt = os.clock()
local lastState = nil

local function sample()
    local character = player.Character
    if not character or not character.Parent then
        return "CHARACTER_MISSING", "character=nil"
    end
    local humanoid = character:FindFirstChildOfClass("Humanoid")
    local root = character:FindFirstChild("HumanoidRootPart")
    if not humanoid or not root or not root:IsA("BasePart") then
        return "CHARACTER_INCOMPLETE",
            string.format("humanoid=%s root=%s", tostring(humanoid~=nil), tostring(root~=nil))
    end
    if humanoid.Health <= 0 then
        return "HUMANOID_DEAD", string.format("hp=%.2f", humanoid.Health)
    end
    local camera = Workspace.CurrentCamera
    if not camera then
        return "CAMERA_MISSING", "Workspace.CurrentCamera=nil"
    end

    local cameraDistance = (camera.CFrame.Position - root.Position).Magnitude
    local visibleTotal, hiddenLocally = 0, 0
    for _, part in ipairs(character:GetDescendants()) do
        if part:IsA("BasePart") and part.Name ~= "HumanoidRootPart"
            and part.Transparency < 0.95 then
            visibleTotal += 1
            if part.LocalTransparencyModifier > 0.95 then
                hiddenLocally += 1
            end
        end
    end

    local subject = camera.CameraSubject
    local subjectValid = subject == humanoid
        or subject == root
        or (subject ~= nil and subject:IsDescendantOf(character))
    local detail = string.format(
        "hp=%.1f parts=%d local_hidden=%d camera_dist=%.1f camera_type=%s subject=%s root_anchored=%s",
        humanoid.Health,
        visibleTotal, hiddenLocally, cameraDistance,
        camera.CameraType.Name,
        subject and subject.Name or "nil",
        tostring(root.Anchored)
    )
    if root.Anchored then
        return "ROOT_ANCHORED_REVIEW", detail
    end
    -- First-person intentionally hides local body parts; do not misdiagnose it.
    if cameraDistance >= 5 and visibleTotal >= 3 and
        hiddenLocally / visibleTotal >= 0.66 then
        return "THIRD_PERSON_LOCAL_TRANSPARENCY_HIGH", detail
    end
    if not subjectValid and camera.CameraType ~= Enum.CameraType.Scriptable then
        return "CAMERA_SUBJECT_REVIEW", detail
    end
    if visibleTotal == 0 then
        return "AVATAR_MESH_PARTS_HIDDEN_OR_ABSENT", detail
    end
    return "SOURCE_STATE_APPEARS_VALID_ENGINE_VISUAL_STILL_NEEDS_OWNER", detail
end

local joined = player.CharacterAdded:Connect(function(character)
    print(MARK, "EVENT_CHARACTER_ADDED", character.Name,
        string.format("t=%.2f", os.clock() - startedAt))
end)
local removing = player.CharacterRemoving:Connect(function(character)
    print(MARK, "EVENT_CHARACTER_REMOVING", character.Name,
        string.format("t=%.2f", os.clock() - startedAt))
end)

print(MARK, "START",
    "jobId=" .. tostring(game.JobId),
    "placeId=" .. tostring(game.PlaceId),
    "userId=" .. tostring(player.UserId),
    "autoLoads=" .. tostring(Players.CharacterAutoLoads))
for i = 1, MAX_PROBES do
    local state, detail = sample()
    if state ~= lastState or i == 1 or i == 5 or i == 10 or i == 20 or i == 30 then
        print(MARK, string.format("t=%.1f", os.clock()-startedAt),
            "STATE=" .. state, detail)
        lastState = state
    end
    task.wait(PROBE_SECONDS)
end
joined:Disconnect()
removing:Disconnect()
print(MARK, "END_NO_GAMEPLAY_MUTATIONS", "OWNER_STUDIO_REVIEW_REQUIRED")
