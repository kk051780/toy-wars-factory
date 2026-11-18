--!strict
-- GQ815. Original castle Host is sole match authority, original CastleMatchRules owns castle HP/eggs.
-- This session-owned defender actor controller consumes EXISTING GQ804 guardian proposal/confirm.
-- Never creates Game/Combat/Remote/Store/Score/Marketplace owners.
local Players=game:GetService("Players")
local Debris=game:GetService("Debris")
local Policy=require(script.Parent:WaitForChild("EGGRUMBLE_CastleSiegeGuardianPolicy"))
local M={}
local MAX_GLOBAL=12
local globalActive=0
local CONFIG={
 WARRIOR={id="SHIELD_KNIGHT",name="鉄壁の騎士",hp=110,range=10,damage=8,period=2.1,reach=15,
  color=Color3.fromRGB(79,120,167),weapon="SHIELD",mind="PROUD"},
 MAGE={id="ICE_MAGE",name="氷晶の魔導兵",hp=70,range=17,damage=6,period=2.7,reach=12,
  color=Color3.fromRGB(100,170,206),weapon="STAFF",mind="SHY"},
 NINJA={id="SHADOW_SCOUT",name="影の斥候",hp=68,range=12,damage=7,period=1.8,reach=19,
  color=Color3.fromRGB(101,87,145),weapon="TWIN_BLADES",mind="CURIOUS"},
 TRAPPER={id="PSY_PUPPET",name="念動人形",hp=86,range=15,damage=5,period=2.3,reach=12,
  color=Color3.fromRGB(148,116,177),weapon="PSI_ORB",mind="PLAYFUL"},
 BUILDER={id="CLOCK_GOLEM",name="歯車ゴーレム",hp=125,range=9,damage=9,period=2.8,reach=9,
  color=Color3.fromRGB(169,135,83),weapon="HAMMER",mind="PATIENT"},
 BEAST={id="GUARD_WOLF",name="守護魔狼",hp=84,range=11,damage=7,period=1.6,reach=20,
  color=Color3.fromRGB(113,143,105),weapon="CLAWS",mind="LOYAL"},
 ZOMBIE={id="CURSE_SOLDIER",name="呪印兵",hp=76,range=15,damage=5,period=2.4,reach=14,
  color=Color3.fromRGB(131,107,129),weapon="CURSE_BANNER",mind="MYSTERIOUS"},
}
local function part(parent:Instance,name:string,at:CFrame,size:Vector3,color:Color3,shape:Enum.PartType?):Part
 local p=Instance.new("Part")
 p.Name=name;p.Anchored=true;p.CanCollide=false;p.CanTouch=false;p.CanQuery=true
 p.Size=size;p.Color=color;p.Material=Enum.Material.SmoothPlastic;p.CFrame=at
 if shape then p.Shape=shape end
 p.Parent=parent
 return p
