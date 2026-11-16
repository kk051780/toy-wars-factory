--!strict
-- EGGRUMBLE V3 PERSONAL-CASTLE live defense; isolated optional SOURCE candidate.
-- Integrate once into the EXISTING author-owned V3 session after BotActors.start().
-- This module never creates a parallel Game, damage Remote, currency or paid product.
local Players=game:GetService("Players")
local RunService=game:GetService("RunService")
local Debris=game:GetService("Debris")
local Policy=require(script.Parent:WaitForChild("EGGRUMBLE_CastleDefensePolicy"))
local Defense={}

local OFFSETS={
 TURRET=Vector3.new(19,6,-18),
 TRAP=Vector3.new(0,1,-30),
 SENSOR=Vector3.new(-19,4,-18),
}
local COLORS={
 TURRET=Color3.fromRGB(251,148,71),
 TRAP=Color3.fromRGB(181,102,241),
 SENSOR=Color3.fromRGB(84,220,210),
}

local function aliveTarget(session:any,id:string):(Model?,Humanoid?,BasePart?,Player?)
 local c=session.rules.castles[id]
 if not c or not c.alive then return nil,nil,nil,nil end
 local model:Model?=nil
 local player:Player?=nil
 if c.isAI then
  model=session.botActors and session.botActors[id] or nil
 else
  local userId=tonumber(id)
  player=userId and Players:GetPlayerByUserId(userId) or nil
  model=player and player.Character or nil
 end
 local h=model and model:FindFirstChildOfClass("Humanoid")
 local at=model and model:FindFirstChild("HumanoidRootPart")
 if not h or h.Health<=0 or not at or not at:IsA("BasePart") then
  return nil,nil,nil,nil
 end
 return model,h,at,player
end

local function clearRay(from:Vector3,point:Vector3,model:Model,defenseFolder:Instance):boolean
 local direction=point-from
 if direction.Magnitude<=0.01 then return true end
 local params=RaycastParams.new()
 params.FilterType=Enum.RaycastFilterType.Exclude
 params.FilterDescendantsInstances={model,defenseFolder}
 params.RespectCanCollide=true
 return workspace:Raycast(from,direction,params)==nil
end

local function pulse(parent:Instance,pos:Vector3,color:Color3)
 local ring=Instance.new("Part")
 ring.Name="DefenseImpact"
 ring.Shape=Enum.PartType.Ball;ring.Anchored=true
 ring.CanCollide=false;ring.CanTouch=false;ring.CanQuery=false
 ring.Material=Enum.Material.Neon;ring.Color=color;ring.Transparency=.42
 ring.Size=Vector3.new(4,4,4);ring.Position=pos;ring.Parent=parent
 Debris:AddItem(ring,.22)
end

local function snare(session:any,model:Model,hum:Humanoid,now:number,isAI:boolean)
 local expires=now+1.1
 if isAI then
  -- Reuse the original BotActors speed-reduction contract.
  model:SetAttribute("EGGRUMBLE_SlowUntil",
   math.max(model:GetAttribute("EGGRUMBLE_SlowUntil") or 0,expires))
  return
 end
 -- Reuse original SevenRoleCombat slow attributes rather than create an
 -- independent speed authority. RoundReplay clears these after the match.
 local previous=hum:GetAttribute("EGGRUMBLE_OriginalWalkSpeed")
 local base=if type(previous)=="number" and previous>=8 and previous<=32
  then previous else hum.WalkSpeed
 if type(base)~="number" or base<8 or base>32 then return end
 hum:SetAttribute("EGGRUMBLE_OriginalWalkSpeed",base)
 hum:SetAttribute("EGGRUMBLE_SlowExpiry",
  math.max(hum:GetAttribute("EGGRUMBLE_SlowExpiry") or 0,expires))
 hum.WalkSpeed=math.max(8,math.min(hum.WalkSpeed,base*.72))
 task.delay(1.2,function()
  -- A delayed callback must not overwrite a new round's movement baseline.
  if session.rules.phase=="ACTIVE" and session.world.Parent
   and hum.Parent and hum.Health>0
   and os.clock()>=(hum:GetAttribute("EGGRUMBLE_SlowExpiry") or math.huge)
   and hum:GetAttribute("EGGRUMBLE_OriginalWalkSpeed")==base then
   hum.WalkSpeed=base
   hum:SetAttribute("EGGRUMBLE_OriginalWalkSpeed",nil)
  end
 end)
end

