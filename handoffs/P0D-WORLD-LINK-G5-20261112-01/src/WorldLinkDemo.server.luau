--!strict
-- P0D G5: opt-in only for isolated nonproduction Roblox Studio place.
-- No official RC, egg, role, damage, Remote, DataStore or paid content.
local ENABLE_WORLD_G5_DEMO = false
if not ENABLE_WORLD_G5_DEMO then return end
local Scene = require(script.Parent.WorldLinkScene)
local scene = Scene.build(workspace)
game:BindToClose(function()
    if scene.folder and scene.folder.Parent then
        scene.folder:Destroy()
    end
end)
