--!strict
-- EGGRUMBLE V3 / isolated Studio-only FLAGSHIP FIELD APPEARANCE PASS
-- Decorates EXISTING V3 lobby battle worlds; does not create a new stage.
-- No terrain collision, path-blocking, changing castle core or egg/damage rules.
local RunService = game:GetService("RunService")
if not RunService:IsStudio() then return end

local ROOT_NAME = "EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW"
local MAX_VISUAL_PARTS_PER_ARENA = 320
local MAX_CASTLE_PARTS = 11
local builtCastles:{[Model]:boolean}={}
local builtArenas:{[Instance]:boolean}={}
local budgets:{[Instance]:number}={}
local sandstone=Color3.fromRGB(163,154,135)
local limestone=Color3.fromRGB(208,200,174)
local darkStone=Color3.fromRGB(101,104,110)
local timber=Color3.fromRGB(93,70,54)
local foliageA=Color3.fromRGB(69,109,80)
local foliageB=Color3.fromRGB(91,134,94)
local bronze=Color3.fromRGB(195,154,80)

local function arenaFor(node:Instance):Instance?
 local ptr:Instance?=node
 while ptr do
  if ptr.Name=="TEAM_Arena" or ptr.Name=="BATTLE_ROYALE_Arena" then
   local root=ptr.Parent
   if root and root.Name==ROOT_NAME then return ptr end
  end
  ptr=ptr.Parent
 end
 return nil
end

local function createVisual(arena:Instance,parent:Instance,name:string,
 kind:string,size:Vector3,cf:CFrame,color:Color3,material:Enum.Material):BasePart?
 if (budgets[arena] or 0)>=MAX_VISUAL_PARTS_PER_ARENA then return nil end
 local p:BasePart
 if kind=="Wedge" then p=Instance.new("WedgePart") else
  local q=Instance.new("Part")
  if kind=="Cylinder" then q.Shape=Enum.PartType.Cylinder end
  if kind=="Ball" then q.Shape=Enum.PartType.Ball end
  p=q
 end
 p.Name="ART_"..name
 p.Size=size
 p.CFrame=cf
 p.Color=color
 p.Material=material
 p.Anchored=true
 p.CanCollide=false
 p.CanTouch=false
 p.CanQuery=false
 p.CastShadow=false -- phone-friendly; primary map still supplies physical shadows
 p.Parent=parent
 budgets[arena]=(budgets[arena] or 0)+1
 return p
end

