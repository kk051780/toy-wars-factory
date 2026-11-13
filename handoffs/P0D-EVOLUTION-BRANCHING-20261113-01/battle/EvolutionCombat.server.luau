--!strict
-- EGG RAID RUMBLE #287: ORIGINAL PRIVATE STUDIO PvE evolution combat sandbox.
-- NOT the actual H1/H2 Game. No real Owned/XP/level save, PvP or live shop.
local RunService=game:GetService("RunService")
if not RunService:IsStudio() then return end
local Players=game:GetService("Players")
local ReplicatedStorage=game:GetService("ReplicatedStorage")
local TweenService=game:GetService("TweenService")
local E=require(script.Parent:WaitForChild("EvolutionRules"))
local remote=Instance.new("RemoteEvent")
remote.Name="EggRumbleEvolutionPvEDemoOnly"
remote.Parent=ReplicatedStorage
local world=Instance.new("Folder")
world.Name="EggRumbleEvolutionPvEPrivateOnly"
world.Parent=workspace
local states={}
local living={}
local castleHealth=120
local maxNpcs=14
local nextNpc=0
local nextDemo=0
local lastStatus=0
local shieldUntil=0
local shieldHits=0
local shieldVisual=nil
local now=function() return os.clock() end
local function part(name,sz,cf,color,parent,material,shape)
    local p=Instance.new("Part")
    p.Name=name;p.Size=sz;p.CFrame=cf;p.Color=color
    p.Anchored=true;p.CanCollide=false;p.CanQuery=false;p.CanTouch=false
    p.Material=material or Enum.Material.SmoothPlastic
    if shape then p.Shape=shape end
    p.Parent=parent or world
    return p
end
local function core(player)
    return player.Character and player.Character:FindFirstChild("HumanoidRootPart")
end
local function msg(player,kind,data)
    if player and player.Parent==Players then remote:FireClient(player,kind,data) end
end
local function notifyAll(text)
    for _,p in ipairs(Players:GetPlayers()) do msg(p,"INFO",text) end
end
part("ArenaFloor",Vector3.new(126,2,126),CFrame.new(0,-1,0),
    Color3.fromRGB(66,139,113),world,Enum.Material.Grass)
local castle=part("CastleCore",Vector3.new(12,10,12),CFrame.new(0,5,0),
    Color3.fromRGB(114,178,238),world,Enum.Material.Slate)
local castleLight=Instance.new("PointLight")
castleLight.Color=Color3.fromRGB(128,210,255)
castleLight.Brightness=2;castleLight.Range=25;castleLight.Parent=castle
local fortBill=Instance.new("BillboardGui")
fortBill.Name="CoreHP";fortBill.Size=UDim2.fromOffset(200,62)
fortBill.StudsOffsetWorldSpace=Vector3.new(0,9,0);fortBill.AlwaysOnTop=true
fortBill.MaxDistance=180;fortBill.Parent=castle
local fortText=Instance.new("TextLabel")
fortText.Size=UDim2.fromScale(1,1);fortText.TextScaled=true
fortText.Font=Enum.Font.GothamBold;fortText.TextColor3=Color3.new(1,1,1)
fortText.BackgroundColor3=Color3.fromRGB(26,44,64)
fortText.BackgroundTransparency=.25;fortText.Text="城のHP 120/120"
fortText.Parent=fortBill
local spawn=Instance.new("SpawnLocation")
spawn.Name="EvolutionTrainingSpawn"
spawn.Size=Vector3.new(10,1,10);spawn.Anchored=true
spawn.Neutral=true;spawn.Position=Vector3.new(0,0,32)
spawn.Parent=world
local function liveCount()
    local n=0
    for _,e in pairs(living) do
        if e.humanoid.Health>0 and e.model.Parent then n+=1 end
    end
    return n
