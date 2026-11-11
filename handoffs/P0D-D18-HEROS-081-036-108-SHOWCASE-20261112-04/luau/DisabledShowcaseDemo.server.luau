--!strict
-- Demonstration intentionally OFF. Not mapped into the real S1 Roblox project.
local ENABLED = false
if not ENABLED then return end
-- Opt in only inside an owner-approved isolated UNPUBLISHED test Place.
local Factory = require(script.Parent:WaitForChild("D18ShowcaseFactory"))
local folder = Instance.new("Folder")
folder.Name = "D18_Optional_Showroom_Only"
folder.Parent = workspace
local ids = {"TRCA-SP-081", "TRCA-VE-036", "TRCA-ZO-108"}
for i,id in ipairs(ids) do
    Factory.Build(folder, id, CFrame.new((i-2)*8, 0, 0))
end
