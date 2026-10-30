-- TOY WARS A14: Edit-mode structural Studio probe, NOT a Play/engine boot test.
-- Run only from a reviewed trusted host via Roblox Studio --task RunScript --localPlaceFile.
local function requireInstance(parent, name, className)
    local instance = parent:FindFirstChild(name)
    assert(instance ~= nil, "TWF_STUDIO_MISSING_" .. name)
    assert(instance.ClassName == className, "TWF_STUDIO_WRONG_CLASS_" .. name)
    return instance
end

local replicated = game:GetService("ReplicatedStorage")
local server = game:GetService("ServerScriptService")
local player = game:GetService("StarterPlayer")
local scripts = requireInstance(player, "StarterPlayerScripts", "StarterPlayerScripts")
requireInstance(replicated, "ToyWarsBalance", "ModuleScript")
requireInstance(replicated, "ToyWarsSelectUnit", "RemoteEvent")
requireInstance(server, "ToyWarsServer", "Script")
requireInstance(server, "ToyWarsSmokeTest", "Script")
requireInstance(scripts, "ToyWarsHUD", "LocalScript")
assert(game:GetService("RunService"):IsStudio(), "TWF_STUDIO_NOT_STUDIO")
-- No Play, public network, upload, save, account credentials or player creation here.
print("TWF_STUDIO_LOCAL_PLACE_STRUCTURE_OK_V1")
