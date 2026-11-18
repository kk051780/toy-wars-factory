--!strict
-- Studio-only, NO-COMMERCE 2-column trade preview opened by existing GQ8_TradeExplanation Prompt.
-- No Remote / inventory grant / data save / paid item exchange. An explicit disabled action.
local RunService=game:GetService("RunService")
if not RunService:IsStudio() then return end
local Players=game:GetService("Players")
local Prompts=game:GetService("ProximityPromptService")
local player=Players.LocalPlayer
if not player then return end
local playerGui=player:WaitForChild("PlayerGui")
if playerGui:FindFirstChild("GQ8_TradeReviewPreview") then return end
local gui=Instance.new("ScreenGui")
gui.Name="GQ8_TradeReviewPreview"
gui.ResetOnSpawn=false;gui.IgnoreGuiInset=false
gui.DisplayOrder=18;gui.Enabled=false;gui.Parent=playerGui
gui:SetAttribute("GQ8_NoTradeAuthority",true)
local veil=Instance.new("Frame")
veil.Name="Shade";veil.Size=UDim2.fromScale(1,1)
veil.BackgroundColor3=Color3.fromRGB(11,18,32);veil.BackgroundTransparency=.18
veil.Parent=gui
local panel=Instance.new("Frame")
panel.Name="TradePanel";panel.AnchorPoint=Vector2.new(.5,.5)
panel.Position=UDim2.fromScale(.5,.5);panel.Size=UDim2.fromScale(.93,.82)
panel.BackgroundColor3=Color3.fromRGB(27,40,61)
panel.BorderSizePixel=0;panel.Parent=veil
local limit=Instance.new("UISizeConstraint")
limit.MaxSize=Vector2.new(720,480);limit.Parent=panel
local corner=Instance.new("UICorner");corner.CornerRadius=UDim.new(0,13);corner.Parent=panel
local stroke=Instance.new("UIStroke");stroke.Color=Color3.fromRGB(138,166,187)
stroke.Thickness=1;stroke.Parent=panel
local function label(name,txt,xy,wh,sz,col,parent)
    local x=Instance.new("TextLabel")
    x.Name=name;x.BackgroundTransparency=1;x.TextColor3=col
    x.Font=Enum.Font.GothamMedium;x.TextWrapped=true;x.TextScaled=true
    x.Text=txt;x.Position=xy;x.Size=wh;x.Parent=parent or panel
    return x
end
local title=label("TradeTitle","トレード広場  |  安全な交換",UDim2.fromScale(.04,.025),
    UDim2.fromScale(.77,.1),21,Color3.fromRGB(253,242,203))
title.TextXAlignment=Enum.TextXAlignment.Left
local function button(name,txt,xy,wh,bg)
    local b=Instance.new("TextButton");b.Name=name;b.Position=xy;b.Size=wh
    b.Text=txt;b.TextScaled=true;b.TextWrapped=true;b.Font=Enum.Font.GothamBold
    b.TextColor3=Color3.fromRGB(251,247,233);b.BackgroundColor3=bg
    b.AutoButtonColor=true;b.Parent=panel
    local c=Instance.new("UICorner");c.CornerRadius=UDim.new(0,7);c.Parent=b
    return b
end
local close=button("CloseTradePreview","× 閉じる",UDim2.fromScale(.82,.03),
  UDim2.fromScale(.14,.09),Color3.fromRGB(99,65,74))
local tabs={"武器","魔獣","守護兵","アイテム"}
local explanations={
 "武器：見た目と属性を確認して交換",
 "魔獣：種類・進化・個体IDを確認",
 "守護兵：役職と個性を確認",
 "アイテム：レア素材・装飾品を確認",
}
local filter=label("SelectedCategory",explanations[1],UDim2.fromScale(.05,.145),
 UDim2.fromScale(.9,.085),14,Color3.fromRGB(199,222,233))
for i,name in ipairs(tabs) do
    local tab=button("Category"..i,name,
      UDim2.fromScale(.05+(i-1)*.23,.25),
      UDim2.fromScale(.21,.08),Color3.fromRGB(64,100,119))
    tab.Activated:Connect(function() filter.Text=explanations[i] end)
end
local yours=label("YourOffer","あなたが出すもの (0/8)\n\n所持品未接続\n出品操作は現在できません",
 UDim2.fromScale(.045,.355),UDim2.fromScale(.44,.31),16,Color3.fromRGB(228,237,236))
local theirs=label("OtherOffer","相手が出すもの (0/8)\n\n交換相手未選択\nアイテムの交換は未稼働",
 UDim2.fromScale(.515,.355),UDim2.fromScale(.44,.31),16,Color3.fromRGB(228,237,236))
for _,p in ipairs({yours,theirs}) do
    p.BackgroundTransparency=0;p.BackgroundColor3=Color3.fromRGB(40,59,78)
    local c=Instance.new("UICorner");c.CornerRadius=UDim.new(0,9);c.Parent=p
end
local notice=label("SafetyNotice",
 "両者の出品内容を固定 → 5秒確認 → 双方の最終承認が必要\n※ 現在は展示・説明のみ／交換やアイテム移動は発生しません",
 UDim2.fromScale(.05,.68),UDim2.fromScale(.9,.16),15,Color3.fromRGB(252,210,142))
local disabled=button("TradeDisabled","交換を確定（未接続）",UDim2.fromScale(.23,.865),
 UDim2.fromScale(.54,.095),Color3.fromRGB(97,103,111))
disabled.Active=false;disabled.AutoButtonColor=false
close.Activated:Connect(function()gui.Enabled=false end)
local function legitimatePrompt(prompt)
    if not prompt or prompt.Name~="GQ8_TradeExplanation" then return false end
    local root=prompt:FindFirstAncestor("GQ8_LobbySocialPlaza")
    if not root or not root:IsDescendantOf(workspace) then return false end
    local char=player.Character
    local hrp=char and char:FindFirstChild("HumanoidRootPart")
    local parent=prompt.Parent
    return hrp and hrp:IsA("BasePart") and parent and parent:IsA("BasePart")
       and (hrp.Position-parent.Position).Magnitude<=13
end
Prompts.PromptTriggered:Connect(function(prompt:ProximityPrompt,who:Player)
    if who~=player then return end
    if legitimatePrompt(prompt) then
        gui.Enabled=true
        filter.Text=explanations[1]
    end
end)
