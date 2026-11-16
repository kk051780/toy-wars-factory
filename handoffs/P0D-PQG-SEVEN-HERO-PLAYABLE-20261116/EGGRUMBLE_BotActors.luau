--!strict
-- EGGRUMBLE V3 isolated Studio-only bot-actor implementation.
-- Real 3D actor movement + visible egg approach/deposit + distance-gated siege.
-- NOT a finished pathfinding/matchmaking or PvP implementation.
local Players=game:GetService("Players")
local RunService=game:GetService("RunService")
local Router=require(script.Parent:WaitForChild("EGGRUMBLE_BotPathRouter"))
local BotActors={}
local AI_TICK=.18
local AI_SPEED=30
local ACTION_DISTANCE=12.5
local SIEGE_INTERVAL=1.6
local BOT_ATTACK_INTERVAL=1.15
local BOT_HERO_DAMAGE=13
local BOT_REBIRTH=6.0
local FIELD_EGG_SEARCH_RADIUS=145

local function makePart(m:Model,name:string,at:Vector3,size:Vector3,color:Color3,collide:boolean):Part
 local p=Instance.new("Part")
 p.Name=name;p.Anchored=true;p.CanCollide=collide
 p.Size=size;p.Position=at;p.Color=color
 p.Material=Enum.Material.SmoothPlastic;p.Parent=m
 return p
end
local function spawnActor(parent:Instance,id:string,at:Vector3,team:string?):Model
 local model=Instance.new("Model")
 model.Name="AI_Actor_"..id;model:SetAttribute("EGGRUMBLE_BotId",id)
 model.Parent=parent
 local base=makePart(model,"HumanoidRootPart",at+Vector3.new(0,3,0),Vector3.new(2.1,3.2,1.6),
  team=="RED" and Color3.fromRGB(227,110,97) or Color3.fromRGB(99,161,237),false)
 local head=makePart(model,"Head",base.Position+Vector3.new(0,2.25,0),Vector3.new(1.8,1.8,1.8),
  Color3.fromRGB(245,209,159),false)
 head.Shape=Enum.PartType.Ball
 local sword=makePart(model,"Blade",base.Position+Vector3.new(1.8,.25,-.4),Vector3.new(.25,3.1,.5),
  Color3.fromRGB(246,221,142),false)
 sword.Material=Enum.Material.Metal
 local shield=makePart(model,"Shield",base.Position+Vector3.new(-1.8,0,-.2),Vector3.new(.35,2.1,1.8),
  Color3.fromRGB(124,139,165),false)
 local eye=makePart(model,"Eyes",head.Position+Vector3.new(0,0,-.9),Vector3.new(1,.18,.18),
  Color3.fromRGB(42,37,50),false)
 local label=Instance.new("BillboardGui")
 label.Name="BotObjective";label.Size=UDim2.fromOffset(180,50)
 label.StudsOffset=Vector3.new(0,3.3,0);label.AlwaysOnTop=false;label.Parent=head
 local text=Instance.new("TextLabel")
 text.Size=UDim2.fromScale(1,1);text.TextScaled=true;text.TextWrapped=true
 text.BackgroundColor3=Color3.fromRGB(20,30,44);text.BackgroundTransparency=.25
 text.TextColor3=Color3.new(1,1,1);text.Font=Enum.Font.GothamBold
 text.Text=id.."\n出陣";text.Parent=label
 local hum=Instance.new("Humanoid")
 hum.Name="Humanoid";hum.RequiresNeck=false;hum.MaxHealth=100;hum.Health=100
 hum.BreakJointsOnDeath=false;hum.Parent=model
 model.PrimaryPart=base
 return model
end
local function desiredTarget(session:any,mode:string,my:any):any
 local target=nil
 local best=math.huge
 local home=session.castleLocations[my.id]
 for id,enemy in pairs(session.rules.castles) do
  if enemy.alive and id~=my.id and (mode~="TEAM" or enemy.team~=my.team) then
   local loc=session.castleLocations[id]
   if loc and home then
    local dist=(loc-home).Magnitude
    if dist<best then target=enemy;best=dist end
   end
  end
 end
 return target
