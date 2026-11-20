--!strict
-- EGGRUMBLE V3: seven role-specific A/B/C skills in THE SAME castle/egg/horde match.
-- Studio-only isolated gameplay scaffold; NOT final animations/art, RC, PvP, mobile QA.
-- WARRIOR etc internal IDs remain stable. 3 server-owned cooldown Tools per role.
local RunService=game:GetService("RunService")
local Debris=game:GetService("Debris")
local CombatBalance=require(script.Parent:WaitForChild("EGGRUMBLE_CombatBalance"))
local SkillFX=require(script.Parent:WaitForChild("EGGRUMBLE_SkillFX"))
local ImpactFeedback=require(script.Parent:WaitForChild("EGGRUMBLE_ImpactFeedback"))
local WeaponSilhouettes=require(script.Parent:WaitForChild("EGGRUMBLE_WeaponSilhouettes"))
local DivineMantle=require(script.Parent:WaitForChild("EGGRUMBLE_DivineMantle"))
local AttackGeometry=require(script.Parent:WaitForChild("EGGRUMBLE_AttackGeometry"))
local HeroCombat={}
local ORDER={"WARRIOR","MAGE","NINJA","TRAPPER","BUILDER","BEAST","ZOMBIE"}
local JOBS={
 WARRIOR={name="武神",color=Color3.fromRGB(235,105,66),weapon="神太刀",skills={"飛翔斬撃","槍陣突撃","神憑き"}},
 MAGE={name="魔法使い",color=Color3.fromRGB(80,155,240),weapon="魔導杖",skills={"氷弾","爆炎陣","雷光治癒"}},
 NINJA={name="暗殺者",color=Color3.fromRGB(114,112,172),weapon="双刃",skills={"瞬影斬","風走り","千刃旋風"}},
 TRAPPER={name="超能力者",color=Color3.fromRGB(193,101,244),weapon="念動球",skills={"念動衝撃","重力牢獄","空間転移"}},
 BUILDER={name="マッドサイエンティスト",color=Color3.fromRGB(62,218,186),weapon="未来銃",skills={"電磁射撃","多弾ロケット","自動砲塔"}},
 BEAST={name="魔獣使い",color=Color3.fromRGB(243,173,66),weapon="獣笛",skills={"獣牙撃","巨獣餌","分裂餌"}},
 ZOMBIE={name="呪術師",color=Color3.fromRGB(164,78,164),weapon="呪印杖",skills={"呪印波動","疫病霧","不死軍団"}},
}
local lastByPlayer:{[number]:{[string]:number}}={}
local castSequence:{[number]:number}={}
local function makeEffect(parent:Instance,at:Vector3,size:Vector3,color:Color3,lifetime:number):Part
 local p=Instance.new("Part")
 p.Name="ClassSkillVFX";p.Shape=Enum.PartType.Ball;p.Anchored=true
 p.CanCollide=false;p.CanTouch=false;p.CanQuery=false;p.Material=Enum.Material.Neon
 p.Transparency=.5;p.Size=size;p.Color=color;p.Position=at;p.Parent=parent
 Debris:AddItem(p,lifetime)
 return p
end
local function characterOf(p:Player):(Model?,BasePart?,Humanoid?)
 local c=p.Character
 if not c then return nil,nil,nil end
 local r=c:FindFirstChild("HumanoidRootPart")::BasePart?
 local h=c:FindFirstChildOfClass("Humanoid")
 if not r or not h or h.Health<=0 then return nil,nil,nil end
 return c,r,h
end
local function rootAdvance(root:BasePart,dist:number):Vector3
 return root.Position+root.CFrame.LookVector*dist
end
local function lineClear(source:Vector3,to:Vector3,first:Model,second:Model):boolean
 local delta=to-source
 if delta.Magnitude<.01 then return true end
 local ray=RaycastParams.new();ray.FilterType=Enum.RaycastFilterType.Exclude
 ray.FilterDescendantsInstances={first,second};ray.RespectCanCollide=true
 return workspace:Raycast(source,delta,ray)==nil
