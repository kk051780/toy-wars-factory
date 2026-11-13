--!strict
-- Private showroom camera/UI ONLY, no live progression or Remote commands.
local RunService=game:GetService("RunService")
if not RunService:IsStudio() then return end
local Players=game:GetService("Players")
local player=Players.LocalPlayer
local gui=Instance.new("ScreenGui")
gui.Name="EggRumbleEvolutionOriginalPreview"
gui.ResetOnSpawn=false;gui.DisplayOrder=20
gui.Parent=player:WaitForChild("PlayerGui")
local names={"幼体","成長体","紅蓮進化","蒼潮進化","天龍神話体"}
local info={
    "卵から生まれた小竜／最初から使える",
    "熟練Lv3 + プレイヤーLv10／育成の第一歩",
    "熟練Lv6 + Lv25／攻撃特化の分岐",
    "熟練Lv6 + Lv25／護衛・防御の分岐",
    "熟練Lv10 + Lv40／伝説形態（展示用）",
}
local positions={-56,-28,0,28,56}
local function decorate(frame)
    local u=Instance.new("UICorner")
    u.CornerRadius=UDim.new(0,8);u.Parent=frame
end
local top=Instance.new("TextLabel")
top.Name="Heading";top.Position=UDim2.fromScale(.08,.04)
top.Size=UDim2.fromScale(.84,.14)
top.BackgroundColor3=Color3.fromRGB(23,31,54)
top.BackgroundTransparency=.12
top.Text="EGG RAID RUMBLE 進化の系譜"
top.Font=Enum.Font.GothamBold;top.TextScaled=true
top.TextColor3=Color3.fromRGB(252,247,215)
top.Parent=gui;decorate(top)
local caption=Instance.new("TextLabel")
caption.Name="Warning";caption.Position=UDim2.fromScale(.1,.80)
caption.Size=UDim2.fromScale(.8,.07)
caption.BackgroundColor3=Color3.fromRGB(24,32,54)
caption.BackgroundTransparency=.13
caption.TextColor3=Color3.fromRGB(255,231,145)
caption.TextScaled=true;caption.Font=Enum.Font.GothamBold
caption.Text="STUDIO専用展示。実ゲームの進化・戦闘・保存ではありません。"
caption.Parent=gui;decorate(caption)
local detail=Instance.new("TextLabel")
detail.Name="Description";detail.Position=UDim2.fromScale(.12,.69)
detail.Size=UDim2.fromScale(.76,.07)
detail.BackgroundColor3=Color3.fromRGB(22,40,65)
detail.BackgroundTransparency=.1
detail.TextColor3=Color3.fromRGB(255,255,255)
detail.Font=Enum.Font.GothamBold;detail.TextScaled=true
detail.Text=info[1];detail.Parent=gui;decorate(detail)
local selected=1
for i,title in ipairs(names) do
    local button=Instance.new("TextButton")
    button.Name="Stage_"..i
    button.Position=UDim2.fromScale(.05+(i-1)*.185,.88)
    button.Size=UDim2.fromScale(.165,.077)
    button.BackgroundColor3=Color3.fromRGB(40,111,153)
    button.TextColor3=Color3.fromRGB(255,255,255)
    button.Font=Enum.Font.GothamBold
    button.TextScaled=true;button.Text=title
    button.Parent=gui;decorate(button)
    button.MouseButton1Click:Connect(function()
        selected=i
        detail.Text=info[i]
    end)
end
local camera=workspace.CurrentCamera
local last=(camera and camera.CFrame) or CFrame.new(0,13,100)
RunService.RenderStepped:Connect(function(dt)
    camera=workspace.CurrentCamera
    if not camera then return end
    camera.CameraType=Enum.CameraType.Scriptable
    local x=positions[selected]
    local origin=Vector3.new(x,9,27)
    local look=Vector3.new(x,5,0)
    local goal=CFrame.lookAt(origin,look)
    local factor=math.clamp(dt*4,0,1)
    last=last:Lerp(goal,factor)
    camera.CFrame=last
end)
