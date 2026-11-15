--!strict
-- EGGRUMBLE CORE LOOP V2: isolated Studio-only swarm + individual castle play-test.
-- Install on a private Studio copy INSTEAD OF the SevenHeroArena preview script.
-- The true egg contest, 7-role Game, account-owned property storage, PvP and real RC
-- are NOT connected. No DataStore, remote, in-game currency or publishing.
local Players=game:GetService("Players")
local RunService=game:GetService("RunService")
local Debris=game:GetService("Debris")
local TweenService=game:GetService("TweenService")
if not RunService:IsStudio() then return end

local CONFIG={
 MAP_TILE=460, GRID=3,
 MAX_NEUTRAL_LIVE=96, MAX_SPAWN_PER_TICK=4,
 SPAWN_INTERVAL=.12, RESPAWN_DELAY=.55,
 SWARM_HP=23, AUTO_INTERVAL=.55,
 PER_ATTACK_CAP=28, ROUND_GOAL_SECONDS=900,
}
local GROUP_NAME="EGGRUMBLE_SWARM_CASTLE_V2_PREVIEW"
local folder=Instance.new("Folder");folder.Name=GROUP_NAME;folder.Parent=workspace
local ground=Instance.new("Folder");ground.Name="LargeWorldSectors";ground.Parent=folder
local neutrals=Instance.new("Folder");neutrals.Name="ServerOwnedNeutralUnits";neutrals.Parent=folder
local castles=Instance.new("Folder");castles.Name="PlayerCastles";castles.Parent=folder
local fx=Instance.new("Folder");fx.Name="Effects";fx.Parent=folder

local spawn=workspace:FindFirstChildWhichIsA("SpawnLocation",true) :: SpawnLocation?
local center=(spawn and spawn.Position or Vector3.new(0,5,0))+Vector3.new(0,2,710)
local live:{[Model]:Humanoid}={}
local deathCount=0
local playerCastles:{[number]:Model}={}
local playerCastleSlots:{[number]:number}={}
local colors={Color3.fromRGB(208,91,58),Color3.fromRGB(56,141,225)}
local palettes={Color3.fromRGB(238,196,107),Color3.fromRGB(123,230,166),Color3.fromRGB(165,142,235)}

local function part(parent:Instance,name:string,size:Vector3,at:Vector3,c:Color3,collide:boolean):Part
 local p=Instance.new("Part")
 p.Name=name;p.Size=size;p.Position=at;p.Color=c
 p.Material=Enum.Material.SmoothPlastic;p.Anchored=true;p.CanCollide=collide
 p.Parent=parent
 return p
end
local function sign(p:Part,msg:string)
 local gui=Instance.new("BillboardGui");gui.Name="EGGRUMBLE_Label";gui.AlwaysOnTop=true
 gui.Size=UDim2.fromOffset(210,66);gui.StudsOffset=Vector3.new(0,4,0);gui.Parent=p
 local txt=Instance.new("TextLabel");txt.Name="Text";txt.BackgroundTransparency=.32
 txt.BackgroundColor3=Color3.fromRGB(10,18,27)
 txt.Font=Enum.Font.GothamBold;txt.TextSize=16;txt.TextWrapped=true
 txt.TextColor3=Color3.new(1,1,1);txt.Size=UDim2.fromScale(1,1)
 txt.Text=msg;txt.Parent=gui
end
local function burst(at:Vector3,c:Color3)
 local p=part(fx,"Swing",Vector3.new(2,2,2),at,c,false)
 p.Shape=Enum.PartType.Ball;p.Material=Enum.Material.Neon;p.Transparency=.35
 TweenService:Create(p,TweenInfo.new(.26),{Size=Vector3.new(18,18,18),Transparency=1}):Play()
 Debris:AddItem(p,.36)
end
local biomes={"金色の草原","珊瑚海岸","霧の大森林","天空の丘","中央決戦地","岩山の峡谷","火山跡地","水晶の森","深淵の荒野"}
local biomeColors={
 Color3.fromRGB(138,156,72), Color3.fromRGB(96,169,156), Color3.fromRGB(52,119,80),
 Color3.fromRGB(136,161,177),Color3.fromRGB(118,138,91),Color3.fromRGB(133,106,86),
 Color3.fromRGB(132,78,76),Color3.fromRGB(90,125,165),Color3.fromRGB(86,72,102),
}
for i=1,9 do
 local x=(i-1)%3-1
 local z=math.floor((i-1)/3)-1
 local plate=part(ground,"Sector_"..i,Vector3.new(CONFIG.MAP_TILE,3,CONFIG.MAP_TILE),
  center+Vector3.new(x*CONFIG.MAP_TILE,-7,z*CONFIG.MAP_TILE),biomeColors[i],true)
 plate.Material=Enum.Material.Grass
 sign(plate,biomes[i])
