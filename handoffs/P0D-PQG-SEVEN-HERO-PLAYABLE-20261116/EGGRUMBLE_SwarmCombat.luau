--!strict
-- EGGRUMBLE V3: standalone lightweight neutral-horde combat controller.
-- Studio-only, server-attributed real Humanoid deaths; NOT production optimized nor tested.
local Players=game:GetService("Players")
local RunService=game:GetService("RunService")
local Debris=game:GetService("Debris")
local AttackGeometry=require(script.Parent:WaitForChild("EGGRUMBLE_AttackGeometry"))
local ImpactFeedback=require(script.Parent:WaitForChild("EGGRUMBLE_ImpactFeedback"))
local Swarm={}
local LIMIT=110
local SPAWN_TICK=.18
local SPAWN_BATCH=5
local MAX_HITS=24
local MAX_LOS_RAYS_PER_ATTACK=48 -- source-only safety/performance cap; measure on Android
local NEUTRAL_HEALTH=32
local NEUTRAL_SPEED=7
local SWARM_RANGE=240
local BOT_ATTACK_CD=.62
local function piece(parent:Instance,name:string,pos:Vector3,size:Vector3,color:Color3):Part
 local p=Instance.new("Part");p.Name=name;p.Anchored=true;p.CanCollide=false
 p.Position=pos;p.Size=size;p.Color=color;p.Material=Enum.Material.SmoothPlastic;p.Parent=parent
 return p
end
local function soldier(parent:Instance,at:Vector3):Model
 local m=Instance.new("Model")
 m.Name="HordeSoldier";m:SetAttribute("EGGRUMBLE_Neutral",true);m.Parent=parent
 local root=piece(m,"HumanoidRootPart",at+Vector3.new(0,2,0),Vector3.new(1.7,2.5,1.5),Color3.fromRGB(127,102,89))
 root.CanTouch=false
 local head=piece(m,"Head",root.Position+Vector3.new(0,1.85,0),Vector3.new(1.3,1.3,1.3),Color3.fromRGB(180,158,128))
 head.Shape=Enum.PartType.Ball;head.CanTouch=false
 piece(m,"Shield",root.Position+Vector3.new(-1.1,-.1,-.25),Vector3.new(.5,1.5,1.4),Color3.fromRGB(94,101,114))
 m.PrimaryPart=root
 local h=Instance.new("Humanoid");h.Name="Humanoid";h.RequiresNeck=false
 h.MaxHealth=NEUTRAL_HEALTH;h.Health=NEUTRAL_HEALTH;h.BreakJointsOnDeath=false;h.Parent=m
 return m
end
local function labelKo(p:Player,n:number)
 p:SetAttribute("EGGRUMBLE_NeutralKOs",n)
 local stats=p:FindFirstChild("leaderstats")
 if not stats then
  stats=Instance.new("Folder");stats.Name="leaderstats";stats.Parent=p
 end
 local value=stats:FindFirstChild("NeutralKO")
 if not value then
  value=Instance.new("IntValue");value.Name="NeutralKO";value.Parent=stats
 end
 if value:IsA("IntValue") then value.Value=n end