end
local function labelState(player)
    local st=states[player]
    if not st then return end
    local form=st.form
    msg(player,"STATE",{
        castle=castleHealth,npcs=liveCount(),
        form=form and form.formId or "未進化",
        branch=form and form.branch or "NONE",
        stage=form and form.stage or 0,
        lastCast=st.lastCast,
        cooldown=12,
        cooldownRemaining=math.max(0,12-(now()-st.lastCast)),
        source="PRIVATE_STUDIO_ONLY",
    })
end
local function updateStatus()
    fortText.Text="城のHP "..tostring(math.max(0,castleHealth)).."/120"
    for _,p in ipairs(Players:GetPlayers()) do labelState(p) end
end
local function makeDragon(player,form)
    local st=states[player]
    if st.dragon then st.dragon:Destroy();st.dragon=nil end
    if not form then return end
    local root=core(player)
    if not root then return end
    local scale=if form.stage>=3 then 2.1 elseif form.stage>=2 then 1.45 else 1
    local hue=if form.branch=="ASSAULT" then Color3.fromRGB(251,110,76)
        elseif form.branch=="GUARD" then Color3.fromRGB(85,189,241)
        else Color3.fromRGB(114,225,170)
    local creature=Instance.new("Model")
    creature.Name="Evolved_"..player.Name.."_"..form.formId
    local origin=root.Position+Vector3.new(5,5,0)
    local body=part("Body",Vector3.new(3.8,3,4.4)*scale,CFrame.new(origin),
        hue,creature,nil,Enum.PartType.Ball)
    part("Head",Vector3.new(3.2,3,3.0)*scale,
        CFrame.new(origin+Vector3.new(0,1.3,-1.45)*scale),
        hue,creature,nil,Enum.PartType.Ball)
    for _,side in ipairs({-1,1}) do
        part("Wing_"..side,Vector3.new(3.2,.45,3.1)*scale,
            CFrame.new(origin+Vector3.new(side*2.3,.9,.8)*scale)*
                CFrame.Angles(0,0,math.rad(side*17)),
            Color3.fromRGB(224,234,241),creature)
        part("Eye_"..side,Vector3.new(.35,.38,.38)*scale,
            CFrame.new(origin+Vector3.new(side*.73,1.5,-2.9)*scale),
            Color3.fromRGB(22,32,56),creature,nil,Enum.PartType.Ball)
    end
    if form.stage==3 then
        local highlight=Instance.new("Highlight")
        highlight.FillColor=hue;highlight.FillTransparency=.75
        highlight.OutlineColor=Color3.fromRGB(251,236,165)
        highlight.Parent=creature
        local light=Instance.new("PointLight")
        light.Brightness=1.5;light.Range=16;light.Color=hue;light.Parent=body
    end
    creature.PrimaryPart=body;creature.Parent=world
    st.dragon=creature
end
local function serverDemoEvolution(player,stage,branch)
    local st=states[player]
    if not st then return false end
    nextDemo+=1
    local serial=tostring(nextDemo)..":"..tostring(st.userId)
    local profile=E.newProfile(st.userId)
    local owned={forest_scout=1}
    -- Explicitly SIMULATED server-certified progression solely for this private
    -- visual QA sandbox. No real match/earned shards/XP; not saved anywhere.
    for i=1,11 do
        local ok=E.creditRound(profile,"PREVIEW_ONLY:"..serial..":"..i,2,240,true)
        if not ok then return false end
    end
    local ok=E.evolve(profile,"forest_scout",owned,10,3,"LOBBY",
        "dev-stage1:"..serial,"NONE",true)
    if not ok then return false end
    ok=E.evolve(profile,"forest_scout",owned,25,6,"LOBBY",
        "dev-stage2:"..serial,branch,true)
    if not ok then return false end
    if stage==3 then
        ok=E.evolve(profile,"forest_scout",owned,40,10,"LOBBY",
            "dev-stage3:"..serial,"NONE",true)
        if not ok then return false end
    end
    st.profile=profile
    st.form=E.form(profile,"forest_scout",owned)
    st.lastCast=-100000
    makeDragon(player,st.form)
    labelState(player)
    return true
