--!nocheck
-- P0D star-shard hunt: a child-visible, session-only six-fragment scavenger quest
-- on the ORIGINAL Starfall Path's 10 safe stepping stones.
-- No second Game, Remote, Store, damage, score, saved XP, purchases or teleport.
local RunService=game:GetService("RunService")
if not RunService:IsStudio() then return end
local ServerStorage=game:GetService("ServerStorage")
if ServerStorage:GetAttribute("P0D_RC_ENABLE_STAR_SHARDS_V1")~=true then return end
if ServerStorage:GetAttribute("P0D_RC_ENABLE_STARRY_PATH_V1")~=true then return end

local Workspace=game:GetService("Workspace")
local Players=game:GetService("Players")
-- WCS predecessor may take 45+45+12 seconds, then the Starfall server
-- may wait for the canyon/bridge. 25s silently disabled this quest on valid
-- slow Studio starts. The bounded 170s budget covers the composed path.
local stage=Workspace:WaitForChild("P0D_STARRY_PATH",170)
if not stage or not stage:IsA("Model") or stage:GetAttribute("FeatureId")~="STARRY_PATH_V1" then
    warn("[P0D/SHARDS] verified original star stage missing; no standalone map")
    return
end
if stage:FindFirstChild("P0D_StarShardHunt") then
    warn("[P0D/SHARDS] duplicate shard quest refused")
    return
end

-- BEGIN_P0D_STAR_SHARDS_POLICY
local TOTAL=6
local function awardShard(oldMap, id)
    if type(oldMap)~="table" then return false,0,false end
    local n=0
    for i=1,TOTAL do
        if oldMap[i]==true then n+=1 end
    end
    if type(id)~="number" or id~=math.floor(id) or id<1 or id>TOTAL or oldMap[id]==true then
        return false,n,n==TOTAL
    end
    oldMap[id]=true
    n+=1
    return true,n,n==TOTAL
end
-- END_P0D_STAR_SHARDS_POLICY

-- Verify ALL physical dependencies before creating any new scene objects.
-- StarStep_1 .. StarStep_10 are part of the original game feature.
local locations={1,3,5,6,8,10}
local stones={}
for shardId,step in ipairs(locations) do
    local p=stage:WaitForChild("StarStep_"..tostring(step),15)
    if not p or not p:IsA("BasePart") or p.Name~="StarStep_"..tostring(step) then
        warn("[P0D/SHARDS] missing original star stone "..tostring(step))
        return
    end
    stones[shardId]=p
end
local root=Instance.new("Folder")
root.Name="P0D_StarShardHunt"
root:SetAttribute("FeatureId","STAR_SHARDS_V1")
root:SetAttribute("TotalShards",TOTAL)
root:SetAttribute("SessionOnly",true)
root:SetAttribute("GameStoreScoreXPUnchanged",true)
root.Parent=stage

local playerClaimed={} -- [UserId] = {[shardId] = true}; no DataStore
local registered={}    -- exactly one CharacterAdded hook per Player
local orbs={}
local prompts={}

local function showBadge(player)
    local char=player.Character
    local hrp=char and char:FindFirstChild("HumanoidRootPart")
    if not hrp or not hrp:IsA("BasePart") then return end
    local gui=hrp:FindFirstChild("P0D_StarShardBadge")
    if not gui then
        gui=Instance.new("BillboardGui")
        gui.Name="P0D_StarShardBadge"
        gui.Adornee=hrp
        gui.Size=UDim2.fromOffset(170,38)
        gui.StudsOffsetWorldSpace=Vector3.new(0,4.7,0)
        gui.MaxDistance=80
        gui.AlwaysOnTop=true
        gui.Parent=hrp
        local label=Instance.new("TextLabel")
        label.Name="Progress"
        label.Size=UDim2.fromScale(1,1)
        label.BackgroundColor3=Color3.fromRGB(22,16,58)
        label.BackgroundTransparency=0.23
        label.TextColor3=Color3.fromRGB(255,243,156)
        label.TextScaled=true
        label.Font=Enum.Font.GothamBold
        label.Parent=gui
    end
    local label=gui:FindFirstChild("Progress")
    if label and label:IsA("TextLabel") then
        local count=player:GetAttribute("P0D_StarShardCount") or 0
        local complete=player:GetAttribute("P0D_StarShardComplete")==true
        label.Text=complete and "星の探検家 ✦ 6/6" or ("星のかけら "..tostring(count).."/6")
    end
end

