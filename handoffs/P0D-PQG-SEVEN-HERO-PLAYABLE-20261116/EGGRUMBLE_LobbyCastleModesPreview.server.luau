--!strict
-- EGGRUMBLE V3 private Studio-only: two queue gates, AI fill, multi-egg, castle-elimination match.
-- Requires a sibling ModuleScript named EGGRUMBLE_CastleMatchRules, containing that file's source.
-- Play ALONE in a separate private Place; no production Game/Store/Remote/paid products.
local Players=game:GetService("Players")
local RunService=game:GetService("RunService")
local Debris=game:GetService("Debris")
if not RunService:IsStudio() then return end
local Rules=require(script.Parent:WaitForChild("EGGRUMBLE_CastleMatchRules"))
local BotActors=require(script.Parent:WaitForChild("EGGRUMBLE_BotActors"))
local SwarmCombat=require(script.Parent:WaitForChild("EGGRUMBLE_SwarmCombat"))
local InteractionGuard=require(script.Parent:WaitForChild("EGGRUMBLE_InteractionGuard"))
local ResultService=require(script.Parent:WaitForChild("EGGRUMBLE_MatchResultService"))
local RoundReplay=require(script.Parent:WaitForChild("EGGRUMBLE_RoundReplay"))
local SevenRoleCombat=require(script.Parent:WaitForChild("EGGRUMBLE_SevenRoleCombat"))
-- Existing ITEM author remains the one and only effect/collection implementation.
local FieldItems=require(script.Parent:WaitForChild("EGGRUMBLE_FieldItemPickups"))
local RaidItemIntake=require(script.Parent:WaitForChild("EGGRUMBLE_RaidItemIntake"))
local NeutralStoneGiant=require(script.Parent:WaitForChild("EGGRUMBLE_NeutralStoneGiant"))
local BossSessionFence=require(script.Parent:WaitForChild("EGGRUMBLE_BossSessionFence"))
local spawn=workspace:FindFirstChildWhichIsA("SpawnLocation",true)::SpawnLocation?
local root=spawn and spawn.Position or Vector3.new(0,4,0)
local folder=Instance.new("Folder");folder.Name="EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW";folder.Parent=workspace
local queues:{[string]:{Player}}={TEAM={},BATTLE_ROYALE={}}
local sessions:{[string]:any}={}
local joined:{[number]:string}={}
local chosenDefense:{[number]:string}={}
local chosenRole:{[number]:string}={}
local queueEpoch:{[string]:number}={TEAM=0,BATTLE_ROYALE=0}
local MODE_SEATS=16 -- humans + AI combined; change only after measured server/client QA
local COUNTDOWN=12 -- seconds for private preview only

local function block(parent:Instance,name:string,pos:Vector3,size:Vector3,color:Color3):Part
 local p=Instance.new("Part");p.Name=name;p.Size=size;p.Position=pos;p.Anchored=true
 p.Color=color;p.Material=Enum.Material.SmoothPlastic;p.Parent=parent
 return p
end
local function board(at:BasePart,label:string)
 local b=Instance.new("BillboardGui");b.Size=UDim2.fromOffset(230,82);b.StudsOffset=Vector3.new(0,4.5,0)
 b.AlwaysOnTop=true;b.Parent=at
 local t=Instance.new("TextLabel");t.Size=UDim2.fromScale(1,1);t.TextScaled=true;t.TextWrapped=true
 t.BackgroundColor3=Color3.fromRGB(24,27,43);t.BackgroundTransparency=.12
 t.TextColor3=Color3.new(1,1,1);t.Font=Enum.Font.GothamBold;t.Text=label;t.Parent=b
end
local function prompt(at:BasePart,action:string,subject:string,callback:(Player)->())
 local p=Instance.new("ProximityPrompt");p.ActionText=action;p.ObjectText=subject
 p.HoldDuration=.2;p.MaxActivationDistance=14;p.RequiresLineOfSight=false;p.Parent=at
 p.Triggered:Connect(function(actor:Player)
  -- All client-originated prompt interactions are server checked, including castle HP damage.
  if InteractionGuard.allow(actor,at,action,at.Name) then callback(actor) end
 end)
