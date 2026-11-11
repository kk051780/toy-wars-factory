--!strict
-- Explicitly disabled and not mapped to any production Rojo project.
local ENABLED = false
if not ENABLED then return end
local Factory = require(script.Parent:WaitForChild("D18ShowcaseFactory"))
local folder = Instance.new("Folder")
folder.Name = "D18_Standalone_Experimental_Showroom"
folder.Parent = workspace
local a = Factory.Build(folder, "TRCA-TR-009", CFrame.new(-4, 2, 0))
local b = Factory.Build(folder, "TRCA-WE-045", CFrame.new(4, 2, 0))
assert(a ~= nil and b ~= nil)
-- The isolated Studio reviewer may call SetPose and SetLod manually.
