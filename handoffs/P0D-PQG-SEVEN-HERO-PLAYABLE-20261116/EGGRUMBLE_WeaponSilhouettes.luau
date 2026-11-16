--!strict
-- EGGRUMBLE V3 7 distinctive low-part in-hand hero weapon models.
-- Server-replicated visual-only, no weapon combat authority or collisions.
-- Placeholder geometry until art team supplies original premium rigs and animations.
local Weapons={}
local PART_BUDGET_PER_AVATAR=8
local CONFIG={
 WARRIOR={base=Color3.fromRGB(212,197,168),accent=Color3.fromRGB(255,199,66)},
 MAGE={base=Color3.fromRGB(100,147,201),accent=Color3.fromRGB(101,226,255)},
 NINJA={base=Color3.fromRGB(60,62,89),accent=Color3.fromRGB(179,113,250)},
 TRAPPER={base=Color3.fromRGB(94,72,135),accent=Color3.fromRGB(223,102,255)},
 BUILDER={base=Color3.fromRGB(54,93,112),accent=Color3.fromRGB(91,247,216)},
 BEAST={base=Color3.fromRGB(128,88,50),accent=Color3.fromRGB(255,174,68)},
 ZOMBIE={base=Color3.fromRGB(80,65,102),accent=Color3.fromRGB(143,232,134)},
}
local function part(root:Model,grip:BasePart,name:string,
 size:Vector3,offset:CFrame,color:Color3,material:Enum.Material,shape:Enum.PartType?):Part
 local p=Instance.new("Part")
 p.Name=name;p.Size=size;p.Color=color;p.Material=material
 p.Shape=shape or Enum.PartType.Block
 p.Anchored=false;p.Massless=true;p.CanCollide=false;p.CanTouch=false;p.CanQuery=false
 p.CastShadow=false;p.CFrame=grip.CFrame*offset;p.Parent=root
 local weld=Instance.new("WeldConstraint")
 weld.Name="EGGRUMBLE_SafeGrip";weld.Part0=grip;weld.Part1=p;weld.Parent=p
 return p
end
local function add(root:Model,grip:BasePart,name:string,size:Vector3,
 offset:CFrame,color:Color3,glow:boolean,shape:Enum.PartType?)
 return part(root,grip,name,size,offset,color,
  if glow then Enum.Material.Neon else Enum.Material.Metal,shape)
end
function Weapons.clear(player:Player)
 local char=player.Character
 if not char then return end
 local old=char:FindFirstChild("EGGRUMBLE_ClassWeapon")
 if old then old:Destroy() end