end
local function getCastlePoint(mode:string,index:number):Vector3
 if mode=="TEAM" then
  -- Strict RED west / BLUE east castle districts. Human roster alternates team colors.
  local isRed=index%2==1
  local localIndex=math.floor((index-1)/2)
  local col=localIndex%2;local row=math.floor(localIndex/2)
  local x=if isRed then -885+col*124 else -475+col*124
  return root+Vector3.new(x,2,260+row*146)
 end
 local base=root+Vector3.new(620,2,0)
 local col=(index-1)%4;local row=math.floor((index-1)/4)
 return base+Vector3.new((col-1.5)*122,0,280+row*112)
end
local function createWorldCastle(session:any,entry:any,index:number)
 local model=Instance.new("Model");model.Name="Castle_"..entry.id;model.Parent=session.world
 local at=getCastlePoint(session.mode,index)
 session.castleLocations[entry.id]=at
 local side=if session.mode=="TEAM" then entry.team else (if index%2==1 then "RED" else "BLUE")
 local tint=if side=="RED" then Color3.fromRGB(207,92,86) else Color3.fromRGB(87,146,218)
 local ground=block(model,"StandardFoundation",at+Vector3.new(0,-2,0),Vector3.new(72,3,72),tint)
 -- Hollow, traversable standard castle shell: every owner gets the same entrance and geometry.
 local core=block(model,"StandardCore",at+Vector3.new(0,14,0),Vector3.new(30,2,27),Color3.fromRGB(172,166,147))
 core.Material=Enum.Material.Brick
 local left=block(model,"CastleSideLeft",at+Vector3.new(-15,6,0),Vector3.new(2,12,26),Color3.fromRGB(160,154,145))
 local right=block(model,"CastleSideRight",at+Vector3.new(15,6,0),Vector3.new(2,12,26),Color3.fromRGB(160,154,145))
 local back=block(model,"CastleBackWall",at+Vector3.new(0,6,13),Vector3.new(30,12,2),Color3.fromRGB(160,154,145))
 local frontL=block(model,"CastleFrontLeft",at+Vector3.new(-10,6,-13),Vector3.new(10,12,2),Color3.fromRGB(160,154,145))
 local frontR=block(model,"CastleFrontRight",at+Vector3.new(10,6,-13),Vector3.new(10,12,2),Color3.fromRGB(160,154,145))
 local door=block(model,"SiegeGate",at+Vector3.new(0,4,-13),Vector3.new(9,8,1.3),Color3.fromRGB(96,69,56))
 door.Transparency=.45;door.CanCollide=false -- open gate permits both human and bot approach
 for _,dx in ipairs({-26,26}) do
  for _,dz in ipairs({-26,26}) do
   block(model,"Tower",at+Vector3.new(dx,9,dz),Vector3.new(9,18,9),Color3.fromRGB(137,137,142))
  end
 end
 local banner=block(model,"OwnerFlag",at+Vector3.new(0,18,0),Vector3.new(6,9,.8),Color3.fromRGB(228,190,110))
 board(core,(entry.isAI and "AI " or "")..entry.id.." の城\n卵×3 / HP1000")
 session.castleModels[entry.id]={model=model,core=core,banner=banner,door=door}
 prompt(door,"攻城攻撃","敵城を攻める",function(p)
  if joined[p.UserId]~=session.mode or not session.rules then return end
  local state=session.rules
  if state.phase~="ACTIVE" then return end
  local from=tostring(p.UserId)
  local src=state.castles[from]
  if not src or not src.alive then return end
  local ok,res=pcall(function() return Rules.damageCastle(state,entry.id,from,120) end)
  if not ok then return end
  session.refresh()
  if res.fallen then session.releaseEggs(entry.id,at,res.releasedEggIds) end
 end)
 local deco=block(model,"DecorStation",at+Vector3.new(18,2,-18),Vector3.new(5,4,4),Color3.fromRGB(214,158,97))
 prompt(deco,"旗の装飾変更","自分の城",function(p)
  if not session.rules or tostring(p.UserId)~=entry.id then return end
  local current=session.rules.castles[entry.id].decoration
  local nextColor=if current=="STONE" then "GOLD" elseif current=="GOLD" then "CYAN" else "STONE"
  if pcall(function() Rules.decorate(session.rules,entry.id,tostring(p.UserId),nextColor) end) then
   banner.Color=if nextColor=="GOLD" then Color3.fromRGB(240,199,70) elseif nextColor=="CYAN" then Color3.fromRGB(73,210,230) else Color3.fromRGB(180,180,180)
  end
 end)
 local deposit=block(model,"OwnEggDeposit",at+Vector3.new(-16,2,-18),Vector3.new(5,3,4),Color3.fromRGB(229,213,125))
 prompt(deposit,"卵を納入","自分の城",function(p)
  if tostring(p.UserId)~=entry.id or not session.rules then return end
  local c=session.rules.castles[entry.id]
  if c.alive and c.heldEggs>0 then pcall(function() Rules.depositEggs(session.rules,entry.id,c.heldEggs) end) end
 end)
 local vault=block(model,"EggVault",at+Vector3.new(0,3,6),Vector3.new(6,5,6),Color3.fromRGB(218,181,75))
 board(vault,"卵倉庫")
 prompt(vault,"敵の卵を奪取","卵3個から1個ずつ",function(p)
  if not session.rules or joined[p.UserId]~=session.mode then return end
  pcall(function() Rules.takeEggs(session.rules,tostring(p.UserId),1,entry.id) end)
  session.refresh()
 end)