end
local function hitBotHeroes(session:any,player:Player,root:BasePart,char:Model,center:Vector3,range:number,damage:number,shape:string):number
 local state=session.rules.castles[tostring(player.UserId)]
 if not state or not state.alive then return 0 end
 local count=0
 for id,enemy in pairs(session.botActors or {}) do
  local target=session.rules.castles[id]
  local er=enemy and enemy.PrimaryPart
  local h=enemy and enemy:FindFirstChildOfClass("Humanoid")
  if target and target.alive and (session.mode~="TEAM" or target.team~=state.team)
   and er and h and h.Health>0
   and AttackGeometry.allowed(root.Position,center,er.Position,range,shape)
   and (er.Position-root.Position).Magnitude<=36
   and count<5 and lineClear(root.Position+Vector3.new(0,1.5,0),er.Position,char,enemy) then
   -- War God has a deliberate single-target duelist edge against a lone opponent.
   local loneEnemy=true
   for otherId,other in pairs(session.botActors or {}) do
    if otherId~=id and other.PrimaryPart then
     local otherState=session.rules.castles[otherId]
     if otherState and otherState.alive
      and (session.mode~="TEAM" or otherState.team~=state.team)
      and (other.PrimaryPart.Position-root.Position).Magnitude<22 then
      loneEnemy=false;break
     end
    end
   end
   local duel=if player:GetAttribute("EGGRUMBLE_Role")=="WARRIOR" and loneEnemy then 1.25 else 1
   local mark=if (h:GetAttribute("EGGRUMBLE_MarkedUntil") or 0)>os.clock() then 1.15 else 1
   h:TakeDamage(damage*duel*mark)
   ImpactFeedback.hit(enemy,player:GetAttribute("EGGRUMBLE_Role") or "WARRIOR")
   count+=1
  end
 end
 return count
end
local function hitHumanHeroes(session:any,p:Player,root:BasePart,char:Model,center:Vector3,range:number,damage:number,shape:string):number
 local state=session.rules.castles[tostring(p.UserId)]
 if not state or not state.alive then return 0 end
 local count=0
 for _,enemyPlayer in ipairs(game:GetService("Players"):GetPlayers()) do
  local enemyState=session.rules.castles[tostring(enemyPlayer.UserId)]
  local enemyChar,enemyRoot,enemyHum=characterOf(enemyPlayer)
  if enemyPlayer~=p and enemyState and enemyState.alive
   and (session.mode~="TEAM" or enemyState.team~=state.team)
   and enemyChar and enemyRoot and enemyHum and enemyHum.Health>0
   and AttackGeometry.allowed(root.Position,center,enemyRoot.Position,range,shape)
   and (enemyRoot.Position-root.Position).Magnitude<=36
   and count<4 and lineClear(root.Position+Vector3.new(0,1.5,0),
    enemyRoot.Position+Vector3.new(0,1,0),char,enemyChar) then
   -- In real PvP, attacking the living opposing hero inflicts actual Humanoid damage;
   -- castle death and hero knockout remain separate match states.
   local duel=if p:GetAttribute("EGGRUMBLE_Role")=="WARRIOR"
    and (enemyRoot.Position-root.Position).Magnitude<=18 then 1.25 else 1
   local mark=if (enemyHum:GetAttribute("EGGRUMBLE_MarkedUntil") or 0)>os.clock() then 1.15 else 1
   enemyHum:TakeDamage(damage*duel*mark)
   ImpactFeedback.hit(enemyChar,p:GetAttribute("EGGRUMBLE_Role") or "WARRIOR")
   count+=1
  end
 end
 return count
end
local function neutralAndBotHit(session:any,p:Player,root:BasePart,char:Model,at:Vector3,range:number,damage:number,c:Color3,shape:string):number
 -- Both hit APIs are SERVER-owned; neutral KO credit only comes from Humanoid.Died.
 local count=0
 if session.swarm then count+=session.swarm.damageFromPlayer(p,at,range,damage,shape) end
 count+=hitBotHeroes(session,p,root,char,at,range,damage,shape)
 count+=hitHumanHeroes(session,p,root,char,at,range,damage,shape)
 -- Unique visual feedback is produced by SkillFX.emit, not a repeated generic orb.
 return count
end
local function safeMove(char:Model,root:BasePart,amount:number):boolean
 -- Egg carriers do not get a short-cut across walls or instantly through a siege route.
 local v=root.CFrame.LookVector
 local ray=RaycastParams.new();ray.FilterType=Enum.RaycastFilterType.Exclude
 ray.FilterDescendantsInstances={char};ray.RespectCanCollide=true
 local start=root.Position+Vector3.new(0,2,0)
 local collision=workspace:Raycast(start,v*amount,ray)
 local distance=if collision then math.max(0,collision.Distance-3) else amount
 if distance<3 then return false end
 -- Airborne crossing is NOT permitted: land only on physical navigable ground.
 local landing=root.Position+v*distance
 local downward=workspace:Raycast(landing+Vector3.new(0,6,0),Vector3.new(0,-17,0),ray)
 if not downward or not downward.Instance.CanCollide then return false end
 if math.abs(landing.Y-downward.Position.Y)>8 then return false end
 char:PivotTo(CFrame.new(Vector3.new(landing.X,downward.Position.Y+3,landing.Z),landing+v))
 return true