local function showReward(player)
    local char=player.Character
    local hrp=char and char:FindFirstChild("HumanoidRootPart")
    if not hrp or not hrp:IsA("BasePart") then return end
    if hrp:FindFirstChild("P0DStarShardsAura") then return end
    local emitter=Instance.new("ParticleEmitter")
    emitter.Name="P0DStarShardsAura"
    emitter.Texture="rbxasset://textures/particles/sparkles_main.dds"
    emitter.Color=ColorSequence.new(Color3.fromRGB(255,220,110),Color3.fromRGB(155,197,255))
    emitter.LightEmission=1
    emitter.Rate=4
    emitter.Lifetime=NumberRange.new(0.5,1.4)
    emitter.Speed=NumberRange.new(0.5,2)
    emitter.SpreadAngle=Vector2.new(85,85)
    emitter.Parent=hrp
    -- Temporary purely visual award. No paid item, buff, persistent state.
    task.delay(30,function()
        if emitter.Parent then emitter:Destroy() end
    end)
end

local function setupPlayer(player)
    if registered[player] then return end
    registered[player]=true
    playerClaimed[player.UserId]={}
    player:SetAttribute("P0D_StarShardCount",0)
    player:SetAttribute("P0D_StarShardComplete",false)
    player.CharacterAdded:Connect(function(char)
        task.defer(function()
            local hrp=char:WaitForChild("HumanoidRootPart",12)
            if not hrp or player.Parent~=Players or player.Character~=char then return end
            showBadge(player)
            if player:GetAttribute("P0D_StarShardComplete")==true then
                showReward(player)
            end
        end)
    end)
    if player.Character then
        task.defer(function() showBadge(player) end)
    end
end
Players.PlayerAdded:Connect(setupPlayer)
Players.PlayerRemoving:Connect(function(player)
    playerClaimed[player.UserId]=nil
    registered[player]=nil
end)
for _,player in ipairs(Players:GetPlayers()) do setupPlayer(player) end

local palette={
    Color3.fromRGB(255,226,114),
    Color3.fromRGB(133,237,255),
    Color3.fromRGB(231,167,255),
    Color3.fromRGB(144,255,180),
    Color3.fromRGB(255,156,160),
    Color3.fromRGB(255,255,224)
}
for shardId,stone in ipairs(stones) do
    local orb=Instance.new("Part")
    orb.Name="StarShard_"..tostring(shardId)
    orb.Shape=Enum.PartType.Ball
    orb.Size=Vector3.new(1.7,1.7,1.7)
    orb.CFrame=stone.CFrame*CFrame.new(0,2.2,0)
    orb.Anchored=true
    orb.CanCollide=false
    orb.CanTouch=false
    orb.CanQuery=false
    orb.Material=Enum.Material.Neon
    orb.Color=palette[shardId]
    orb.Transparency=1
    orb.Parent=root
    orbs[shardId]=orb

    local prompt=Instance.new("ProximityPrompt")
    prompt.Name="CollectStarShard"
    prompt.ActionText="かけらを拾う"
    prompt.ObjectText="星のかけら "..tostring(shardId).."/6"
    prompt.HoldDuration=0.25
    prompt.MaxActivationDistance=7
    prompt.RequiresLineOfSight=false
    prompt.Enabled=false
    prompt.Parent=orb
    prompts[shardId]=prompt

    prompt.Triggered:Connect(function(player)
        if not player or player.Parent~=Players or stage:GetAttribute("PathOpen")~=true then return end
        if not stone.CanCollide then return end
        local char=player.Character
        local hrp=char and char:FindFirstChild("HumanoidRootPart")
        local humanoid=char and char:FindFirstChildOfClass("Humanoid")
        if not hrp or not humanoid or humanoid.Health<=0 then return end
        if (hrp.Position-orb.Position).Magnitude>9 then return end
        if not playerClaimed[player.UserId] then return end
        local accepted,count,complete=awardShard(playerClaimed[player.UserId],shardId)
        if not accepted then return end
        player:SetAttribute("P0D_StarShardCount",count)
        if complete then player:SetAttribute("P0D_StarShardComplete",true) end
        showBadge(player)
        if complete then showReward(player) end
    end)
end

local function updateVisibility()
    local active=stage:GetAttribute("PathOpen")==true
    for i=1,TOTAL do
        prompts[i].Enabled=active
        orbs[i].Transparency=active and 0.08 or 1
    end
    root:SetAttribute("PathActive",active)
end
stage:GetAttributeChangedSignal("PathOpen"):Connect(updateVisibility)
updateVisibility()