end

local function startSession(mode:string)
 local state=sessions[mode]
 if state then return end
 local queue=queues[mode];if #queue==0 then return end
 local humans={}
 for _,p in ipairs(queue) do
  if p.Parent and joined[p.UserId]==mode then table.insert(humans,tostring(p.UserId)) end
 end
 if #humans==0 then return end
 local roster=Rules.makeRoster(mode,humans,MODE_SEATS)
 local session={
  mode=mode,roster=roster,rules=Rules.new(mode,roster,24),
  castleLocations={},castleModels={},world=Instance.new("Folder"),groundY=root.Y-3,
  lifeConnections={},walkBaseline={},
 }
 session.world.Name=mode.."_Arena";session.world.Parent=folder
 local worldX=mode=="TEAM" and -620 or 620
 local floor=block(session.world,"TacticalBattlefield",root+Vector3.new(worldX,-4,465),Vector3.new(890,2,1050),Color3.fromRGB(96,126,83))
 floor.Material=Enum.Material.Grass
 -- Moveable routes between personal fortresses; demo geometry only, not a finished detailed terrain.
 for j=1,3 do
  -- Three west-east infiltration corridors: northern ridge, river ford and forest flank.
  local lane=block(session.world,"TacticalRoute_"..j,root+Vector3.new(worldX,-2.75,295+(j-1)*170),
   Vector3.new(835,.7,23),Color3.fromRGB(152,133,99))
  lane.Material=Enum.Material.Ground
 end
 if mode=="TEAM" then
  local ridge=block(session.world,"CentralRidge",root+Vector3.new(-620,15,475),
   Vector3.new(54,34,190),Color3.fromRGB(105,103,93))
  ridge.Material=Enum.Material.Slate
  local valley=block(session.world,"ValleyOverlook",root+Vector3.new(-610,5,695),
   Vector3.new(85,11,30),Color3.fromRGB(118,130,94))
  valley.Material=Enum.Material.Rock
  for n=1,7 do
   local x=-800+(n%4)*38
   local z=470+math.floor(n/4)*110
   local tree=block(session.world,"ForestAmbushCover_"..n,root+Vector3.new(x,11,z),
    Vector3.new(7,24,7),Color3.fromRGB(66,104,65))
   tree.Material=Enum.Material.Grass
  end
 end
 sessions[mode]=session
 -- Clean up only this finished match; queues and matches for the other mode survive.
 session.closeRound=function(abandoned:boolean?)
  if sessions[mode]~=session or (not abandoned and session.rules.phase~="FINISHED") then return end
  if abandoned then session.rules.phase="ABANDONED" end
  for _,connection in ipairs(session.lifeConnections) do connection:Disconnect() end
  for _,entry in ipairs(session.roster) do
   if not entry.isAI then
    local player=Players:GetPlayerByUserId(tonumber(entry.id) or -1)
    if player and joined[player.UserId]==mode then
     joined[player.UserId]=nil
     SevenRoleCombat.clear(player)
     InteractionGuard.clear(player) -- avoid prompt cooldown state leaking across rounds
     RoundReplay.resetHuman(player,root+Vector3.new(0,8,-5),session.walkBaseline[tostring(player.UserId)])
    end
   end
  end
  if session.world.Parent then session.world:Destroy() end
  sessions[mode]=nil
  queues[mode]={}
  queueEpoch[mode]+=1
 end
 for _,entry in ipairs(roster) do
  if not entry.isAI then
   local p=Players:GetPlayerByUserId(tonumber(entry.id) or -1)
   if p then
    local module=chosenDefense[p.UserId] or "SENSOR"
    Rules.loadDefense(session.rules,entry.id,{module})
   end
  else Rules.loadDefense(session.rules,entry.id,{"SENSOR"}) end
 end
 session.releaseEggs=function(ownerId:string,at:Vector3,eggIds:{string})
  for i,eggId in ipairs(eggIds) do
   local egg=block(session.world,"ReleasedEgg_"..eggId,at+Vector3.new((i-2)*3,4,-17),Vector3.new(2,3,2),Color3.fromRGB(245,219,94))
   egg.Shape=Enum.PartType.Ball
   prompt(egg,"拾う","解放された卵",function(p)
    if joined[p.UserId]~=mode or egg.Parent==nil then return end
    if pcall(function() Rules.takeFieldEgg(session.rules,tostring(p.UserId),eggId) end) then egg:Destroy() end
   end)
  end
 end

 -- A defeated carrier drops physical eggs; never leave an invisible stock increase.
 -- The Rules module owns the count mutation and is idempotent after the first drop.
 session.dropCarrierEggs=function(ownerId:string,at:Vector3):number
  if session.rules.phase~="ACTIVE" then return 0 end
  local carrier=session.rules.castles[ownerId]
  if not carrier or not carrier.alive or carrier.heldEggs<=0 then return 0 end
  local dropped,dropIds=Rules.onCarrierEliminated(session.rules,ownerId)
  if dropped>0 then
   local landing=Vector3.new(at.X,session.groundY or at.Y,at.Z+17)
   session.releaseEggs(ownerId,landing,dropIds)
   session.refresh()
  end
  return dropped
 end
 session.refresh=function()
  for id,bits in pairs(session.castleModels) do
   local c=session.rules.castles[id]
   if c then
    bits.core.Color=if c.alive then Color3.fromRGB(172,166,147) else Color3.fromRGB(59,54,55)
    local gui=bits.core:FindFirstChildOfClass("BillboardGui")
    local t=gui and gui:FindFirstChildOfClass("TextLabel")
    if t then t.Text=(c.isAI and "AI " or "")..id.."\nHP"..math.floor(c.hp).." / 卵"..c.vaultEggs end
   end
  end
  for _,player in ipairs(queue) do
   if player.Parent and joined[player.UserId]==mode then
    local c=session.rules.castles[tostring(player.UserId)]
    if c and not c.alive and player:GetAttribute("EGGRUMBLE_Eliminated")~=true then
     player:SetAttribute("EGGRUMBLE_Eliminated",true)
     local ch=player.Character
     local rootPart=ch and ch:FindFirstChild("HumanoidRootPart")::BasePart?
     if rootPart then rootPart.CFrame=CFrame.new(root+Vector3.new(0,12,-35)) end
     SevenRoleCombat.clear(player)
    end
   end
  end
  if session.rules.winner~=nil then
   -- Short factual result shown exactly once, never a permanent play-blocking HUD.
   ResultService.showIfFinished(session,queue,mode)
   RoundReplay.schedule(session,session.closeRound)
   print("[EGGRUMBLE "..mode.."] Castle elimination winner:",session.rules.winner)
  end
 end
 for idx,entry in ipairs(roster) do createWorldCastle(session,entry,idx) end
 -- Field eggs available in both modes, not single/multi mode toggles.
 for i=1,24 do
  local col=(i-1)%8;local row=math.floor((i-1)/8)
  local worldX=mode=="TEAM" and -620 or 620
  local at=root+Vector3.new(worldX+(col-3.5)*93,3,290+row*200)
  local eggId="FIELD_"..i
  local egg=block(session.world,"FieldEgg_"..i,at,Vector3.new(2.6,3.3,2.6),Color3.fromRGB(238,214,108))
  egg.Shape=Enum.PartType.Ball
  prompt(egg,"卵を拾う","フィールドの卵",function(p)
   if joined[p.UserId]~=mode or egg.Parent==nil then return end
   if pcall(function() Rules.takeFieldEgg(session.rules,tostring(p.UserId),eggId) end) then egg:Destroy() end
  end)
 end
 Rules.start(session.rules)
 -- Connect existing HEAL/DASH/SHIELD world pickups to *both* actual match modes,
 -- without spawning separate item preview worlds or inventing a second inventory.
 local itemsOK,itemCountOrError=pcall(function()
  return RaidItemIntake.start(session,root,FieldItems)
 end)
 if itemsOK then
  session.fieldItemCount=itemCountOrError
  session.itemIntakeStatus="READY"
 else
  session.fieldItemCount=0
  session.itemIntakeStatus="YELLOW_ITEM_OPTIONAL"
  warn("[EGGRUMBLE ITEM INTAKE] optional field-item failure; core egg/castle match continues:",itemCountOrError)
 end
 -- ORIGINAL author StoneGiant per real session; never cross-hit the other mode.
 -- Optional source fail = YELLOW; castle/eggs and neutral horde are still playable.
 local bossX=if mode=="TEAM" then -620 else 620
 local bossOK,bossOrError=pcall(function()
  return NeutralStoneGiant.spawn(session.world,
   root+Vector3.new(bossX+100,-3,590),{
    isMatchActive=function()
     return BossSessionFence.active(mode,session,sessions)
    end,
    canEngage=function(player:Player)
     return BossSessionFence.mayEngage(mode,session,sessions,joined,
      player.UserId,player:GetAttribute("EGGRUMBLE_Eliminated")==true)
    end,
    onDefeat=function(player:Player)
     -- Dedicated boss credit, NOT falsely counted as regular Humanoid.Died KO.
     session.bossDefeats=(session.bossDefeats or 0)+1
     local total=player:GetAttribute("EGGRUMBLE_BossDefeats") or 0
     player:SetAttribute("EGGRUMBLE_BossDefeats",total+1)
    end,
   })
 end)
 if bossOK then
  session.boss=bossOrError
  session.bossStatus="READY"
 else
  local orphan=session.world:FindFirstChild("NEUTRAL_BOSS_STONE_GIANT")
  if orphan then orphan:Destroy() end
  session.bossStatus="YELLOW_BOSS_OPTIONAL"
  warn("[EGGRUMBLE BOSS] optional boss source failed; core match continues:",bossOrError)
 end
 for _,p in ipairs(queue) do
  if p.Parent and joined[p.UserId]==mode then
   -- Persist only for this one server-owned session; never trust client attributes.
   session.walkBaseline[tostring(p.UserId)]=RoundReplay.captureWalkBaseline(p)
   local ch=p.Character;local rootPart=ch and ch:FindFirstChild("HumanoidRootPart")::BasePart?
   local idx=table.find(humans,tostring(p.UserId))
   if rootPart and idx then rootPart.CFrame=CFrame.new(getCastlePoint(mode,idx)+Vector3.new(0,7,-45)) end
  end
 end
 -- Drop carried eggs on every human death, including post-respawn deaths.
 -- CharacterAdded reconnects only for this one preview session; no new Remote/Game.
 for _,player in ipairs(queue) do
  if player.Parent and joined[player.UserId]==mode then
   local function bindCarrierLife(character:Model)
    local humanoid=character:FindFirstChildOfClass("Humanoid") or character:WaitForChild("Humanoid",5)
    if humanoid and humanoid:IsA("Humanoid") then
     table.insert(session.lifeConnections,humanoid.Died:Connect(function()
      if joined[player.UserId]~=mode then return end
      local rootPart=character:FindFirstChild("HumanoidRootPart")::BasePart?
      local fallback=session.castleLocations[tostring(player.UserId)] or root
      session.dropCarrierEggs(tostring(player.UserId),rootPart and rootPart.Position or fallback)
     end))
    end
   end
   table.insert(session.lifeConnections,player.CharacterAdded:Connect(bindCarrierLife))
   if player.Character then task.spawn(bindCarrierLife,player.Character) end
  end
 end
 -- Actual anchored 3D bot actors roam between castles and must reach their goal
 -- before stealing/depositing eggs or damaging the castle. No remote numerical sieges.
 BotActors.start(session,Rules)
 SwarmCombat.start(session)
 -- All seven roles now use the SAME neutral, AI-duel, castle/egg V3 session.
 -- Select role in the lobby; default 武神 if the human enters a portal immediately.
 for _,p in ipairs(queue) do
  if p.Parent and joined[p.UserId]==mode then
   local role=chosenRole[p.UserId] or "WARRIOR"
   SevenRoleCombat.equip(session,p,role)
   table.insert(session.lifeConnections,p.CharacterAdded:Connect(function(character)
    task.delay(.8,function()
     if p.Parent and joined[p.UserId]==mode and p.Character==character
      and sessions[mode]==session and session.rules.phase=="ACTIVE" then
      local id=tostring(p.UserId)
      local castle=session.rules.castles[id]
      local home=session.castleLocations[id]
      if castle and castle.alive and home then
       -- Wait for a physical live Avatar before entering the same castle match.
       -- The helper rejects stale characters, dead Humanoids and destroyed castles.
       local rootPart=character:FindFirstChild("HumanoidRootPart")
        or character:WaitForChild("HumanoidRootPart",5)
       if rootPart and RoundReplay.returnToActiveCastle(session,p,character,home+Vector3.new(0,7,-45)) then
        SevenRoleCombat.equip(session,p,role)
       end
      end
     end
    end)
   end))
  end
 end

