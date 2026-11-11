-- No auto-start; even when manually mounted it is explicitly OFF.
local ENABLED = false
if not ENABLED then return end
-- In OWNER-approved isolated unpublished Studio only:
-- ModuleScripts ShowcaseCatalog and ShowcaseFactory must be siblings.
local factory = require(script.Parent.ShowcaseFactory)
local player = game:GetService("Players").LocalPlayer
local screen = Instance.new("ScreenGui")
screen.Name = "D18LastTwoDemoOnly"
screen.ResetOnSpawn = false
local view = Instance.new("ViewportFrame")
view.Size = UDim2.fromOffset(320,260)
view.Parent = screen
local world=Instance.new("WorldModel")
world.Parent=view
local camera=Instance.new("Camera")
camera.CFrame=CFrame.new(0,2,11)*CFrame.Angles(0,0,0)
camera.Parent=view
view.CurrentCamera=camera
local model,err=factory.Build(world,"TRCA-TR-063",CFrame.new(0,0,0))
if not model then warn(err) end
screen.Parent=player:WaitForChild("PlayerGui")
