--!nonstrict
-- EGGRUMBLE: opt-in Studio-only land/sea/sky gameplay slice.
-- Installs as ONE extra ServerScriptService Script beside the 31 canonical
-- V3 sources. No replacement Game, Combat, Swarm, Remote, Store, score or KO.
-- Removing this Script rolls back 100% of these world additions.
local RunService = game:GetService("RunService")
if not RunService:IsStudio() then return end

local Players = game:GetService("Players")
local Debris = game:GetService("Debris")
local TweenService = game:GetService("TweenService")
local Workspace = game:GetService("Workspace")

local LOBBY = "EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW"
local NAME = "EGGRUMBLE_LAND_SEA_SKY_20261117"
local MAX_CRAFT = 4
local MAX_PARTS_PER_WORLD = 95
local MAX_LIVE_TRAPS = 2
local PUBLIC_TRAVEL_COOLDOWN = 2.5 -- voluntary shortcut cooldown
local MOVE_INTERVAL = 0.10
local TRAP_LIFETIME = 24
local VEHICLE_LIFETIME = 180
-- Studio-only stepped altitude controls: server-owned, no free client CFrame.
local FLIGHT_STEP = 18
local FLIGHT_VERTICAL_SPEED = 22
local FLIGHT_MIN_Y_ABOVE_GROUND = 28
local FLIGHT_MAX_Y_ABOVE_GROUND = 148
-- World-scoped offshore corridor, not Terrain water or an additional AI field.
local SEA_OUTER_LENGTH = 260
local SEA_ROUTE_HALF_WIDTH = 275
local SEA_OUTER_MARGIN = 32
-- Only confirmed neutral-KO combo milestones produce a short cosmetic surge.
-- Existing Swarm retains all actual spawn, damage, KO credit, and combo authority.
local MUSOU_COMBO_STEP = 12
local MUSOU_MAX_BURSTS_PER_SEC = 2
local MUSOU_EFFECT_TTL = 0.46
local MUSOU_BEACON_RADIUS = 155
-- Server Swarm may set Combo and NeutralKOs in either order.
-- A pulse requires a fresh increase of BOTH within the same short KO event.
local MUSOU_ATTRIBUTE_SYNC_SECONDS = 0.75
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
  -- GQ8_LSS_PROMPT_SERVER_SIGHT_20261118: forged Triggered events must
  -- obey the same reach and solid-wall visibility as an ordinary prompt.
  -- RequiresLineOfSight only controls client presentation, not server trust.
  if (root.Position-part.Position).Magnitude>q.MaxActivationDistance+1 then return end
  local head=ch:FindFirstChild("Head")
  local origin=(head and head:IsA("BasePart")) and head.Position or root.Position
  local direction=part.Position-origin
  if direction.Magnitude>0.1 then
   local params=RaycastParams.new()
   params.FilterType=Enum.RaycastFilterType.Exclude
   params.FilterDescendantsInstances={ch}
   params.RespectCanCollide=true
   local hit=Workspace:Raycast(origin,direction,params)
   -- A cockpit lever may be behind its own hull; only a confirmed pilot
   -- can activate it because the flight callback also checks seat.Occupant.
   if hit and hit.Instance~=part
    and not (part.Parent:IsA("Model") and hit.Instance:IsDescendantOf(part.Parent)) then return end
  end
  callback(player,hum,root)
 end)
 return q
end

local function matchHuman(player,mode,world,role)
 return world.Parent~=nil and world:IsDescendantOf(Workspace)
  and world.Parent.Name==LOBBY
  and world.Parent:FindFirstChild(world.Name)==world
  and player.Parent==Players and player:GetAttribute("EGGRUMBLE_QueuedMode")==mode
  -- A queue attribute alone is insufficient; require the current match castle.
  and world:FindFirstChild("Castle_"..tostring(player.UserId))~=nil
  and player:GetAttribute("EGGRUMBLE_Eliminated")~=true
  and (not role or player:GetAttribute("EGGRUMBLE_Role")==role)
end

