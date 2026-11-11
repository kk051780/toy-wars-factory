-- This demo intentionally does NOT run unless an integrator explicitly opts in.
-- Place controller, catalog and preview as siblings under this LocalScript and approve via #220.
local ENABLED = false
if not ENABLED then return end
local Players = game:GetService("Players")
local localPlayer = Players.LocalPlayer
if not localPlayer then return end
local playerGui = localPlayer:WaitForChild("PlayerGui")
local Gallery = require(script.Parent:WaitForChild("D18GalleryController"))
Gallery.mount(playerGui)
