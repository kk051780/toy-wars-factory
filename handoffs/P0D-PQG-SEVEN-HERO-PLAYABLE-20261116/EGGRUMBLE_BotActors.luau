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
-- A short action radius is not enough: side-wall adjacency must not let AI
-- steal vault eggs, deposit or damage castles through collidable geometry.
-- Stop the cast just before its interactable (vault/door/deposit) target part.
local function clearActionPath(actor:Model,actors:Instance,target:Vector3):boolean
 local origin=actor:GetPivot().Position
 if math.abs(origin.Y-target.Y)>4.0 then return false end
 local delta=Vector3.new(target.X-origin.X,0,target.Z-origin.Z)
 if delta.Magnitude<=4 then return true end
 local params=RaycastParams.new()
 params.FilterType=Enum.RaycastFilterType.Exclude
 params.FilterDescendantsInstances={actor,actors}
 params.RespectCanCollide=true
 return workspace:Raycast(origin+Vector3.new(0,0.4,0),delta.Unit*(delta.Magnitude-4),params)==nil
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
local function tryHeroAttack(actor:Model,my:any,session:any,lastHit:{[string]:number}):boolean
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
    bots[entry.id]=spawnActor(actors,entry.id,pos+Vector3.new(0,5,-34),entry.team)
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
        if home then bots[id]=spawnActor(actors,id,home+Vector3.new(0,5,-34),me.team) end
       end
      else
       tryHeroAttack(actor,me,session,lastHit)
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
         local goal=if goHome then own+Vector3.new(-16,3,-18)
          elseif hasEgg then (if nearFront then enemyLoc+Vector3.new(0,3,-2) else front)
          else enemyLoc+Vector3.new(0,3,-12)
         goals[id]=if goHome then "RETURN" elseif hasEgg then "STEAL" else "SIEGE"
         local slow=if (actor:GetAttribute("EGGRUMBLE_SlowUntil") or 0)>now then .45 else 1
         local dist=Router.navigate(mode..":"..id,actor,goal,AI_TICK*slow,actors)
         local label=actor:FindFirstChild("Head") and actor.Head:FindFirstChild("BotObjective")
         local ui=label and label:FindFirstChildOfClass("TextLabel")
         if ui then
          ui.Text=id.."\n"..(if goHome then "🥚 卵を帰還" elseif hasEgg then "🥚 敵城に潜入" else "⚔ 城攻め")
         end
         -- A bot cannot steal eggs, deposit them or attack from across the map.
         local at=actor:GetPivot().Position
         local actualTarget=if goHome then own+Vector3.new(-16,3,-18)
          elseif hasEgg then enemyLoc+Vector3.new(0,3,6)
          else enemyLoc+Vector3.new(0,3,-12)
         local actualDist=(Vector3.new(at.X,0,at.Z)-Vector3.new(actualTarget.X,0,actualTarget.Z)).Magnitude
         if actualDist<=ACTION_DISTANCE and clearActionPath(actor,actors,actualTarget) then
          if goHome then
           pcall(function() Rules.depositEggs(session.rules,id,me.heldEggs) end)
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
  bots[id]=spawnActor(actors,id,home+Vector3.new(0,5,-34),state.team)
  return true
 end
end
return BotActors