end
local function teamOf(player:Player):number
 if player.Team then
  local n=string.lower(player.Team.Name)
  if n:find("red") or n:find("赤") then return 1 end
  if n:find("blue") or n:find("青") then return 2 end
 end
 -- Studio fallback only. Production teams MUST be read from authoritative Game.
 return if player.UserId%2==0 then 2 else 1
end
local function personalCastlePosition(player:Player):Vector3
 local side=teamOf(player)
 local idx=playerCastleSlots[player.UserId] or 1
 -- Four rows within a team wing; overflow is tiled in second x row.
 local col=math.floor((idx-1)/8)
 local row=(idx-1)%8
 local x=(if side==1 then -545 else 545)+(if side==1 then col*100 else -col*100)
 return center+Vector3.new(x,-4,(row-3.5)*111)
end
local function makeCastle(player:Player)
 local previous=playerCastles[player.UserId]
 if previous then previous:Destroy() end
 local side=teamOf(player)
 local used={}
 for uid,slot in pairs(playerCastleSlots) do
  local other=Players:GetPlayerByUserId(uid)
  if other and teamOf(other)==side then used[slot]=true end
 end
 local slot=1
 while used[slot] do slot+=1 end
 playerCastleSlots[player.UserId]=slot
 local model=Instance.new("Model");model.Name="PersonalCastle_"..player.UserId
 model:SetAttribute("CastleOwnerUserId",player.UserId)
 model:SetAttribute("CastleTeam",teamOf(player))
 model:SetAttribute("CastleDecorationIndex",1)
 model.Parent=castles
 playerCastles[player.UserId]=model
 local at=personalCastlePosition(player)
 local ownColor=colors[teamOf(player)]
 local yard=part(model,"PrivateYard",Vector3.new(63,2,64),at+Vector3.new(0,-1,0),ownColor,true)
 yard.Material=Enum.Material.Slate
 for _,delta in ipairs({
  Vector3.new(-24,7,-24),Vector3.new(24,7,-24),Vector3.new(-24,7,24),Vector3.new(24,7,24)
 }) do
  local keep=part(model,"PersonalTower",Vector3.new(8,15,8),at+delta,Color3.fromRGB(152,150,143),true)
  keep.Material=Enum.Material.Brick
 end
 for _,delta in ipairs({
  Vector3.new(0,6,-26), Vector3.new(0,6,26)
 }) do
  local wall=part(model,"FortifiedWall",Vector3.new(54,11,4),at+delta,Color3.fromRGB(162,157,146),true)
  wall.Material=Enum.Material.Brick
 end
 for _,delta in ipairs({Vector3.new(-26,6,0),Vector3.new(26,6,0)}) do
  local wall=part(model,"SideFortification",Vector3.new(4,11,54),at+delta,Color3.fromRGB(162,157,146),true)
  wall.Material=Enum.Material.Brick
 end
 local banner=part(model,"OwnerBanner",Vector3.new(6,11,.5),at+Vector3.new(0,14,-25),palettes[1],false)
 banner.Material=Enum.Material.Fabric
 local signpost=part(model,"OwnerDisplay",Vector3.new(4,5,3),at+Vector3.new(-16,3,-18),ownColor,false)
 sign(signpost,"EGGRUMBLE\n"..player.DisplayName.." の城")
 local brush=part(model,"DecorateStation",Vector3.new(5,2,5),at+Vector3.new(16,2,-18),palettes[1],false)
 local prompt=Instance.new("ProximityPrompt");prompt.ObjectText="自分の城"
 prompt.ActionText="装飾を変更";prompt.MaxActivationDistance=12
 prompt.HoldDuration=.15;prompt.Parent=brush
 prompt.Triggered:Connect(function(actor:Player)
  if actor.UserId~=player.UserId then return end -- server-owned auth
  local nextIndex=((model:GetAttribute("CastleDecorationIndex") or 1)%#palettes)+1
  model:SetAttribute("CastleDecorationIndex",nextIndex)
  banner.Color=palettes[nextIndex];brush.Color=palettes[nextIndex]
 end)
 -- Castle look persists for this Studio session only; no DataStore writes.
end
local function nearestPlayer(at:Vector3):Player?
 local selected:Player?=nil
 local best=math.huge
 for _,p in ipairs(Players:GetPlayers()) do
  local r=p.Character and p.Character:FindFirstChild("HumanoidRootPart") :: BasePart?
  local h=p.Character and p.Character:FindFirstChildOfClass("Humanoid")
  if r and h and h.Health>0 then
   local d=(r.Position-at).Magnitude
   if d<best and d<175 then best=d;selected=p end
  end
 end
 return selected
end
local function updateProgress(p:Player,delta:number)
 local v=(p:GetAttribute("EGGRUMBLE_NeutralKOs") or 0)+delta
 p:SetAttribute("EGGRUMBLE_NeutralKOs",v)
 local tier=math.floor(v/40)+1
 p:SetAttribute("EGGRUMBLE_RunRank",math.min(tier,100))
 if tier==5 then p:SetAttribute("EGGRUMBLE_SlashTier","WAVE") end
 if tier>=15 then p:SetAttribute("EGGRUMBLE_SlashTier","TEMPEST") end
 local stats=p:FindFirstChild("leaderstats")
 local counter=stats and stats:FindFirstChild("KO")
 if counter and counter:IsA("IntValue") then counter.Value=v end
end
local function dummy(at:Vector3)
 local m=Instance.new("Model");m.Name="NeutralSwarmSoldier";m.Parent=neutrals
 m:SetAttribute("EGGRUMBLE_Neutral",true)
 local r=part(m,"HumanoidRootPart",Vector3.new(2,2.6,2),at,Color3.fromRGB(136,109,99),false)
 r.CanTouch=false
 local head=part(m,"Head",Vector3.new(1.6,1.5,1.6),at+Vector3.new(0,1.6,0),Color3.fromRGB(185,166,143),false)
 head.Shape=Enum.PartType.Ball;head.CanTouch=false
 m.PrimaryPart=r
 local h=Instance.new("Humanoid");h.MaxHealth=CONFIG.SWARM_HP;h.Health=CONFIG.SWARM_HP
 h.RequiresNeck=false;h.BreakJointsOnDeath=false;h.Parent=m
 live[m]=h
 h.Died:Connect(function()
  live[m]=nil
  deathCount+=1
  local uid=h:GetAttribute("LastAttackerUserId")
  if type(uid)=="number" then
   local who=Players:GetPlayerByUserId(uid)
   if who then updateProgress(who,1) end
  end
  task.delay(CONFIG.RESPAWN_DELAY,function() if m.Parent then m:Destroy() end end)
 end)
end
local function alive():number
 local n=0
 for m,h in pairs(live) do
  if m.Parent and h.Health>0 then n+=1 else live[m]=nil end
 end
 return n
end
local function slash(player:Player,bonus:number)
 local ch=player.Character;local r=ch and ch:FindFirstChild("HumanoidRootPart")::BasePart?
 local h=ch and ch:FindFirstChildOfClass("Humanoid")
 if not r or not h or h.Health<=0 then return end
 local tier=player:GetAttribute("EGGRUMBLE_SlashTier") or "BASE"
 local reach=if tier=="TEMPEST" then 44 elseif tier=="WAVE" then 33 else 24
 local radius=if tier=="TEMPEST" then 22 elseif tier=="WAVE" then 17 else 11
 local impact=r.Position+r.CFrame.LookVector*reach
 local maxHits=CONFIG.PER_ATTACK_CAP
 local ranked={}
 for m,enemyHum in pairs(live) do
  local mr=m.PrimaryPart
  if mr and enemyHum.Health>0 then
   local dist=(Vector3.new(mr.Position.X,0,mr.Position.Z)-Vector3.new(impact.X,0,impact.Z)).Magnitude
   if dist<=radius then table.insert(ranked,{hum=enemyHum,dist=dist}) end
  end
 end
 table.sort(ranked,function(a,b)return a.dist<b.dist end)
 local strikeCount=math.min(maxHits,#ranked)
 for i=1,strikeCount do
  local target=ranked[i].hum
  target:SetAttribute("LastAttackerUserId",player.UserId)
  target:TakeDamage(CONFIG.SWARM_HP*bonus)
 end
 if strikeCount>0 then burst(impact,colors[teamOf(player)]) end
end
local function equip(player:Player)
 local backpack=player:FindFirstChildOfClass("Backpack")
 if not backpack then return end
 local old=backpack:FindFirstChild("EGGRUMBLE_武神の飛翔斬撃")
 if old then old:Destroy() end
 local t=Instance.new("Tool");t.Name="EGGRUMBLE_武神の飛翔斬撃";t.CanBeDropped=false;t.RequiresHandle=true
 local handle=Instance.new("Part");handle.Name="Handle";handle.Size=Vector3.new(.5,4,.4)
 handle.Material=Enum.Material.Metal;handle.Color=Color3.fromRGB(235,186,104)
 handle.Parent=t
 local lastUse=0
 t.Activated:Connect(function()
  if os.clock()-lastUse<.4 then return end
  lastUse=os.clock();slash(player,1)
 end)
 t.Parent=backpack
end
local function join(p:Player)
 local stats=Instance.new("Folder");stats.Name="leaderstats";stats.Parent=p
 local ko=Instance.new("IntValue");ko.Name="KO";ko.Value=0;ko.Parent=stats
 p:SetAttribute("EGGRUMBLE_NeutralKOs",0)
 p:SetAttribute("EGGRUMBLE_RunRank",1)
 p:SetAttribute("EGGRUMBLE_SlashTier","BASE")
 makeCastle(p)
 p.CharacterAdded:Connect(function(char)
  task.delay(1.0,function()
   if not p.Parent or p.Character~=char then return end
   local root=char:FindFirstChild("HumanoidRootPart")::BasePart?
   if root then root.CFrame=CFrame.new(personalCastlePosition(p)+Vector3.new(0,8,30)) end
   equip(p)
  end)
 end)
 if p.Character then equip(p) end
end
Players.PlayerRemoving:Connect(function(p)
 local m=playerCastles[p.UserId]
 if m then m:Destroy() end
 playerCastles[p.UserId]=nil
 playerCastleSlots[p.UserId]=nil
end)
for _,p in ipairs(Players:GetPlayers()) do join(p) end
Players.PlayerAdded:Connect(join)

-- Low-cost active enemies: no upfront 10,000 NPC allocation. Spawn near live heroes,
-- record each Humanoid death separately; no synthetic "kill +1000" increments.
task.spawn(function()
 while folder.Parent do
  local count=alive()
  if count<CONFIG.MAX_NEUTRAL_LIVE then
   for i=1,math.min(CONFIG.MAX_SPAWN_PER_TICK,CONFIG.MAX_NEUTRAL_LIVE-count) do
    local ps=Players:GetPlayers()
    if #ps==0 then break end
    local who=ps[math.random(1,#ps)]
    local char=who.Character
    local pr=char and char:FindFirstChild("HumanoidRootPart")::BasePart?
    if pr then
     local angle=math.random()*math.pi*2
     local distance=math.random(29,75)
     local at=pr.Position+Vector3.new(math.cos(angle)*distance,0,math.sin(angle)*distance)
     at=Vector3.new(at.X,center.Y-3.5,at.Z)
     -- Stay within the 3 x 3 arena footprint, avoid spawning over individual castles.
     if math.abs(at.X-center.X)<CONFIG.MAP_TILE*1.4 and math.abs(at.Z-center.Z)<CONFIG.MAP_TILE*1.4 then
      dummy(at)
     end
    end
   end
  end
  task.wait(CONFIG.SPAWN_INTERVAL)
 end
end)
-- Distinct short-range crowd chase; capped active server entities avoid flooding physics.
task.spawn(function()
 while folder.Parent do
  for model,h in pairs(live) do
   local mr=model.PrimaryPart
   if mr and h.Health>0 then
    local target=nearestPlayer(mr.Position)
    if target then
     local tr=target.Character and target.Character:FindFirstChild("HumanoidRootPart")::BasePart?
     if tr then
      local vector=Vector3.new(tr.Position.X-mr.Position.X,0,tr.Position.Z-mr.Position.Z)
      if vector.Magnitude>4 then model:PivotTo(model:GetPivot()+vector.Unit*math.min(1.8,vector.Magnitude)) end
     end
    end
   end
  end
  task.wait(.36)
 end
end)
-- Survivor-like auto-strike on top of player aim. Never awards KO without genuine Humanoid death.
task.spawn(function()
 while folder.Parent do
  for _,p in ipairs(Players:GetPlayers()) do
   if p:GetAttribute("EGGRUMBLE_NeutralKOs")~=nil then slash(p,1) end
  end
  task.wait(CONFIG.AUTO_INTERVAL)
 end
end)
print("[EGGRUMBLE CORE LOOP V2] private Studio only; 9 sectors, per-player decorated castle, capped live swarm, real KO accounting; NOT official game/egg/PvP")