end
local function cleanNpc(id)
    local entry=living[id]
    if not entry then return end
    living[id]=nil
    if entry.model and entry.model.Parent then entry.model:Destroy() end
end
local function makeNpc()
    if liveCount()>=maxNpcs then return end
    nextNpc+=1
    local id=nextNpc
    local angle=(id*2.399963229728653)% (2*math.pi)
    local start=Vector3.new(math.cos(angle)*52,3,math.sin(angle)*52)
    local npc=Instance.new("Model")
    npc.Name="TrainingNeutral_"..id
    local body=part("TrainingBody",Vector3.new(4.1,4.1,4.1),
        CFrame.new(start),Color3.fromRGB(180,118,212),npc,nil,Enum.PartType.Ball)
    part("OneEye",Vector3.new(.85,.85,.85),
        CFrame.new(start+Vector3.new(0,.3,-1.95)),
        Color3.fromRGB(255,242,158),npc,nil,Enum.PartType.Ball)
    npc.PrimaryPart=body
    local hum=Instance.new("Humanoid")
    hum.Name="TrainingNeutralHealth";hum.MaxHealth=60;hum.Health=60
    hum.DisplayDistanceType=Enum.HumanoidDisplayDistanceType.Always
    hum.Parent=npc
    npc:SetAttribute("EvolutionStudioTrainingNPC",true)
    npc.Parent=world
    living[id]={id=id,model=npc,humanoid=hum,pos=start,attackAt=0}
    hum.Died:Connect(function()
        task.delay(.25,function() cleanNpc(id) end)
    end)
end
local function pulse(center,radius,color)
    local orb=part("AbilityPulse",Vector3.new(1,1,1),
        CFrame.new(center),color,world,Enum.Material.Neon,Enum.PartType.Ball)
    orb.Transparency=.3
    local tween=TweenService:Create(orb,TweenInfo.new(.55),
        {Size=Vector3.new(radius*2,radius*2,radius*2),Transparency=1})
    tween:Play()
    task.delay(.7,function() orb:Destroy() end)
end
local function clearShield()
    shieldHits=0;shieldUntil=0
    if shieldVisual then shieldVisual:Destroy();shieldVisual=nil end
end
local function cast(player)
    local st=states[player]
    if not st or not st.form or st.form.stage<2 or not st.dragon then return end
    if not core(player) then return end
    if now()-st.lastCast<12 then msg(player,"ERROR","技の再使用まで待ってね");return end
    local form=E.form(st.profile,"forest_scout",{forest_scout=1})
    if not form or form.formId~=st.form.formId or form.category~="BEAST" then
        msg(player,"ERROR","進化状態が無効");return
    end
    -- Defensive evolution must actually be near the castle; neither
    -- a teammate across the map nor an egg carrier can remote-shield it.
    if form.branch=="GUARD" and
        (core(player).Position-castle.Position).Magnitude>33 then
        msg(player,"ERROR","守護技は城の近くで発動してね")
        return
    end
    st.lastCast=now()
    if form.branch=="ASSAULT" then
        local origin=core(player).Position
        local radius=if form.stage>=3 then 25 else 17
        pulse(origin,radius,Color3.fromRGB(255,138,88))
        local hits=0
        for _,entry in pairs(living) do
            if entry.model.Parent and entry.humanoid.Health>0 and
                (entry.pos-origin).Magnitude<=radius then
                entry.humanoid:TakeDamage(if form.stage>=3 then 120 else 70)
                hits+=1
            end
        end
        msg(player,"INFO","進化奥義！中立の敵"..tostring(hits).."体に広範囲攻撃")
    elseif form.branch=="GUARD" then
        clearShield()
        shieldHits=if form.stage>=3 then 5 else 3
        shieldUntil=now()+8
        local barrier=part("GuardianProtectsCastle",Vector3.new(24,24,24),
            CFrame.new(0,5,0),Color3.fromRGB(85,195,253),
            world,Enum.Material.ForceField,Enum.PartType.Ball)
        barrier.Transparency=.75
        shieldVisual=barrier
        msg(player,"INFO","守護進化！城を8秒間・"..tostring(shieldHits).."回まで守る")
    end
    labelState(player)