end
local function healAllies(session:any,player:Player,root:BasePart)
 local state=session.rules.castles[tostring(player.UserId)]
 if not state then return end
 for _,other in ipairs(game:GetService("Players"):GetPlayers()) do
  local c=session.rules.castles[tostring(other.UserId)]
  local char,otherRoot,h=characterOf(other)
  if c and c.alive and char and otherRoot and h
   and (session.mode~="TEAM" and other==player or session.mode=="TEAM" and c.team==state.team)
   and (otherRoot.Position-root.Position).Magnitude<=22 then
   h.Health=math.min(h.MaxHealth,h.Health+25)
  end
 end
end
-- Status effects are real server damage / movement changes (not only colored VFX).
-- Hard caps and team checks keep control roles useful without stun-locking a duel.
local function secondaryEffect(session:any,p:Player,root:BasePart,char:Model,
 center:Vector3,radius:number,effect:string,shape:string)
 if effect~="CHILL_2S" and effect~="SLOW_3S" and effect~="BURN_3S"
  and effect~="MARK" and effect~="PUSH" and effect~="PREDATOR" then return end
 local state=session.rules.castles[tostring(p.UserId)]
 if not state or not state.alive then return end
 local now=os.clock()
 local duration=if effect=="CHILL_2S" then 2 elseif effect=="PUSH" then 1.2 else 3
 local affected=0
 local function apply(h:Humanoid,bot:Model?)
  if h.Health<=0 or affected>=5 then return end
  affected+=1
  if effect=="CHILL_2S" or effect=="SLOW_3S" or effect=="PUSH" then
   if bot then
    bot:SetAttribute("EGGRUMBLE_SlowUntil",math.max(bot:GetAttribute("EGGRUMBLE_SlowUntil") or 0,now+duration))
   else
    local base=h:GetAttribute("EGGRUMBLE_OriginalWalkSpeed") or h.WalkSpeed
    if type(base)~="number" then return end
    h:SetAttribute("EGGRUMBLE_OriginalWalkSpeed",base)
    h:SetAttribute("EGGRUMBLE_SlowExpiry",now+duration)
    h.WalkSpeed=math.max(8,base*(if effect=="PUSH" then .58 else .72))
    task.delay(duration+.1,function()
     if h.Parent and os.clock()>=(h:GetAttribute("EGGRUMBLE_SlowExpiry") or math.huge) then
      h.WalkSpeed=base
      h:SetAttribute("EGGRUMBLE_OriginalWalkSpeed",nil)
     end
    end)
   end
  elseif effect=="MARK" then
   h:SetAttribute("EGGRUMBLE_MarkedUntil",now+4)
  elseif effect=="BURN_3S" or effect=="PREDATOR" then
   local untilTime=h:GetAttribute("EGGRUMBLE_BurnUntil") or 0
   if now<untilTime then return end
   h:SetAttribute("EGGRUMBLE_BurnUntil",now+3)
   local tick=if effect=="PREDATOR" then 5 else 4
   for i=1,3 do
    task.delay(i,function()
     if h.Parent and h.Health>0 and session.rules.phase=="ACTIVE" then h:TakeDamage(tick) end
    end)
   end
  end
 end
 for id,actor in pairs(session.botActors or {}) do
  local target=session.rules.castles[id]
  local enemy=actor and actor.PrimaryPart
  local hum=actor and actor:FindFirstChildOfClass("Humanoid")
  if target and target.alive and enemy and hum
   and (session.mode~="TEAM" or target.team~=state.team)
   and AttackGeometry.allowed(root.Position,center,enemy.Position,radius,shape)
   and (enemy.Position-root.Position).Magnitude<=36
   and lineClear(root.Position+Vector3.new(0,1,0),enemy.Position,char,actor) then
   apply(hum,actor)
  end
 end
 for _,targetPlayer in ipairs(game:GetService("Players"):GetPlayers()) do
  local target=session.rules.castles[tostring(targetPlayer.UserId)]
  local enemyChar,enemyRoot,hum=characterOf(targetPlayer)
  if targetPlayer~=p and target and target.alive and enemyChar and enemyRoot and hum
   and (session.mode~="TEAM" or target.team~=state.team)
   and AttackGeometry.allowed(root.Position,center,enemyRoot.Position,radius,shape)
   and (enemyRoot.Position-root.Position).Magnitude<=36
   and lineClear(root.Position+Vector3.new(0,1,0),enemyRoot.Position, char,enemyChar) then
   apply(hum,nil)
  end
 end