end
local function decorate(model:Model,role:string,root:Part,c:any)
 -- Stylized short silhouette: armor, shoulders, headgear, tool, emblem. 8-12 total Parts.
 local at=root.CFrame
 part(model,"ArmoredTorso",at*CFrame.new(0,2.2,0),Vector3.new(2.4,2.2,1.5),c.color)
 part(model,"Helm",at*CFrame.new(0,4,0),Vector3.new(1.6,1.5,1.45),Color3.fromRGB(232,218,176),
   Enum.PartType.Ball)
 part(model,"Visor",at*CFrame.new(0,4,-.78),Vector3.new(1.3,.25,.15),Color3.fromRGB(53,65,88))
 for _,side in ipairs({-1,1}) do
  part(model,"Pauldron",at*CFrame.new(side*1.45,2.65,0),Vector3.new(.85,.7,1.25),
   Color3.fromRGB(214,189,129),Enum.PartType.Ball)
  part(model,"Boot",at*CFrame.new(side*.62,.65,0),Vector3.new(.85,1.15,1),
   Color3.fromRGB(58,66,76))
 end
 local gear=part(model,"Signature_"..c.weapon,
    at*CFrame.new(1.95,2.25,-.7)*CFrame.Angles(0,0,math.rad(12)),
    Vector3.new(.45,3.1,.45),Color3.fromRGB(223,198,131))
 if role=="WARRIOR" then
  part(model,"Shield",at*CFrame.new(-1.65,2.3,-.65),Vector3.new(1.3,2.3,.35),
   Color3.fromRGB(187,201,212))
 elseif role=="MAGE" then
  part(model,"IceCrystal",at*CFrame.new(1.95,4.1,-.7),
   Vector3.new(.95,1.1,.95),Color3.fromRGB(119,212,240),Enum.PartType.Ball)
 elseif role=="NINJA" then
  part(model,"ShadowScarf",at*CFrame.new(0,3.5,.7),Vector3.new(2.1,.42,.7),
   Color3.fromRGB(62,49,85))
 elseif role=="TRAPPER" then
  part(model,"Orb",at*CFrame.new(1.95,4.2,-.7),Vector3.new(.88,.88,.88),
   Color3.fromRGB(209,153,236),Enum.PartType.Ball)
 elseif role=="BUILDER" then
  gear.Size=Vector3.new(.9,3.1,.9)
  part(model,"HammerHead",at*CFrame.new(1.95,3.7,-.7),
   Vector3.new(1.9,.9,.95),Color3.fromRGB(136,144,152))
 elseif role=="BEAST" then
  for _,side in ipairs({-1,1}) do
   part(model,"Ear",at*CFrame.new(side*.7,4.85,.2),
    Vector3.new(.42,.95,.45),Color3.fromRGB(121,137,98))
  end
 elseif role=="ZOMBIE" then
  part(model,"CursedFlag",at*CFrame.new(2.4,3.65,-.65),
   Vector3.new(1.3,.95,.13),Color3.fromRGB(83,72,123))
 end
end
local function createActor(parent:Instance,owner:string,role:string,where:Vector3):Model
 local c=CONFIG[role]
 local model=Instance.new("Model");model.Name="Guardian_"..c.id
 local anchor=part(model,"HumanoidRootPart",CFrame.new(where),
  Vector3.new(1.3,1.0,1.0),c.color)
 anchor.Transparency=1
 model.PrimaryPart=anchor
 decorate(model,role,anchor,c)
 local humanoid=Instance.new("Humanoid");humanoid.Name="Humanoid"
 humanoid.RequiresNeck=false;humanoid.BreakJointsOnDeath=false
 humanoid.MaxHealth=c.hp;humanoid.Health=c.hp;humanoid.Parent=model
 model:SetAttribute("EGGRUMBLE_GuardianOwner",owner)
 model:SetAttribute("EGGRUMBLE_GuardianRole",role)
 model:SetAttribute("EGGRUMBLE_GuardianFreeStarter",true)
 local gui=Instance.new("BillboardGui")
 gui.Name="GuardianHP";gui.Size=UDim2.fromOffset(130,40)
 gui.StudsOffset=Vector3.new(0,6.2,0);gui.MaxDistance=52;gui.AlwaysOnTop=false
 gui.Parent=anchor
 local label=Instance.new("TextLabel");label.Size=UDim2.fromScale(1,1)
 label.BackgroundColor3=Color3.fromRGB(26,32,46);label.BackgroundTransparency=.25
 label.TextColor3=Color3.fromRGB(245,232,199);label.TextScaled=true
 label.Font=Enum.Font.GothamBold;label.Parent=gui
 local function update()
  label.Text=c.name.."  "..tostring(math.max(0,math.ceil(humanoid.Health))).."/"..c.hp
 end
 humanoid.HealthChanged:Connect(update);update()
 model.Parent=parent
 return model
end
local function enemy(session:any,owner:string,id:string):boolean
 local a=session.rules.castles[owner];local b=session.rules.castles[id]
 return a~=nil and b~=nil and a.alive==true and b.alive==true
  and owner~=id and (session.mode~="TEAM" or a.team~=b.team)
