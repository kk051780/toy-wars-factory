--!strict
-- EGGRUMBLE isolated CASTLE INTERIOR lane. No RC host edits.
-- Physical, walkable gate + vault room; identical competitive footprint for all owners.
local RunService=game:GetService("RunService")
local Castle={}
local function brick(parent:Instance,name:string,cf:CFrame,size:Vector3,color:Color3,solid:boolean):Part
 local p=Instance.new("Part");p.Name=name;p.CFrame=cf;p.Size=size;p.Anchored=true
 p.Color=color;p.Material=Enum.Material.Slate;p.CanCollide=solid;p.CanTouch=false;p.Parent=parent
 return p
end
function Castle.build(parent:Instance,origin:Vector3,teamColor:Color3):any
 assert(RunService:IsStudio(),"castle interior prototype is Studio-only")
 local m=Instance.new("Model");m.Name="EGGRUMBLE_EnterableCastle";m.Parent=parent
 local stone=Color3.fromRGB(113,119,130)
 local trim=Color3.fromRGB(76,83,95)
 local w=40;local depth=48;local height=18
 brick(m,"Foundation",CFrame.new(origin+Vector3.new(0,-1,0)),Vector3.new(w,2,depth),stone,true)
 -- Door is on negative Z. Keep a 10-stud opening for avatars, bots and mobile camera.
 for _,x in ipairs({-12.5,12.5}) do
  brick(m,"FrontWallPier",CFrame.new(origin+Vector3.new(x,9,-depth/2)),Vector3.new(15,height,3),stone,true)
 end
 brick(m,"DoorLintel",CFrame.new(origin+Vector3.new(0,15,-depth/2)),Vector3.new(10,6,3),stone,true)
 brick(m,"BackWall",CFrame.new(origin+Vector3.new(0,9,depth/2)),Vector3.new(w,height,3),stone,true)
 for _,x in ipairs({-w/2,w/2}) do
  brick(m,"SideWall",CFrame.new(origin+Vector3.new(x,9,0)),Vector3.new(3,height,depth),stone,true)
 end
 -- No low opaque ceiling: camera can follow the player inside.
 for _,x in ipairs({-16,16}) do
  brick(m,"Parapet",CFrame.new(origin+Vector3.new(x,19,0)),Vector3.new(8,2,depth),trim,true)
 end
 local door=brick(m,"CastleGate",CFrame.new(origin+Vector3.new(0,6,-depth/2)),Vector3.new(10,12,1),
  Color3.fromRGB(111,78,51),true)
 door.Material=Enum.Material.WoodPlanks
 local prompt=Instance.new("ProximityPrompt")
 prompt.Name="OpenGate";prompt.ActionText="門を開閉";prompt.ObjectText="城門"
 prompt.MaxActivationDistance=9;prompt.RequiresLineOfSight=true;prompt.HoldDuration=.2;prompt.Parent=door
 local gateOpen=false
 local lastToggle=0
 prompt.Triggered:Connect(function(player:Player)
  local character=player.Character
  local h=character and character:FindFirstChildOfClass("Humanoid")
  local root=character and character:FindFirstChild("HumanoidRootPart")
  if not h or h.Health<=0 or not root or not root:IsA("BasePart") then return end
  if (root.Position-door.Position).Magnitude>11 then return end
  local now=os.clock()
  if now-lastToggle<0.8 then return end
  lastToggle=now
  gateOpen=not gateOpen
  door.CanCollide=not gateOpen
  door.Transparency=if gateOpen then 0.75 else 0
  door.Color=if gateOpen then Color3.fromRGB(125,116,96) else Color3.fromRGB(111,78,51)
 end)
 -- Vault sits behind the gate; no exterior prompt or through-wall egg pickup.
 local vault=brick(m,"EggVault",CFrame.new(origin+Vector3.new(0,2,15)),Vector3.new(10,4,8),
  Color3.fromRGB(192,151,69),true)
 vault.Material=Enum.Material.Metal
 local egg=brick(m,"EggVisual",CFrame.new(origin+Vector3.new(0,5.4,15)),Vector3.new(2.4,3,2.4),
  Color3.fromRGB(242,205,109),false)
 egg.Shape=Enum.PartType.Ball;egg.Material=Enum.Material.Neon
 local core=brick(m,"SiegeCore",CFrame.new(origin+Vector3.new(0,6,22)),Vector3.new(7,10,2),teamColor,true)
 core.Material=Enum.Material.Neon
 -- Visual marker only. Match rules and real egg/castle ownership remain elsewhere.
 local marker=Instance.new("Attachment");marker.Name="InteriorVaultMarker";marker.Parent=vault
 return {model=m,gate=door,vault=vault,core=core,footprint=Vector3.new(w,height,depth),
  entryWidth=10,openGate=function():boolean return gateOpen end}
end
return Castle