local function castleAt(arena:Instance,castle:Model)
 if builtCastles[castle] then return end
 local core=castle:FindFirstChild("StandardCore")
 local foundation=castle:FindFirstChild("StandardFoundation")
 if not core or not core:IsA("BasePart") or not foundation or not foundation:IsA("BasePart") then return end
 builtCastles[castle]=true
 local at=core.Position-Vector3.new(0,14,0)
 local isRed=foundation.Color.R>foundation.Color.B
 local teamTrim=if isRed then Color3.fromRGB(174,80,79) else Color3.fromRGB(81,129,183)
 local deco=Instance.new("Folder")
 deco.Name="EGGRUMBLE_CastleArt_VisualOnly"
 deco.Parent=castle
 local used=0
 local function add(name:string,kind:string,size:Vector3,offset:Vector3,color:Color3,material:Enum.Material,rotY:number?):BasePart?
  if used>=MAX_CASTLE_PARTS then return nil end
  local cf=CFrame.new(at+offset)*CFrame.Angles(0,math.rad(rotY or 0),0)
  local p=createVisual(arena,deco,name,kind,size,cf,color,material)
  if p then used+=1 end
  return p
 end
 -- Four layered tower roofs: readable from long-range but door remains uncovered.
 for _,x in ipairs({-26,26}) do
  for _,z in ipairs({-26,26}) do
   add("CornerGabledCap","Wedge",Vector3.new(10,4.2,10),
    Vector3.new(x,20,z),darkStone,Enum.Material.Slate,if x*z>0 then 0 else 180)
  end
 end
 -- Entry must remain open. Decorative cornices are above, not in, the 9-stud gate.
 add("DoorKeystone","Wedge",Vector3.new(6.4,2.5,2),
  Vector3.new(0,10.0,-13.1),limestone,Enum.Material.Limestone,180)
 for _,x in ipairs({-8,8}) do
  add("EntryButtress","Wedge",Vector3.new(2.2,8,3),
   Vector3.new(x,6,-13.2),sandstone,Enum.Material.Limestone,if x<0 then 90 else -90)
 end
 -- Two roofline trims + a team-readable heraldic crest.
 for _,z in ipairs({-12.1,12.1}) do
  add("RoofCornice","Block",Vector3.new(29,.8,1.3),
   Vector3.new(0,14.8,z),limestone,Enum.Material.Limestone)
 end
 add("HeraldicCrest","Cylinder",Vector3.new(.4,3,3),
  Vector3.new(0,12,-14.15),teamTrim,Enum.Material.Metal,90)
 local finial=add("TowerFinial","Wedge",Vector3.new(2.8,2.6,2.8),
  Vector3.new(26,23.1,-26),bronze,Enum.Material.Metal)
 -- Personal home ornament echoes an existing, owner-authorized flag change.
 -- Fixed red/blue HeraldicCrest remains intact for TEAM friend/foe clarity.
 -- NEVER change OwnerFlag, decorate rules, castle HP or defense budget here.
 local bannerBound=false
 local function watchOwnerFlag(flag:Instance)
  if bannerBound or not finial or not flag:IsA("BasePart") then return end
  bannerBound=true
  finial.Color=flag.Color
  flag:GetPropertyChangedSignal("Color"):Connect(function()
   if finial.Parent and flag.Parent then finial.Color=flag.Color end
  end)
 end
 local existingFlag=castle:FindFirstChild("OwnerFlag")
 if existingFlag then watchOwnerFlag(existingFlag) end
 if not bannerBound then
  local later
  later=castle.ChildAdded:Connect(function(child)
   if child.Name=="OwnerFlag" then
    watchOwnerFlag(child)
    if bannerBound and later then later:Disconnect() end
   end
  end)
 end
end

local function drawTree(arena:Instance,deco:Instance,base:Vector3,variant:number,index:number)
 local canopy=if variant==1 then foliageA else foliageB
 local height=14+(index%4)*3
 local trunkH=height*.75
 createVisual(arena,deco,"TimberTrunk"..index,"Cylinder",Vector3.new(3.0,trunkH,3),
  CFrame.new(base+Vector3.new(0,trunkH/2,0)),timber,Enum.Material.Wood)
 -- Three broad overlapping cedar wedges create distance-readable foliage masses,
 -- instead of dozens of expensive leaves / transparent alpha cards.
 for layer=1,3 do
  local spread=10.8-layer*2.1
  local y=trunkH*.63+layer*3
  createVisual(arena,deco,"Canopy"..index.."_"..layer,"Wedge",
   Vector3.new(spread,5.6,spread),
   CFrame.new(base+Vector3.new(0,y,0))*CFrame.Angles(0,math.rad((index*37+layer*61)%360),0),
   if layer==2 then foliageB else canopy,Enum.Material.Grass)
 end
end

local function drawRocks(arena:Instance,deco:Instance,base:Vector3,index:number)
 for i=1,2 do
  local shift=(i-1.5)*6
  createVisual(arena,deco,"Boulder"..index.."_"..i,"Wedge",
   Vector3.new(5+(index%3)*2,3.6+i,8),
   CFrame.new(base+Vector3.new(shift,1.4,0))*CFrame.Angles(0,math.rad(index*47+i*75),0),
   if i==1 then darkStone else sandstone,Enum.Material.Slate)
 end
end

