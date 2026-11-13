--!nocheck
-- P0D REALM_HUNT_V1: tiny client-only discovery HUD, driven exclusively by server attributes.
local RunService=game:GetService("RunService")
if not RunService:IsStudio() then return end
local Players=game:GetService("Players")
local player=Players.LocalPlayer
if not player then return end
local playerGui=player:WaitForChild("PlayerGui",20)
if not playerGui then return end
local old=playerGui:FindFirstChild("P0DRealmHuntHUD")
if old then old:Destroy() end
local gui=Instance.new("ScreenGui")
gui.Name="P0DRealmHuntHUD"
gui.ResetOnSpawn=false
gui.IgnoreGuiInset=false
gui.DisplayOrder=5
gui.Parent=playerGui

local card=Instance.new("Frame")
card.Name="RealmProgress"
card.AnchorPoint=Vector2.new(1,0)
card.Position=UDim2.new(1,-12,0,80)
card.Size=UDim2.fromOffset(150,48)
card.BackgroundColor3=Color3.fromRGB(27,33,53)
card.BackgroundTransparency=0.24
card.BorderSizePixel=0
card.Parent=gui
local corner=Instance.new("UICorner")
corner.CornerRadius=UDim.new(0,9)
corner.Parent=card
local heading=Instance.new("TextLabel")
heading.Name="CountLabel"
heading.Size=UDim2.new(1,-12,0,25)
heading.Position=UDim2.fromOffset(6,2)
heading.BackgroundTransparency=1
heading.Font=Enum.Font.GothamBold
heading.TextScaled=true
heading.TextColor3=Color3.fromRGB(255,245,195)
heading.Parent=card
local detail=Instance.new("TextLabel")
detail.Name="RealmNames"
detail.Size=UDim2.new(1,-12,0,17)
detail.Position=UDim2.fromOffset(6,28)
detail.BackgroundTransparency=1
detail.Font=Enum.Font.Gotham
detail.TextScaled=true
detail.TextColor3=Color3.fromRGB(220,228,248)
detail.Parent=card
local prefix="P0D_RealmHunt_"
local function update()
    local enabled=player:GetAttribute(prefix.."Enabled")==true
    card.Visible=enabled
    if not enabled then return end
    local n=player:GetAttribute(prefix.."Count")
    if type(n)~="number" then n=0 end
    n=math.clamp(math.floor(n),0,4)
    local complete=player:GetAttribute(prefix.."Complete")==true
    heading.Text=complete and "★ 秘境制覇 4/4 ★" or ("✦ 秘境発見 "..tostring(n).."/4")
    local names={}
    for _,s in ipairs({"SKY","SEA","EMBER","STAR"}) do
        table.insert(names,player:GetAttribute(prefix..s)==true and "●" or "○")
    end
    detail.Text=table.concat(names,"  ").."  空 海 炎 星"
    if complete then
        card.BackgroundColor3=Color3.fromRGB(100,71,21)
    else
        card.BackgroundColor3=Color3.fromRGB(27,33,53)
    end
end
for _,key in ipairs({"Enabled","Count","Complete","SKY","SEA","EMBER","STAR"}) do
    player:GetAttributeChangedSignal(prefix..key):Connect(update)
end
update()