end
function Weapons.attach(player:Player,role:string):boolean
 local char=player.Character
 if not char then return false end
 local hand=char:FindFirstChild("RightHand") or char:FindFirstChild("Right Arm")
 if not hand or not hand:IsA("BasePart") then return false end
 local cfg=CONFIG[role]
 if not cfg then return false end
 Weapons.clear(player)
 local model=Instance.new("Model");model.Name="EGGRUMBLE_ClassWeapon"
 model:SetAttribute("Role",role);model.Parent=char
 local a=cfg.base;local b=cfg.accent
 local count=0
 local function piece(name:string,size:Vector3,off:CFrame,color:Color3,glow:boolean,shape:Enum.PartType?)
  if count>=PART_BUDGET_PER_AVATAR then return end
  count+=1
  add(model,hand,name,size,off,color,glow,shape)
 end
 if role=="WARRIOR" then
  -- Oversized general's odachi, gold guard, red oath mark.
  piece("OdachiGrip",Vector3.new(.24,1.9,.28),CFrame.new(0,-.7,-.35),a,false)
  piece("OdachiGuard",Vector3.new(1.55,.19,.45),CFrame.new(0,-1.56,-.35),b,true)
  piece("OdachiBlade",Vector3.new(.38,4.5,.17),CFrame.new(0,-3.87,-.35),a,false)
  piece("OdachiGoldEdge",Vector3.new(.1,4.2,.12),CFrame.new(.2,-3.8,-.35),b,true)
  piece("WarGodCrest",Vector3.new(.65,.64,.22),CFrame.new(0,-1.45,-.35),b,true,Enum.PartType.Ball)
 elseif role=="MAGE" then
  piece("RuneStaff",Vector3.new(.25,5.5,.25),CFrame.new(0,-2.3,-.3),a,false)
  piece("PrismHeart",Vector3.new(1.2,1.2,1.2),CFrame.new(0,.75,-.3),b,true,Enum.PartType.Ball)
  piece("PrismProngLeft",Vector3.new(.25,1.1,.25),CFrame.new(-.65,.4,-.3)*CFrame.Angles(0,0,.55),a,false)
  piece("PrismProngRight",Vector3.new(.25,1.1,.25),CFrame.new(.65,.4,-.3)*CFrame.Angles(0,0,-.55),a,false)
 elseif role=="NINJA" then
  piece("TwinDaggerNear",Vector3.new(.26,2.7,.15),CFrame.new(-.55,-1.6,-.4)*CFrame.Angles(0,0,-.18),a,false)
  piece("TwinDaggerNearEdge",Vector3.new(.12,2.4,.10),CFrame.new(-.7,-1.6,-.4)*CFrame.Angles(0,0,-.18),b,true)
  piece("TwinDaggerFar",Vector3.new(.26,2.7,.15),CFrame.new(.57,-1.5,-.4)*CFrame.Angles(0,0,.2),a,false)
  piece("TwinDaggerFarEdge",Vector3.new(.12,2.4,.10),CFrame.new(.7,-1.5,-.4)*CFrame.Angles(0,0,.2),b,true)
  piece("ShadowGuard",Vector3.new(1.5,.2,.36),CFrame.new(0,-.65,-.4),a,false)
 elseif role=="TRAPPER" then
  piece("PsiGauntlet",Vector3.new(.65,1.55,.74),CFrame.new(0,-.45,-.35),a,false)
  piece("PsiCore",Vector3.new(.95,.95,.95),CFrame.new(0,.85,-.35),b,true,Enum.PartType.Ball)
  piece("PsiOrbitLeft",Vector3.new(.18,1.8,.2),CFrame.new(-.56,.85,-.35)*CFrame.Angles(0,0,.52),a,false)
  piece("PsiOrbitRight",Vector3.new(.18,1.8,.2),CFrame.new(.56,.85,-.35)*CFrame.Angles(0,0,-.52),a,false)
 elseif role=="BUILDER" then
  piece("RailGunReceiver",Vector3.new(1,1.25,2.4),CFrame.new(0,-.5,-1.1),a,false)
  piece("RailGunBarrelLeft",Vector3.new(.22,.2,2.8),CFrame.new(-.36,-.5,-2.3),b,true)
  piece("RailGunBarrelRight",Vector3.new(.22,.2,2.8),CFrame.new(.36,-.5,-2.3),b,true)
  piece("RailGunScope",Vector3.new(.32,.4,.9),CFrame.new(0,.26,-.9),b,true)
  piece("RailGunGrip",Vector3.new(.38,1.3,.5),CFrame.new(0,-1.4,-.4),a,false)
 elseif role=="BEAST" then
  piece("BeastHornHandle",Vector3.new(.6,1.6,.7),CFrame.new(0,-.7,-.4),a,false)
  piece("TamingHorn",Vector3.new(.8,2.4,.7),CFrame.new(0,.65,-.4),b,true)
  piece("BeastClawLeft",Vector3.new(.22,1.75,.4),CFrame.new(-.45,-1.3,-.5)*CFrame.Angles(0,0,.2),b,false)
  piece("BeastClawRight",Vector3.new(.22,1.75,.4),CFrame.new(.45,-1.3,-.5)*CFrame.Angles(0,0,-.2),b,false)
 elseif role=="ZOMBIE" then
  piece("CurseStaff",Vector3.new(.25,4.3,.24),CFrame.new(0,-1.8,-.4),a,false)
  piece("SoulCage",Vector3.new(1.25,1.25,1.25),CFrame.new(0,.6,-.4),b,true,Enum.PartType.Ball)
  piece("SoulProngLeft",Vector3.new(.22,1,.23),CFrame.new(-.7,.5,-.4),a,false)
  piece("SoulProngRight",Vector3.new(.22,1,.23),CFrame.new(.7,.5,-.4),a,false)
  piece("CurseSigil",Vector3.new(.72,.16,.72),CFrame.new(0,.1,-.4),a,false,Enum.PartType.Cylinder)
 end
 model:SetAttribute("VisualParts",count)
 return true
end
return Weapons
