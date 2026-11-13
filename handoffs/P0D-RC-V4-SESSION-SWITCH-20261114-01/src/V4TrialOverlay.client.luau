--!nocheck
-- OWNER-private six-skill UI; reads replicated Player attributes ONLY.
-- Original H1 BEAST/WEAPON real XP and all 47 Luau sources remain untouched.
local RunService=game:GetService("RunService")
if not RunService:IsStudio() then return end
local Players=game:GetService("Players")
local ReplicatedStorage=game:GetService("ReplicatedStorage")
local PUBLIC_KEY="P0D_RC_V4_SESSION_ACTIVE"
local player=Players.LocalPlayer
if not player then return end
local gui=Instance.new("ScreenGui")
gui.Name="P0D_V4_SIX_SKILL_STUDIO_SESSION_ONLY"
gui.ResetOnSpawn=false
gui.IgnoreGuiInset=false
gui.DisplayOrder=18
gui.Parent=player:WaitForChild("PlayerGui")
-- OFF until the trusted server explicitly advertises enablement; nil fails closed.
gui.Enabled=ReplicatedStorage:GetAttribute(PUBLIC_KEY)==true
ReplicatedStorage:GetAttributeChangedSignal(PUBLIC_KEY):Connect(function()
    gui.Enabled=ReplicatedStorage:GetAttribute(PUBLIC_KEY)==true
end)
local box=Instance.new("Frame")
box.Name="Panel"; box.AnchorPoint=Vector2.new(0,1)
box.Position=UDim2.new(0,8,1,-20); box.Size=UDim2.fromOffset(224,231)
box.BackgroundColor3=Color3.fromRGB(16,27,48)
box.BackgroundTransparency=.14
box.Parent=gui
local corner=Instance.new("UICorner")
corner.CornerRadius=UDim.new(0,9);corner.Parent=box
local function label(name,y,h,sz,color)
    local text=Instance.new("TextLabel")
    text.Name=name
    text.BackgroundTransparency=1
    text.Position=UDim2.fromOffset(8,y)
    text.Size=UDim2.new(1,-16,0,h)
    text.Font=Enum.Font.GothamBold
    text.TextSize=sz
    text.TextColor3=color or Color3.fromRGB(255,255,255)
    text.TextXAlignment=Enum.TextXAlignment.Left
    text.TextYAlignment=Enum.TextYAlignment.Center
    text.Text=""
    text.Parent=box
    return text
end
local title=label("Title",5,21,14,Color3.fromRGB(232,216,128))
title.Text="6系統 修行（体験版）"
local status=label("Status",27,29,11,Color3.fromRGB(187,233,255))
local skills={
    {"BEAST","魔獣"},{"MAGIC","魔法"},{"WEAPON","武器"},
    {"ZOMBIE","ゾンビ"},{"VEHICLE","乗り物"},{"BUILDING","建築"}
}
local rows={}
for i,entry in ipairs(skills) do
    rows[i]=label(entry[1],53+(i-1)*23,22,12,Color3.fromRGB(236,240,248))
end
local footer=label("Important",198,30,11,Color3.fromRGB(255,189,156))
footer.Text="保存なし / 対戦強化なし / 課金なし"
local function render()
    local active=player:GetAttribute("P0D_V4_Active")==true
    local mode=player:GetAttribute("P0D_V4_Mode")
    local left=tonumber(player:GetAttribute("P0D_V4_Remaining")) or 1800
    local current=player:GetAttribute("P0D_V4_Current") or "-"
    local friends=tonumber(player:GetAttribute("P0D_V4_Friends")) or 0
    status.Text=string.format("%s  %s %s / 残り%dm / 友達%d",
        active and "修行中" or "待機", mode=="FOCUS" and "集中" or "ランダム",
        tostring(current), math.ceil(left/60), math.floor(friends))
    for i,entry in ipairs(skills) do
        local skill,display=entry[1],entry[2]
        local lv=tonumber(player:GetAttribute("P0D_V4_"..skill.."_LV")) or 1
        local xp=tonumber(player:GetAttribute("P0D_V4_"..skill.."_XP")) or 0
        local nextXP=tonumber(player:GetAttribute("P0D_V4_"..skill.."_NEXT")) or 100
        rows[i].Text=string.format("%s   Lv%d   XP%d  次まで%d",display,lv,xp,nextXP)
    end
end
local toggle=Instance.new("TextButton")
toggle.Name="Fold";toggle.AnchorPoint=Vector2.new(0,1)
toggle.Position=UDim2.new(0,8,1,-256)
toggle.Size=UDim2.fromOffset(92,24)
toggle.BackgroundColor3=Color3.fromRGB(52,69,112)
toggle.TextColor3=Color3.fromRGB(255,255,255)
toggle.TextSize=12;toggle.Font=Enum.Font.GothamBold
toggle.Text="修行表示：ON"
toggle.Parent=gui
local folded=false
toggle.MouseButton1Click:Connect(function()
    folded=not folded
    box.Visible=not folded
    toggle.Text=folded and "修行表示：OFF" or "修行表示：ON"
end)
player.AttributeChanged:Connect(function(attr)
    if string.sub(attr,1,7)=="P0D_V4_" then render() end
end)
render()
print("[P0D_V4_BRIDGE] SESSION_ONLY_UI_LOADED; NOT real saved skills")