end
function Swarm.start(session:any)
 assert(RunService:IsStudio(),"Studio-only neutral controller")
 local all=Instance.new("Folder");all.Name="NeutralHorde";all.Parent=session.world
 local live:{[Model]:Humanoid}={}
 local kills:{[string]:number}={}
 local lastBotHit:{[string]:number}={}
 local total=0
 local comboById:{[string]:number}={}
 local lastKillAt:{[string]:number}={}
 local bestCombo:{[string]:number}={}
 local ended=false
 local function credit(id:string)
  kills[id]=(kills[id] or 0)+1
  total+=1
  local n=kills[id]
  local now=os.clock()
  local combo=if now-(lastKillAt[id] or -100)<4 then (comboById[id] or 0)+1 else 1
  comboById[id]=combo
  lastKillAt[id]=now
  bestCombo[id]=math.max(bestCombo[id] or 0,combo)
  local p=Players:GetPlayerByUserId(tonumber(id) or -1)
  if p then
   labelKo(p,n)
   p:SetAttribute("EGGRUMBLE_BattleLevel",math.min(50,1+math.floor(n/25)))
   p:SetAttribute("EGGRUMBLE_Combo",combo)
   p:SetAttribute("EGGRUMBLE_BestCombo",bestCombo[id])
   if combo%25==0 then
    local character=p.Character
    local root=character and character:FindFirstChild("HumanoidRootPart")::BasePart?
    if root then
     -- Light diegetic KO celebration, never a giant permanently blocking mobile HUD.
     local gui=Instance.new("BillboardGui")
     gui.Name="EGGRUMBLE_ComboBurst";gui.Size=UDim2.fromOffset(150,45)
     gui.StudsOffset=Vector3.new(0,4,0);gui.AlwaysOnTop=false;gui.Parent=root
     local txt=Instance.new("TextLabel")
     txt.Size=UDim2.fromScale(1,1);txt.BackgroundTransparency=1
     txt.TextColor3=Color3.fromRGB(255,216,78)
     txt.TextStrokeTransparency=.15;txt.Font=Enum.Font.GothamBlack
     txt.TextScaled=true;txt.Text=tostring(combo).." COMBO!"
     txt.Parent=gui;Debris:AddItem(gui,.95)
    end
   end
   p:SetAttribute("EGGRUMBLE_SlashEvolution",if n>=100 then "TEMPEST" elseif n>=40 then "WAVE" else "BASE")
  end
  session.neutralTotal=total
 end
 local function addEnemy(at:Vector3)
  local m=soldier(all,at)
  local h=m:FindFirstChildOfClass("Humanoid") :: Humanoid
  live[m]=h
  h.Died:Connect(function()
   live[m]=nil
   local id=h:GetAttribute("LastAttackerId")
   if type(id)=="string" and session.rules.castles[id] then
    local attacker=Players:GetPlayerByUserId(tonumber(id) or -1)
    ImpactFeedback.ko(all,m,attacker and (attacker:GetAttribute("EGGRUMBLE_Role") or "WARRIOR") or "WARRIOR")
    credit(id)
   end
   task.delay(.25,function() if m.Parent then m:Destroy() end end)
  end)
 end
 local function aliveTargets():{Vector3}
  local a={}
  for _,p in ipairs(Players:GetPlayers()) do
   local c=session.rules.castles[tostring(p.UserId)]
   if c and c.alive then
    local ch=p.Character
    local root=ch and ch:FindFirstChild("HumanoidRootPart")::BasePart?
    if root then table.insert(a,root.Position) end
   end
  end
  for id,m in pairs(session.botActors or {}) do
   local c=session.rules.castles[id]
   if c and c.alive and m.Parent and m.PrimaryPart then table.insert(a,m.PrimaryPart.Position) end
  end
  return a
 end
 -- Area skills have a visible area, not the ability to hit through solid castle walls.
 local function lineOfSightToNeutral(origin:Vector3,attacker:Model,target:Model):boolean
  local root=target.PrimaryPart
  if not root then return false end
  local params=RaycastParams.new()
  params.FilterType=Enum.RaycastFilterType.Exclude
  params.FilterDescendantsInstances={attacker,target}
  params.RespectCanCollide=true
  local delta=(root.Position+Vector3.new(0,1,0))-origin
  if delta.Magnitude<=.01 then return true end
  return workspace:Raycast(origin,delta,params)==nil
 end
 local function strike(id:string,at:Vector3,radius:number,damage:number,origin:Vector3,attacker:Model,shape:string):number
  if session.rules.phase~="ACTIVE" then return 0 end
  local player=session.rules.castles[id]
  if not player or not player.alive then return 0 end
  local nearest={}
  for m,h in pairs(live) do
   if m.Parent and h.Health>0 and m.PrimaryPart then
    local delta=m.PrimaryPart.Position-at
    local dis=math.sqrt(delta.X*delta.X+delta.Z*delta.Z)
    if AttackGeometry.allowed(origin,at,m.PrimaryPart.Position,radius,shape) then
     table.insert(nearest,{target=h,dist=dis})
    end
   end
  end
  table.sort(nearest,function(x,y)return x.dist<y.dist end)
  -- A blocked target never consumes a KO/HIT slot; guard CPU with a fixed ray budget.
  local hits=0
  local rays=0
  for _,candidate in ipairs(nearest) do
   if hits>=MAX_HITS or rays>=MAX_LOS_RAYS_PER_ATTACK then break end
   rays+=1
   local h=candidate.target
   local model=h.Parent
   if model and model:IsA("Model") and lineOfSightToNeutral(origin,attacker,model) then
    h:SetAttribute("LastAttackerId",id)
    h:TakeDamage(damage)
    local user=Players:GetPlayerByUserId(tonumber(id) or -1)
    ImpactFeedback.hit(model,user and (user:GetAttribute("EGGRUMBLE_Role") or "WARRIOR") or "WARRIOR")
    hits+=1
   end
  end
  return hits
 end
 local api={
  kills=kills,
  damageFromPlayer=function(player:Player,at:Vector3,radius:number,damage:number,shape:string?):number
   local character=player.Character
   local root=character and character:FindFirstChild("HumanoidRootPart")::BasePart?
   local humanoid=character and character:FindFirstChildOfClass("Humanoid")
   if not character or not root or not humanoid or humanoid.Health<=0 then return 0 end
   -- Splash center is server-generated and stays in reach of the living attacker.
   if (at-root.Position).Magnitude>36 then return 0 end
   -- Survival-like neutral-only momentum: max +12%, NEVER affects human PvP/castle HP.
   local currentCombo=if os.clock()-(lastKillAt[tostring(player.UserId)] or -100)<4
    then (comboById[tostring(player.UserId)] or 0) else 0
   local bonus=if currentCombo>=60 then 1.12 elseif currentCombo>=20 then 1.06 else 1
   return strike(tostring(player.UserId),at,radius,damage*bonus,
    root.Position+Vector3.new(0,1,0),character,shape or "CIRCLE")
  end,
  damageFromBot=function(botId:string,at:Vector3):number
   local actor=session.botActors and session.botActors[botId]
   local root=actor and actor.PrimaryPart
   local h=actor and actor:FindFirstChildOfClass("Humanoid")
   if not actor or not root or not h or h.Health<=0 then return 0 end
   if (root.Position-at).Magnitude>5 then return 0 end
   local now=os.clock()
   if now-(lastBotHit[botId] or 0)<BOT_ATTACK_CD then return 0 end
   lastBotHit[botId]=now
   local center=root.Position+root.CFrame.LookVector*3
   return strike(botId,center,9,NEUTRAL_HEALTH,root.Position+Vector3.new(0,1,0),actor,"FANG")
  end,
  getAliveCount=function():number
   local n=0;for m,h in pairs(live) do if m.Parent and h.Health>0 then n+=1 end end
   return n
  end,
  getTotal=function():number return total end,
 }
 session.swarm=api
 task.spawn(function()
  while all.Parent and session.rules.phase=="ACTIVE" do
   local candidates=aliveTargets()
   if #candidates>0 then
    local n=api.getAliveCount()
    for _=1,math.min(SPAWN_BATCH,LIMIT-n) do
     local target=candidates[math.random(1,#candidates)]
     local a=math.random()*math.pi*2
     local d=math.random(21,58)
     local at=target+Vector3.new(math.cos(a)*d,0,math.sin(a)*d)
     -- Always in the same wide battle district as its current moving hero.
     addEnemy(Vector3.new(at.X,session.groundY or target.Y-4,at.Z))
    end
   end
   task.wait(SPAWN_TICK)
  end
  ended=true
 end)
 task.spawn(function()
  while all.Parent and session.rules.phase=="ACTIVE" do
   local candidates=aliveTargets()
   if #candidates>0 then
    for m,h in pairs(live) do
     if m.Parent and m.PrimaryPart and h.Health>0 then
      local at=m:GetPivot().Position
      local near=nil;local best=SWARM_RANGE
      for _,target in ipairs(candidates) do
       local delta=Vector3.new(target.X-at.X,0,target.Z-at.Z)
       if delta.Magnitude<best then near=delta;best=delta.Magnitude end
      end
      if near and best>3 then
       local travel=math.min(NEUTRAL_SPEED*.38,best)
       local forward=near.Unit*travel
       local params=RaycastParams.new()
       params.FilterType=Enum.RaycastFilterType.Exclude
       params.FilterDescendantsInstances={all}
       params.RespectCanCollide=true
       local origin=at+Vector3.new(0,1,0)
       local function free(step:Vector3):boolean
        if step.Magnitude<=.01 then return false end
        return workspace:Raycast(origin,step+step.Unit*.35,params)==nil
       end
       local chosen:Vector3?=nil
       if free(forward) then
        chosen=forward
       else
        -- NPCs take a small sidestep, never ghost through a solid gate or wall.
        local sideways=Vector3.new(-near.Unit.Z,0,near.Unit.X)*travel
        if free(sideways) then chosen=sideways
        elseif free(-sideways) then chosen=-sideways end
       end
       if chosen then
        local next=at+chosen
        m:PivotTo(CFrame.lookAt(next,next+near.Unit))
       end
      end
     end
    end
   end
   task.wait(.38)
  end
 end)
 print("[EGGRUMBLE_SWARM] attached to actual two-mode preview; live neutral cap",LIMIT,
  "KO counts are real deaths, not multiplier rewards")
 return api
end
return Swarm
