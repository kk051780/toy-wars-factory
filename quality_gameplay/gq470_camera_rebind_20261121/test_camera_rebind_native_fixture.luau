--!nocheck
-- Native Luau mock execution of the genuine selected new LocalScript.
-- This is NOT Roblox Studio or avatar/physics evidence.
local function event()
    local calls = {}
    local e = {}
    function e:Connect(callback)
        table.insert(calls, callback)
        return {Disconnect = function() end}
    end
    function e:Fire(character)
        for _, callback in calls do callback(character) end
    end
    return e
end
local queued = {}
local task = {
    delay = function(_, callback) table.insert(queued, callback) end,
    defer = function(callback, ...) callback(...) end,
}
local function drain()
    local toRun = queued
    queued = {}
    for _, f in toRun do f() end
end
local Enum = {CameraType = {Custom = "CUSTOM", Scriptable = "SCRIPTABLE"}}
local fakeClockSeconds = 0
local os = {clock = function() return fakeClockSeconds end}
local fakePlayer = {Character = nil, CharacterAdded = event(), CharacterRemoving = event()}
local fakeCamera = {CameraType = Enum.CameraType.Custom, CameraSubject = nil}
local fakeWorld = {CurrentCamera = fakeCamera}
local game = {}
function game:GetService(service)
    if service == "Players" then return {LocalPlayer = fakePlayer} end
    if service == "Workspace" then return fakeWorld end
    error("unexpected service " .. tostring(service))
end
local function makeSubject(kind, parent)
    local subject = {Parent = parent, Health = 100}
    function subject:IsA(class)
        return class == kind
    end
    function subject:IsDescendantOf(_root)
        return self.Parent ~= nil
    end
    return subject
end
local function makeCharacter()
    local char = {Parent = fakeWorld}
    char.Humanoid = makeSubject("Humanoid", char)
    function char:FindFirstChildOfClass(class)
        if class == "Humanoid" then return self.Humanoid end
        return nil
    end
    function char:WaitForChild(class, _seconds)
        if class == "Humanoid" then return self.Humanoid end
        return nil
    end
    return char, char.Humanoid
end

-- INSERT_ACTUAL_SOURCE_HERE

local checks = 0
local function check(value, explanation)
    checks += 1
    assert(value, "CAMERA_MOCK_RED_" .. explanation)