end
-- Existing #531 Host is the only current-human membership authority.
-- Fail closed on disconnected/rejoined players; never infer match ownership from stale castle IDs.
local function currentHumanMember(session:any,p:Player):boolean
 if not session or not p then return false end
 local verify=session.isCurrentHuman
 if type(verify)~="function" then return false end
 local ok,allowed=pcall(verify,p)
 return ok and allowed==true
end
local function targetOf(session:any,owner:string,at:Vector3,range:number,exclude:Model):any
 local best=nil;local nearest=range
 local candidates={}
 for _,player in ipairs(Players:GetPlayers()) do
  local id=tostring(player.UserId)
  local ch=player.Character
  local hum=ch and ch:FindFirstChildOfClass("Humanoid")
  local hrp=ch and ch:FindFirstChild("HumanoidRootPart")
  if hum and hrp and hrp:IsA("BasePart") and hum.Health>0
   and player:GetAttribute("EGGRUMBLE_Eliminated")~=true
   and currentHumanMember(session,player)
   and enemy(session,owner,id) then
   table.insert(candidates,{id=id,model=ch,hum=hum,root=hrp})
  end
 end
 if type(session.botActors)=="table" then
  for id,actor in pairs(session.botActors) do
   local h=actor:FindFirstChildOfClass("Humanoid")
   local root=actor:FindFirstChild("HumanoidRootPart")
   if h and root and root:IsA("BasePart") and h.Health>0 and enemy(session,owner,id) then
    table.insert(candidates,{id=id,model=actor,hum=h,root=root})
   end
  end
 end
 for _,entry in ipairs(candidates) do
  local diff=entry.root.Position-at;local d=diff.Magnitude
  if d<nearest then
   local ray=RaycastParams.new()
   ray.FilterType=Enum.RaycastFilterType.Exclude
   ray.FilterDescendantsInstances={exclude,entry.model}
   local hit=workspace:Raycast(at,diff,ray)
   if hit==nil then nearest=d;best=entry end
  end
 end
 return best,nearest
end
local function impact(parent:Instance,where:Vector3,color:Color3)
 local piece=part(parent,"GuardianHitFlash",CFrame.new(where),Vector3.new(1.1,1.1,1.1),color,Enum.PartType.Ball)
 piece.CanQuery=false;piece.Material=Enum.Material.Neon
 Debris:AddItem(piece,.18)
