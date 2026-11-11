--!strict
-- SELF-CONTAINED OPTIONAL STUDIO EXAMPLE; NEVER mount into official RC without #220 review.
-- Must be manually enabled in a backed-up NONPRODUCTION place for final owner-directed QA.
local ENABLE_WF13_ISOLATED_DEMO = false
if not ENABLE_WF13_ISOLATED_DEMO then return end

local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local Scene = require(script.Parent.WF13Scene)
local Controller = require(script.Parent.WF13ZoneController)

if workspace:FindFirstChild("TRAP_RAIDERS_S1") then
    error("WF13 isolated scene refuses an existing S1 match map; choose a standalone test Place")
end
local scene = Scene.build(workspace)
local controller = Controller.new({
    players = Players,
    runService = RunService,
    workspace = workspace,
    zone = scene.zone,
    safePad = scene.safePad,
})
controller:start()

game:BindToClose(function()
    controller:stop()
    if scene.folder and scene.folder.Parent then scene.folder:Destroy() end
end)
