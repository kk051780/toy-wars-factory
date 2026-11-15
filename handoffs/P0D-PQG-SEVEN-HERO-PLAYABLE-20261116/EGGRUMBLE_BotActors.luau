--!strict
-- EGGRUMBLE V3 isolated Studio-only bot-actor implementation.
-- Real 3D actor movement + visible egg approach/deposit + distance-gated siege.
-- NOT a finished pathfinding/matchmaking or PvP implementation.
local Players=game:GetService("Players")
local RunService=game:GetService("RunService")
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
    and clearHeroStrike(actor,character,at+Vector3.new(0,1.5,0),root.Position+Vector3.new(0,1,0)) then
    lastHit[my.id]=now
    h:TakeDamage(BOT_HERO_DAMAGE)
    return true
   end
  end
 end
 return false
end
local function planarDistance(a:Vector3,b:Vector3):number
 return (Vector3.new(a.X,0,a.Z)-Vector3.new(b.X,0,b.Z)).Magnitude
end

local function steeringStep(model:Model,target:Vector3,dt:number,_folder:Instance):number
 local current=model:GetPivot().Position
 local horizontal=Vector3.new(target.X-current.X,0,target.Z-current.Z)
 local distance=horizontal.Magnitude
 if distance<=.05 then return distance end
 local direction=horizontal.Unit
 local forwardDistance=math.min(AI_SPEED*dt,distance)
 local params=RaycastParams.new()
 params.FilterType=Enum.RaycastFilterType.Exclude
 params.FilterDescendantsInstances={model}
 params.RespectCanCollide=true
 local resultPivot:CFrame?=nil
 local function tryStep(heading:Vector3):boolean
  local delta=heading*forwardDistance
  local ahead=workspace:Raycast(current+Vector3.new(0,1,0),delta+heading*1.4,params)
  if ahead~=nil then return false end
  local nextXZ=current+delta
  -- Anchored preview actors still need physical support: no walking over a gap,
  -- up a steep wall or through the roof. A shared 2D arena floor is not assumed.
  local support=workspace:Raycast(nextXZ+Vector3.new(0,6,0),Vector3.new(0,-19,0),params)
  if support==nil or support.Normal.Y<.65 or not support.Instance.Anchored then return false end
  local nextY=support.Position.Y+2.4
  if math.abs(nextY-current.Y)>7.5 then return false end
  local next=Vector3.new(nextXZ.X,nextY,nextXZ.Z)
  resultPivot=CFrame.lookAt(next,next+heading)
  return true
 end
 local advanced=tryStep(direction)
 if not advanced then
  local lateral=Vector3.new(-direction.Z,0,direction.X)
  advanced=tryStep(lateral)
  if not advanced then advanced=tryStep(-lateral) end
 end
 if resultPivot~=nil then model:PivotTo(resultPivot) end
 return distance
end
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
 local raidStage:{[string]:number}={}
 local raidTargetOwner:{[string]:string}={}
 -- True 3D actor models, not just logical AI roster entries.
 for _,entry in ipairs(session.roster) do
  if entry.isAI then
   local pos=session.castleLocations[entry.id]
   if pos then
    bots[entry.id]=spawnActor(actors,entry.id,pos+Vector3.new(0,-3,-34),entry.team)
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
       if not deaths[id] then deaths[id]=now+BOT_REBIRTH end
       if now>=deaths[id] then
        deaths[id]=nil
        raidStage[id]=nil;raidTargetOwner[id]=nil
        local home=session.castleLocations[id]
        actor:Destroy()
        if home then bots[id]=spawnActor(actors,id,home+Vector3.new(0,-3,-34),me.team) end
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
         -- Approach enemy vault along its exterior, not through the solid 26x22 core.
         -- Three physical waypoints prevent an instant through-wall egg steal.
         local front=enemyLoc+Vector3.new(0,3,-27)
         local flank=enemyLoc+Vector3.new(20,3,-18)
         local raid=enemyLoc+Vector3.new(20,3,9)
         local goal:Vector3
         if goHome then
          raidStage[id]=nil;raidTargetOwner[id]=nil
          goal=own+Vector3.new(-16,3,-18)
         elseif hasEgg then
          if raidTargetOwner[id]~=enemy.id then
           raidTargetOwner[id]=enemy.id;raidStage[id]=1
          end
          local stage=raidStage[id] or 1
          local here=actor:GetPivot().Position
          if stage==1 and planarDistance(here,front)<=9 then stage=2 end
          if stage==2 and planarDistance(here,flank)<=9 then stage=3 end
          raidStage[id]=stage
          goal=if stage==1 then front elseif stage==2 then flank else raid
         else
          raidStage[id]=nil;raidTargetOwner[id]=nil
          goal=enemyLoc+Vector3.new(0,3,-12)
         end
         goals[id]=if goHome then "RETURN" elseif hasEgg then "STEAL" else "SIEGE"
         local dist=steeringStep(actor,goal,AI_TICK,actors)
         local label=actor:FindFirstChild("Head") and actor.Head:FindFirstChild("BotObjective")
         local ui=label and label:FindFirstChildOfClass("TextLabel")
         if ui then
          ui.Text=id.."\n"..(if goHome then "🥚 卵を帰還" elseif hasEgg then "🥚 敵城に潜入" else "⚔ 城攻め")
         end
         -- A bot cannot steal eggs, deposit them or attack from across the map.
         local at=actor:GetPivot().Position
         local actualTarget=if goHome then own+Vector3.new(-16,3,-18)
          elseif hasEgg then raid
          else enemyLoc+Vector3.new(0,3,-12)
         local actualDist=planarDistance(at,actualTarget)
         -- Reaching the castle front alone is insufficient; traverse the flank first.
         if actualDist<=ACTION_DISTANCE and (goHome or not hasEgg or raidStage[id]==3) then
          if goHome then
           pcall(function() Rules.depositEggs(session.rules,id,me.heldEggs) end)
          elseif hasEgg then
           pcall(function() Rules.takeEggs(session.rules,id,1,enemy.id) end)
          elseif now-(lastSiege[id] or 0)>=SIEGE_INTERVAL then
           lastSiege[id]=now
           local ok,result=pcall(function() return Rules.damageCastle(session.rules,enemy.id,id,26) end)
           if ok then
            if result.fallen and session.releaseEggs then
             session.releaseEggs(enemy.id,enemyLoc,result.releasedEggs)
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
     if actor.Parent then actor:Destroy() end
    end
   end
   task.wait(AI_TICK)
  end
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
  bots[id]=spawnActor(actors,id,home+Vector3.new(0,-3,-34),state.team)
  return true
 end
end
return BotActors