end
function M.attach(session:any,chosenRole:any):any
 assert(session and session.rules and session.world and session.castleSiegeStates,
  "GQ815_EXPECT_EXISTING_SINGLE_HOST_AND_SIEGE")
 local actors={}
 local closed=false
 local seq=0
 local function retire(id:string)
  local data=actors[id];if not data then return end
  actors[id]=nil;globalActive=math.max(0,globalActive-1)
  Policy.releaseGuardian(data.siege,id,true)
  if data.model.Parent then data.model:Destroy() end
 end
 local function shutdown()
  if closed then return end
  closed=true
  local ids={}
  for id in pairs(actors) do table.insert(ids,id) end
  for _,id in ipairs(ids) do retire(id) end
 end
 local function advance(id:string)
  local d=actors[id];if not d then return end
  local model=d.model;local h=model:FindFirstChildOfClass("Humanoid")
  if not h or h.Health<=0 or not model.Parent or not d.siege.alive
   or session.rules.phase~="ACTIVE" or os.clock()>=d.expires then
   retire(id);return
  end
  local now=os.clock()
  local base=session.castleLocations[d.owner]
  if not base then retire(id);return end
  local c=CONFIG[d.role]
  local at=model:GetPivot().Position
  local foe,dist=targetOf(session,d.owner,at,c.range,model)
  if foe and dist<=c.range and now>=d.nextAttack then
   d.nextAttack=now+c.period
   foe.hum:TakeDamage(c.damage)
   impact(session.world,foe.root.Position,c.color)
  end
  -- Guardian protects its local castle; bounded motion, never pursues across arena.
  local desired=base+Vector3.new(math.sin(now*.8+d.seed)*c.reach*.45,3,math.cos(now*.7+d.seed)*c.reach*.45)
  if foe then
   local relative=foe.root.Position-base
   if relative.Magnitude<=22 then
    desired=base+relative.Unit*math.min(c.reach*.6,relative.Magnitude)
    desired=Vector3.new(desired.X,base.Y+3,desired.Z)
   end
  end
  local delta=desired-at
  local step=math.min(delta.Magnitude,if d.role=="NINJA" or d.role=="BEAST" then 1.35 else .8)
  if step>.01 then
   local nextPos=at+delta.Unit*step
   model:PivotTo(CFrame.new(nextPos)*CFrame.Angles(0,now*.8,0))
  end
 end
 local function spawn(owner:string,siege:any,proposal:any,now:number)
  if globalActive>=MAX_GLOBAL then return end
  local base=session.castleLocations[owner]
  if not base then return end
  seq+=1
  local id=tostring(session)..":G"..seq
  local initial=base+Vector3.new(7+seq%3,3,5)
  local model=createActor(session.world,owner,proposal.role,initial)
  local candidate={verifiedByServer=true,matchId=siege.matchId,targetCastleId=owner,
   phase="ACTIVE",ownerCastleAlive=true,serverSpawnAccepted=true,actorId=id,now=now}
  if not Policy.confirmGuardianSpawn(siege,proposal,candidate) then
   model:Destroy();return end
  globalActive+=1
  local d={owner=owner,role=proposal.role,model=model,siege=siege,
   expires=now+math.min(45,proposal.maxLifetimeSeconds),nextAttack=now+1.6,seed=seq}
  actors[id]=d
  local hum=model:FindFirstChildOfClass("Humanoid")
  if hum then hum.Died:Connect(function() retire(id) end) end
  task.spawn(function()
   while not closed and actors[id]==d do
    advance(id)
    task.wait(.33)
   end
  end)
 end
 local function refresh()
  if closed then return end
  if not session.rules or session.rules.phase~="ACTIVE" or session.world.Parent==nil then
   shutdown();return
  end
  local now=os.clock()
  for owner,s in pairs(session.castleSiegeStates) do
   local castle=session.rules.castles[owner]
   if castle and castle.alive and s.alive and s.stage~="GATE" and globalActive<MAX_GLOBAL then
    local role="WARRIOR"
    local humanId=tonumber(owner)
    if humanId and type(chosenRole)=="table" then
     local selection=chosenRole[humanId]
     if CONFIG[selection] then role=selection end
    end
    local proposal=Policy.guardianProposal(s,{
     verifiedByServer=true,matchId=s.matchId,targetCastleId=owner,
     phase="ACTIVE",ownerCastleAlive=true,now=now,role=role,
     guardianMasteryLevel=1,
     equippedGuardianType=CONFIG[role].id,
     equippedGuardianOwnedByCastle=true, -- FREE role starter only, no paid inventory claim
    })
    if proposal then spawn(owner,s,proposal,now) end
   end
  end
 end
 local function damageFromPlayer(p:Player,at:Vector3,radius:number,damage:number,_shape:string):number
  if closed or session.rules.phase~="ACTIVE" then return 0 end
  local owner=tostring(p.UserId)
  local c=session.rules.castles[owner]
  if not c or not c.alive or not currentHumanMember(session,p)
   or p:GetAttribute("EGGRUMBLE_Eliminated")==true then return 0 end
  local n=0
  for id,d in pairs(actors) do
   local hum=d.model:FindFirstChildOfClass("Humanoid")
   local root=d.model.PrimaryPart
   if n>=3 then break end
   if hum and hum.Health>0 and root and enemy(session,owner,d.owner)
    and (root.Position-at).Magnitude<=radius then
    local ray=RaycastParams.new()
    ray.FilterType=Enum.RaycastFilterType.Exclude
    ray.FilterDescendantsInstances={p.Character,d.model}
    if workspace:Raycast(at,root.Position-at,ray)==nil then
     hum:TakeDamage(math.min(damage,45));n+=1
    end
   end
  end
  return n
 end
 return {refresh=refresh,shutdown=shutdown,damageFromPlayer=damageFromPlayer}
end
return M
