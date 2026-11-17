--!nonstrict
-- EGGRUMBLE: opt-in Studio-only land/sea/sky gameplay slice.
-- Installs as ONE extra ServerScriptService Script beside the 31 canonical
-- V3 sources. No replacement Game, Combat, Swarm, Remote, Store, score or KO.
-- Removing this Script rolls back 100% of these world additions.
local RunService = game:GetService("RunService")
if not RunService:IsStudio() then return end

local Players = game:GetService("Players")
local Debris = game:GetService("Debris")
local Workspace = game:GetService("Workspace")

local LOBBY = "EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW"
local NAME = "EGGRUMBLE_LAND_SEA_SKY_20261117"
local MAX_CRAFT = 4
local MAX_PARTS_PER_WORLD = 95
local MAX_LIVE_TRAPS = 2
local MOVE_INTERVAL = 0.10
local TRAP_LIFETIME = 24
local VEHICLE_LIFETIME = 180
local UP = Vector3.new(0,1,0)
local scenes = {}

local function block(parent,name,cf,size,color,material,collide,transparency)
 local p = Instance.new("Part")
 p.Name=name; p.Size=size; p.CFrame=cf; p.Anchored=true
 p.CanCollide=collide; p.CanTouch=collide
 p.Color=color; p.Material=material; p.Transparency=transparency or 0
 p.TopSurface=Enum.SurfaceType.Smooth
 p.BottomSurface=Enum.SurfaceType.Smooth
 p.Parent=parent
 return p
end

local function prompt(part,verb,object,callback)
 local q=Instance.new("ProximityPrompt")
 q.Name="EGGRUMBLE_SeaSky_Use"
 q.ActionText=verb; q.ObjectText=object
 q.HoldDuration=0.25; q.MaxActivationDistance=14
 q.RequiresLineOfSight=true; q.Parent=part
 q.Triggered:Connect(function(player)
  local ch=player.Character
  local root=ch and ch:FindFirstChild("HumanoidRootPart")
  local hum=ch and ch:FindFirstChildOfClass("Humanoid")
  -- Client activation range is NOT authoritative; check it server-side.
  if not root or not hum or hum.Health<=0 then return end
  if (root.Position-part.Position).Magnitude>17 then return end
  callback(player,hum,root)
 end)
 return q
end

local function matchHuman(player,mode,world,role)
 return world.Parent~=nil and world:IsDescendantOf(Workspace)
  and player.Parent==Players and player:GetAttribute("EGGRUMBLE_QueuedMode")==mode
  and player:GetAttribute("EGGRUMBLE_Eliminated")~=true
  and (not role or player:GetAttribute("EGGRUMBLE_Role")==role)
end

local function safeMove(player,at,mode,world)
 if not matchHuman(player,mode,world,nil) then return false end
 local ch=player.Character
 local root=ch and ch:FindFirstChild("HumanoidRootPart")
 local hum=ch and ch:FindFirstChildOfClass("Humanoid")
 if not root or not hum or hum.Health<=0 then return false end
 -- A voluntary move may dismount, never changes HP, coins, eggs or scores.
 hum.Sit=false
 ch:PivotTo(CFrame.new(at+Vector3.new(0,4,0)))
 return true
end