end
-- Server-owned world egg parts are physically present in this private preview.
-- Identify only the exact single-use Rules token associated with each part.
-- This is separate from the original author's special FieldItem pickups.
local function nearestWorldEgg(session:any,at:Vector3):(string?,BasePart?,number)
 local chosenId:string?=nil
 local chosenPart:BasePart?=nil
 local best=FIELD_EGG_SEARCH_RADIUS
 for _,part in ipairs(session.world:GetChildren()) do
  if part:IsA("BasePart") then
   local serial=part.Name:match("^FieldEgg_(%d+)$")
   local released=part.Name:match("^ReleasedEgg_(RELEASE_%d+)$")
    or part.Name:match("^ReleasedEgg_(CARRIER_DROP_%d+)$")
   local eggId=if serial then "FIELD_"..serial else released
   if eggId and session.rules.fieldEggTokens[eggId]==true then
    local dist=(Vector3.new(at.X,0,at.Z)-Vector3.new(part.Position.X,0,part.Position.Z)).Magnitude
    if dist<best then chosenId=eggId;chosenPart=part;best=dist end
   end
  end
 end
 return chosenId,chosenPart,best
end
-- A short action radius is not enough: side-wall adjacency must not let AI
-- steal vault eggs, deposit or damage castles through collidable geometry.
-- Stop the cast just before its interactable (vault/door/deposit) target part.
local function clearActionPath(actor:Model,actors:Instance,target:Vector3,targetPart:BasePart?):boolean
 local origin=actor:GetPivot().Position
 if math.abs(origin.Y-target.Y)>4.0 then return false end
 local start=origin+Vector3.new(0,0.4,0)
 local segment=target-start
 if segment.Magnitude<=0.01 then return true end
 local params=RaycastParams.new()
 params.FilterType=Enum.RaycastFilterType.Exclude
 params.FilterDescendantsInstances={actor,actors}
 params.RespectCanCollide=true
 -- Do not skip the final 4 studs: a thin castle wall can separate actor and vault.
 -- A direct hit on the intended interactable (vault/deposit/item) is permitted,
 -- while any other first collidable hit, even at close range, blocks the action.
 local hit=workspace:Raycast(start,segment,params)
 return hit==nil or (targetPart~=nil and hit.Instance==targetPart)
end

local function clearHeroStrike(actor:Model,target:Model,origin:Vector3,destination:Vector3):boolean
 local delta=destination-origin
 if delta.Magnitude<=0.01 then return true end
 local params=RaycastParams.new()
 params.FilterType=Enum.RaycastFilterType.Exclude
 params.FilterDescendantsInstances={actor,target}
 params.RespectCanCollide=true
 -- A solid castle core, wall, or gate must prevent a bot hero strike.
 return workspace:Raycast(origin,delta,params)==nil
end
local function tryHeroAttack(actor:Model,my:any,session:any,lastHit:{[string]:number},bots:{[string]:Model}):boolean
 local at=actor:GetPivot().Position
 local now=os.clock()
 if now-(lastHit[my.id] or 0)<BOT_ATTACK_INTERVAL then return false end
 -- Bot-vs-human combat actually checks spatial distance and humanoid health.
 for _,player in ipairs(Players:GetPlayers()) do
  local pc=session.rules.castles[tostring(player.UserId)]
  if pc and pc.alive and pc.id~=my.id and (session.mode~="TEAM" or pc.team~=my.team) then
   local character=player.Character
   local root=character and character:FindFirstChild("HumanoidRootPart")::BasePart?
   local h=character and character:FindFirstChildOfClass("Humanoid")
   if character and root and h and h.Health>0 and (root.Position-at).Magnitude<11
    and os.clock()>=(player:GetAttribute("EGGRUMBLE_StealthUntil") or 0)
    and clearHeroStrike(actor,character,at+Vector3.new(0,1.5,0),root.Position+Vector3.new(0,1,0)) then
    lastHit[my.id]=now
    h:TakeDamage(BOT_HERO_DAMAGE)
    return true
   end
  end
 end
 -- Enemy moving AI heroes must fight one another in bot-filled matches, too.
 -- Shares the real melee cooldown, actor humanoid HP and collision LOS.
 for targetId,targetActor in pairs(bots) do
  local enemyCastle=session.rules.castles[targetId]
  if enemyCastle and enemyCastle.alive and enemyCastle.id~=my.id
   and (session.mode~="TEAM" or enemyCastle.team~=my.team)
   and targetActor~=actor and targetActor.Parent then
   local targetRoot=targetActor.PrimaryPart
   local targetHumanoid=targetActor:FindFirstChildOfClass("Humanoid")
   if targetRoot and targetHumanoid and targetHumanoid.Health>0
    and (targetRoot.Position-at).Magnitude<11
    and clearHeroStrike(actor,targetActor,at+Vector3.new(0,1.5,0),
     targetRoot.Position+Vector3.new(0,1,0)) then
    lastHit[my.id]=now
    targetHumanoid:TakeDamage(BOT_HERO_DAMAGE)
    return true
   end
  end
 end
 return false
