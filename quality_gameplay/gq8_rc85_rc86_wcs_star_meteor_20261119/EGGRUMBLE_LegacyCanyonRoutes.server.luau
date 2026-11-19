--!strict
-- GQ8_RC85_RC86_WCS_STARRY_METEOR_REAL67_20261119
-- Port ONLY original RC85/86 WCS_F01_C01 physical canyon and Moguron gate.
-- ORIGINAL Starfall10 (#879) and MeteorFourth (#884) are ALREADY in V3 Realm;
-- both reused at the same canyon, never cloned.
-- ONE existing V3 TEAM/BR world, one *environment* Script,
-- zero Game/HP/score/combat/egg/Remote/Store/paid authority. Studio only.
-- Original provenance: original 85-script Place artifact 14158848286.
local RunService=game:GetService("RunService")
if not RunService:IsStudio() then return end
local Workspace=game:GetService("Workspace")
local Players=game:GetService("Players")
local LOBBY="EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW"
local FEATURE="GQ8_RC85_WCS_REUSE_STAR_METEOR_REAL67_20261119"
local installed:{[Instance]:boolean}={}
local boundLobby:{[Instance]:boolean}={}

local function create(parent:Instance,name:string,size:Vector3,cf:CFrame,
 color:Color3,material:Enum.Material,collide:boolean,transparency:number?):Part
 local p=Instance.new("Part")
 p.Name=name;p.Size=size;p.CFrame=cf
 p.Anchored=true;p.CanTouch=false;p.CanQuery=collide;p.CanCollide=collide
 p.Color=color;p.Material=material;p.Transparency=transparency or 0
 p.TopSurface=Enum.SurfaceType.Smooth;p.BottomSurface=Enum.SurfaceType.Smooth
 p.Parent=parent
 return p
end
local function addPrompt(part:BasePart,text:string,object:string,
 callback:(Player)->()):ProximityPrompt
 local p=Instance.new("ProximityPrompt")
 p.Name="GQ8_OriginalLegacyRoutePrompt"
 p.ActionText=text;p.ObjectText=object
 p.HoldDuration=.45;p.MaxActivationDistance=12
 p.RequiresLineOfSight=true;p.Parent=part
 p.Triggered:Connect(callback)
 return p
end
local function setup(arena:Instance,mode:string,lobby:Instance,floor:BasePart)
 if installed[arena] or arena.Parent~=lobby then return end
 if floor.Size.X<750 or floor.Size.Z<900 or not floor.Anchored or not floor.CanCollide then return end
 if arena:FindFirstChild("GQ8_RC85_WCS_StarMeteor") then return end
 installed[arena]=true
 local stage=Instance.new("Model")
 stage.Name="GQ8_RC85_WCS_StarMeteor"
 stage:SetAttribute("FeatureId",FEATURE)
 stage:SetAttribute("GameOwner","EXISTING_EGGRUMBLE_LobbyCastleModesPreview")
 stage:SetAttribute("StageMode",mode)
 stage:SetAttribute("LegacyFlags","WCS_F01_C01")
 stage:SetAttribute("ExistingStarSource","GQ8_RC86_STARRY_PATH_SINGLE_REALM_REAL66_20261119")
 stage:SetAttribute("NoCombatStoreScoreRemotes",true)
 stage:SetAttribute("SafeRouteAlwaysAvailable",true)
 stage:SetAttribute("StarStepsOwned",0)
 stage:SetAttribute("ExistingStarStepsReused",10)
 stage:SetAttribute("ExistingMeteorSegmentsReused",12)
 stage:SetAttribute("MeteorOwnedSegments",0)
 stage.Parent=arena
 -- Raised stage with 20 climbable physical entry steps; the original entire
 -- floor remains safe if someone falls (never deletes/overwrites V3 terrain).
 local origin=floor.CFrame*CFrame.new(0,floor.Size.Y/2+12,-175)
 local grass=Color3.fromRGB(80,151,107)
 local slate=Color3.fromRGB(72,83,112)
 local violet=Color3.fromRGB(175,113,237)
 local gold=Color3.fromRGB(246,212,109)
 local blue=Color3.fromRGB(93,197,241)
 local function block(name:string,size:Vector3,xyz:Vector3,col:Color3,
  mat:Enum.Material,collide:boolean,alpha:number?):Part
  return create(stage,name,size,origin*CFrame.new(xyz),col,mat,collide,alpha)
 end
 local function live():boolean
  return stage.Parent==arena and arena.Parent==lobby
 end
 local function rootState(p:Player):(BasePart?,Humanoid?)
  if p.Parent~=Players or not live()
   or p:GetAttribute("EGGRUMBLE_QueuedMode")~=mode
   or p:GetAttribute("EGGRUMBLE_Eliminated")==true then return nil,nil end
  local char=p.Character
  if not char then return nil,nil end
  local root=char:FindFirstChild("HumanoidRootPart")
  local hum=char:FindFirstChildOfClass("Humanoid")
  if not root or not root:IsA("BasePart") or not hum or hum.Health<=0 then
   return nil,nil
  end
  return root,hum
 end
 local function authorized(p:Player,target:BasePart):boolean
  local root,_=rootState(p)
  if not root or (root.Position-target.Position).Magnitude>13 then return false end
  -- A spoofed ProximityPrompt event may bypass visual LOS; trust server ray.
  local direction=target.Position-(root.Position+Vector3.new(0,1.5,0))
  local rp=RaycastParams.new();rp.FilterType=Enum.RaycastFilterType.Exclude
  rp.FilterDescendantsInstances={p.Character,target};rp.RespectCanCollide=true
  local hit=Workspace:Raycast(root.Position+Vector3.new(0,1.5,0),direction,rp)
  return hit==nil or not hit.Instance.CanCollide
 end
 local function occupied(zoneZ:number,limitY:number):boolean
  -- Wait until *all* living players have cleared the full 50-stud walkway.
  for _,p in ipairs(Players:GetPlayers()) do
   local char=p.Character
   local root=char and char:FindFirstChild("HumanoidRootPart")
   local hum=char and char:FindFirstChildOfClass("Humanoid")
   if root and root:IsA("BasePart") and hum and hum.Health>0 then
    local pos=origin:PointToObjectSpace(root.Position)
    if math.abs(pos.X)<29 and math.abs(pos.Z-zoneZ)<9
     and pos.Y>=-5 and pos.Y<=limitY then return true end
   end
  end
  return false
 end
 local west=block("WestBank",Vector3.new(50,4,85),
  Vector3.new(-50,-2,0),grass,Enum.Material.Grass,true)
 local east=block("EastBank",Vector3.new(50,4,85),
  Vector3.new(50,-2,0),grass,Enum.Material.Grass,true)
 local safe=block("AlwaysOpenSafeRoute",Vector3.new(50,3,12),
  Vector3.new(0,-1.5,-30),slate,Enum.Material.Slate,true)
 block("CrystalCanyonBottom",Vector3.new(50,1.5,85),
  Vector3.new(0,-21,0),Color3.fromRGB(42,66,85),Enum.Material.Slate,true)
 for i=1,6 do
  local d=80+(i-1)*10
  local h=-1.5-(i-1)*2.2
  block("WestAccessStep_"..i,Vector3.new(12,1.2,15),
   Vector3.new(-d,h,0),slate,Enum.Material.Cobblestone,true)
  block("EastAccessStep_"..i,Vector3.new(12,1.2,15),
   Vector3.new(d,h,0),slate,Enum.Material.Cobblestone,true)
 end
 for i=1,7 do
  local crystal=block("CanyonCrystal_"..i,Vector3.new(2,7+i%3*2,2),
   Vector3.new(-23+i*6,3,-13),violet,Enum.Material.Neon,false,.13)
  crystal.CanQuery=false
 end
 local shortcut=block("ShortcutBridge",Vector3.new(50,2,12),
  Vector3.new(0,-1,-15),slate,Enum.Material.Slate,true)
 local gate=block("ShortcutGate",Vector3.new(3,9,12),
  Vector3.new(0,4.5,-15),violet,Enum.Material.Neon,true,.2)
 local gateOpen=false
 local gateUntil=0
 local nextGate=0
 local function setGate(open:boolean)
  if gateOpen and not open then nextGate=os.clock()+4 end
  gateOpen=open
  gate.CanCollide=not open;gate.CanQuery=not open
  gate.Transparency=if open then .88 else .2
  stage:SetAttribute("MoguronGateOpen",open)
 end
 local function mole(side:string,x:number)
  local torso=block("Moguron_"..side.."_Body",Vector3.new(4,3,4),
   Vector3.new(x,2.4,-15),Color3.fromRGB(155,106,72),Enum.Material.SmoothPlastic,false)
  torso.Shape=Enum.PartType.Ball
  local nose=block("Moguron_"..side.."_Nose",Vector3.new(1.5,1.2,1.5),
   Vector3.new(x,2.65,-17),gold,Enum.Material.Neon,false)
  nose.Shape=Enum.PartType.Ball
  addPrompt(torso,"橋をひらく","橋掘りモグロン",function(p:Player)
   if not authorized(p,torso) or gateOpen or os.clock()<nextGate then return end
   setGate(true);gateUntil=os.clock()+14
  end)
 end
 mole("WEST",-34);mole("EAST",34)
 setGate(false)
 -- Original Starfall's 10 timed physical stones belong to EXISTING Realm owner.
 -- This world attaches next to that exact route; NEVER duplicate those stones.
 local originalRealm=arena:FindFirstChild("EGGRUMBLE_REALM_BATTLE_CORE")
 local existingStar=originalRealm and originalRealm:FindFirstChild("GQ8_RC86_StarfallPath")
 if not existingStar or existingStar:GetAttribute("TimedStarSteps")~=10 then
  stage:Destroy();installed[arena]=nil;return
 end
 stage:SetAttribute("UniqueStarPathReused",true)
 -- MeteorFourth is ALREADY selected by PR #884 in this same Realm.
 -- Reuse the original 12-part route at +30 Z; do not create an owner here.
 local existingMeteor=originalRealm and originalRealm:FindFirstChild("GQ8_RC86_MeteorShortcut")
 if not existingMeteor or existingMeteor:GetAttribute("TemporaryBridgeParts")~=12 then
  stage:Destroy();installed[arena]=nil;return
 end
 stage:SetAttribute("UniqueMeteorRouteReused",true)
 -- Non-blocking per-arena lifecycle. Never retire an occupied walkway.
 task.spawn(function()
  while live() do
   if gateOpen and os.clock()>=gateUntil and not occupied(-15,13) then
    setGate(false)
   end
   task.wait(.45)
  end
 end)

 arena.Destroying:Connect(function()
  installed[arena]=nil
 end)
end

local function bindLobby(lobby:Instance)
 if boundLobby[lobby] or lobby.Name~=LOBBY or lobby.Parent~=Workspace then return end
 boundLobby[lobby]=true
 local function observe(candidate:Instance)
  local mode=if candidate.Name=="TEAM_Arena" then "TEAM"
   elseif candidate.Name=="BATTLE_ROYALE_Arena" then "BATTLE_ROYALE" else nil
  if not mode then return end
  task.spawn(function()
   -- Never disarm permanently because field world finished booting late.
   while candidate.Parent==lobby and (candidate:FindFirstChild("TacticalBattlefield")==nil
    or not candidate:FindFirstChild("EGGRUMBLE_REALM_BATTLE_CORE")
    or not candidate.EGGRUMBLE_REALM_BATTLE_CORE:FindFirstChild("GQ8_RC86_StarfallPath")
    or not candidate.EGGRUMBLE_REALM_BATTLE_CORE:FindFirstChild("GQ8_RC86_MeteorShortcut")) do
    task.wait(.3)
   end
   local floor=candidate:FindFirstChild("TacticalBattlefield")
   if floor and floor:IsA("BasePart") then setup(candidate,mode,lobby,floor) end
  end)
 end
 for _,ch in ipairs(lobby:GetChildren()) do observe(ch) end
 lobby.ChildAdded:Connect(observe)
 lobby.Destroying:Connect(function()boundLobby[lobby]=nil end)
end
for _,ch in ipairs(Workspace:GetChildren()) do
 if ch.Name==LOBBY then bindLobby(ch) end
end
Workspace.ChildAdded:Connect(function(ch:Instance)
 if ch.Name==LOBBY then bindLobby(ch) end
end)
