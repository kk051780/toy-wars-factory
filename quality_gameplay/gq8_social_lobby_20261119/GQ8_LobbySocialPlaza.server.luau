--!strict
-- Optional Studio-only social and trade showroom. No Store, Remote, or player-item authority.
local RunService = game:GetService("RunService")
if not RunService:IsStudio() then return end
local Players = game:GetService("Players")
if workspace:FindFirstChild("GQ8_LobbySocialPlaza", true) then return end
local spawn = workspace:FindFirstChildWhichIsA("SpawnLocation", true)
if not spawn then warn("[GQ8 SOCIAL] no safe SpawnLocation: skip") return end
local center = spawn.Position + Vector3.new(-49, -spawn.Size.Y*0.5, 8)
local plaza = Instance.new("Model")
plaza.Name = "GQ8_LobbySocialPlaza"
plaza:SetAttribute("GQ8_StudioPreviewOnly",true)
plaza:SetAttribute("GQ8_TradeSettlementDisabled",true)
plaza:SetAttribute("GQ8_FeatureId","GQ8_LOBBY_SOCIAL_TRADE_20261119")
plaza.Parent = workspace
local partCount = 0
local function part(name:string,at:Vector3,size:Vector3,color:Color3,material:Enum.Material,solid:boolean):Part
    local p=Instance.new("Part")
    p.Name=name; p.Size=size;p.Position=center+at
    p.Anchored=true;p.CanCollide=solid;p.CanTouch=false;p.CanQuery=solid
    p.Material=material;p.Color=color;p.TopSurface=Enum.SurfaceType.Smooth
    p.BottomSurface=Enum.SurfaceType.Smooth;p.Parent=plaza
    partCount+=1
    return p
end
local function label(at:BasePart,contents:string):TextLabel
    local b=Instance.new("BillboardGui");b.Name="SocialTitle"
    b.Size=UDim2.fromOffset(180,50)
    b.StudsOffsetWorldSpace=Vector3.new(0,2.4,0)
    b.MaxDistance=42;b.AlwaysOnTop=false;b.Parent=at
    local t=Instance.new("TextLabel");t.Size=UDim2.fromScale(1,1)
    t.BackgroundColor3=Color3.fromRGB(22,35,50);t.BackgroundTransparency=.18
    t.TextColor3=Color3.fromRGB(255,242,204);t.Font=Enum.Font.GothamBold
    t.TextScaled=true;t.TextWrapped=true;t.Text=contents;t.Parent=b
    return t
end
local stone=Color3.fromRGB(113,131,143)
local wood=Color3.fromRGB(117,84,63)
local gold=Color3.fromRGB(223,187,112)
part("SpawnToPlazaPath",Vector3.new(26,-.5,-8),Vector3.new(52,1,7),stone,Enum.Material.Slate,true)
part("PlazaBase",Vector3.new(0,-1.2,0),Vector3.new(72,2.4,48),stone,Enum.Material.Cobblestone,true)
part("GrassTop",Vector3.new(0,.07,0),Vector3.new(69,.14,45),Color3.fromRGB(97,158,115),Enum.Material.Grass,true)
part("MainPath",Vector3.new(0,.22,0),Vector3.new(66,.24,6),stone,Enum.Material.Slate,true)
part("CrossPath",Vector3.new(0,.23,0),Vector3.new(6,.25,41),stone,Enum.Material.Slate,true)
local meeting={
    {"01","森の集合所",-23,-13,Color3.fromRGB(103,180,134)},
    {"02","海の集合所",23,-13,Color3.fromRGB(81,157,217)},
    {"03","空の集合所",-23,13,Color3.fromRGB(164,122,217)},
    {"04","城の集合所",23,13,Color3.fromRGB(224,154,91)},
}
local counts={}
for i,m in ipairs(meeting) do
    local x=m[3]::number;local z=m[4]::number
    part("MeetingRug_"..m[1],Vector3.new(x,.27,z),Vector3.new(10,.3,9),m[5]::Color3,Enum.Material.Fabric,true)
    local flag=part("MeetingFlag_"..m[1],Vector3.new(x,4,z-3),Vector3.new(5,6,.35),m[5]::Color3,Enum.Material.Fabric,false)
    part("MeetingPole_"..m[1],Vector3.new(x-3,3.4,z-3),Vector3.new(.5,7,.5),wood,Enum.Material.Wood,false)
    counts[i]=label(flag,m[1].." "..m[2].."\n待ち合わせ")
