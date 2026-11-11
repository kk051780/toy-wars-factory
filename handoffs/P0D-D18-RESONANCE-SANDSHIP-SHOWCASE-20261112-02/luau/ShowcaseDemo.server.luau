--!strict
-- OPTIONAL demo only. Not part of any S1 startup or published experience.
local ENABLED = false
if not ENABLED then return end
local Factory = require(script.Parent:WaitForChild("ShowcaseFactory"))
local folder = Instance.new("Folder")
folder.Name = "D18_Optional_Two_Standalone_Samples"
folder.Parent = workspace
local left = Factory.Build(folder, "TRCA-SP-027", CFrame.new(-4, 1, 0))
local right = Factory.Build(folder, "TRCA-VE-090", CFrame.new(4, 1, 0))
Factory.SetPose(left, "idle")
Factory.SetPose(right, "idle")
-- Display-only sample: no timers, callbacks or gameplay state.