end
local function execute(session:any,p:Player,role:string,slot:string)
 if session.rules.phase~="ACTIVE" then return end
 local owner=session.rules.castles[tostring(p.UserId)]
 if not owner or not owner.alive then return end
 if p:GetAttribute("EGGRUMBLE_Eliminated")==true then return end
 if p:GetAttribute("EGGRUMBLE_Role")~=role then return end
 local char,root,h=characterOf(p)
 if not char or not root or not h then return end
 local now=os.clock()
 local perPlayer=lastByPlayer[p.UserId]
 if not perPlayer then perPlayer={};lastByPlayer[p.UserId]=perPlayer end
 local key=session.mode..":"..role..":"..slot
 local spec=CombatBalance.skill(role,slot)
 local cd=spec.cooldown
 if now-(perPlayer[key] or -10000)<cd then return end
 perPlayer[key]=now
 -- One atomic, server-confirmed cast signature for local R6/R15/AJU presentation.
 -- No client request can authorize damage: tools, ownership and cooldown are above.
 castSequence[p.UserId]=(castSequence[p.UserId] or 0)+1
 p:SetAttribute("EGGRUMBLE_SkillCastSignature",
  role..":"..slot..":"..tostring(castSequence[p.UserId]))
 local def=JOBS[role]
 local boost=if role=="WARRIOR" and now<(char:GetAttribute("EGGRUMBLE_KamiUntil") or 0) then 1.6
  elseif role=="BEAST" and now<(char:GetAttribute("EGGRUMBLE_GiantFeedUntil") or 0) then 1.2 else 1
 local function blast(distance:number?,radius:number?,damage:number?):number
  -- Delayed bursts never hit after death, castle elimination or a new character spawn.
  if not p.Parent or p.Character~=char or h.Health<=0
   or not owner.alive or session.rules.phase~="ACTIVE" then return 0 end
  local forward=distance or spec.reach
  local area=radius or spec.radius
  local amount=damage or spec.damage
  local center=rootAdvance(root,forward)
  local hits=neutralAndBotHit(session,p,root,char,center,area,amount*boost,def.color,spec.shape)
  -- The original author-owned StoneGiant is a real optional shared-world enemy,
  -- not a second neutral boss implementation or an invented regular KO.
  local boss=session.boss
  local weakpoint=boss and boss.weakpoint
  if boss and boss.model and boss.model.Parent and weakpoint and weakpoint.Parent
   and AttackGeometry.allowed(root.Position,center,weakpoint.Position,area,spec.shape)
   and lineClear(root.Position+Vector3.new(0,1.5,0),weakpoint.Position,char,boss.model) then
   local validBossHit=boss.damageFrom(p,math.min(100,amount*boost),true)
   if validBossHit then
    hits+=1
    if boss.model.Parent then ImpactFeedback.hit(boss.model,role) end
   end
  end
  secondaryEffect(session,p,root,char,center,area,spec.effect,spec.shape)
  SkillFX.emit(session.world,role,slot,root.Position,root.CFrame.LookVector,center,area)
  ImpactFeedback.attacker(p,role,slot,hits)
  return hits
 end
 if role=="WARRIOR" then
  if slot=="A" then blast()
  elseif slot=="B" then
   for i=1,3 do
    task.delay((i-1)*.1,function()
     if session.rules.phase=="ACTIVE" and owner.alive and p.Character==char and h.Health>0 and root.Parent then
      blast(spec.reach+(i-2)*6)
     end
    end)
   end
  else
   DivineMantle.activate(p,6)
   blast()
  end
 elseif role=="MAGE" then
  if slot=="A" then blast()
  elseif slot=="B" then blast()
  else healAllies(session,p,root);blast() end
 elseif role=="NINJA" then
  if slot=="A" then blast()
  elseif slot=="B" then
   if owner.heldEggs==0 and safeMove(char,root,25) then
    p:SetAttribute("EGGRUMBLE_StealthUntil",now+3)
   end
   blast()
  else
   for i=1,3 do
    task.delay((i-1)*.14,function() if session.rules.phase=="ACTIVE" and owner.alive and root.Parent then blast(spec.reach+(i-2)*2) end end)
   end
  end
 elseif role=="TRAPPER" then
  if slot=="A" then blast()
  elseif slot=="B" then
   blast()
  else
   if owner.heldEggs==0 then safeMove(char,root,20) end
   blast()
  end
 elseif role=="BUILDER" then
  if slot=="A" then blast()
  elseif slot=="B" then
   for i=1,3 do
    task.delay(i*.15,function()
     if session.rules.phase=="ACTIVE" and owner.alive and root.Parent then blast(spec.reach+(i-2)*4) end
    end)
   end
  else
   local turret=makeEffect(session.world,rootAdvance(root,6),Vector3.new(4,5,4),def.color,4.2)
   turret.Name="MadScientistTurret"
   for i=1,4 do
    task.delay(i*.72,function()
     if session.rules.phase=="ACTIVE" and owner.alive and root.Parent and turret.Parent then blast() end
    end)
   end
  end
 elseif role=="BEAST" then
  if slot=="A" then blast()
  elseif slot=="B" then
   local giant=makeEffect(session.world,rootAdvance(root,11),Vector3.new(12,15,12),def.color,1.6)
   giant.Name="BeastFeedGiant";char:SetAttribute("EGGRUMBLE_GiantFeedUntil",now+5);blast()
  else
   for i=1,3 do
    local angle=i*math.pi*2/3
    local pos=root.Position+Vector3.new(math.cos(angle)*8,3,math.sin(angle)*8)
    local child=makeEffect(session.world,pos,Vector3.new(4,5,4),def.color,2)
    child.Name="BeastFeedSplit_"..i
    task.delay(i*.12,function()
     if session.rules.phase=="ACTIVE" and owner.alive and root.Parent then
      blast(spec.reach+(i-2)*4)
     end
    end)
   end
  end
 elseif role=="ZOMBIE" then
  if slot=="A" then blast()
  elseif slot=="B" then
   blast()
  else
   for i=1,3 do
    local puppet=makeEffect(session.world,rootAdvance(root,5+i*3),Vector3.new(3,7,3),def.color,2.4)
    puppet.Name="CurseUndead_"..i
    task.delay(i*.22,function()
     if session.rules.phase=="ACTIVE" and owner.alive and root.Parent then blast(spec.reach+(i-2)*3) end
    end)
   end
  end
 end