end

local function joinQueue(mode:string,p:Player)
 if sessions[mode] then return end
 local previous=joined[p.UserId]
 if previous then
  -- Joining the same gate cancels; choosing the other switches mode while waiting.
  -- Never remove a player from a live match.
  if sessions[previous] then return end
  if not RoundReplay.leaveWaitingQueue(previous,p,queues,joined,queueEpoch,sessions) then return end
  p:SetAttribute("EGGRUMBLE_QueuedMode",nil)
  if previous==mode then return end
 end
 joined[p.UserId]=mode
 table.insert(queues[mode],p)
 p:SetAttribute("EGGRUMBLE_QueuedMode",mode)
 if #queues[mode]==1 then
  local expectedEpoch=queueEpoch[mode]
  task.delay(COUNTDOWN,function()
   if RoundReplay.canStartCountdown(mode,expectedEpoch,queues,queueEpoch,sessions) then
    startSession(mode)
   end
  end)
 end
 if #queues[mode]>=MODE_SEATS then startSession(mode) end
end
-- Seven job-selection stands: small world prompts, no permanent large HUD.
for i,role in ipairs(SevenRoleCombat.roleOrder()) do
 local data=SevenRoleCombat.info(role)
 local stand=block(folder,"ROLE_"..role,root+Vector3.new((i-4)*9,1,69),Vector3.new(5,4,5),data.color)
 board(stand,data.name.."\n"..data.weapon)
 prompt(stand,"職業選択",data.name,function(p)
  if joined[p.UserId] and sessions[joined[p.UserId]] then return end
  chosenRole[p.UserId]=role
  p:SetAttribute("EGGRUMBLE_SelectedRole",role)
 end)
