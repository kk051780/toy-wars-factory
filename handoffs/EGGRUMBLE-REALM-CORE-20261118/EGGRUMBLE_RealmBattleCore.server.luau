--!nonstrict
-- GQ8 REALM CORE: dedicated server-owned land/sea/air/subsea battle layer.
-- This is a private RC candidate. It does not replace canonical Game, Combat,
-- Swarm, score, DataStore or egg authority. Existing human PvP is deliberately
-- excluded until Host supplies a reliable same-session TEAM membership API.
-- Unlike legacy LSS traversal, the runtime does NOT require Studio.
local Players = game:GetService("Players")
local Workspace = game:GetService("Workspace")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Debris = game:GetService("Debris")
local LOBBY_NAME = "EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW"
local LSS_NAME = "EGGRUMBLE_LAND_SEA_SKY_20261117"
local CORE_NAME = "EGGRUMBLE_REALM_BATTLE_CORE"
local REMOTE_NAME = "EGGRUMBLE_RealmBattleIntent_V1"
local MAX_AIRCRAFT = 2
local MAX_SEA_CREATURES = 3
local AIRCRAFT_HP = 120
local AIRCRAFT_BOMBS = 3
local GUN_INTERVAL = .20
local BOMB_INTERVAL = 8
local CANNON_INTERVAL = 2.0
local BREATH_INTERVAL = 1.25
local HYDRO_INTERVAL = .75
local SERVER_TICK = .10
local WEATHER_PHASE_SECONDS = 35
local STORM_WARNING_SECONDS = 2
local LIGHTNING_INTERVAL = 7
local GROUND_FLIGHT_MIN = 22
local GROUND_FLIGHT_MAX = 170
local scenes = {}
local remote = ReplicatedStorage:FindFirstChild(REMOTE_NAME)
if not remote then
 remote = Instance.new("RemoteEvent")
 remote.Name = REMOTE_NAME
 remote.Parent = ReplicatedStorage
end
local function part(parent,name,cf,size,color,collide,alpha)
 local p = Instance.new("Part")
 p.Name=name; p.Anchored=true; p.CFrame=cf; p.Size=size
 p.Color=color; p.CanCollide=collide; p.CanTouch=collide
 p.Transparency=alpha or 0; p.Material=Enum.Material.SmoothPlastic
 p.Parent=parent
 return p
end
local function eligible(p,mode,world)
 if not p or p.Parent~=Players or not world.Parent
  or world.Parent.Name~=LOBBY_NAME
  or p:GetAttribute("EGGRUMBLE_QueuedMode")~=mode
  or p:GetAttribute("EGGRUMBLE_Eliminated")==true then return false end
 if world:FindFirstChild("Castle_"..tostring(p.UserId))==nil then return false end
 local c=p.Character
 local h=c and c:FindFirstChildOfClass("Humanoid")
 return h~=nil and h.Health>0 and c:FindFirstChild("HumanoidRootPart")~=nil
end
local function prompt(p,action,object,callback)
 local q=Instance.new("ProximityPrompt")
 q.ActionText=action; q.ObjectText=object
 q.HoldDuration=.25; q.MaxActivationDistance=13; q.RequiresLineOfSight=true
 q.Parent=p
 q.Triggered:Connect(function(player)
  local c=player.Character
  local r=c and c:FindFirstChild("HumanoidRootPart")
  local h=c and c:FindFirstChildOfClass("Humanoid")
  if not r or not h or h.Health<=0 or (r.Position-p.Position).Magnitude>16 then return end
  callback(player,h)
 end)
 return q
end
local function damageMultiplier(element,underwater)
 if underwater then
  if element=="FIRE" then return .15 end
  if element=="LIGHTNING" then return 1.35 end
 end
 return 1
end
local function safeReturn(p,at,mode,world)
 if not eligible(p,mode,world) then return end
 local c=p.Character
 local h=c:FindFirstChildOfClass("Humanoid")
 h.Sit=false
 c:PivotTo(CFrame.new(at+Vector3.new(0,4,0)))
