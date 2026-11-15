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
local spawn=workspace:FindFirstChildWhichIsA("SpawnLocation",true)::SpawnLocation?
local root=spawn and spawn.Position or Vector3.new(0,4,0)
local folder=Instance.new("Folder");folder.Name="EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW";folder.Parent=workspace
local queues:{[string]:{Player}}={TEAM={},BATTLE_ROYALE={}}
local sessions:{[string]:any}={}
local joined:{[number]:string}={}
local chosenDefense:{[number]:string}={}
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
 p.Triggered:Connect(callback)
end
local function getCastlePoint(mode:string,index:number):Vector3
 local base=root+Vector3.new(mode=="TEAM" and -620 or 620,2,0)
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
 local core=block(model,"StandardCore",at+Vector3.new(0,6,0),Vector3.new(26,13,22),Color3.fromRGB(172,166,147))
 core.Material=Enum.Material.Brick
 local door=block(model,"SiegeGate",at+Vector3.new(0,4,-12),Vector3.new(10,8,1.5),Color3.fromRGB(96,69,56))
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
  if res.fallen then session.releaseEggs(entry.id,at,res.releasedEggs) end
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
 local vault=block(model,"EggVault",at+Vector3.new(13,3,9),Vector3.new(6,5,6),Color3.fromRGB(218,181,75))
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
  castleLocations={},castleModels={},world=Instance.new("Folder"),
 }
 session.world.Name=mode.."_Arena";session.world.Parent=folder
 sessions[mode]=session
 for _,entry in ipairs(roster) do
  if not entry.isAI then
   local p=Players:GetPlayerByUserId(tonumber(entry.id) or -1)
   if p then
    local module=chosenDefense[p.UserId] or "SENSOR"
    Rules.loadDefense(session.rules,entry.id,{module})
   end
  else Rules.loadDefense(session.rules,entry.id,{"SENSOR"}) end
 end
 session.releaseEggs=function(ownerId:string,at:Vector3,count:number)
  for i=1,count do
   local egg=block(session.world,"ReleasedEgg",at+Vector3.new((i-2)*3,4,-17),Vector3.new(2,3,2),Color3.fromRGB(245,219,94))
   egg.Shape=Enum.PartType.Ball
   prompt(egg,"拾う","解放された卵",function(p)
    if joined[p.UserId]~=mode or egg.Parent==nil then return end
    if pcall(function() Rules.takeEggs(session.rules,tostring(p.UserId),1) end) then egg:Destroy() end
   end)
  end
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
  if session.rules.winner~=nil then
   print("[EGGRUMBLE "..mode.."] Castle elimination winner:",session.rules.winner)
  end
 end
 for idx,entry in ipairs(roster) do createWorldCastle(session,entry,idx) end
 -- Field eggs available in both modes, not single/multi mode toggles.
 for i=1,24 do
  local at=getCastlePoint(mode,1)+Vector3.new((i%6)*40-115,2,math.floor(i/6)*55+230)
  local egg=block(session.world,"FieldEgg_"..i,at,Vector3.new(2.6,3.3,2.6),Color3.fromRGB(238,214,108))
  egg.Shape=Enum.PartType.Ball
  prompt(egg,"卵を拾う","フィールドの卵",function(p)
   if joined[p.UserId]~=mode or egg.Parent==nil then return end
   if pcall(function() Rules.takeEggs(session.rules,tostring(p.UserId),1) end) then egg:Destroy() end
  end)
 end
 Rules.start(session.rules)
 for _,p in ipairs(queue) do
  if p.Parent and joined[p.UserId]==mode then
   local ch=p.Character;local rootPart=ch and ch:FindFirstChild("HumanoidRootPart")::BasePart?
   local idx=table.find(humans,tostring(p.UserId))
   if rootPart and idx then rootPart.CFrame=CFrame.new(getCastlePoint(mode,idx)+Vector3.new(0,7,-45)) end
  end
 end
 -- Existing bot-actor module owns the ONLY AI combat/egg/siege loop.
 -- Never advance castle damage or eggs from a timer without spatial movement.
 BotActors.start(session,Rules)
end

local function joinQueue(mode:string,p:Player)
 if sessions[mode] then return end
 if joined[p.UserId] then return end
 joined[p.UserId]=mode
 table.insert(queues[mode],p)
 p:SetAttribute("EGGRUMBLE_QueuedMode",mode)
 if #queues[mode]==1 then task.delay(COUNTDOWN,function() startSession(mode) end) end
 if #queues[mode]>=MODE_SEATS then startSession(mode) end
end
local gateTeam=block(folder,"TEAM_PORTAL",root+Vector3.new(-12,6,28),Vector3.new(9,12,2),Color3.fromRGB(206,74,67))
local gateBR=block(folder,"BATTLE_ROYALE_PORTAL",root+Vector3.new(12,6,28),Vector3.new(9,12,2),Color3.fromRGB(79,132,230))
board(gateTeam,"EGGRUMBLE\nチーム戦｜全味方城陥落で敗北")
board(gateBR,"EGGRUMBLE\nバトルロワイヤル｜最後の城が勝者")
prompt(gateTeam,"参加する","チーム戦",function(p) joinQueue("TEAM",p) end)
prompt(gateBR,"参加する","バトルロワイヤル",function(p) joinQueue("BATTLE_ROYALE",p) end)
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
 local mode=joined[p.UserId];joined[p.UserId]=nil
 if mode and not sessions[mode] then
  local q=queues[mode]
  local idx=table.find(q,p)
  if idx then table.remove(q,idx) end
 end
 chosenDefense[p.UserId]=nil
 -- Production policy must decide whether an active disconnected castle persists under AI.
end)
print("[EGGRUMBLE V3] Studio-only two mode gates, bot filling/egg vault/field eggs and castle elimination preview; production teleport & full AI UNIMPLEMENTED")