end
local gateTeam=block(folder,"TEAM_PORTAL",root+Vector3.new(-12,6,28),Vector3.new(9,12,2),Color3.fromRGB(206,74,67))
local gateBR=block(folder,"BATTLE_ROYALE_PORTAL",root+Vector3.new(12,6,28),Vector3.new(9,12,2),Color3.fromRGB(79,132,230))
board(gateTeam,"EGGRUMBLE\nチーム戦｜全味方城陥落で敗北")
board(gateBR,"EGGRUMBLE\nバトルロワイヤル｜最後の城が勝者")
prompt(gateTeam,"参加する","チーム戦（再操作で解除）",function(p) joinQueue("TEAM",p) end)
prompt(gateBR,"参加する","BR戦（再操作で解除）",function(p) joinQueue("BATTLE_ROYALE",p) end)
for i,name in ipairs({"HARDENED","REPAIR","TURRET","TRAP","SENSOR"}) do
 local stand=block(folder,"DEFENSE_"..name,root+Vector3.new((i-3)*9,1,47),Vector3.new(5,3,5),Color3.fromRGB(149,164,121))
 board(stand,name.."\n出撃前の防衛選択")
 prompt(stand,"装備する","全員同一防衛予算",function(p)
  if joined[p.UserId]==nil or sessions[joined[p.UserId]]==nil then
   chosenDefense[p.UserId]=name
   p:SetAttribute("EGGRUMBLE_DefenseLoadout",name)
  end
 end)