end
function HeroCombat.roleOrder():{string}
 return table.clone(ORDER)
end
function HeroCombat.info(role:string):any
 return JOBS[role]
end
function HeroCombat.equip(session:any,p:Player,role:string):()
 assert(RunService:IsStudio(),"Seven-role V3 combat is a private Studio source preview only")
 if not JOBS[role] then role="WARRIOR" end
 if session.rules.phase~="ACTIVE" then return end
 local owner=session.rules.castles[tostring(p.UserId)]
 if not owner or not owner.alive or not p.Parent then return end
 local backpack=p:FindFirstChildOfClass("Backpack")
 if not backpack then return end
 local current=p.Character
 if not current then return end
 DivineMantle.cancel(p)
 current:SetAttribute("EGGRUMBLE_GiantFeedUntil",0)
 p:SetAttribute("EGGRUMBLE_Role",role)
 WeaponSilhouettes.attach(p,role)
 for _,container in ipairs({backpack,current}) do
  for _,instance in ipairs(container:GetChildren()) do
   if instance:IsA("Tool") and string.sub(instance.Name,1,16)=="EGGRUMBLE_SKILL_" then instance:Destroy() end
  end
 end
 local data=JOBS[role]
 for index,slot in ipairs({"A","B","C"}) do
  local tool=Instance.new("Tool")
  tool.Name="EGGRUMBLE_SKILL_"..slot.."_"..data.skills[index]
  local spec=CombatBalance.skill(role,slot)
  tool.ToolTip=string.format("%s｜%s｜威力%d｜射程%d｜範囲%d｜再使用%.1fs",
   data.name,data.skills[index],spec.damage,spec.reach,spec.radius,spec.cooldown)
  tool.RequiresHandle=false;tool.CanBeDropped=false
  tool.Activated:Connect(function()
   if tool.Parent~=p.Character then return end
   execute(session,p,role,slot)
  end)
  tool.Parent=backpack
 end
end
function HeroCombat.clear(p:Player)
 lastByPlayer[p.UserId]=nil
 ImpactFeedback.clear(p)
 DivineMantle.cancel(p)
 local c=p.Character
 if c then c:SetAttribute("EGGRUMBLE_GiantFeedUntil",0) end
 WeaponSilhouettes.clear(p)
 for _,container in ipairs({p:FindFirstChildOfClass("Backpack"),p.Character}) do
  if container then
   for _,item in ipairs(container:GetChildren()) do
    if item:IsA("Tool") and string.sub(item.Name,1,16)=="EGGRUMBLE_SKILL_" then item:Destroy() end
   end
  end
 end
end
return HeroCombat