local function install(world)
 if scenes[world] or not world:IsA("Folder") then return end
 local mode=if world.Name=="TEAM_Arena" then "TEAM"
  elseif world.Name=="BATTLE_ROYALE_Arena" then "BATTLE_ROYALE" else nil
 if not mode then return end
 local floor=world:FindFirstChild("TacticalBattlefield")
 if not floor or not floor:IsA("BasePart") then return end
 if floor.Size.X<600 or floor.Size.Z<700 then return end
 scenes[world]=true

 local scene=Instance.new("Folder")
 scene.Name=NAME; scene.Parent=world
 local y=floor.Position.Y+floor.Size.Y/2
 local x=floor.Position.X
 local z=floor.Position.Z
 local halfX=floor.Size.X/2-45
 local halfZ=floor.Size.Z/2-45
 local shoreZ=z+halfZ-85
 local skyZ=z-halfZ+160
 local cloudY=y+90
 local waterColor=Color3.fromRGB(51,167,194)
 local cloudColor=Color3.fromRGB(191,227,238)
 local goldColor=Color3.fromRGB(242,192,71)
 local vessels={}
 local traps={}
 local perUser={}
 local lastConstruct={}
 local totalParts=0
 local active=true

 local function put(parent,name,cf,size,color,material,collide,alpha)
  totalParts+=1
  assert(totalParts<=MAX_PARTS_PER_WORLD,"EGGRUMBLE_LSS_PART_BUDGET")
  return block(parent,name,cf,size,color,material,collide,alpha)
 end
 local function station(name,at,color,verb,description,cb)
  local p=put(scene,name,CFrame.new(at),Vector3.new(9,2,9),color,
   Enum.Material.Neon,true,0.10)
  prompt(p,verb,description,function(p2,h,r)
   if active and matchHuman(p2,mode,world,nil) then cb(p2,h,r) end
  end)
  return p
 end

 -- All players retain the original three land routes, castle, eggs and horde.
 -- The ocean is an additive visual water lane above existing solid ground:
 -- nobody is forced to swim and no Terrain in another match is overwritten.
 local water=put(scene,"COASTAL_WATER_VISUAL_ONLY",
  CFrame.new(x,y+0.08,shoreZ),Vector3.new(math.min(650,floor.Size.X-95),0.14,180),
  waterColor,Enum.Material.Glass,false,.28)
 for i=1,6 do
  local xi=x-265+(i-1)*106
  local foam=put(scene,"ShoreFoam_"..i,
   CFrame.new(xi,y+0.21,shoreZ-63),Vector3.new(55,.10,2.3),
   Color3.fromRGB(225,247,248),Enum.Material.SmoothPlastic,false,.19)
 end
 -- Dock markers form a safe, ground-based free path for every class.
 local landDock=put(scene,"PublicSeaDock",
  CFrame.new(x,y+0.9,shoreZ-92),Vector3.new(35,1.5,18),
  Color3.fromRGB(143,98,59),Enum.Material.WoodPlanks,true,0)
 local seaRaft=put(scene,"SeaTrapRecoveryRaft",
  CFrame.new(x+170,y+1.6,shoreZ+5),Vector3.new(20,2.5,20),
  Color3.fromRGB(202,172,100),Enum.Material.Wood,true,0)

 for side=-1,1,2 do
  local sx=x+side*220
  local skyIsland=put(scene,"SkyIsland_"..tostring(side),
   CFrame.new(sx,cloudY,skyZ),Vector3.new(86,5,69),
   cloudColor,Enum.Material.Slate,true,0)
  put(scene,"SkyIslandGrass_"..tostring(side),
   CFrame.new(sx,cloudY+2.7,skyZ),Vector3.new(80,.6,63),
   Color3.fromRGB(111,177,133),Enum.Material.Grass,true,0)
  local groundLift=station("PublicCloudLift_"..tostring(side),
   Vector3.new(sx,y+1,skyZ),goldColor,"空島へ","みんなの雲リフト",
   function(p)
    safeMove(p,Vector3.new(sx,cloudY+5,skyZ),mode,world)
   end)
  station("SkyReturn_"..tostring(side),
   Vector3.new(sx,cloudY+4,skyZ+22),goldColor,"地上へ","安全に帰還",
   function(p)
    safeMove(p,groundLift.Position+Vector3.new(0,2,0),mode,world)
   end)
 end

 -- Vehicles use Roblox VehicleSeat standard mobile/keyboard throttle + steer.
 -- Server controls PivotTo; no user Remote or free-form client CFrame accepted.
 local function makeRide(player,role,kind,at)
  if not matchHuman(player,mode,world,role) then return end
  if perUser[player.UserId] and perUser[player.UserId].model.Parent then return end
  local count=0
  for _,v in pairs(vessels) do if v.model.Parent then count+=1 end end
  if count>=MAX_CRAFT then return end
  local now=os.clock()
  if now-(lastConstruct[player.UserId] or -100)<12 then return end
  lastConstruct[player.UserId]=now
  local flying=(kind=="AIRSHIP" or kind=="SKY_BEAST")
  local speed=if role=="BUILDER" then (if flying then 43 else 35)
   else (if flying then 48 else 39)
  local craft=Instance.new("Model")
  craft.Name=role.."_"..kind.."_"..tostring(player.UserId)
  craft.Parent=scene
  local tint=if role=="BUILDER" then Color3.fromRGB(238,160,70)
   else Color3.fromRGB(98,216,171)
  local start=CFrame.new(at+Vector3.new(0,3,0))
  local hull=put(craft,"Hull",start,Vector3.new(9,2.3,13),tint,
   Enum.Material.SmoothPlastic,true,0)
  hull.Shape=if role=="BEAST" then Enum.PartType.Ball else Enum.PartType.Block
  local seat=Instance.new("VehicleSeat")
  seat.Name="PilotSeat";seat.Size=Vector3.new(4,1,4)
  seat.CFrame=start*CFrame.new(0,2.2,0)
  seat.Anchored=true;seat.CanCollide=true;seat.Parent=craft
  craft.PrimaryPart=hull
  put(craft,"Bow",start*CFrame.new(0,0,-6),Vector3.new(3,2,5),
   tint,Enum.Material.SmoothPlastic,false,0)
  if flying then
   for side=-1,1,2 do
    put(craft,"Wing_"..tostring(side),start*CFrame.new(side*7,0,0),
     Vector3.new(9,.6,5),cloudColor,Enum.Material.SmoothPlastic,false,.06)
   end
  else
   for side=-1,1,2 do
    put(craft,"Pontoon_"..tostring(side),start*CFrame.new(side*6,-.3,2),
     Vector3.new(3,2,10),waterColor,Enum.Material.SmoothPlastic,false,0)
   end
  end
  local data={model=craft,seat=seat,owner=player,role=role,
   flying=flying,speed=speed,at=at,alive=true,acc=0}
  vessels[craft]=data;perUser[player.UserId]=data
  local character=player.Character
  local hum=character and character:FindFirstChildOfClass("Humanoid")
  if hum and hum.Health>0 then
   character:PivotTo(start*CFrame.new(0,4,0))
   seat:Sit(hum)
  end
  Debris:AddItem(craft,VEHICLE_LIFETIME)
  craft.Destroying:Connect(function()
   data.alive=false
   vessels[craft]=nil
   if perUser[player.UserId]==data then perUser[player.UserId]=nil end
  end)
 end

 local seaSpawn=Vector3.new(x-120,y+2,shoreZ+15)
 local skySpawn=Vector3.new(x+220,cloudY+6,skyZ)
 station("ScientistShipyard",Vector3.new(x-123,y+1,shoreZ-92),
  goldColor,"造船","マッドサイエンティスト専用",
  function(p)makeRide(p,"BUILDER","SEA_BOAT",seaSpawn)end)
 station("BeastSeaNest",Vector3.new(x+122,y+1,shoreZ-92),
  Color3.fromRGB(102,224,153),"海獣召喚","魔獣使い専用",
  function(p)makeRide(p,"BEAST","SEA_BEAST",seaSpawn+Vector3.new(70,0,0))end)
 station("ScientistFlightLab",Vector3.new(x-220,cloudY+4,skyZ-17),
  goldColor,"飛行艇を造る","マッドサイエンティスト専用",
  function(p)makeRide(p,"BUILDER","AIRSHIP",Vector3.new(x-220,cloudY+5,skyZ-20))end)
 station("BeastSkyNest",Vector3.new(x+220,cloudY+4,skyZ-17),
  Color3.fromRGB(102,224,153),"飛行獣召喚","魔獣使い専用",
  function(p)makeRide(p,"BEAST","SKY_BEAST",skySpawn)end)

 -- A visible psychic snare, not an unavoidable or lethal teleport.
 -- TEAM team-authority is private inside Host, so BR ONLY until a proper
 -- same-session/team server API exists; never infer allies from cosmetics.
 station("PsychicTideTrapConsole",Vector3.new(x+48,y+1,shoreZ-92),
  Color3.fromRGB(174,105,227),"潮流ワナ","超能力者・BR専用",
  function(owner)
   if mode~="BATTLE_ROYALE" or not matchHuman(owner,mode,world,"TRAPPER") then return end
   local number=0
   for part in pairs(traps) do if part.Parent then number+=1 end end
   if number>=MAX_LIVE_TRAPS then return end
   local anchor=Vector3.new(x+48,y+3,shoreZ-57)
   local t=put(scene,"VISIBLE_PSYCHIC_SEA_TRAP",
    CFrame.new(anchor),Vector3.new(15,.8,15),
    Color3.fromRGB(187,93,241),Enum.Material.Neon,false,.22)
   t.CanTouch=true
   traps[t]=true
   local fired=false
   t.Touched:Connect(function(other)
    if fired or not active or not t.Parent then return end
    local ch=other:FindFirstAncestorOfClass("Model")
    local guest=ch and Players:GetPlayerFromCharacter(ch)
    if not guest or guest==owner or not matchHuman(guest,mode,world,nil) then return end
    local root=ch:FindFirstChild("HumanoidRootPart")
    if not root or (root.Position-t.Position).Magnitude>12 then return end
    fired=true
    safeMove(guest,seaRaft.Position+Vector3.new(0,3,0),mode,world)
    t:Destroy()
   end)
   Debris:AddItem(t,TRAP_LIFETIME)
  end)

 -- No new soldiers or duplicate KO writer. Real neutral hordes remain owned by
 -- the existing one EGGRUMBLE_SwarmCombat and retain its 4HP, budgets and credit.
 local comboArena=put(scene,"NeutralHordeCoastBeacon",
  CFrame.new(x,y+1,shoreZ-162),Vector3.new(14,2,14),
  Color3.fromRGB(232,101,84),Enum.Material.Neon,false,.28)
 comboArena.CanTouch=false

 local elapsed=0
 local heartbeat
 heartbeat=RunService.Heartbeat:Connect(function(dt)
  if not active or not world.Parent or not scene.Parent then
   if heartbeat then heartbeat:Disconnect() end
   return
  end
  elapsed+=dt
  if elapsed<MOVE_INTERVAL then return end
  local step=math.min(elapsed,.2);elapsed=0
  for craft,v in pairs(vessels) do
   if not craft.Parent or not v.alive then
    vessels[craft]=nil
   else
    local hum=v.seat.Occupant
    local driver=hum and Players:GetPlayerFromCharacter(hum.Parent)
    if hum and (driver~=v.owner or not matchHuman(v.owner,mode,world,v.role)
      or hum.Health<=0) then
     hum.Sit=false
    elseif hum and driver==v.owner then
     local throttle=math.clamp(v.seat.ThrottleFloat,-1,1)
     local steer=math.clamp(v.seat.SteerFloat,-1,1)
     local cf=craft:GetPivot()*CFrame.Angles(0,-steer*step*1.25,0)
     local displacement=cf.LookVector*throttle*v.speed*step
     local point=cf.Position+displacement
     point=Vector3.new(
      math.clamp(point.X,x-halfX+25,x+halfX-25),
      v.flying and cloudY+8 or y+5,
      math.clamp(point.Z,z-halfZ+25,z+halfZ-25))
     local delta=point-cf.Position
     local allowed=true
     if delta.Magnitude>.1 then
      local params=RaycastParams.new()
      params.FilterType=Enum.RaycastFilterType.Exclude
      params.FilterDescendantsInstances={craft,water}
      params.RespectCanCollide=true
      -- Server wall check; flying craft cannot ghost through solid sky islands.
      allowed=Workspace:Blockcast(v.model.PrimaryPart.CFrame,
       Vector3.new(8,2,11),delta,params)==nil
     end
     if allowed then
      craft:PivotTo(CFrame.new(point)*cf.Rotation)
     end
    end
   end
  end
 end)
 world.Destroying:Connect(function()
  active=false
  if heartbeat then heartbeat:Disconnect() end
  for _,v in pairs(vessels) do v.alive=false end
  scenes[world]=nil
 end)
 print("[EGGRUMBLE-LSS] Studio-only world slice ready",mode,"parts",totalParts,
  "ground/sea/sky; original Swarm preserved")
end

local function watchWorld(world)
 if not world:IsA("Folder") then return end
 if world.Name~="TEAM_Arena" and world.Name~="BATTLE_ROYALE_Arena" then return end
 task.defer(function()
  local floor=world:WaitForChild("TacticalBattlefield",8)
  if floor and world.Parent then install(world) end
 end)
end

local lobby=Workspace:WaitForChild(LOBBY,20)
if not lobby then
 warn("[EGGRUMBLE-LSS] Original V3 Host absent; no scene created")
 return
end
for _,world in ipairs(lobby:GetChildren()) do watchWorld(world) end
lobby.ChildAdded:Connect(watchWorld)
