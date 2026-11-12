-- D18 PUBLIC_SOURCE_V1. This demo is not mounted in S1 and is OFF by default.
local ENABLED = false
if not ENABLED then return end
-- Integrator may mount only in unpublished local clone after review.
local player = game:GetService("Players").LocalPlayer
local screen = Instance.new("ScreenGui")
screen.Name="D18SixPilotOptInPreview"
screen.ResetOnSpawn=false
screen.Parent=player:WaitForChild("PlayerGui")
local view=Instance.new("ViewportFrame")
view.Size=UDim2.new(0,360,0,260)
view.Position=UDim2.new(.5,-180,.5,-130)
view.Parent=screen
local world=Instance.new("WorldModel")
world.Parent=view
local camera=Instance.new("Camera")
camera.CFrame=CFrame.new(Vector3.new(0,1.2,8),Vector3.new(0,0,0))
camera.Parent=view
view.CurrentCamera=camera
local Factory=require(script.Parent.D18BatchFactory)
local model,err=Factory.Build(world,"TRCA-BE-009",CFrame.new(0,0,0))
if model then Factory.SetPose(model,"idle");Factory.SetLod(model,false) end