local function drawRouteMarker(arena:Instance,deco:Instance,position:Vector3,lane:number,index:number)
 local accent=if lane==1 then Color3.fromRGB(92,164,129)
  elseif lane==2 then Color3.fromRGB(205,162,88)
  else Color3.fromRGB(123,151,197)
 local pole=createVisual(arena,deco,"Waystone_"..lane.."_"..index,"Cylinder",
  Vector3.new(2.6,8,2.6),CFrame.new(position+Vector3.new(0,4,0)),darkStone,Enum.Material.Slate)
 if not pole then return end
 createVisual(arena,deco,"WaystoneCap_"..lane.."_"..index,"Wedge",
  Vector3.new(3.4,2.4,3.4),CFrame.new(position+Vector3.new(0,9,0)),accent,Enum.Material.Metal)
 -- The markers show lane identity without a large text billboard or collision.
end

local function drawLaneIdentityVista(arena:Instance,art:Instance,ground:Vector3,lane:number)
 -- Four nonblocking silhouettes per lane, placed outside its 23-stud road surface:
 -- ridge-watch / river-ford / forest-altar. They are navigation REFERENCE art only,
 -- never a substitute for the author's route, hill, bridge or actual cover.
 local stone=if lane==1 then limestone elseif lane==2 then sandstone else darkStone
 local motif=if lane==1 then foliageA elseif lane==2 then bronze else foliageB
 local label="LaneIdentity_"..lane
 if lane==1 then
  createVisual(arena,art,label.."_SpireL","Wedge",Vector3.new(4,18,5),
   CFrame.new(ground+Vector3.new(-5.5,9,0)),stone,Enum.Material.Limestone)
  createVisual(arena,art,label.."_SpireR","Wedge",Vector3.new(4,13,5),
   CFrame.new(ground+Vector3.new(5.5,6.5,0))*CFrame.Angles(0,math.pi,0),stone,Enum.Material.Limestone)
  createVisual(arena,art,label.."_Brazier","Cylinder",Vector3.new(2.4,3.8,2.4),
   CFrame.new(ground+Vector3.new(0,11.6,0)),bronze,Enum.Material.Metal)
  createVisual(arena,art,label.."_Signal","Wedge",Vector3.new(2.8,4.0,2.7),
   CFrame.new(ground+Vector3.new(0,15.2,0)),motif,Enum.Material.Fabric)
 elseif lane==2 then
  for _,side in ipairs({-1,1}) do
   createVisual(arena,art,label.."_FordPier","Cylinder",Vector3.new(3.5,12,3.5),
    CFrame.new(ground+Vector3.new(side*6,6,0)),stone,Enum.Material.Limestone)
  end
  createVisual(arena,art,label.."_StoneArc","Wedge",Vector3.new(15.5,3.4,4.7),
   CFrame.new(ground+Vector3.new(0,13,0)),limestone,Enum.Material.Limestone)
  createVisual(arena,art,label.."_CopperMedal","Cylinder",Vector3.new(.5,3,3),
   CFrame.new(ground+Vector3.new(0,15,0))*CFrame.Angles(0,0,math.rad(90)),
   motif,Enum.Material.Metal)
 else
  createVisual(arena,art,label.."_TimberPillar","Cylinder",Vector3.new(3.8,17,3.8),
   CFrame.new(ground+Vector3.new(0,8.5,0)),timber,Enum.Material.Wood)
  for _,side in ipairs({-1,1}) do
   createVisual(arena,art,label.."_Branch","Wedge",Vector3.new(5.4,8.2,4.1),
    CFrame.new(ground+Vector3.new(side*3.8,15,0))
     *CFrame.Angles(0,0,math.rad(side*30)),motif,Enum.Material.Grass)
  end
  createVisual(arena,art,label.."_Shrine","Cylinder",Vector3.new(.48,3.7,3.7),
   CFrame.new(ground+Vector3.new(0,14.8,-2.2))*CFrame.Angles(0,0,math.rad(90)),
   bronze,Enum.Material.Metal)
 end
end