local function defenseAnchor(parent:Instance,kind:string,origin:Vector3):BasePart
 local p=Instance.new("Part")
 p.Name="CastleDefense_"..kind
 p.Size=if kind=="TRAP" then Vector3.new(5,.65,5) else Vector3.new(3.5,3.5,3.5)
 p.Shape=if kind=="TRAP" then Enum.PartType.Block else Enum.PartType.Ball
 p.Material=Enum.Material.Neon;p.Color=COLORS[kind];p.Transparency=.16
 p.Anchored=true;p.CanCollide=false;p.CanTouch=false;p.CanQuery=false
 p.Position=origin+OFFSETS[kind]
 p.Parent=parent
 return p
end

function Defense.start(session:any):()->()
 assert(RunService:IsStudio(),"castle defense preview may only run in private Studio")
 assert(session and session.rules and session.world and session.castleLocations
  and session.castleModels,"existing castle match required")
 assert(#session.roster<=Policy.MAX_CASTLES,"mobile hero/defense budget exceeded")
 local folder=Instance.new("Folder")
 folder.Name="EGGRUMBLE_CastleDefenseLive";folder.Parent=session.world
 local stations:{[string]:{[string]:BasePart}}={}
 local last:{[string]:{[string]:number}}={}
 local active=true
 for id,owner in pairs(session.rules.castles) do
  local castle=session.castleModels[id]
  local origin=session.castleLocations[id]
  if origin and castle and castle.model and castle.model.Parent then
   local available:{[string]:BasePart}={}
   for _,kind in ipairs(Policy.ORDER) do
    if Policy.hasModule(owner,kind) then
     available[kind]=defenseAnchor(folder,kind,origin)
    end
   end
   stations[id]=available
   last[id]={}
  end
 end
 local function stillRunning():boolean
  return active and folder.Parent~=nil and session.world.Parent~=nil
   and session.rules.phase=="ACTIVE"
 end
 local function tickOne(id:string,owner:any,kind:string,part:BasePart,now:number)
  if not owner.alive or not part.Parent or not Policy.hasModule(owner,kind) then return end
  local closest:{id:string,model:Model,hum:Humanoid,root:BasePart,player:Player?}?=nil
  local best=math.huge
  -- Source-locked same-session roster only; never scan unrelated match folders.
  for enemyId,enemy in pairs(session.rules.castles) do
   if Policy.canTarget(session.mode,owner,enemy) then
    local model,hum,root,player=aliveTarget(session,enemyId)
    if model and hum and root then
     local distance=(root.Position-part.Position).Magnitude
     if distance<=Policy.CONFIG[kind].range
      and (distance<best or (distance==best and closest and enemyId<closest.id)) then
      local los=kind=="SENSOR" or clearRay(part.Position,root.Position,model,folder)
      if Policy.mayActivate(kind,"ACTIVE",now,last[id][kind],distance,los) then
       local stealthUntil=player and (player:GetAttribute("EGGRUMBLE_StealthUntil") or 0) or 0
       if Policy.canAcquire(kind,now,stealthUntil) then
        best=distance
        closest={id=enemyId,model=model,hum=hum,root=root,player=player}
       end
      end
     end
    end
   end
  end
  if not closest or not stillRunning() or not owner.alive then return end
  local targetState=session.rules.castles[closest.id]
  if not targetState or not Policy.canTarget(session.mode,owner,targetState)
   or closest.hum.Health<=0 then return end
  -- The moment of effect is the only point that consumes the per-castle cooldown.
  last[id][kind]=now
  if kind=="SENSOR" then
   local p=closest.player
   if p then
    p:SetAttribute("EGGRUMBLE_StealthUntil",now)
    p:SetAttribute("EGGRUMBLE_SensorPingUntil",now+1.5)
   end
  else
   closest.hum:TakeDamage(Policy.CONFIG[kind].damage)
   if kind=="TRAP" and closest.hum.Health>0 then
    snare(session,closest.model,closest.hum,now,targetState.isAI==true)
   end
  end
  pulse(folder,closest.root.Position,COLORS[kind])
 end
 task.spawn(function()
  while stillRunning() do
   local now=os.clock()
   for id,kinds in pairs(stations) do
    local state=session.rules.castles[id]
    if state and state.alive then
     for _,kind in ipairs(Policy.ORDER) do
      local p=kinds[kind]
      if p and stillRunning() then tickOne(id,state,kind,p,now) end
     end
    end
   end
   task.wait(Policy.TICK_SECONDS)
  end
  if folder.Parent then folder:Destroy() end
 end)
 local function stop()
  active=false
  if folder.Parent then folder:Destroy() end
 end
 session.castleDefenseStop=stop
 return stop
end

return Defense