-- GQ8_LSS_ORPHAN_CRAFT_OWNER_LIFECYCLE_20261118
-- Retire idle craft when its server-owned player is no longer alive/current.
-- An empty but otherwise valid craft stays available for a normal dismount.
local function currentCraftOwner(owner,mode,world,role)
 if not matchHuman(owner,mode,world,role) then return false end
 local ch=owner.Character
 local hum=ch and ch:FindFirstChildOfClass("Humanoid")
 return hum~=nil and hum.Health>0
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

-- Seat welds the live pilot to the assembly, but the Character is NOT
-- parented under the craft Model. Without this exception, Blockcast can
-- collide with the pilot's own body and prevent every boat/flight step.
-- Ignore only the server-confirmed seated pilot; other players and castle
-- solids remain eligible collision targets.
local function vehicleSweepExclusions(craft,water,offshoreWater,pilotCharacter)
 local ignore={craft,water,offshoreWater}
 if pilotCharacter then table.insert(ignore,pilotCharacter) end
 return ignore
end

-- GQ8_LSS_FULL_CRAFT_SWEEP_20261118: account for *all* physical
-- boat pontoons and aircraft wings, not just the 8x2x11 hull. A shared
-- envelope keeps up to four craft affordable on low-end devices.
local function craftSweepSize(flying)
 return flying and Vector3.new(24,8,19) or Vector3.new(18,8,19)
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
 local offshoreStartZ=z+halfZ-35
 local offshoreEndZ=z+halfZ+SEA_OUTER_LENGTH
 local skyZ=z-halfZ+160
 local cloudY=y+90
 local waterColor=Color3.fromRGB(51,167,194)
 local cloudColor=Color3.fromRGB(191,227,238)
 local goldColor=Color3.fromRGB(242,192,71)
 local vessels={}
 local traps={}
 local perUser={}
 local lastConstruct={}
 local liveParts=0
 local active=true
 -- GQ8_LSS_PUBLIC_TRAVEL_PACING_20261118_BEGIN
 -- Rate-limit voluntary public travel only; emergency rescue stays unlimited.
 local publicTravelAt={}
 local function publicTravel(player,at)
  if not active then return false end
  local now=os.clock()
  local prev=publicTravelAt[player.UserId]
  if prev and now-prev<PUBLIC_TRAVEL_COOLDOWN then return false end
  if not safeMove(player,at,mode,world) then return false end
  publicTravelAt[player.UserId]=now -- failed move does not consume cooldown
  return true
 end
 -- GQ8_LSS_PUBLIC_TRAVEL_PACING_20261118_END

 -- Live Instance budget, not a lifetime counter: destroyed crafts/traps return
 -- capacity for later rounds of building without a false budget crash.
 local function put(parent,name,cf,size,color,material,collide,alpha)
  assert(liveParts<MAX_PARTS_PER_WORLD,"EGGRUMBLE_LSS_PART_BUDGET")
  local part=block(parent,name,cf,size,color,material,collide,alpha)
  liveParts+=1
  part.Destroying:Connect(function()
   liveParts=math.max(0,liveParts-1)
  end)
  return part
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
 -- Extension crosses the original floor edge, without editing shared Terrain.
 -- A server-controlled sea craft can traverse this otherwise unfloored region.
 local offshoreWater=put(scene,"OFFSHORE_NAVIGABLE_SEA_LANE",
  CFrame.new(x,y+0.08,(offshoreStartZ+offshoreEndZ)/2),
  Vector3.new(SEA_ROUTE_HALF_WIDTH*2,0.14,offshoreEndZ-offshoreStartZ),
  waterColor,Enum.Material.Glass,false,.24)
 local offshorePads={}
 for side=-1,1,2 do
  local sx=x+side*195
  local pad=put(scene,"OffshoreSafeDock_"..tostring(side),
   CFrame.new(sx,y+1.65,z+halfZ+188),Vector3.new(30,2.6,27),
   Color3.fromRGB(161,118,77),Enum.Material.WoodPlanks,true,0)
  offshorePads[side]=pad
 end
 -- GQ470_FB011_FB015_LSS_SHORE_FOAM_FACETS_REAL69_20261121
 -- Six original, visual-only surf patches. Varied ellipses break up the
 -- six glaring rectangular stripes while preserving route and part budget.
 -- All foam stays shallow, noncolliding and outside the public land dock.
 for i=1,6 do
  local xi=x-265+(i-1)*106
  local sideways=if i%2==0 then 1 else -1
  local drift=math.sin(i*1.73)*1.55
  local surfAngle=math.rad(sideways*(7+(i%3)*4))
  local width=47+(i%3)*5
  local foam=put(scene,"ShoreFoam_"..i,
   CFrame.new(xi,y+0.21,shoreZ-63+drift)*CFrame.Angles(0,surfAngle,0),
   Vector3.new(width,.10,2.0+(i%2)*.45),
   if i%2==0 then Color3.fromRGB(190,225,228)
    else Color3.fromRGB(207,235,237),
   Enum.Material.SmoothPlastic,false,.33)
  -- Cylinder's local X axis is the length: flattened oval-like surf,
  -- not a thick pipe, and neither casts nor receives physics queries.
  foam.Shape=Enum.PartType.Cylinder
  foam.CastShadow=false
  foam.CanQuery=false
 end
 -- Dock markers form a safe, ground-based free path for every class.
 local landDock=put(scene,"PublicSeaDock",
  CFrame.new(x,y+0.9,shoreZ-92),Vector3.new(35,1.5,18),
  Color3.fromRGB(143,98,59),Enum.Material.WoodPlanks,true,0)
 local seaRaft=put(scene,"SeaTrapRecoveryRaft",
  CFrame.new(x+170,y+1.6,shoreZ+5),Vector3.new(20,2.5,20),
  Color3.fromRGB(202,172,100),Enum.Material.Wood,true,0)
 -- All seven roles can reach the offshore safe docks using public shuttles.
 -- This is teleport transport, NOT a claim of working player swimming.
 station("PublicOffshoreShuttle",Vector3.new(x,y+1,shoreZ-92),
  goldColor,"沖の桟橋へ","公共の海上シャトル",function(p)
   publicTravel(p,offshorePads[-1].Position+Vector3.new(0,4,0))
  end)
 for side=-1,1,2 do
  prompt(offshorePads[side],"海岸へ戻る","公共の帰還桟橋",function(p)
   publicTravel(p,landDock.Position+Vector3.new(0,4,0))
  end)
 end

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
    publicTravel(p,Vector3.new(sx,cloudY+5,skyZ))
   end)
  station("SkyReturn_"..tostring(side),
   Vector3.new(sx,cloudY+4,skyZ+22),goldColor,"地上へ","安全に帰還",
   function(p)
    publicTravel(p,groundLift.Position+Vector3.new(0,2,0))
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
  local flying=(kind=="AIRSHIP" or kind=="SKY_BEAST")
  -- Prevent partial craft construction when the bounded world is full.
  local craftPartCost=if flying then 6 else 4
  if liveParts+craftPartCost>MAX_PARTS_PER_WORLD then return end
  lastConstruct[player.UserId]=now
  local speed=if role=="BUILDER" then (if flying then 43 else 35)
   else (if flying then 48 else 39)
  local craft=Instance.new("Model")
  craft.Name=role.."_"..kind.."_"..tostring(player.UserId)
  craft.Parent=scene
  local tint=if role=="BUILDER" then Color3.fromRGB(238,160,70)
   else Color3.fromRGB(98,216,171)
  -- Forward sea throttle steers offshore, while aircraft retain prior orientation.
  local start=CFrame.new(at+Vector3.new(0,3,0))
   *(flying and CFrame.new() or CFrame.Angles(0,math.pi,0))
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
   flying=flying,speed=speed,at=at,alive=true,acc=0,
   targetY=math.clamp(start.Position.Y,
    y+FLIGHT_MIN_Y_ABOVE_GROUND,y+FLIGHT_MAX_Y_ABOVE_GROUND)}
  vessels[craft]=data;perUser[player.UserId]=data
  if flying then
   -- Two visible on-board proximity prompts work on desktop and touch clients.
   -- Only the actual current seat pilot can command a climb or descent.
   for _,ctrl in ipairs({
    {name="FlyAscendControl",sign=1,offset=-3,verb="上昇"},
    {name="FlyDescendControl",sign=-1,offset=3,verb="下降"},
   }) do
    local lever=put(craft,ctrl.name,start*CFrame.new(ctrl.offset,3,2),
     Vector3.new(1.5,1.5,1.5),goldColor,Enum.Material.Neon,false,0)
    prompt(lever,ctrl.verb,"飛行操縦",function(requester,h)
     if requester~=player or not matchHuman(requester,mode,world,role)
      or seat.Occupant~=h or not data.alive or not craft.Parent then return end
     data.targetY=math.clamp(data.targetY+ctrl.sign*FLIGHT_STEP,
      y+FLIGHT_MIN_Y_ABOVE_GROUND,y+FLIGHT_MAX_Y_ABOVE_GROUND)
     craft:SetAttribute("FlightTargetAltitude",
      math.floor(data.targetY-y+0.5))
    end)
   end
   craft:SetAttribute("FlightTargetAltitude",math.floor(data.targetY-y+0.5))
  end
  local character=player.Character
  local hum=character and character:FindFirstChildOfClass("Humanoid")
  if hum and hum.Health>0 then
   character:PivotTo(start*CFrame.new(0,4,0))
   seat:Sit(hum)
  end
  Debris:AddItem(craft,VEHICLE_LIFETIME)
  craft.Destroying:Connect(function()
   -- GQ8_LSS_CRAFT_EXPIRY_OFFSHORE_RESCUE_20261118
   -- Debris expiry can destroy a still-occupied sea craft beyond the floor.
   -- Recover only its previously server-verified, live and current pilot.
   if active and not data.flying then
    local pilot=data.lastPilot
    local ch=player.Character
    local root=ch and ch:FindFirstChild("HumanoidRootPart")
    if pilot and pilot.Parent==ch and pilot.Health>0 and root
     and matchHuman(player,mode,world,role)
     and (root.Position-craft:GetPivot().Position).Magnitude<28
     and craft:GetPivot().Position.Z>z+halfZ+10 then
     local standingOnDock=false
     for _,dock in pairs(offshorePads) do
      if math.abs(root.Position.X-dock.Position.X)<=dock.Size.X/2-2
       and math.abs(root.Position.Z-dock.Position.Z)<=dock.Size.Z/2-2 then
       standingOnDock=true
       break
      end
     end
     if not standingOnDock then
      safeMove(player,landDock.Position+Vector3.new(0,4,0),mode,world)
     end
    end
   end
   -- GQ8_LSS_FLIGHT_EXPIRY_SAFE_LANDING_20261118
   -- The 180s Debris timer also expires occupied flying craft, which lack
   -- the sea-only rescue above. Never drop the live, current seated pilot
   -- from high altitude; return to the existing grounded public dock.
   -- Do not move a dismounted player or a stale/dead/replaced character.
   if active and data.flying then
    local pilot=data.lastPilot
    local ch=player.Character
    local root=ch and ch:FindFirstChild("HumanoidRootPart")
    if pilot and pilot.Parent==ch and pilot.Health>0 and root
     and pilot.Sit and seat.Occupant==pilot
     and matchHuman(player,mode,world,role)
     and (root.Position-craft:GetPivot().Position).Magnitude<28
     and craft:GetPivot().Position.Y>y+FLIGHT_MIN_Y_ABOVE_GROUND-4 then
     safeMove(player,landDock.Position+Vector3.new(0,4,0),mode,world)
    end
   end
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
 -- GQ8_LSS_TRAP_OWNER_FAIRNESS_20261118_BEGIN
 -- Prevent a single caster from monopolizing the two global BR trap slots.
 -- Destroyed traps release their owner and global capacity immediately.
 local function canReserveTrapSlot(ownerId:number):boolean
  local live=0
  for part,previousOwner in pairs(traps) do
   if part.Parent then
    if previousOwner==ownerId then return false end
    live+=1
   end
  end
  return live<MAX_LIVE_TRAPS
 end
 -- GQ8_LSS_TRAP_OWNER_FAIRNESS_20261118_END

 -- GQ8_LSS_TRAP_SPATIAL_SLOTS_20261118_BEGIN
 -- Two separate 15-stud trap footprints: a second valid BR owner never
 -- deploys an invisible, overlapping duplicate at the first owner's spot.
 -- Slots are server-owned metadata, not client-selectable coordinates.
 local function chooseUnoccupiedTrapSlot()
  local occupied={}
  for part in pairs(traps) do
   if part.Parent then
    local slot=part:GetAttribute("LSS_TrapSlot")
    if slot==1 or slot==2 then occupied[slot]=true end
   end
  end
  if not occupied[1] then return 1 end
  if not occupied[2] then return 2 end
  return nil
 end
 -- GQ8_LSS_TRAP_SPATIAL_SLOTS_20261118_END

 -- TEAM team-authority is private inside Host, so BR ONLY until a proper
 -- same-session/team server API exists; never infer allies from cosmetics.
 station("PsychicTideTrapConsole",Vector3.new(x+48,y+1,shoreZ-92),
  Color3.fromRGB(174,105,227),"潮流ワナ","超能力者・BR専用",
  function(owner)
   if mode~="BATTLE_ROYALE" or not matchHuman(owner,mode,world,"TRAPPER") then return end
   if not canReserveTrapSlot(owner.UserId) or liveParts>=MAX_PARTS_PER_WORLD then return end
   local slot=chooseUnoccupiedTrapSlot()
   if not slot then return end
   -- 30 studs center separation leaves 15 studs clear between 15-wide traps.
   local anchor=Vector3.new(x+48+(slot-1)*30,y+3,shoreZ-57)
   local t=put(scene,"VISIBLE_PSYCHIC_SEA_TRAP",
    CFrame.new(anchor),Vector3.new(15,.8,15),
    Color3.fromRGB(187,93,241),Enum.Material.Neon,false,.22)
   t.CanTouch=true
   t:SetAttribute("LSS_TrapSlot",slot)
   traps[t]=owner.UserId
   t.Destroying:Connect(function() traps[t]=nil end)
   -- GQ8_LSS_PSYCHIC_OWNER_LIFECYCLE_BEGIN
   -- A defeated/disconnected caster cannot leave a live ocean warp behind.
   local casterCharacter=owner.Character
   local casterHumanoid=casterCharacter
    and casterCharacter:FindFirstChildOfClass("Humanoid")
   if not casterHumanoid or casterHumanoid.Health<=0 then
    t:Destroy()
    return
   end
   local diedConnection=casterHumanoid.Died:Connect(function()
    if t.Parent then t:Destroy() end
   end)
   local respawnConnection=owner.CharacterRemoving:Connect(function()
    if t.Parent then t:Destroy() end
   end)
   local eliminatedConnection=owner:GetAttributeChangedSignal(
    "EGGRUMBLE_Eliminated"):Connect(function()
    if owner:GetAttribute("EGGRUMBLE_Eliminated")==true and t.Parent then
     t:Destroy()
    end
   end)
   local ancestryConnection=owner.AncestryChanged:Connect(function()
    if not owner.Parent and t.Parent then t:Destroy() end
   end)
   t.Destroying:Connect(function()
    diedConnection:Disconnect()
    respawnConnection:Disconnect()
    eliminatedConnection:Disconnect()
    ancestryConnection:Disconnect()
   end)
   -- GQ8_LSS_PSYCHIC_OWNER_LIFECYCLE_END
   local fired=false
   t.Touched:Connect(function(other)
    if fired or not active or not t.Parent then return end
    if not matchHuman(owner,mode,world,"TRAPPER")
     or casterHumanoid.Health<=0 or owner.Character~=casterCharacter then
     t:Destroy()
     return
    end
    local ch=other:FindFirstAncestorOfClass("Model")
    local guest=ch and Players:GetPlayerFromCharacter(ch)
    if not guest or guest==owner or not matchHuman(guest,mode,world,nil) then return end
    -- Ignore expired avatar parts and dead players; one trap can only consume
    -- a living current character, not another character's residual collision.
    if guest.Character~=ch then return end
    local hum=ch:FindFirstChildOfClass("Humanoid")
    local root=ch:FindFirstChild("HumanoidRootPart")
    if not hum or hum.Health<=0 or not root
     or (root.Position-t.Position).Magnitude>12 then return end
    fired=true
    -- Keep the one-use trap available if the authoritative move is rejected.
    if not safeMove(guest,seaRaft.Position+Vector3.new(0,3,0),mode,world) then
     fired=false
     return
    end
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

 -- Source of truth: count only actual alive Humanoids created by the one Swarm.
 -- No local fake soldiers, score setters, new damage callbacks or spawn controls.
 local frontlineBillboard=Instance.new("BillboardGui")
 frontlineBillboard.Name="RealHordeFrontlineCounter"
 frontlineBillboard.AlwaysOnTop=false
 frontlineBillboard.Size=UDim2.fromOffset(250,58)
 frontlineBillboard.StudsOffset=Vector3.new(0,5,0)
 frontlineBillboard.MaxDistance=150
 frontlineBillboard.Parent=comboArena
 local frontlineText=Instance.new("TextLabel")
 frontlineText.BackgroundColor3=Color3.fromRGB(35,40,44)
 frontlineText.BackgroundTransparency=0.20
 frontlineText.TextColor3=Color3.fromRGB(248,233,157)
 frontlineText.Font=Enum.Font.GothamBold
 frontlineText.TextScaled=true
 frontlineText.Text="海岸の中立兵を探索中"
 frontlineText.Size=UDim2.fromScale(1,1)
 frontlineText.Parent=frontlineBillboard

 -- Attribute ordering is not authoritative, but both original server
 -- counters are. Requiring observed increases of both prevents fake rings
 -- from unrelated Combo changes or stale KO after a round reset.
 local function musouConfirmedMilestone(ko,combo,koAt,comboAt,shown,now)
  if typeof(ko)~="number" or typeof(combo)~="number" then return false end
  if ko<0 or combo<MUSOU_COMBO_STEP or combo>ko
   or combo%MUSOU_COMBO_STEP~=0 or shown==combo then return false end
  if typeof(koAt)~="number" or typeof(comboAt)~="number" then return false end
  if math.abs(koAt-comboAt)>MUSOU_ATTRIBUTE_SYNC_SECONDS then return false end
  if now-math.max(koAt,comboAt)>MUSOU_ATTRIBUTE_SYNC_SECONDS then return false end
  return true
 end
 local lastNeutralCount={}
 local lastComboCount={}
 local lastKOAdvanceAt={}
 local lastComboAdvanceAt={}
 local lastShownCombo={}
 local lastSurgeAt={}
 local combatConnections={}
 local burstSecond=-1
 local burstsThisSecond=0
 local function onCombatCombo(player)
  if not active or not matchHuman(player,mode,world,nil) then return end
  local ko=player:GetAttribute("EGGRUMBLE_NeutralKOs")
  local combo=player:GetAttribute("EGGRUMBLE_Combo")
  if typeof(ko)~="number" or typeof(combo)~="number" then return end
  local userId=player.UserId
  local oldKO=lastNeutralCount[userId] or 0
  local oldCombo=lastComboCount[userId] or 0
  local now=os.clock()
  if ko<oldKO or combo<oldCombo then
   lastKOAdvanceAt[userId]=nil
   lastComboAdvanceAt[userId]=nil
   lastShownCombo[userId]=nil
  end
  if ko>oldKO then lastKOAdvanceAt[userId]=now end
  if combo>oldCombo then lastComboAdvanceAt[userId]=now end
  lastNeutralCount[userId]=ko
  lastComboCount[userId]=combo
  if not musouConfirmedMilestone(ko,combo,lastKOAdvanceAt[userId],
   lastComboAdvanceAt[userId],lastShownCombo[userId],now) then return end
  local ch=player.Character
  local root=ch and ch:FindFirstChild("HumanoidRootPart")
  local hum=ch and ch:FindFirstChildOfClass("Humanoid")
  if not root or not hum or hum.Health<=0 then return end
  if (root.Position-comboArena.Position).Magnitude>MUSOU_BEACON_RADIUS then return end
  local second=math.floor(now)
  if burstSecond~=second then burstSecond=second;burstsThisSecond=0 end
  if burstsThisSecond>=MUSOU_MAX_BURSTS_PER_SEC then return end
  if now-(lastSurgeAt[player.UserId] or -100)<0.8 then return end
  burstsThisSecond+=1
  lastSurgeAt[userId]=now
  lastShownCombo[userId]=combo
  local wave=Instance.new("Part")
  wave.Name="EGGRUMBLE_REAL_KO_MUSOU_WAVE"
  wave.Shape=Enum.PartType.Ball
  wave.Size=Vector3.new(1,.18,1)
  wave.CFrame=CFrame.new(root.Position-Vector3.new(0,2.4,0))
  wave.Anchored=true
  wave.CanCollide=false;wave.CanTouch=false;wave.CanQuery=false
  wave.CastShadow=false;wave.Material=Enum.Material.Neon
  wave.Color=Color3.fromRGB(255,188,73)
  wave.Transparency=.34
  wave.Parent=scene
  TweenService:Create(wave,
   TweenInfo.new(.34,Enum.EasingStyle.Quad,Enum.EasingDirection.Out),
   {Size=Vector3.new(14,.26,14),Transparency=1}):Play()
  Debris:AddItem(wave,MUSOU_EFFECT_TTL)
 end
 local function unwatchCombo(player)
  local pair=combatConnections[player]
  if pair then
   for _,conn in ipairs(pair) do conn:Disconnect() end
   combatConnections[player]=nil
  end
  local userId=player.UserId
  lastNeutralCount[userId]=nil
  lastComboCount[userId]=nil
  lastKOAdvanceAt[userId]=nil
  lastComboAdvanceAt[userId]=nil
  lastShownCombo[userId]=nil
  lastSurgeAt[userId]=nil
 end
 local function watchCombo(player)
  if combatConnections[player] then return end
  local userId=player.UserId
  lastNeutralCount[userId]=player:GetAttribute("EGGRUMBLE_NeutralKOs") or 0
  lastComboCount[userId]=player:GetAttribute("EGGRUMBLE_Combo") or 0
  combatConnections[player]={
   player:GetAttributeChangedSignal("EGGRUMBLE_Combo"):Connect(
    function() onCombatCombo(player) end),
   player:GetAttributeChangedSignal("EGGRUMBLE_NeutralKOs"):Connect(
    function() onCombatCombo(player) end),
  }
 end
 local entered=Players.PlayerAdded:Connect(watchCombo)
 local exited=Players.PlayerRemoving:Connect(unwatchCombo)
 for _,player in ipairs(Players:GetPlayers()) do watchCombo(player) end

 local hordeSampleElapsed=0
 local elapsed=0
 local heartbeat
 heartbeat=RunService.Heartbeat:Connect(function(dt)
  if not active or not world.Parent or not scene.Parent then
   if heartbeat then heartbeat:Disconnect() end
   return
  end
  hordeSampleElapsed+=dt
  if hordeSampleElapsed>=1 then
   hordeSampleElapsed=0
   local soldiers=world:FindFirstChild("NeutralHorde")
   local count=0
   if soldiers then
    for _,model in ipairs(soldiers:GetChildren()) do
     if model:IsA("Model") and model:GetAttribute("EGGRUMBLE_Neutral")==true
      and model.PrimaryPart then
      local h=model:FindFirstChildOfClass("Humanoid")
      if h and h.Health>0
       and (model.PrimaryPart.Position-comboArena.Position).Magnitude<=MUSOU_BEACON_RADIUS then
       count+=1
      end
     end
    end
   end
   frontlineText.Text="海岸の中立兵 "..tostring(count).." 体 | 12連撃で波動！"
  end
  elapsed+=dt
  if elapsed<MOVE_INTERVAL then return end
  local step=math.min(elapsed,.2);elapsed=0
  for craft,v in pairs(vessels) do
   if not craft.Parent or not v.alive then
    vessels[craft]=nil
   elseif not currentCraftOwner(v.owner,mode,world,v.role) then
    -- Clear the previously-seated rider before Destroying: an eliminated or
    -- disconnected owner must not trigger the healthy offshore rescue.
    v.lastPilot=nil
    craft:Destroy()
   else
    local hum=v.seat.Occupant
    local driver=hum and Players:GetPlayerFromCharacter(hum.Parent)
    if not hum and v.lastPilot then
     local departed=v.lastPilot
     v.lastPilot=nil
     local ch=v.owner.Character
     local root=ch and ch:FindFirstChild("HumanoidRootPart")
     local dismountOnDock=false
     if root then
      for _,dock in pairs(offshorePads) do
       -- A real landing on a collision pad is not a void dismount.
       if math.abs(root.Position.X-dock.Position.X)<=dock.Size.X/2-2
        and math.abs(root.Position.Z-dock.Position.Z)<=dock.Size.Z/2-2 then
        dismountOnDock=true
        break
       end
      end
     end
     if not v.flying and ch and departed.Parent==ch and root
      and not dismountOnDock
      and craft:GetPivot().Position.Z>z+halfZ+10
      and (root.Position-craft:GetPivot().Position).Magnitude<28
      and matchHuman(v.owner,mode,world,v.role) then
      -- A sea pilot who dismounts offshore is rescued, never dropped into void.
      safeMove(v.owner,landDock.Position+Vector3.new(0,4,0),mode,world)
      craft:Destroy()
     end
    end
    if hum and (driver~=v.owner or not matchHuman(v.owner,mode,world,v.role)
      or hum.Health<=0) then
     hum.Sit=false
    elseif hum and driver==v.owner then
     v.lastPilot=hum
     local throttle=math.clamp(v.seat.ThrottleFloat,-1,1)
     local steer=math.clamp(v.seat.SteerFloat,-1,1)
     local cf=craft:GetPivot()*CFrame.Angles(0,-steer*step*1.25,0)
     local displacement=cf.LookVector*throttle*v.speed*step
     local rise=if v.flying then math.clamp(
       v.targetY-cf.Position.Y,-FLIGHT_VERTICAL_SPEED*step,
       FLIGHT_VERTICAL_SPEED*step) else 0
     local point=cf.Position+displacement+Vector3.new(0,rise,0)
     local lateralBound=if v.flying then halfX-25
      else math.min(SEA_ROUTE_HALF_WIDTH,halfX-25)
     local minTravelZ=if v.flying then z-halfZ+25 else shoreZ-90
     local maxTravelZ=if v.flying then z+halfZ-25
      else offshoreEndZ-SEA_OUTER_MARGIN
     point=Vector3.new(
      math.clamp(point.X,x-lateralBound,x+lateralBound),
      v.flying and math.clamp(point.Y,
       y+FLIGHT_MIN_Y_ABOVE_GROUND,y+FLIGHT_MAX_Y_ABOVE_GROUND) or y+5,
      math.clamp(point.Z,minTravelZ,maxTravelZ))
     local delta=point-cf.Position
     local targetCF=CFrame.new(point)*cf.Rotation
     local sweepSize=craftSweepSize(v.flying)
     local exclude=vehicleSweepExclusions(
      craft,water,offshoreWater,hum.Parent)
     local allowed=true
     if delta.Magnitude>.1 then
      local params=RaycastParams.new()
      params.FilterType=Enum.RaycastFilterType.Exclude
      params.FilterDescendantsInstances=exclude
      params.RespectCanCollide=true
      -- Sweep the full boat/wing footprint along the requested path.
      allowed=Workspace:Blockcast(cf,sweepSize,delta,params)==nil
     end
     if allowed then
      -- Rotation-only turns have zero translation, so Blockcast alone
      -- cannot catch wings clipping a nearby wall at the final yaw.
      local overlap=OverlapParams.new()
      overlap.FilterType=Enum.RaycastFilterType.Exclude
      overlap.FilterDescendantsInstances=exclude
      overlap.RespectCanCollide=true
      overlap.MaxParts=1
      allowed=#Workspace:GetPartBoundsInBox(targetCF,sweepSize,overlap)==0
     end
     if allowed then
      craft:PivotTo(targetCF)
     elseif v.flying then
      -- An obstructed climb must stop requesting an unsafe destination.
      v.targetY=cf.Position.Y
     end
    end
   end
  end
 end)
 world.Destroying:Connect(function()
  active=false
  if heartbeat then heartbeat:Disconnect() end
  entered:Disconnect()
  exited:Disconnect()
  for player in pairs(combatConnections) do unwatchCombo(player) end
  table.clear(combatConnections)
  table.clear(lastNeutralCount)
  table.clear(lastComboCount)
  table.clear(lastKOAdvanceAt)
  table.clear(lastComboAdvanceAt)
  table.clear(lastShownCombo)
  table.clear(lastSurgeAt)
  table.clear(publicTravelAt)
  for _,v in pairs(vessels) do v.alive=false end
  scenes[world]=nil
 end)
 print("[EGGRUMBLE-LSS] Studio-only world slice ready",mode,"live parts",liveParts,
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
