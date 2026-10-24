--!strict
-- TOY WARS FACTORY v1.2: lightweight touch + keyboard UI.
local Players=game:GetService("Players")
local ReplicatedStorage=game:GetService("ReplicatedStorage")
local player=Players.LocalPlayer
local event=ReplicatedStorage:WaitForChild("ToyWarsSelectUnit")
local B=require(ReplicatedStorage:WaitForChild("ToyWarsBalance"))
local stats=player:WaitForChild("leaderstats")
local status=player:WaitForChild("ToyWarsStatus")
local coins=stats:WaitForChild("Coins")
local wave=stats:WaitForChild("Wave")
local kills=stats:WaitForChild("Defeated")
local hp=status:WaitForChild("BaseHP")
local lv=status:WaitForChild("FactoryLevel")
local allies=status:WaitForChild("Allies")
local enemies=status:WaitForChild("Enemies")
local selected=status:WaitForChild("SelectedToy")
local gui=Instance.new("ScreenGui")
gui.Name="ToyWarsHUD"
gui.ResetOnSpawn=false
gui.DisplayOrder=10
gui.Parent=player:WaitForChild("PlayerGui")
local function round(parent,r)
    local c=Instance.new("UICorner")
    c.CornerRadius=UDim.new(0,r)
    c.Parent=parent
end
local function addText(parent,sz,pos,txt,col)
    local l=Instance.new("TextLabel")
    l.Size=sz
    l.Position=pos
    l.BackgroundTransparency=1
    l.Text=txt
    l.TextColor3=col or Color3.fromRGB(248,251,255)
    l.Font=Enum.Font.GothamBold
    l.TextScaled=true
    l.TextWrapped=true
    l.Parent=parent
    return l
end
local panel=Instance.new("Frame")
panel.Name="StatusPanel"
panel.Size=UDim2.new(0.55,0,0,106)
panel.Position=UDim2.new(0.025,0,0.035,0)
panel.BackgroundColor3=Color3.fromRGB(23,35,54)
panel.BackgroundTransparency=0.12
panel.Parent=gui
round(panel,13)
local title=addText(panel,UDim2.new(1,-20,0,28),UDim2.new(0,10,0,5),"TOY WARS FACTORY",Color3.fromRGB(255,216,115))
local summary=addText(panel,UDim2.new(1,-20,0,29),UDim2.new(0,10,0,39),"Loading...",Color3.fromRGB(251,251,255))
local subt=addText(panel,UDim2.new(1,-20,0,27),UDim2.new(0,10,0,69),"",Color3.fromRGB(169,226,231))
local pane=Instance.new("Frame")
pane.Name="SelectToy"
pane.Size=UDim2.new(0.88,0,0,90)
pane.Position=UDim2.new(0.06,0,1,-112)
pane.BackgroundColor3=Color3.fromRGB(20,33,53)
pane.BackgroundTransparency=0.12
pane.Parent=gui
round(pane,14)
local buttons={}
local choices={{"pon","PON",Color3.fromRGB(44,175,179)},{"guardon","GUARDON",Color3.fromRGB(64,113,205)},{"tankuru","TANKURU",Color3.fromRGB(218,135,72)}}
for i,spec in ipairs(choices) do
    local button=Instance.new("TextButton")
    button.Name=spec[1]
    -- Display authoritative prices from the shared balance module, never hard-code HUD prices.
    button.Text=string.format("%s | %d",spec[2],B.UNITS[spec[1]].cost)
    button.Size=UDim2.new(1/3,-12,0,62)
    button.Position=UDim2.new((i-1)/3,7,0,14)
    button.BackgroundColor3=spec[3]
    button.TextColor3=Color3.fromRGB(255,255,255)
    button.Font=Enum.Font.GothamBold
    button.TextScaled=true
    button.Parent=pane
    round(button,10)
    button.Activated:Connect(function()event:FireServer(spec[1])end)
    buttons[spec[1]]=button
end
local tip=addText(gui,UDim2.new(0.8,0,0,34),UDim2.new(0.1,0,1,-160),"SELECT A TOY TO AUTO-PRODUCE • UPGRADE AT THE GOLD PLATFORM",Color3.fromRGB(255,255,255))
tip.TextStrokeTransparency=0.4
local function refresh()
    summary.Text=string.format("COINS %d  |  WAVE %d  |  VAULT %d%%",coins.Value,wave.Value,hp.Value)
    subt.Text=string.format("LV %d  •  TOYS %d  •  JUNK %d  •  KILLS %d",lv.Value,allies.Value,enemies.Value,kills.Value)
    for id,button in pairs(buttons) do
        button.BorderSizePixel=(string.upper(id)==selected.Value) and 3 or 0
        button.BorderColor3=Color3.fromRGB(255,255,255)
    end
end
for _,v in ipairs({coins,wave,kills,hp,lv,allies,enemies,selected}) do v.Changed:Connect(refresh) end
refresh()
print("TWF_HUD_OK v1.2")