end
Players.PlayerRemoving:Connect(function(p)
 InteractionGuard.clear(p)
 local mode=joined[p.UserId]
 if mode and not sessions[mode] then
  -- Cancel countdown if the last queued human disconnects; the next entrant
  -- must receive a fresh full COUNTDOWN rather than inherit the stale timer.
  RoundReplay.leaveWaitingQueue(mode,p,queues,joined,queueEpoch,sessions)
 end
 joined[p.UserId]=nil
 chosenDefense[p.UserId]=nil
 chosenRole[p.UserId]=nil
 SevenRoleCombat.clear(p)
 if mode and sessions[mode] and sessions[mode].rules.phase=="ACTIVE" then
  local scene=sessions[mode]
  local ch=p.Character
  local rootPart=ch and ch:FindFirstChild("HumanoidRootPart")::BasePart?
  scene.dropCarrierEggs(tostring(p.UserId),rootPart and rootPart.Position or scene.castleLocations[tostring(p.UserId)] or root)
  -- If no human remains, retire the bot-only arena immediately instead of
  -- trapping the next player behind an occupied session forever.
  local abandoned=RoundReplay.abandonIfEmpty(scene,joined,function()
   scene.closeRound(true)
  end)
  -- Preserve an existing match by transferring a disconnected castle to AI.
  if not abandoned and scene.takeover then scene.takeover(tostring(p.UserId)) end
 end
end)
print("[EGGRUMBLE V3] Studio-only two mode gates; moving AI actors, shared horde and castle multi-egg combat; real platform matchmaking/production AI UNIMPLEMENTED")
