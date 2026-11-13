--!nocheck
-- D18 Ext1 twelve original extension characters. PRIVATE Studio only.
-- This client-only gallery is not loaded into the S1 game/RC or live Roblox.
local RunService=game:GetService("RunService")
if not RunService:IsStudio() then return end
local Players=game:GetService("Players")
local me=Players.LocalPlayer
if not me then return end
local parent=me:WaitForChild("PlayerGui",15)
if not parent then return end
local Catalog=require(script.Parent:WaitForChild("D18Ext1Catalog"))
local Factory=require(script.Parent:WaitForChild("D18Ext1Factory"))
if parent:FindFirstChild("D18_X1_PRIVATE_GALLERY") then return end

local gui=Instance.new("ScreenGui")
gui.Name="D18_X1_PRIVATE_GALLERY"
gui.ResetOnSpawn=false
gui.IgnoreGuiInset=false
gui.DisplayOrder=30
gui.ZIndexBehavior=Enum.ZIndexBehavior.Sibling
gui.Parent=parent

local panel=Instance.new("Frame")
panel.Name="GalleryPanel"
panel.AnchorPoint=Vector2.new(.5,.5)
panel.Position=UDim2.fromScale(.5,.5)
panel.Size=UDim2.fromScale(.96,.88)
panel.BackgroundColor3=Color3.fromRGB(31,36,63)
panel.BorderSizePixel=0
panel.Parent=gui
local corner=Instance.new("UICorner")
corner.CornerRadius=UDim.new(0,16)
corner.Parent=panel

local head=Instance.new("TextLabel")
head.Name="Title"
head.BackgroundTransparency=1
head.Size=UDim2.new(1,-82,0,54)
head.Position=UDim2.fromOffset(12,0)
head.Text="D18 拡張Vol.1｜オリジナルキャラ 12体（Studio限定）"
head.TextScaled=true
head.TextColor3=Color3.fromRGB(246,231,185)
head.Font=Enum.Font.GothamBold
head.Parent=panel

local close=Instance.new("TextButton")
close.Name="CloseGallery"
close.AnchorPoint=Vector2.new(1,0)
close.Position=UDim2.new(1,-10,0,9)
close.Size=UDim2.fromOffset(48,38)
close.Text="×"
close.TextScaled=true
close.Font=Enum.Font.GothamBold
close.BackgroundColor3=Color3.fromRGB(150,72,79)
close.TextColor3=Color3.fromRGB(255,255,255)
close.Parent=panel

local scroll=Instance.new("ScrollingFrame")
scroll.Name="SixOriginalPreviews"
scroll.BackgroundTransparency=1
scroll.BorderSizePixel=0
scroll.Position=UDim2.new(0,12,0,60)
scroll.Size=UDim2.new(1,-24,1,-78)
scroll.ScrollBarThickness=5
scroll.AutomaticCanvasSize=Enum.AutomaticSize.Y
scroll.CanvasSize=UDim2.fromScale(0,0)
scroll.Parent=panel
local grid=Instance.new("UIGridLayout")
grid.CellSize=UDim2.new(0.32,-5,0,218)
grid.CellPadding=UDim2.fromOffset(8,8)
grid.SortOrder=Enum.SortOrder.LayoutOrder
grid.Parent=scroll

local created={}
local poses={"idle","tap","win","loss"}
local ids=Catalog.ids()
assert(#ids==12,"D18_X1_TWELVE_PREVIEW_ONLY")
for i,id in ipairs(ids) do
    local data=Catalog.get(id)
    if data then
        local card=Instance.new("TextButton")
        card.Name="Show_"..id
        card.LayoutOrder=i
        card.Text=""
        card.AutoButtonColor=true
        card.BackgroundColor3=Color3.fromRGB(52,63,94)
        card.Parent=scroll
        local round=Instance.new("UICorner")
        round.CornerRadius=UDim.new(0,12)
        round.Parent=card

        local frame=Instance.new("ViewportFrame")
        frame.Name="Original3D"
        frame.Position=UDim2.fromScale(.02,.01)
        frame.Size=UDim2.fromScale(.96,.72)
        frame.BackgroundColor3=Color3.fromRGB(74,90,133)
        frame.BackgroundTransparency=.12
        frame.BorderSizePixel=0
        frame.Ambient=Color3.fromRGB(210,215,220)
        frame.LightColor=Color3.fromRGB(255,240,215)
        frame.LightDirection=Vector3.new(-1,-1,-1)
        frame.Parent=card
        local world=Instance.new("WorldModel")
        world.Name="NoncombatViewportWorld"
        world.Parent=frame
        local cam=Instance.new("Camera")
        cam.Name="PreviewCamera"
        cam.FieldOfView=40
        cam.CFrame=CFrame.lookAt(Vector3.new(5,3.3,8.6),Vector3.new(0,.6,0))
        cam.Parent=frame
        frame.CurrentCamera=cam

        local model,why=Factory.Build(world,id,CFrame.new())
        if not model then
            warn("D18_X1_GALLERY_MODEL_FAILED",id,why)
        else
            Factory.SetYaw(model,45)
            Factory.SetPose(model,"idle")
            table.insert(created,model)
        end
        local name=Instance.new("TextLabel")
        name.Name="CharacterName"
        name.Size=UDim2.new(1,-8,0,30)
        name.Position=UDim2.new(0,4,.73,0)
        name.BackgroundTransparency=1
        name.Text=data.name
        name.TextColor3=Color3.fromRGB(252,238,197)
        name.TextScaled=true
        name.Font=Enum.Font.GothamBold
        name.Parent=card
        local worldLabel=Instance.new("TextLabel")
        worldLabel.Name="RarityAndRealm"
        worldLabel.Position=UDim2.new(0,4,.87,0)
        worldLabel.Size=UDim2.new(1,-8,0,24)
        worldLabel.Text=data.rarity.."｜"..data.world.."  / タップで表情"
        worldLabel.BackgroundTransparency=1
        worldLabel.TextColor3=Color3.fromRGB(217,221,239)
        worldLabel.TextScaled=true
        worldLabel.Font=Enum.Font.Gotham
        worldLabel.Parent=card
        local poseIdx=1
        card.Activated:Connect(function()
            if model and model.Parent then
                poseIdx=poseIdx%#poses+1
                Factory.SetPose(model,poses[poseIdx])
                Factory.SetYaw(model,(poseIdx*45)%360)
            end
        end)
    end
end
close.Activated:Connect(function()
    for _,model in ipairs(created) do
        if model.Parent then Factory.Destroy(model) end
    end
    gui:Destroy()
end)
gui.Destroying:Connect(function()
    for _,model in ipairs(created) do
        if model.Parent then Factory.Destroy(model) end
    end
end)
print("D18_X1_PRIVATE_GALLERY_SOURCE_MOUNTED_NOT_STUDIO_QA_PASS; no gameplay authority")