end
local function damageRealm(model,damage,element,underwater)
 if not model or not model.Parent then return false end
 local hp=model:GetAttribute("RealmHP")
 if typeof(hp)~="number" or hp<=0 then return false end
 local dealt=math.max(0,math.floor(damage*damageMultiplier(element,underwater)+.5))
 hp=math.max(0,hp-dealt)
 model:SetAttribute("RealmHP",hp)
 if hp==0 then
  if model:GetAttribute("RealmKind")=="FIGHTER" then
   model:SetAttribute("RealmCrash",true)
  end
  model:Destroy()
 end
 return dealt>0
end
local function install(world)
 if scenes[world] or not world:IsA("Folder") then return end
 local mode=world.Name=="TEAM_Arena" and "TEAM"
  or world.Name=="BATTLE_ROYALE_Arena" and "BATTLE_ROYALE" or nil
 if not mode or not world.Parent or world.Parent.Name~=LOBBY_NAME then return end
 local floor=world:FindFirstChild("TacticalBattlefield")
 if not floor or not floor:IsA("BasePart") or floor.Size.X<600 then return end
 local x,y,z=floor.Position.X,floor.Position.Y+floor.Size.Y/2,floor.Position.Z
 local halfX,halfZ=floor.Size.X/2-50,floor.Size.Z/2-50
 local core=Instance.new("Folder")
 core.Name=CORE_NAME;core.Parent=world
 local state={mode=mode,world=world,core=core,started=os.clock(),
  planes={},divers={},creatures={},controls={},weapons={},lastSpawn={},
  active=true,lastLightning=0,pendingLightning=nil,weather="CLEAR"}
 scenes[world]=state
 -- A physical underwater cavern reachable by everyone. Water is represented
 -- by an exclusive collision-safe arena: no shared Terrain mutation.
 local depthY=y-66
 local seabed=part(core,"SubseaFloor",
  CFrame.new(x,depthY-5,z+halfZ-85),Vector3.new(240,4,160),
  Color3.fromRGB(25,95,120),true)
 local seaCenter=seabed.Position+Vector3.new(0,14,0)
 local oceanSurface=part(core,"SubseaSurface",
  CFrame.new(seaCenter+Vector3.new(0,35,0)),Vector3.new(245,1,166),
  Color3.fromRGB(48,163,198),false,.60)
 part(core,"CoralReefLeft",CFrame.new(seaCenter+Vector3.new(-70,-5,0)),
  Vector3.new(23,16,18),Color3.fromRGB(220,94,164),true)
 part(core,"CoralReefRight",CFrame.new(seaCenter+Vector3.new(70,-5,0)),
  Vector3.new(20,12,28),Color3.fromRGB(67,205,160),true)
 local dive=part(core,"PublicDiveStation",CFrame.new(x+75,y+2,z+halfZ-120),
  Vector3.new(15,2,12),Color3.fromRGB(38,174,201),true)
 local rise=part(core,"SubseaReturnDock",CFrame.new(seaCenter+Vector3.new(0,-2,45)),
  Vector3.new(16,2,14),Color3.fromRGB(235,198,75),true)
 local flightPad=part(core,"PublicFighterHangar",
  CFrame.new(x-160,y+2,z-halfZ+115),Vector3.new(22,2,22),
  Color3.fromRGB(230,178,62),true)
 local function clearDive(player)
  state.divers[player]=nil
  if player.Parent==Players then
   player:SetAttribute("EGGRUMBLE_RealmDepth","SURFACE")
  end
 end
 prompt(dive,"潜水する","海中戦へ",function(p)
  if not eligible(p,mode,world) then return end
  safeReturn(p,seaCenter+Vector3.new(0,0,20),mode,world)
  state.divers[p]=true
  p:SetAttribute("EGGRUMBLE_RealmDepth","SUBSEA")
 end)
 prompt(rise,"浮上する","地上へ帰還",function(p)
  if not eligible(p,mode,world) or not state.divers[p] then return end
  clearDive(p);safeReturn(p,dive.Position,mode,world)
 end)
 local function findCurrentMount(p)
  if not eligible(p,mode,world) then return nil,nil,nil end
  local c=p.Character
  local h=c:FindFirstChildOfClass("Humanoid")
  local seat=h and h.SeatPart
  if not seat or seat.Name~="PilotSeat" or seat.Occupant~=h then return nil,nil,nil end
  local model=seat.Parent
  if not model or not model:IsA("Model") or not model:IsDescendantOf(world) then return nil,nil,nil end
  local kind=model:GetAttribute("RealmKind")
  if kind=="FIGHTER" and state.planes[model]==p
   and model:GetAttribute("RealmPilot")==p.UserId then
   return model,kind,h
  end
  local lss=world:FindFirstChild(LSS_NAME)
  if not lss or not model:IsDescendantOf(lss)
   or model.Name:match("_(%d+)$")~=tostring(p.UserId) then return nil,nil,nil end
  if model.Name:find("_SEA_BOAT_") then kind="SHIP"
  elseif model.Name:find("_SEA_BEAST_") then kind="SEA_BEAST"
  elseif model.Name:find("_SKY_BEAST_") then kind="SKY_BEAST"
  elseif model.Name:find("_AIRSHIP_") then kind="AIRSHIP"
  else return nil,nil,nil end
  if (model.Name:find("^BUILDER_") and p:GetAttribute("EGGRUMBLE_Role")~="BUILDER")
   or (model.Name:find("^BEAST_") and p:GetAttribute("EGGRUMBLE_Role")~="BEAST") then
   return nil,nil,nil
  end
  return model,kind,h
 end
 prompt(flightPad,"戦闘機に搭乗","全職業共通",function(p,h)
  if not eligible(p,mode,world) then return end
  local now=os.clock()
  if now-(state.lastSpawn[p] or -100)<18 then return end
  for craft,pilot in pairs(state.planes) do
   if pilot==p and craft.Parent then return end
  end
  local live=0
  for craft in pairs(state.planes) do if craft.Parent then live+=1 end end
  if live>=MAX_AIRCRAFT then return end
  state.lastSpawn[p]=now
  local m=Instance.new("Model")
  m.Name="GQ8_Fighter_"..tostring(p.UserId);m.Parent=core
  local cf=CFrame.new(x-160,y+65,z-halfZ+115)
  local hull=part(m,"FighterHull",cf,Vector3.new(8,2.5,17),
   Color3.fromRGB(66,164,221),true)
  m.PrimaryPart=hull
  for side=-1,1,2 do
   part(m,"FighterWing_"..tostring(side),cf*CFrame.new(side*8,0,0),
    Vector3.new(11,1,5),Color3.fromRGB(110,193,235),false)
  end
  part(m,"FighterTail",cf*CFrame.new(0,2,7),Vector3.new(1,4,3),
   Color3.fromRGB(230,208,82),false)
  local seat=Instance.new("VehicleSeat")
  seat.Name="PilotSeat";seat.Size=Vector3.new(3,1,4)
  seat.CFrame=cf*CFrame.new(0,2.3,0);seat.Anchored=true
  seat.Parent=m
  m:SetAttribute("RealmPilot",p.UserId)
  m:SetAttribute("RealmKind","FIGHTER")
  m:SetAttribute("RealmHP",AIRCRAFT_HP)
  m:SetAttribute("RealmBombs",AIRCRAFT_BOMBS)
  state.planes[m]=p
  m.Destroying:Connect(function()
   if m:GetAttribute("RealmCrash")==true and eligible(p,mode,world) then
    local pilotHumanoid=p.Character:FindFirstChildOfClass("Humanoid")
    safeReturn(p,flightPad.Position,mode,world)
    if pilotHumanoid then pilotHumanoid:TakeDamage(18) end
   end
   state.planes[m]=nil;state.controls[p]=nil
  end)
  p.Character:PivotTo(cf*CFrame.new(0,4,0))
  seat:Sit(h)
 end)
 local function spawnCreature(i)
  local m=Instance.new("Model")
  m.Name="SubseaLeviathan_"..i;m.Parent=core
  local cf=CFrame.new(seaCenter+Vector3.new((i-2)*67,0, -20))
  local root=part(m,"CreatureCore",cf,Vector3.new(15,9,25),
   Color3.fromRGB(39,138,150),false)
  root.Shape=Enum.PartType.Ball;m.PrimaryPart=root
  m:SetAttribute("RealmKind","LEVIATHAN")
  m:SetAttribute("RealmHP",70)
  state.creatures[m]={at=cf.Position,lastHit=0}
  m.Destroying:Connect(function() state.creatures[m]=nil end)
 end
 for i=1,MAX_SEA_CREATURES do spawnCreature(i) end
 local function targetModel(hit)
  local m=hit and hit:FindFirstAncestorOfClass("Model")
  if not m or not m:IsDescendantOf(world) then return nil end
  if m:GetAttribute("RealmKind")=="LEVIATHAN" then return m end
  -- Existing LSS craft may be attacked in BR only (TEAM alliance is private).
  if mode~="BATTLE_ROYALE" then return nil end
  if m:GetAttribute("RealmKind")=="FIGHTER" and state.planes[m] then return m end
  local lss=world:FindFirstChild(LSS_NAME)
  if lss and m:IsDescendantOf(lss) and m.Name:match("_(%d+)$") then
   if m:GetAttribute("RealmHP")==nil then m:SetAttribute("RealmHP",100) end
   return m
  end
  return nil
 end
 local function attackLine(shooter,range,damage,element)
  local pivot=shooter:GetPivot()
  local exclude={shooter}
  -- Never allow a realm weapon to use a human avatar as a Roblox ray target.
  for _,pl in ipairs(Players:GetPlayers()) do
   if pl.Character then table.insert(exclude,pl.Character) end
  end
  local params=RaycastParams.new()
  params.FilterType=Enum.RaycastFilterType.Exclude
  params.FilterDescendantsInstances=exclude
  local result=Workspace:Raycast(pivot.Position+pivot.LookVector*9,
   pivot.LookVector*range,params)
  local target=result and targetModel(result.Instance)
  if target and target~=shooter then
   damageRealm(target,damage,element,target:GetAttribute("RealmKind")=="LEVIATHAN")
  end
 end
 local function fire(player,weapon)
  if not eligible(player,mode,world) then return end
  local now=os.clock()
  if state.divers[player] then
   if weapon~="HYDRO" then return end
   local root=player.Character:FindFirstChild("HumanoidRootPart")
   if not root or (root.Position-seaCenter).Magnitude>125 then return end
   local last=state.weapons[player] or {}
   if now-(last.HYDRO or -100)<HYDRO_INTERVAL then return end
   last.HYDRO=now;state.weapons[player]=last
   local best,bestDistance=nil,38
   for m in pairs(state.creatures) do
    if m.Parent then
     local d=(m:GetPivot().Position-root.Position).Magnitude
     if d<bestDistance then best,bestDistance=m,d end
    end
   end
   if best then
    local params=RaycastParams.new()
    params.FilterType=Enum.RaycastFilterType.Exclude
    params.FilterDescendantsInstances={player.Character}
    local delta=best:GetPivot().Position-root.Position
    local first=Workspace:Raycast(root.Position,delta,params)
    if not first or first.Instance:IsDescendantOf(best) then
     damageRealm(best,14,"WATER",true)
    end
   end
   return
  end
  -- HYDRO is diver-only. Reject it before the mounted cooldown lookup.
  if weapon=="HYDRO" then return end
  local model,kind=findCurrentMount(player)
  if not model then return end
  if (weapon=="GUN" and kind~="FIGHTER" and kind~="AIRSHIP")
   or (weapon=="BOMB" and kind~="FIGHTER")
   or (weapon=="CANNON" and kind~="SHIP")
   or (weapon=="BREATH" and kind~="SEA_BEAST" and kind~="SKY_BEAST") then return end
  local delays={GUN=GUN_INTERVAL,BOMB=BOMB_INTERVAL,CANNON=CANNON_INTERVAL,BREATH=BREATH_INTERVAL}
  local last=state.weapons[player] or {}
  if now-(last[weapon] or -100)<delays[weapon] then return end
  if weapon=="BOMB" and (model:GetAttribute("RealmBombs") or 0)<=0 then return end
  last[weapon]=now;state.weapons[player]=last
  if weapon=="BOMB" then
   model:SetAttribute("RealmBombs",model:GetAttribute("RealmBombs")-1)
   local impact=model:GetPivot().Position
   local query=RaycastParams.new()
   query.FilterType=Enum.RaycastFilterType.Exclude
   query.FilterDescendantsInstances={model,player.Character}
   local ray=Workspace:Raycast(impact,Vector3.new(0,-260,0),query)
   if ray then impact=ray.Position else impact=impact-Vector3.new(0,60,0) end
   local fx=part(core,"BombImpact",CFrame.new(impact),
    Vector3.new(26,2,26),Color3.fromRGB(245,167,65),false,.45)
   fx.CanQuery=false;Debris:AddItem(fx,.4)
   for m in pairs(state.creatures) do
    if m.Parent and (m:GetPivot().Position-impact).Magnitude<=27 then
     damageRealm(m,46,"BLAST",true)
    end
   end
   if mode=="BATTLE_ROYALE" then
    for other in pairs(state.planes) do
     if other~=model and other.Parent and (other:GetPivot().Position-impact).Magnitude<=27 then
      damageRealm(other,46,"BLAST",false)
     end
    end
    local lss=world:FindFirstChild(LSS_NAME)
    if lss then
     for _,other in ipairs(lss:GetChildren()) do
      if other:IsA("Model") and other~=model and other:FindFirstChild("PilotSeat")
       and other.Name:match("_(%d+)$")
       and (other:GetPivot().Position-impact).Magnitude<=27 then
       if other:GetAttribute("RealmHP")==nil then other:SetAttribute("RealmHP",100) end
       damageRealm(other,46,"BLAST",false)
      end
     end
    end
   end
  elseif weapon=="GUN" then attackLine(model,240,9,"KINETIC")
  elseif weapon=="CANNON" then attackLine(model,185,30,"KINETIC")
  else attackLine(model,125,20,"FIRE") end
 end
 local controlConnection
 controlConnection=remote.OnServerEvent:Connect(function(p,command,payload)
  if not state.active or not world.Parent or not eligible(p,mode,world) then return end
  if command=="FIRE" and typeof(payload)=="string" then
   if payload=="GUN" or payload=="BOMB" or payload=="CANNON"
    or payload=="BREATH" or payload=="HYDRO" then fire(p,payload) end
  elseif command=="FLIGHT" and typeof(payload)=="table" then
   local model,kind=findCurrentMount(p)
   if kind~="FIGHTER" then return end
   local pitch,roll=payload.pitch,payload.roll
   if typeof(pitch)~="number" or typeof(roll)~="number" then return end
   if pitch~=pitch or roll~=roll or math.abs(pitch)>1 or math.abs(roll)>1 then return end
   state.controls[p]={pitch=pitch,roll=roll,time=os.clock()}
  end
 end)
 local elapsed=0
 local heartbeat
 heartbeat=RunService.Heartbeat:Connect(function(dt)
  if not state.active or not world.Parent then
   if heartbeat then heartbeat:Disconnect() end
   return
  end
  elapsed+=dt
  if elapsed<SERVER_TICK then return end
  local step=math.min(elapsed,.22);elapsed=0
  local now=os.clock()
  local phase=math.floor((now-state.started)/WEATHER_PHASE_SECONDS)%4
  local weather=phase==3 and "THUNDER" or phase==2 and "RAIN"
   or phase==1 and "WIND" or "CLEAR"
  if state.weather~=weather then
   state.weather=weather;core:SetAttribute("RealmWeather",weather)
  end
  if weather=="THUNDER" and now-state.lastLightning>LIGHTNING_INTERVAL
   and not state.pendingLightning then
   state.pendingLightning=now+STORM_WARNING_SECONDS
   core:SetAttribute("LightningWarning",true)
  end
  if state.pendingLightning and now>=state.pendingLightning then
   state.lastLightning=now;state.pendingLightning=nil
   core:SetAttribute("LightningWarning",false)
   for model,pilot in pairs(state.planes) do
    if model.Parent and model:GetPivot().Position.Y>y+70
     and eligible(pilot,mode,world) then
     damageRealm(model,20,"LIGHTNING",false)
    end
   end
  end
  for model,pilot in pairs(state.planes) do
   if not model.Parent then state.planes[model]=nil
   elseif not eligible(pilot,mode,world) then model:Destroy()
   else
    local seat=model:FindFirstChild("PilotSeat")
    local h=pilot.Character:FindFirstChildOfClass("Humanoid")
    if not seat or seat.Occupant~=h then
     -- Returning on dismount avoids hanging unsupported pilots mid-air.
     safeReturn(pilot,flightPad.Position,mode,world)
     model:Destroy()
    else
     local cf=model:GetPivot()
     local c=state.controls[pilot]
     local fresh=c and now-c.time<.7
     local pitch=fresh and c.pitch or 0
     local roll=fresh and c.roll or 0
     local yaw=math.clamp(seat.SteerFloat,-1,1)
     local throttle=math.clamp(seat.ThrottleFloat,-1,1)
     local heading=cf*CFrame.Angles(-pitch*step*.8,-yaw*step*1.25,-roll*step*1.0)
     local speed=52+throttle*23
     if weather=="WIND" then speed*=.82 end
     if weather=="THUNDER" then speed*=.72 end
     local dest=heading.Position+heading.LookVector*(speed*step)
     dest=Vector3.new(math.clamp(dest.X,x-halfX,x+halfX),
      math.clamp(dest.Y,y+GROUND_FLIGHT_MIN,y+GROUND_FLIGHT_MAX),
      math.clamp(dest.Z,z-halfZ,z+halfZ))
     local delta=dest-cf.Position
     local params=RaycastParams.new()
     params.FilterType=Enum.RaycastFilterType.Exclude
     local ignore={model,pilot.Character,oceanSurface}
     local lss=world:FindFirstChild(LSS_NAME)
     if lss then
      for _,v in ipairs(lss:GetChildren()) do
       if v.Name=="COASTAL_WATER_VISUAL_ONLY" or v.Name=="OFFSHORE_NAVIGABLE_SEA_LANE" then
        table.insert(ignore,v)
       end
      end
     end
     params.FilterDescendantsInstances=ignore
     params.RespectCanCollide=true
     if delta.Magnitude>.02 and Workspace:Blockcast(
      cf,Vector3.new(19,5,19),delta,params)==nil then
      model:PivotTo(CFrame.new(dest)*heading.Rotation)
     end
    end
   end
  end
  for p in pairs(state.divers) do
   if not eligible(p,mode,world) then clearDive(p)
   else
    local root=p.Character:FindFirstChild("HumanoidRootPart")
    if not root or (root.Position-seaCenter).Magnitude>125 then clearDive(p) end
   end
  end
  for creature,data in pairs(state.creatures) do
   if creature.Parent then
    local nearest,distance=nil,90
    for p in pairs(state.divers) do
     if eligible(p,mode,world) then
      local root=p.Character:FindFirstChild("HumanoidRootPart")
      if root then
       local d=(root.Position-creature:GetPivot().Position).Magnitude
       if d<distance then distance,nearest=d,p end
      end
     end
    end
    if nearest then
     local root=nearest.Character:FindFirstChild("HumanoidRootPart")
     if root and distance>13 then
      local pos=creature:GetPivot().Position
      local towards=(root.Position-pos)
      if towards.Magnitude>.01 then
       local nextPos=pos+towards.Unit*math.min(7*step,distance-12)
       creature:PivotTo(CFrame.lookAt(nextPos,root.Position))
      end
     elseif root and now-data.lastHit>=2 then
      data.lastHit=now
      local h=nearest.Character:FindFirstChildOfClass("Humanoid")
      if h then h:TakeDamage(6) end -- new underwater neutral only, no KO/score
     end
    end
   end
  end
 end)
 world.Destroying:Connect(function()
  state.active=false
  if heartbeat then heartbeat:Disconnect() end
  if controlConnection then controlConnection:Disconnect() end
  for p in pairs(state.divers) do clearDive(p) end
  for p in pairs(state.controls) do state.controls[p]=nil end
  scenes[world]=nil
 end)
 print("[GQ8-REALM] realm combat live",mode,"aircraft, ship mounts, subsea, storms")
end
local lobby=Workspace:WaitForChild(LOBBY_NAME,20)
if not lobby then warn("[GQ8-REALM] V3 Host absent; no realm created");return end
local function watchWorld(world)
 if world.Name~="TEAM_Arena" and world.Name~="BATTLE_ROYALE_Arena" then return end
 task.defer(function()
  local floor=world:WaitForChild("TacticalBattlefield",8)
  if floor and world.Parent then install(world) end
 end)
end
for _,w in ipairs(lobby:GetChildren()) do watchWorld(w) end
lobby.ChildAdded:Connect(watchWorld)