end
local function userId(player,index)
    return if player.UserId>0 then player.UserId else 100000000+index
end
local joined=0
local function join(player)
    joined+=1
    states[player]={userId=userId(player,joined),profile=nil,
        form=nil,dragon=nil,lastCast=-100000,lastSelect=-100000}
    player.CharacterAdded:Connect(function(c)
        task.defer(function()
            local root=c:WaitForChild("HumanoidRootPart",5)
            if root then root.CFrame=CFrame.new((joined%2)*10,8,30) end
            local st=states[player]
            if st and st.form then makeDragon(player,st.form) end
        end)
    end)
    msg(player,"INFO","STUDIO専用。紅蓮か守護の進化を選んで、技を使ってみてね")
    labelState(player)
end
Players.PlayerAdded:Connect(join)
for _,p in ipairs(Players:GetPlayers()) do join(p) end
Players.PlayerRemoving:Connect(function(p)
    local st=states[p]
    if st and st.dragon then st.dragon:Destroy() end
    states[p]=nil
end)
remote.OnServerEvent:Connect(function(player,action,argument)
    if type(action)~="string" then return end
    local st=states[player]
    if not st then return end
    if action=="PREVIEW" then
        local options={ASSAULT2={2,"ASSAULT"},GUARD2={2,"GUARD"},
            ASSAULT3={3,"ASSAULT"},GUARD3={3,"GUARD"}}
        if type(argument)~="string" then return end
        local selection=options[argument]
        if not selection then return end
        if now()-st.lastSelect<1 then return end
        st.lastSelect=now()
        if not serverDemoEvolution(player,selection[1],selection[2]) then
            msg(player,"ERROR","デモ進化失敗")
        else
            msg(player,"INFO","サーバーで進化を再現！実アカウントLv/報酬は変更しない")
        end
    elseif action=="CAST" then
        cast(player)
    end
end)
local lastSpawn=0
RunService.Heartbeat:Connect(function(dt)
    local t=now()
    if t-lastSpawn>2.6 then lastSpawn=t;makeNpc() end
    if shieldUntil>0 and t>shieldUntil then clearShield() end
    if castleHealth<=0 then
        castleHealth=120
        notifyAll("城が破壊された！もう一度防衛チャレンジ")
    end
    for id,entry in pairs(living) do
        if not entry.model.Parent or entry.humanoid.Health<=0 then
            cleanNpc(id)
        else
            local diff=Vector3.new(0,3,0)-entry.pos
            if diff.Magnitude>9 then
                local step=math.min(diff.Magnitude,7.0*dt)
                entry.pos+=diff.Unit*step
                entry.model:PivotTo(CFrame.new(entry.pos))
            elseif t-entry.attackAt>=2.0 then
                entry.attackAt=t
                if shieldUntil>t and shieldHits>0 then
                    shieldHits-=1
                    if shieldHits==0 then clearShield() end
                else
                    castleHealth=math.max(0,castleHealth-7)
                end
            end
        end
    end
    for p,st in pairs(states) do
        if st.dragon and st.dragon.Parent then
            local root=core(p)
            if root then
                local moveTo=root.Position+Vector3.new(4,5,1)
                local cur=st.dragon:GetPivot().Position
                st.dragon:PivotTo(CFrame.new(cur:Lerp(moveTo,math.clamp(dt*4,0,1))))
            end
        end
    end
    if t-lastStatus>.6 then lastStatus=t;updateStatus() end
end)
