--!strict
-- EGGRUMBLE FIELD ART lane: isolated, deterministic, low-part-count landmark kit.
-- No changes to hero, castle, bot, lobby, items, balance, or authoritative RC.
local RunService=game:GetService("RunService")
local Kit={}
local function part(parent:Instance,name:string,cf:CFrame,size:Vector3,color:Color3,material:Enum.Material,solid:boolean):BasePart
 local p=Instance.new("Part");p.Name=name;p.CFrame=cf;p.Size=size;p.Color=color;p.Material=material
 p.Anchored=true;p.CanCollide=solid;p.CanTouch=false;p.CanQuery=solid
 p.CastShadow=solid;p.Parent=parent;return p
end
local function wedge(parent:Instance,name:string,cf:CFrame,size:Vector3,color:Color3):()
 local p=Instance.new("WedgePart");p.Name=name;p.CFrame=cf;p.Size=size
 p.Color=color;p.Material=Enum.Material.Slate;p.Anchored=true;p.CanCollide=true
 p.CanTouch=false;p.Parent=parent
end
local function addTree(parent:Instance,at:Vector3,height:number):()
 local trunk=part(parent,"TreeTrunk",CFrame.new(at+Vector3.new(0,height*0.35,0)),Vector3.new(2,height*0.7,2),
  Color3.fromRGB(99,68,45),Enum.Material.Wood,true)
 trunk.Shape=Enum.PartType.Cylinder
 local crown=part(parent,"TreeCrown",CFrame.new(at+Vector3.new(0,height*0.9,0)),Vector3.new(height*0.9,height*0.8,height*0.9),
  Color3.fromRGB(52,120,72),Enum.Material.Grass,false)
 crown.Shape=Enum.PartType.Ball
end
local function addRock(parent:Instance,at:Vector3,scale:number):()
 local p=part(parent,"Rock",CFrame.new(at)*CFrame.Angles(0,math.rad(25),math.rad(12)),
  Vector3.new(scale*1.2,scale*0.8,scale),Color3.fromRGB(98,106,112),Enum.Material.Slate,true)
 p.Shape=Enum.PartType.Ball
end
function Kit.build(parent:Instance,origin:Vector3,seed:number):any
 assert(RunService:IsStudio(),"private FIELD art preview only")
 assert(type(seed)=="number" and seed==seed,"finite seed required")
 local rng=Random.new(math.floor(seed))
 local model=Instance.new("Model");model.Name="EGGRUMBLE_ValleyLandmarkKit";model.Parent=parent
 local grass=Color3.fromRGB(80,133,83)
 local cliff=Color3.fromRGB(112,118,114)
 local road=Color3.fromRGB(156,140,113)
 local water=Color3.fromRGB(51,155,182)
 local width=300
 -- Continuous playable central corridor; no invisible blocking props.
 part(model,"Ground",CFrame.new(origin+Vector3.new(0,-2,0)),Vector3.new(width,4,width),grass,Enum.Material.Grass,true)
 part(model,"RaidRoad",CFrame.new(origin+Vector3.new(0,0.04,0)),Vector3.new(18,0.12,260),road,Enum.Material.Ground,false)
 -- The river is shallow visual-only water: traversable, no lethal collision or teleport.
 part(model,"RiverSurface",CFrame.new(origin+Vector3.new(55,0.1,0)),Vector3.new(16,0.18,260),water,Enum.Material.Glass,false).Transparency=0.24
 for i=1,3 do
  local z=-95+(i-1)*95
  -- Physical bridges are level with terrain and broad enough for AI and mobile controls.
  part(model,"BridgeDeck_"..i,CFrame.new(origin+Vector3.new(55,0.4,z)),Vector3.new(22,0.8,13),
   Color3.fromRGB(127,91,60),Enum.Material.WoodPlanks,true)
  for side=-1,1,2 do
   part(model,"BridgeRail_"..i.."_"..side,CFrame.new(origin+Vector3.new(55,1.8,z+side*6.1)),
    Vector3.new(22,1.5,0.6),Color3.fromRGB(97,68,49),Enum.Material.Wood,true)
  end
 end
 -- Border hills keep the raid lane open; all actual obstacles are visible.
 for side=-1,1,2 do
  for i=1,5 do
   local z=-112+(i-1)*56
   local x=side*(108+rng:NextNumber(0,10))
   wedge(model,"BorderCliff",CFrame.new(origin+Vector3.new(x,8,z))*CFrame.Angles(0,if side==1 then math.pi else 0,0),
    Vector3.new(32,16,48),cliff)
  end
 end
 for i=1,22 do
  local side=if i%2==0 then 1 else -1
  local x=side*rng:NextNumber(74,97)
  local z=rng:NextNumber(-120,120)
  addTree(model,origin+Vector3.new(x,0,z),rng:NextNumber(10,17))
 end
 for i=1,12 do
  local side=if i%2==0 then 1 else -1
  addRock(model,origin+Vector3.new(side*rng:NextNumber(83,101),2,rng:NextNumber(-125,125)),rng:NextNumber(4,8))
 end
 -- Central sightline markers help children navigate to enemy castles.
 for side=-1,1,2 do
  local z=side*108
  part(model,"RaidBannerPole",CFrame.new(origin+Vector3.new(-12,8,z)),Vector3.new(0.8,16,0.8),
   Color3.fromRGB(105,75,51),Enum.Material.Wood,true)
  local flag=part(model,"RaidBanner",CFrame.new(origin+Vector3.new(-9,13,z)),Vector3.new(6,3,0.2),
   if side==1 then Color3.fromRGB(72,137,232) else Color3.fromRGB(229,81,82),Enum.Material.Fabric,false)
  flag.CastShadow=false
 end
 return {model=model,partCount=#model:GetDescendants()-1,bridgeCount=3,fieldWidth=width,
  noInvisibleWalls=true,seed=seed}
end
return Kit