end
-- Actor pathfinding is in the reusable, budgeted EGGRUMBLE_BotPathRouter module.
function BotActors.start(session:any,Rules:any):()
 assert(RunService:IsStudio(),"preview bot actors are Studio-only")
 local mode=session.mode
 local folder=session.world
 local actors=Instance.new("Folder");actors.Name="MovingBotHeroes";actors.Parent=folder
 local bots:{[string]:Model}={}
 local lastSiege:{[string]:number}={}
 local lastHit:{[string]:number}={}
 local deaths:{[string]:number}={}
 local goals:{[string]:string}={}
 -- True 3D actor models, not just logical AI roster entries.
 for _,entry in ipairs(session.roster) do
  if entry.isAI then
   local pos=session.castleLocations[entry.id]
   if pos then
    bots[entry.id]=spawnActor(actors,entry.id,pos+Vector3.new(0,-1.5,-34),entry.team)
   end
  end
 end
 task.spawn(function()
  while session.rules.phase=="ACTIVE" and folder.Parent do
   local now=os.clock()
   for id,actor in pairs(bots) do
    local me=session.rules.castles[id]
    if me and me.alive and actor.Parent then
     local hum=actor:FindFirstChildOfClass("Humanoid")
     if hum then
      if hum.Health<=0 then
       if not deaths[id] then
        -- Do not let a bot respawn with an invisible carried egg. One physical drop.
        if session.dropCarrierEggs then session.dropCarrierEggs(id,actor:GetPivot().Position) end
        deaths[id]=now+BOT_REBIRTH
       end
       if now>=deaths[id] then
        deaths[id]=nil
        local home=session.castleLocations[id]
        Router.clear(mode..":"..id)
        actor:Destroy()
        if home then bots[id]=spawnActor(actors,id,home+Vector3.new(0,-1.5,-34),me.team) end
       end
      else
       tryHeroAttack(actor,me,session,lastHit,bots)
       if session.swarm then session.swarm.damageFromBot(id,actor:GetPivot().Position) end
       local enemy=desiredTarget(session,mode,me)
       if enemy then
        local own=session.castleLocations[id]
        local enemyLoc=session.castleLocations[enemy.id]
        if own and enemyLoc then
         local goHome=me.heldEggs>0
         local hasEgg=enemy.vaultEggs>0
         local front=enemyLoc+Vector3.new(0,3,-26)
         local nearFront=(Vector3.new(actor:GetPivot().Position.X,0,actor:GetPivot().Position.Z)-Vector3.new(front.X,0,front.Z)).Magnitude<18
         local fieldId:string?=nil
         local fieldPart:BasePart?=nil
         local fieldDist=math.huge
         if not goHome then
          fieldId,fieldPart,fieldDist=nearestWorldEgg(session,actor:GetPivot().Position)
         end
         -- Field eggs are actual objectives, not unused props. While right at
         -- an enemy vault, finish that raid; otherwise pick nearby field eggs.
         local collectField=fieldId~=nil and fieldPart~=nil
          and (not hasEgg or (not nearFront and fieldDist<115))
         local goal=if goHome then own+Vector3.new(-16,3,-18)
          elseif collectField and fieldPart then fieldPart.Position
          elseif hasEgg then (if nearFront then enemyLoc+Vector3.new(0,3,-2) else front)
          else enemyLoc+Vector3.new(0,3,-12)
         goals[id]=if goHome then "RETURN" elseif collectField then "FIELD_EGG" elseif hasEgg then "STEAL" else "SIEGE"
         local slow=if (actor:GetAttribute("EGGRUMBLE_SlowUntil") or 0)>now then .45 else 1
         local dist=Router.navigate(mode..":"..id,actor,goal,AI_TICK*slow,actors)
         local label=actor:FindFirstChild("Head") and actor.Head:FindFirstChild("BotObjective")
         local ui=label and label:FindFirstChildOfClass("TextLabel")
         if ui then
          ui.Text=id.."\n"..(if goHome then "🥚 卵を帰還" elseif collectField then "🥚 野外卵を回収" elseif hasEgg then "🥚 敵城に潜入" else "⚔ 城攻め")
         end
         -- A bot cannot steal eggs, deposit them or attack from across the map.
         local at=actor:GetPivot().Position
         local actualTarget=if goHome then own+Vector3.new(-16,3,-18)
          elseif collectField and fieldPart then fieldPart.Position
          elseif hasEgg then enemyLoc+Vector3.new(0,3,6)
          else enemyLoc+Vector3.new(0,3,-12)
         local actualDist=(Vector3.new(at.X,0,at.Z)-Vector3.new(actualTarget.X,0,actualTarget.Z)).Magnitude
         local actionTarget:BasePart?=nil
         if goHome then
          local ownCastle=session.castleModels[id]
          actionTarget=ownCastle and (ownCastle.model:FindFirstChild("OwnEggDeposit")::BasePart?)
         elseif collectField then
          actionTarget=fieldPart
         elseif hasEgg then
          local enemyCastle=session.castleModels[enemy.id]
          actionTarget=enemyCastle and (enemyCastle.model:FindFirstChild("EggVault")::BasePart?)
         else
          local enemyCastle=session.castleModels[enemy.id]
          actionTarget=enemyCastle and enemyCastle.door
         end
         if actualDist<=ACTION_DISTANCE and clearActionPath(actor,actors,actualTarget,actionTarget) then
          if goHome then
           pcall(function() Rules.depositEggs(session.rules,id,me.heldEggs) end)
          elseif collectField and fieldId and fieldPart and fieldPart.Parent==session.world
           and session.rules.fieldEggTokens[fieldId]==true then
           -- Atomic server-issued token spend; world visual disappears only
           -- after successful pickup. Concurrent human prompt attempts fail safe.
           local ok=pcall(function() Rules.takeFieldEgg(session.rules,id,fieldId) end)
           if ok then fieldPart:Destroy() end
          elseif hasEgg then
           pcall(function() Rules.takeEggs(session.rules,id,1,enemy.id) end)
          elseif now-(lastSiege[id] or 0)>=SIEGE_INTERVAL then
           lastSiege[id]=now
           local ok,result=pcall(function() return Rules.damageCastle(session.rules,enemy.id,id,26) end)
           if ok then
            if result.fallen and session.releaseEggs then
             session.releaseEggs(enemy.id,enemyLoc,result.releasedEggIds)
            end
           end
          end
          if session.refresh then session.refresh() end
         end
        end
       end
      end
     end
    else
     Router.clear(mode..":"..id)
     if actor.Parent then actor:Destroy() end
    end
   end
   task.wait(AI_TICK)
  end
  for id,_ in pairs(bots) do Router.clear(mode..":"..id) end
 end)
 session.botActors=bots
 session.botObjectives=goals
 session.takeover=function(id:string):boolean
  local state=session.rules.castles[id]
  if not state or not state.alive or bots[id] then return false end
  local home=session.castleLocations[id]
  if not home then return false end
  -- Keep the disconnected player's castle in the match under equal-budget AI defense.
  state.isAI=true
  bots[id]=spawnActor(actors,id,home+Vector3.new(0,-1.5,-34),state.team)
  return true
 end
end
return BotActors
