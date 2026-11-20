--!strict
-- Independent CHARACTER VISUAL IDENTITY lane; 7 distinct silhouette/weapon prototypes.
-- No combat/ability edits and no integration with existing seven-role writer.
local RunService=game:GetService("RunService")
local Kit={}
local ROLES={
 {id="WARRIOR",name="武神",weapon="大太刀",color=Color3.fromRGB(239,104,66),shape="BLADE"},
 {id="MAGE",name="魔法使い",weapon="魔導杖",color=Color3.fromRGB(97,163,249),shape="STAFF"},
 {id="NINJA",name="暗殺者",weapon="双短剣",color=Color3.fromRGB(125,112,197),shape="DUAL"},
 {id="TRAPPER",name="超能力者",weapon="念動キューブ",color=Color3.fromRGB(195,117,246),shape="CUBE"},
 {id="BUILDER",name="マッドサイエンティスト",weapon="未来銃",color=Color3.fromRGB(80,225,194),shape="GUN"},
 {id="BEAST",name="魔獣使い",weapon="獣笛",color=Color3.fromRGB(229,175,82),shape="HORN"},
 {id="ZOMBIE",name="呪術師",weapon="呪杖",color=Color3.fromRGB(178,91,184),shape="CURSE"},
}
local function part(parent:Instance,name:string,cf:CFrame,size:Vector3,color:Color3,material:Enum.Material):Part
 local p=Instance.new("Part");p.Name=name;p.CFrame=cf;p.Size=size;p.Color=color
 p.Material=material;p.Anchored=true;p.CanCollide=false;p.CanTouch=false;p.CanQuery=false
 p.Parent=parent;return p
end
local function weapon(model:Model,origin:Vector3,entry:any):()
 local c=entry.color
 if entry.shape=="BLADE" then
  part(model,"GreatSwordGrip",CFrame.new(origin+Vector3.new(2.2,4,0)),Vector3.new(.5,3,.5),Color3.fromRGB(75,66,59),Enum.Material.Metal)
  part(model,"GreatSwordBlade",CFrame.new(origin+Vector3.new(2.2,7.1,0)),Vector3.new(1.2,4.5,.3),c,Enum.Material.Metal)
 elseif entry.shape=="STAFF" then
  part(model,"MagicStaff",CFrame.new(origin+Vector3.new(2,5,0)),Vector3.new(.5,8,.5),Color3.fromRGB(99,70,52),Enum.Material.Wood)
  local gem=part(model,"ArcaneGem",CFrame.new(origin+Vector3.new(2,9.2,0)),Vector3.new(2,2,2),c,Enum.Material.Neon)
  gem.Shape=Enum.PartType.Ball
 elseif entry.shape=="DUAL" then
  for side=-1,1,2 do
   part(model,"DaggerGrip",CFrame.new(origin+Vector3.new(side*2.4,3,0)),Vector3.new(.5,1.8,.5),Color3.fromRGB(61,65,82),Enum.Material.Metal)
   part(model,"DaggerBlade",CFrame.new(origin+Vector3.new(side*2.4,4.7,0)),Vector3.new(.7,2.2,.25),c,Enum.Material.Metal)
  end
 elseif entry.shape=="CUBE" then
  for i=1,3 do
   local x=math.sin(i*math.pi*2/3)*2.5
   local z=math.cos(i*math.pi*2/3)*2.5
   part(model,"TelekineticCube",CFrame.new(origin+Vector3.new(x,7+i*.5,z))*CFrame.Angles(.3*i,.5*i,0),
    Vector3.new(1.6,1.6,1.6),c,Enum.Material.Neon)
  end
 elseif entry.shape=="GUN" then
  part(model,"ScienceGunBarrel",CFrame.new(origin+Vector3.new(2.5,4,-1)),Vector3.new(1.3,1.4,5),Color3.fromRGB(83,94,103),Enum.Material.Metal)
  part(model,"ScienceGunCore",CFrame.new(origin+Vector3.new(2.5,4.8,-.8)),Vector3.new(1,1,1),c,Enum.Material.Neon)
 elseif entry.shape=="HORN" then
  local horn=part(model,"BeastHorn",CFrame.new(origin+Vector3.new(2.3,4,-.5))*CFrame.Angles(math.rad(30),0,0),
   Vector3.new(1,3,1),c,Enum.Material.Wood)
  horn.Shape=Enum.PartType.Cylinder
  part(model,"BeastTotem",CFrame.new(origin+Vector3.new(0,9,0)),Vector3.new(2.5,2,2.5),c,Enum.Material.Neon)
 elseif entry.shape=="CURSE" then
  part(model,"CurseStaff",CFrame.new(origin+Vector3.new(2.1,5,0)),Vector3.new(.5,8,.5),Color3.fromRGB(72,51,80),Enum.Material.Wood)
  local skull=part(model,"CurseOrb",CFrame.new(origin+Vector3.new(2.1,9.4,0)),Vector3.new(2.2,2.2,2.2),c,Enum.Material.Neon)
  skull.Shape=Enum.PartType.Ball
  for i=1,3 do
   part(model,"CurseCharm",CFrame.new(origin+Vector3.new(-2+i*.8,5.7,-1.1)),Vector3.new(.4,1.5,.1),c,Enum.Material.Fabric)
  end
 end
end
function Kit.build(parent:Instance,at:Vector3,roleId:string):Model
 assert(RunService:IsStudio(),"character art kit is Studio-only")
 local entry=nil
 for _,r in ipairs(ROLES) do if r.id==roleId then entry=r;break end end
 assert(entry~=nil,"invalid role")
 local m=Instance.new("Model");m.Name="CHARACTER_"..roleId;m.Parent=parent
 local cloth=entry.color
 part(m,"Body",CFrame.new(at+Vector3.new(0,4.5,0)),Vector3.new(3,4,2),cloth,Enum.Material.Fabric)
 local head=part(m,"Head",CFrame.new(at+Vector3.new(0,8,0)),Vector3.new(2.3,2.3,2.3),Color3.fromRGB(232,198,167),Enum.Material.SmoothPlastic)
 head.Shape=Enum.PartType.Ball
 for side=-1,1,2 do
  part(m,"Leg",CFrame.new(at+Vector3.new(side*.85,1.3,0)),Vector3.new(1.1,2.6,1.2),Color3.fromRGB(58,64,77),Enum.Material.Fabric)
  part(m,"Arm",CFrame.new(at+Vector3.new(side*2.2,4.7,0)),Vector3.new(1,3,1),cloth,Enum.Material.Fabric)
 end
 part(m,"ChestEmblem",CFrame.new(at+Vector3.new(0,5.2,-1.05)),Vector3.new(1.4,1.4,.2),Color3.fromRGB(245,220,126),Enum.Material.Metal)
 weapon(m,at,entry)
 m:SetAttribute("EGGRUMBLE_RoleId",roleId)
 m:SetAttribute("EGGRUMBLE_WeaponName",entry.weapon)
 return m
end
function Kit.roleIds():{string}
 local ids={}
 for _,r in ipairs(ROLES) do table.insert(ids,r.id) end
 return ids
end
return Kit