end
-- Trading bazaar is adjacent to the photo pavilion, never overlap existing GQ805 shop at spawn+43.
for i,title in ipairs({"武器の交換展示","魔獣の交換展示","守護兵の交換展示"}) do
    local x=-19+(i-1)*19
    local basePlate=part("TradeBooth_"..i,Vector3.new(x,.5,22),Vector3.new(13,1,6),wood,Enum.Material.WoodPlanks,true)
    local board=part("TradeBoard_"..i,Vector3.new(x,5,23.5),Vector3.new(10,5,.6),gold,Enum.Material.Wood,false)
    label(board,title.."\n正式交換は準備中")
    local pr=Instance.new("ProximityPrompt")
    pr.Name="GQ8_TradeExplanation";pr.ActionText="交換の説明"
    pr.ObjectText=title.."（決済OFF）"
    pr.MaxActivationDistance=10;pr.HoldDuration=.3;pr.RequiresLineOfSight=true;pr.Parent=basePlate
    local textLabel=board:FindFirstChild("SocialTitle") :: BillboardGui?
    local msg=(textLabel and textLabel:FindFirstChildWhichIsA("TextLabel")) :: TextLabel?
    pr.Triggered:Connect(function(player:Player)
        local c=player.Character;local root=c and c:FindFirstChild("HumanoidRootPart")
        if player.Parent~=Players or not (root and root:IsA("BasePart")) then return end
        if (root.Position-basePlate.Position).Magnitude>12 then return end
        if msg then
            msg.Text="交換は双方の確認で成立\n現在は展示のみ"
            task.delay(4,function()
                if msg and msg.Parent then msg.Text=title.."\n正式交換は準備中" end
            end)
        end
    end)
end
for _,x in ipairs({-7,7}) do
    for _,z in ipairs({-4,4}) do
        part("PhotoPillar",Vector3.new(x,4,z),Vector3.new(1.4,8,1.4),wood,Enum.Material.Wood,true)
    end
end
part("PhotoRoof",Vector3.new(0,8.8,0),Vector3.new(18,1.5,12),Color3.fromRGB(78,128,166),Enum.Material.Slate,false)
local photo=part("FriendPhoto",Vector3.new(0,.45,0),Vector3.new(10,.5,6),gold,Enum.Material.WoodPlanks,true)
local text=label(photo,"2人で記念ライト\n無料・参加自由")
local prompt=Instance.new("ProximityPrompt")
prompt.Name="GQ8_PhotoOptIn";prompt.ActionText="参加する";prompt.ObjectText="フレンドフォト"
prompt.MaxActivationDistance=9;prompt.HoldDuration=.3;prompt.RequiresLineOfSight=true;prompt.Parent=photo
local light=Instance.new("PointLight")
light.Enabled=false;light.Brightness=2;light.Range=19;light.Color=Color3.fromRGB(253,217,136);light.Parent=photo
local particles=Instance.new("ParticleEmitter")
particles.Rate=0;particles.Lifetime=NumberRange.new(.5,.9);particles.Speed=NumberRange.new(2,5)
particles.Size=NumberSequence.new(.2);particles.Parent=photo
local opted:{[number]:number}={}
local untilNext=0
local function aliveRoot(player:Player):BasePart?
    local char=player.Character
    local hum=char and char:FindFirstChildWhichIsA("Humanoid")
    local root=char and char:FindFirstChild("HumanoidRootPart")
    if hum and hum.Health>0 and root and root:IsA("BasePart") then return root end
    return nil
end
prompt.Triggered:Connect(function(player:Player)
    local root=aliveRoot(player)
    if player.Parent==Players and root and (root.Position-photo.Position).Magnitude<=10 then
        opted[player.UserId]=time()+20
    end
end)
Players.PlayerRemoving:Connect(function(player:Player) opted[player.UserId]=nil end)
local t=0
local hb:RBXScriptConnection?
hb=RunService.Heartbeat:Connect(function(dt)
    if not plaza.Parent then if hb then hb:Disconnect() end return end
    t+=dt;if t<1 then return end;t=0
    local now=time()
    local count={0,0,0,0};local joins={}
    for _,player in ipairs(Players:GetPlayers()) do
        local root=aliveRoot(player)
        if root then
            for i,m in ipairs(meeting) do
                if (root.Position-(center+Vector3.new(m[3]::number,1,m[4]::number))).Magnitude<7 then count[i]+=1 end
            end
            if (opted[player.UserId] or 0)>now and (root.Position-photo.Position).Magnitude<10 then
                table.insert(joins,player.UserId)
            end
        end
    end
    for i,m in ipairs(meeting) do counts[i].Text=m[1].." "..m[2].."\n集合中 "..count[i].."人" end
    if #joins>=2 and now>=untilNext then
        untilNext=now+12
        for _,id in ipairs(joins) do opted[id]=nil end
        light.Enabled=true;particles:Emit(12);text.Text="フレンドと記念ライト！\nまた集まろう"
        task.delay(2,function()
            if photo.Parent then light.Enabled=false;text.Text="2人で記念ライト\n無料・参加自由" end
        end)
    end
end)
plaza:SetAttribute("GQ8_PartBudget",partCount)
print("[GQ8 LOBBY SOCIAL] safe Studio preview, 4 meeting areas, 3 no-commerce stalls, 2-player photo",partCount)