local function paintArena(arena:Instance)
 if builtArenas[arena] then return end
 local floor=arena:FindFirstChild("TacticalBattlefield")
 if not floor or not floor:IsA("BasePart") then return end
 builtArenas[arena]=true
 budgets[arena]=budgets[arena] or 0
 local art=Instance.new("Folder")
 art.Name="EGGRUMBLE_FlagshipLandscape_VisualOnly"
 art.Parent=arena
 local center=floor.Position
 -- Ground surface of the real floor; all decorative pieces are NONCOLLIDING.
 local groundY=center.Y+floor.Size.Y/2
 local function onGround(x:number,z:number):Vector3
  return Vector3.new(center.X+x,groundY,center.Z+z)
 end
 -- Three separate visual signatures for three existing physical routes.
 -- Side markers deliberately remain outside the 23-stud route width.
 for lane=1,3 do
  local z=(lane-2)*170
  for index=1,4 do
   local x=(index-2.5)*164
   local side=if index%2==0 then -1 else 1
   drawRouteMarker(arena,art,onGround(x,z+side*24),lane,index)
  end
 end
 -- The three lanes have unique *distant silhouettes* as well as their color-coded waystones.
 -- Stay to the side and never add a physical barrier across an assault route.
 for lane=1,3 do
  local z=(lane-2)*170+63
  local x=if lane==1 then -96 elseif lane==2 then 0 else 96
  drawLaneIdentityVista(arena,art,onGround(x,z),lane)
 end
 -- 20 sculpted tree clusters around forest edge and flanks. Avoid center
 -- corridor and castle foundations; existing block cover remains authoritative.
 for i=1,20 do
  local left=i<=10
  local j=if left then i else i-10
  local x=(if left then -1 else 1)*(348+(j%3)*25)
  local z=-414+(j-1)*84
  drawTree(arena,art,onGround(x,z),if i%2==0 then 1 else 2,i)
 end
 -- Rocky viewpoint rhythm at wide outer edges; decorative only.
 for i=1,10 do
  local side=if i%2==0 then -1 else 1
  local x=side*(322+(i%3)*25)
  local z=-388+(i-1)*81
  drawRocks(arena,art,onGround(x,z),i)
 end
 -- Broken long-distance ruin silhouette at the central axis; not a new wall.
 for _,side in ipairs({-1,1}) do
  local at=onGround(side*92,-155)
  createVisual(arena,art,"RuinedArchPillar","Cylinder",Vector3.new(4,17,4),
   CFrame.new(at+Vector3.new(0,8.5,0)),sandstone,Enum.Material.Limestone)
  createVisual(arena,art,"RuinedArchCap","Wedge",Vector3.new(7,4,5),
   CFrame.new(at+Vector3.new(0,17.5,0))*CFrame.Angles(0,math.rad(side*35),0),
   limestone,Enum.Material.Limestone)
 end
 for _,child in ipairs(arena:GetChildren()) do
  if child:IsA("Model") and child.Name:sub(1,7)=="Castle_" then castleAt(arena,child) end
 end
end

local function handleNew(instance:Instance)
 local arena=arenaFor(instance)
 if not arena then return end
 if instance:IsA("BasePart") and instance.Name=="TacticalBattlefield" then
  paintArena(arena)
 elseif instance:IsA("BasePart") and instance.Name=="StandardFoundation" then
  local castle=instance.Parent
  if castle and castle:IsA("Model") then
   -- Castle core is created immediately after foundation, so try when it appears.
   castle.ChildAdded:Connect(function(child)
    if child.Name=="StandardCore" then task.defer(function() castleAt(arena,castle) end) end
   end)
  end
 elseif instance:IsA("BasePart") and instance.Name=="StandardCore" then
  local castle=instance.Parent
  if castle and castle:IsA("Model") then task.defer(function() castleAt(arena,castle) end) end
 end
end

for _,instance in ipairs(workspace:GetDescendants()) do handleNew(instance) end
workspace.DescendantAdded:Connect(handleNew)
print("[EGGRUMBLE FIELD ART] layered castle roofs + three-route waystones + forest and ruins / Studio only; device QA pending")
