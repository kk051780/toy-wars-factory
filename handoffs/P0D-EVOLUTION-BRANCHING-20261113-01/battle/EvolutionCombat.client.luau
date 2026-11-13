--!strict
-- Independent Studio-private mobile touch controls for evolutionary BEAST PvE.
-- Deliberately no P0D production Game Remote, no purchase and no XP authority.
local RunService=game:GetService("RunService")
if not RunService:IsStudio() then return end
local Players=game:GetService("Players")
local ReplicatedStorage=game:GetService("ReplicatedStorage")
local remote=ReplicatedStorage:WaitForChild("EggRumbleEvolutionPvEDemoOnly",15)
if not remote then return end
local player=Players.LocalPlayer
local gui=Instance.new("ScreenGui")
gui.Name="EggRumbleEvoCombatPrivateHUD"
gui.ResetOnSpawn=false
gui.DisplayOrder=30
gui.IgnoreGuiInset=false
gui.Parent=player:WaitForChild("PlayerGui")
local function corner(parent)
    local c=Instance.new("UICorner")
    c.CornerRadius=UDim.new(0,10)
    c.Parent=parent
end
local function title(name,text,pos,size)
    local v=Instance.new("TextLabel")
    v.Name=name;v.Position=pos;v.Size=size
    v.BackgroundColor3=Color3.fromRGB(22,37,64)
    v.BackgroundTransparency=.1
    v.Text=text;v.TextColor3=Color3.fromRGB(253,253,255)
    v.TextScaled=true;v.Font=Enum.Font.GothamBold
    v.Parent=gui;corner(v)
    return v
end
local header=title("Progress","進化実戦デモ | 城のHP 120 / 敵 0",
    UDim2.fromScale(.16,.025),UDim2.fromScale(.68,.09))
local status=title("Form","魔獣の進化形態を選んでね",
    UDim2.fromScale(.20,.13),UDim2.fromScale(.60,.07))
local formDexLabel=title("FormDex","進化図鑑：未発見 / 6形態",
    UDim2.fromScale(.18,.22),UDim2.fromScale(.64,.07))
local formHistory=title("FormHistory","幼体 □  成長 □  紅蓮 □  蒼潮 □  神話紅蓮 □  神話蒼潮 □",
    UDim2.fromScale(.06,.31),UDim2.fromScale(.88,.085))
formHistory.TextScaled=true
local statusLine=title("CombatStatus","技の準備OK",
    UDim2.fromScale(.24,.73),UDim2.fromScale(.52,.07))
local footer=title("Safety","STUDIO専用の実戦試作｜ゲームの本当の経験値・報酬・保存には影響しません",
    UDim2.fromScale(.06,.92),UDim2.fromScale(.88,.055))
footer.TextColor3=Color3.fromRGB(255,218,141)
local function button(name,text,pos,color)
    local b=Instance.new("TextButton")
    b.Name=name;b.Position=pos
    b.Size=UDim2.fromScale(.19,.09)
    b.BackgroundColor3=color
    b.TextColor3=Color3.new(1,1,1)
    b.Font=Enum.Font.GothamBold;b.TextScaled=true
    b.Text=text;b.Parent=gui;corner(b)
    return b
end
local actions={
    {key="ASSAULT2",text="紅蓮進化",color=Color3.fromRGB(221,103,80)},
    {key="GUARD2",text="蒼潮進化",color=Color3.fromRGB(64,161,211)},
    {key="ASSAULT3",text="神話・紅蓮",color=Color3.fromRGB(189,85,71)},
    {key="GUARD3",text="神話・守護",color=Color3.fromRGB(62,128,184)},
}
for i,opt in ipairs(actions) do
    local b=button(opt.key,opt.text,
        UDim2.fromScale(.04+(i-1)*.245,.81),opt.color)
    b.MouseButton1Click:Connect(function()
        remote:FireServer("PREVIEW",opt.key)
    end)
end
local cast=button("Cast","進化技 発動",UDim2.fromScale(.73,.57),
    Color3.fromRGB(107,72,193))
cast.Size=UDim2.fromScale(.24,.12)
cast.MouseButton1Click:Connect(function()
    remote:FireServer("CAST")
end)
local lastState={castle=120,npcs=0,stage=0,branch="NONE",cooldown=12,cooldownRemaining=0}
local lastStateReceivedAt=os.clock()
local lastNoticeAt=0
remote.OnClientEvent:Connect(function(kind,payload)
    if kind=="STATE" and type(payload)=="table" then
        lastState=payload
        lastStateReceivedAt=os.clock()
        header.Text="EGG RAID RUMBLE | 城HP "..tostring(payload.castle)..
            " | 中立 "..tostring(payload.npcs).."体"
        local branch=if payload.branch=="ASSAULT" then "紅蓮・範囲攻撃"
            elseif payload.branch=="GUARD" then "蒼潮・城の守護" else "初期"
        status.Text="進化Lv"..tostring(payload.stage).." "..branch..
            " | "..tostring(payload.form or "")
    elseif kind=="FORMDEX" and type(payload)=="table" and
        payload.schema=="EGG_RUMBLE_FORM_DEX_V1" then
        local row=type(payload.items)=="table" and payload.items[1] or nil
        if type(row)=="table" and row.itemId=="forest_scout" then
            local found={}
            if type(row.discoveredForms)=="table" then
                for _,form in ipairs(row.discoveredForms) do
                    if type(form)=="table" and type(form.formId)=="string" then
                        found[form.formId]=true
                    end
                end
            end
            local ids={"forest_scout_S0","forest_scout_S1",
                "forest_scout_S2_ASSAULT","forest_scout_S2_GUARD",
                "forest_scout_S3_ASSAULT","forest_scout_S3_GUARD"}
            local labels={"幼体","成長","紅蓮","蒼潮","神話紅蓮","神話蒼潮"}
            local pieces={}
            for i,id in ipairs(ids) do
                table.insert(pieces,labels[i]..(found[id] and " ✓" or " □"))
            end
            formDexLabel.Text="進化図鑑：発見 "..tostring(row.discoveredCount)..
                " / "..tostring(row.totalPossibleForms).."（試作用データ）"
            formHistory.Text=table.concat(pieces,"   ")
        end
    elseif (kind=="INFO" or kind=="ERROR") and type(payload)=="string" then
        statusLine.Text=payload
        lastNoticeAt=os.clock()
    end
end)
RunService.RenderStepped:Connect(function()
    -- Server and client os.clock() epochs may differ. Only count down the
    -- server-certified REMAINING cooldown from local receipt time.
    local remain=math.max(0,(tonumber(lastState.cooldownRemaining) or 0)-
        (os.clock()-lastStateReceivedAt))
    cast.Text=if remain>0 then ("再使用まで "..tostring(math.ceil(remain)).."秒")
        else "進化技 発動"
    cast.BackgroundColor3=if remain>0 then Color3.fromRGB(86,86,101)
        else Color3.fromRGB(107,72,193)
    if os.clock()-lastNoticeAt>7 and (lastState.stage or 0)>0 then
        statusLine.Text=if lastState.branch=="ASSAULT"
            then "中立モンスターに近づき、範囲攻撃してみよう"
            else "城のそばで守護障壁を発動して、城のHPを守ろう"
    end
end)
