-- Place as StarterPlayer/StarterPlayerScripts/D18Ext2Gallery/StudioGallery.client.luau
-- with adjacent Catalog and Factory modules. Preview never exists in live servers.
local RunService = game:GetService("RunService")
if not RunService:IsStudio() then return end
local Players = game:GetService("Players")
local Catalog = require(script.Parent.Ext2Catalog)
local Factory = require(script.Parent.Ext2Factory)
local player = Players.LocalPlayer
local parentGui = player:WaitForChild("PlayerGui")
local gui = Instance.new("ScreenGui")
gui.Name = "D18Ext2StudioOnlyGallery"
gui.ResetOnSpawn = false
gui.IgnoreGuiInset = true
gui.Parent = parentGui
local holder = Instance.new("Frame")
holder.Name = "Gallery"; holder.AnchorPoint = Vector2.new(.5,.5); holder.Position=UDim2.fromScale(.5,.5)
holder.Size=UDim2.fromScale(.76,.78); holder.BackgroundColor3=Color3.fromRGB(19,28,52); holder.Parent=gui
local view = Instance.new("ViewportFrame")
view.Name="Preview";view.Position=UDim2.fromScale(.08,.11);view.Size=UDim2.fromScale(.84,.64)
view.BackgroundColor3=Color3.fromRGB(39,52,75);view.Ambient=Color3.fromRGB(190,192,210);view.Parent=holder
local world=Instance.new("WorldModel"); world.Parent=view
local camera=Instance.new("Camera"); camera.CFrame=CFrame.lookAt(Vector3.new(8,6,12),Vector3.new(0,1.5,0))
camera.Parent=view;view.CurrentCamera=camera
local label=Instance.new("TextLabel");label.Position=UDim2.fromScale(.08,.01);label.Size=UDim2.fromScale(.84,.1)
label.TextScaled=true;label.TextColor3=Color3.new(1,1,1);label.BackgroundTransparency=1;label.Parent=holder
local function btn(txt,x)
 local b=Instance.new("TextButton");b.Size=UDim2.fromScale(.25,.15);b.Position=UDim2.fromScale(x,.8)
 b.Text=txt;b.TextScaled=true;b.BackgroundColor3=Color3.fromRGB(66,102,149);b.TextColor3=Color3.new(1,1,1)
 b.Parent=holder;return b
end
local prev=btn("前へ",.08);local pose=btn("ポーズ",.38);local next=btn("次へ",.68)
local current=1;local currentPose=1;local model=nil
local poses={"IDLE","TAP","WIN","LOSE"}
local function draw()
 if model then model:Destroy() end
 local item=Catalog.Entries[current]
 model=Factory.build(item,world,false)
 currentPose=1
 label.Text=tostring(current).."/16　"..item.name.."　"..item.category.."　"..item.rarity
 if model then Factory.previewPose(model,poses[currentPose]) end
end
prev.Activated:Connect(function() current=(current-2)%#Catalog.Entries+1;draw() end)
next.Activated:Connect(function() current=current%#Catalog.Entries+1;draw() end)
pose.Activated:Connect(function() if model then currentPose=currentPose%#poses+1;Factory.previewPose(model,poses[currentPose]) end end)
draw()