end
-- 1: nil current subject is recovered (only own player).
local c1, h1 = makeCharacter()
fakePlayer.Character = c1
fakeCamera.CameraSubject = nil
fakePlayer.CharacterAdded:Fire(c1)
check(#queued == 5, "bounded_five_retries")
drain()
check(fakeCamera.CameraSubject == h1, "nil_subject_rebound")

-- 2: own previous humanoid is rebound after CharacterRemoving.
fakePlayer.CharacterRemoving:Fire(c1)
local c2, h2 = makeCharacter()
fakePlayer.Character = c2
fakeCamera.CameraSubject = h1
fakePlayer.CharacterAdded:Fire(c2)
drain()
check(fakeCamera.CameraSubject == h2, "previous_own_rebound")

-- 3: Scriptable camera, including cutscene, is never overridden.
fakePlayer.CharacterRemoving:Fire(c2)
local c3, h3 = makeCharacter()
fakePlayer.Character = c3
fakeCamera.CameraType = Enum.CameraType.Scriptable
fakeCamera.CameraSubject = nil
fakePlayer.CharacterAdded:Fire(c3)
drain()
check(fakeCamera.CameraSubject == nil, "scriptable_cutscene_preserved")
fakeCamera.CameraType = Enum.CameraType.Custom

-- 4: live spectator humanoid is preserved.
fakePlayer.CharacterRemoving:Fire(c3)
local c4, h4 = makeCharacter()
local watched, watchedHumanoid = makeCharacter()
fakePlayer.Character = c4
fakeCamera.CameraSubject = watchedHumanoid
fakePlayer.CharacterAdded:Fire(c4)
drain()
check(fakeCamera.CameraSubject == watchedHumanoid, "other_spectator_preserved")

-- 5: a vehicle/seat CameraSubject is preserved.
fakePlayer.CharacterRemoving:Fire(c4)
local c5, h5 = makeCharacter()
local vehicleSeat = makeSubject("VehicleSeat", fakeWorld)
fakePlayer.Character = c5
fakeCamera.CameraSubject = vehicleSeat
fakePlayer.CharacterAdded:Fire(c5)
drain()
check(fakeCamera.CameraSubject == vehicleSeat, "seat_preserved")

-- 6: all legitimate current local humanoid subjects are left untouched.
fakePlayer.CharacterRemoving:Fire(c5)
local c6, h6 = makeCharacter()
fakePlayer.Character = c6
fakeCamera.CameraSubject = h6
fakePlayer.CharacterAdded:Fire(c6)
drain()
check(fakeCamera.CameraSubject == h6, "already_correct_subject_kept")

-- 7: stale scheduled callbacks must not bind an already removed character.
fakePlayer.CharacterRemoving:Fire(c6)
local c7, h7 = makeCharacter()
fakePlayer.Character = c7
fakeCamera.CameraSubject = nil
fakePlayer.CharacterAdded:Fire(c7)
fakePlayer.CharacterRemoving:Fire(c7)
fakePlayer.Character = nil
drain()
check(fakeCamera.CameraSubject == nil, "stale_generation_rejected")

-- 8: deleted/current camera not ready, then next camera is handled safely.
local c8, h8 = makeCharacter()
fakeWorld.CurrentCamera = nil
fakePlayer.Character = c8
fakePlayer.CharacterAdded:Fire(c8)
drain()
check(fakeWorld.CurrentCamera == nil, "nil_camera_safe")
fakeWorld.CurrentCamera = fakeCamera

-- 9: dead own Humanoid does not bind.
fakePlayer.CharacterRemoving:Fire(c8)
local c9, h9 = makeCharacter()
h9.Health = 0
fakePlayer.Character = c9
fakeCamera.CameraSubject = nil
fakePlayer.CharacterAdded:Fire(c9)
drain()
check(fakeCamera.CameraSubject == nil, "dead_humanoid_not_bound")

-- 10: non-Humanoid live target is preserved.
fakePlayer.CharacterRemoving:Fire(c9)
local c10, h10 = makeCharacter()
local activeBossCameraSubject = makeSubject("BasePart", fakeWorld)
fakePlayer.Character = c10
fakeCamera.CameraSubject = activeBossCameraSubject
fakePlayer.CharacterAdded:Fire(c10)
drain()
check(fakeCamera.CameraSubject == activeBossCameraSubject, "live_other_subject_preserved")

-- 11: deadline expired; do not steal the camera after the four-second window.
fakePlayer.CharacterRemoving:Fire(c10)
local c11, h11 = makeCharacter()
fakePlayer.Character = c11
fakeCamera.CameraSubject = nil
fakePlayer.CharacterAdded:Fire(c11)
fakeClockSeconds += 4.1
drain()
check(fakeCamera.CameraSubject == nil, "expired_window_no_bind")

-- 12: no Humanoid yet (or streaming removes it); must not enqueue a camera loop.
fakePlayer.CharacterRemoving:Fire(c11)
local noHumanoid = {Parent = fakeWorld}
function noHumanoid:FindFirstChildOfClass(_) return nil end
function noHumanoid:WaitForChild(_, _) return nil end
fakePlayer.Character = noHumanoid
fakeCamera.CameraSubject = nil
fakePlayer.CharacterAdded:Fire(noHumanoid)
check(#queued == 0, "no_humanoid_no_work")
check(fakeCamera.CameraSubject == nil, "no_humanoid_no_camera_change")

-- 13: stale callback should not resurrect an outdated character even without CharacterRemoving.
local c13, h13 = makeCharacter()
fakePlayer.Character = c13
fakeCamera.CameraSubject = nil
fakePlayer.CharacterAdded:Fire(c13)
fakePlayer.Character = {Parent = fakeWorld}
drain()
check(fakeCamera.CameraSubject == nil, "changed_player_character_blocked")

print("GQ470_CAMERA_MOCK_NATIVE_13_SCENARIOS_15_ASSERTIONS_PASS", checks)

