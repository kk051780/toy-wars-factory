--!strict
-- EGGRUMBLE V3 / isolated Studio-only CHARACTER VISUAL LAYER (2026-11-16)
-- Seven distinctive role silhouettes for the original SevenHeroArena stands/players.
-- Adds decorative 3D forms to existing moving BotActors without changing combat.
-- No gameplay authority, physics collisions, RemoteEvents, GUI, store or RC writes.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
if not RunService:IsStudio() then return end

local HERO_SOURCE = "P0D_SEVEN_HERO_STUDIO_ONLY"
local PART_BUDGET_PER_SUBJECT = 13
local HERO_ROLES = {"WARRIOR","MAGE","NINJA","TRAPPER","BUILDER","BEAST","ZOMBIE"}
local COLORS = {
 WARRIOR={base=Color3.fromRGB(62,63,76),accent=Color3.fromRGB(224,177,83),cloth=Color3.fromRGB(133,47,56)},
 MAGE={base=Color3.fromRGB(33,46,95),accent=Color3.fromRGB(111,197,232),cloth=Color3.fromRGB(69,75,151)},
 NINJA={base=Color3.fromRGB(35,37,53),accent=Color3.fromRGB(124,130,180),cloth=Color3.fromRGB(65,64,86)},
 TRAPPER={base=Color3.fromRGB(52,43,86),accent=Color3.fromRGB(186,120,212),cloth=Color3.fromRGB(78,62,113)},
 BUILDER={base=Color3.fromRGB(60,74,78),accent=Color3.fromRGB(103,223,188),cloth=Color3.fromRGB(222,218,190)},
 BEAST={base=Color3.fromRGB(90,66,49),accent=Color3.fromRGB(208,168,91),cloth=Color3.fromRGB(110,81,57)},
 ZOMBIE={base=Color3.fromRGB(42,37,57),accent=Color3.fromRGB(166,124,182),cloth=Color3.fromRGB(73,47,89)},
}
local roleSet:{[string]:boolean}={}
for _,role in ipairs(HERO_ROLES) do roleSet[role]=true end
local marked:{[Instance]:boolean}={}

local function piece(parent:Instance,anchor:BasePart,tag:string,shape:string,
 size:Vector3,relative:CFrame,color:Color3,material:Enum.Material,static:boolean):BasePart
 local p:BasePart
 if shape=="Wedge" then p=Instance.new("WedgePart") else
  local plain=Instance.new("Part")
  if shape=="Cylinder" then plain.Shape=Enum.PartType.Cylinder end
  if shape=="Ball" then plain.Shape=Enum.PartType.Ball end
  p=plain
 end
 p.Name="ART_"..tag
 p.Size=size
 p.CFrame=anchor.CFrame*relative
 p.Color=color
 p.Material=material
 p.Anchored=static
 p.CanCollide=false
 p.CanTouch=false
 p.CanQuery=false
 p.CastShadow=false
 p.Massless=true
 p.Parent=parent
 if not static then
  local weld=Instance.new("WeldConstraint")
  weld.Part0=anchor
  weld.Part1=p
  weld.Parent=p
 end
 return p
end

local function sculpt(parent:Instance,anchor:BasePart,role:string,static:boolean)
 local palette=COLORS[role]
 if not palette then return end
 local b=palette.base
 local a=palette.accent
 local c=palette.cloth
 local metal=Enum.Material.Metal
 local cloth=Enum.Material.Fabric
 local stone=Enum.Material.SmoothPlastic
 local made=0
 local function add(n:string,shape:string,s:Vector3,x:number,y:number,z:number,col:Color3,mat:Enum.Material,rx:number?,ry:number?,rz:number?)
  if made>=PART_BUDGET_PER_SUBJECT then return end
  made+=1
  piece(parent,anchor,n,shape,s,
   CFrame.new(x,y,z)*CFrame.Angles(math.rad(rx or 0),math.rad(ry or 0),math.rad(rz or 0)),
   col,mat,static)
 end
 -- All seven jobs share a subdued metallic trim; only silhouettes change.
 add("WaistBelt","Block",Vector3.new(2.75,.3,1.68),0,-1.12,0,b,metal)
 if role=="WARRIOR" then
  -- War God: massive shoulder fins, long split war coat and a crown of blades.
  for _,side in ipairs({-1,1}) do
   add("GoldShoulder"..side,"Wedge",Vector3.new(1.45,1.25,1.7),side*1.64,1.18,0,a,metal,0,side*90,0)
   add("LegWarcoat"..side,"Wedge",Vector3.new(1.05,2.65,.45),side*.91,-2.56,.83,c,cloth,7,0,0)
  end
  add("CrestBlade","Wedge",Vector3.new(.5,2.1,1.1),0,2.44,-.1,a,metal,0,0,0)
  add("Breastplate","Wedge",Vector3.new(2.35,2.4,.55),0,.16,-1.0,b,metal,0,180,0)
  add("WarGodSigil","Cylinder",Vector3.new(.14,.93,.93),0,.31,-1.40,a,metal,0,0,90)
 elseif role=="MAGE" then
  -- Mage: pointed two-level collar, sweeping silk sash, star diadem.
  for _,side in ipairs({-1,1}) do
   add("HighCollar"..side,"Wedge",Vector3.new(.9,2.7,1.0),side*1.35,1.07,.47,b,cloth,0,side*90,0)
   add("RobeTail"..side,"Wedge",Vector3.new(1.25,3.3,.45),side*.72,-2.61,.97,c,cloth,-7,0,0)
  end
  add("Diadem","Cylinder",Vector3.new(.24,1.6,1.6),0,2.85,0,a,metal,0,0,90)
  add("Core","Ball",Vector3.new(.72,.72,.72),0,.56,-1.12,a,Enum.Material.Glass)
  add("BackScroll","Cylinder",Vector3.new(.8,2.65,.85),-.87,.25,1.07,b,stone,0,0,0)
 elseif role=="NINJA" then
  -- Assassin: low roofline hood, asymmetric short mantles, paired blade silhouettes.
  add("Hood","Wedge",Vector3.new(2.35,1.95,1.95),0,2.14,.09,b,cloth,0,180,0)
  add("FaceGuard","Block",Vector3.new(1.8,.57,.39),0,1.71,-1.01,c,cloth)
  for _,side in ipairs({-1,1}) do
   add("ShoulderMantle"..side,"Wedge",Vector3.new(1.24,.62,1.83),side*1.53,.91,.1,c,cloth,0,side*90,0)
   add("BackBlade"..side,"Wedge",Vector3.new(.35,2.7,.39),side*.66,.24,1.37,a,metal,-22,0,side*20)
  end
 elseif role=="TRAPPER" then
  -- Esper: four angular psychic stabilizers and an unmistakable V collar.
  for _,side in ipairs({-1,1}) do
   add("FloatFin"..side,"Wedge",Vector3.new(.6,2.25,1.8),side*2.05,.3,.22,a,metal,0,side*90,side*18)
   add("VCollar"..side,"Wedge",Vector3.new(.83,1.2,.73),side*.65,1.33,-.91,c,cloth,0,0,side*22)
  end
  add("ForeheadLens","Ball",Vector3.new(.57,.57,.36),0,2.43,-.95,a,Enum.Material.Glass)
  add("BackSpine","Wedge",Vector3.new(1.15,3.1,.73),0,.05,1.12,b,metal,0,0,0)
 elseif role=="BUILDER" then
  -- Mad Scientist: industrial backpack, broad asymmetric equipment arms.
  add("LabCoat","Wedge",Vector3.new(2.85,3.75,.52),0,-1.72,.89,c,cloth,0,180,0)
  add("ReactorPack","Block",Vector3.new(2.35,2.7,.83),0,.15,1.35,b,metal)
  add("ReactorDial","Cylinder",Vector3.new(.18,1.45,1.45),0,.26,1.84,a,metal,0,0,90)
  add("Lens","Block",Vector3.new(2.1,.51,.34),0,2.31,-.98,a,Enum.Material.Glass)
  add("ToolArm","Block",Vector3.new(.8,2.7,1.05),1.69,.10,-.17,b,metal)
  add("Antenna","Cylinder",Vector3.new(.14,1.9,.14),-.86,2.92,.18,a,metal)
 elseif role=="BEAST" then
  -- Beast Master: antler silhouette, shaggy triangular cape, horn-shell shoulder.
  for _,side in ipairs({-1,1}) do
   add("Antler"..side,"Wedge",Vector3.new(.58,2.4,.78),side*.88,2.96,.10,a,metal,0,side*90,side*16)
   add("FurGuard"..side,"Wedge",Vector3.new(1.44,1.56,1.77),side*1.59,.90,.18,c,cloth,0,side*90,0)
  end
  add("HideCape","Wedge",Vector3.new(3.18,3.65,.72),0,-1.45,1.04,b,cloth,-7,180,0)
  add("HornTrophy","Wedge",Vector3.new(.9,1.55,.72),0,.60,-1.21,a,metal)
 elseif role=="ZOMBIE" then
  -- Shaman: tall ritual crown, paired hanging talismans, skirted robe.
  add("RitualCrown","Cylinder",Vector3.new(.33,2.52,2.52),0,2.83,0,a,metal,0,0,90)
  add("TallHorn","Wedge",Vector3.new(.70,2.1,.62),0,3.45,-.20,b,metal)
  for _,side in ipairs({-1,1}) do
   add("Talisman"..side,"Wedge",Vector3.new(.74,2.95,.34),side*1.18,-1.91,-.83,a,cloth,0,0,side*8)
   add("Sleeve"..side,"Wedge",Vector3.new(1.37,2.11,1.21),side*1.59,.29,.12,c,cloth,0,side*90,0)
  end
 end
end

local function decorateHeroCharacter(player:Player)
 local char=player.Character
 if not char then return end
 -- Full V3 uses SelectedRole in lobby and Role when its real three skills equip.
 -- Legacy SevenHeroArena only uses P0DPreviewRole; keep all three read-only.
 local role=player:GetAttribute("EGGRUMBLE_Role")
  or player:GetAttribute("EGGRUMBLE_SelectedRole")
  or player:GetAttribute("P0DPreviewRole")
 local existing=char:FindFirstChild("EGGRUMBLE_RoleVisuals")
 if existing then existing:Destroy() end
 if type(role)~="string" or not roleSet[role] then return end
 local anchor=char:FindFirstChild("UpperTorso") or char:FindFirstChild("Torso")
 if not anchor or not anchor:IsA("BasePart") then return end
 local art=Instance.new("Folder")
 art.Name="EGGRUMBLE_RoleVisuals"
 art.Parent=char
 sculpt(art,anchor,role,false)
end

local function decorateArenaStand(source:Instance,role:string)
 if not roleSet[role] then return end
 local anchor=source:FindFirstChild(role.."_Torso")
 if not anchor or not anchor:IsA("BasePart") or marked[anchor] then return end
 marked[anchor]=true
 local art=Instance.new("Folder")
 art.Name="ART_"..role.."_Silhouette"
 art.Parent=source
 sculpt(art,anchor,role,true)
end

local function connectStandSource(source:Instance)
 if source.Name~=HERO_SOURCE then return end
 for _,role in ipairs(HERO_ROLES) do decorateArenaStand(source,role) end
 source.ChildAdded:Connect(function(child)
  if not child:IsA("BasePart") then return end
  for _,role in ipairs(HERO_ROLES) do
   if child.Name==role.."_Torso" then decorateArenaStand(source,role) end
  end
 end)
end

local function decorateLobbyRoleStand(stand:BasePart)
 local root=stand.Parent
 if not root or root.Name~="EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW" then return end
 local role=stand.Name:match("^ROLE_([A-Z]+)$")
 if not role or not roleSet[role] or marked[stand] then return end
 marked[stand]=true
 local palette=COLORS[role]
 local art=Instance.new("Folder")
 art.Name="EGGRUMBLE_LobbyRoleMiniatures_VisualOnly"
 art.Parent=stand
 -- Compact, tactile heraldic miniatures on the existing 7 hero-selection stands.
 -- They never create/trigger new selection prompts; the original author owns jobs.
 local function shape(name:string,kind:string,sz:Vector3,cf:CFrame,c:Color3,mat:Enum.Material)
  piece(art,stand,name,kind,sz,cf,c,mat,true)
 end
 shape("BaseMedal","Cylinder",Vector3.new(.18,2.6,2.6),
  CFrame.new(0,2.31,0)*CFrame.Angles(0,0,math.rad(90)),palette.accent,Enum.Material.Metal)
 if role=="WARRIOR" then
  shape("WarCrest","Wedge",Vector3.new(1.5,3,.65),CFrame.new(0,4.6,0),palette.base,Enum.Material.Metal)
  shape("WarWingL","Wedge",Vector3.new(1.3,1.6,1.2),CFrame.new(-1.35,3.5,0),palette.cloth,Enum.Material.Metal)
  shape("WarWingR","Wedge",Vector3.new(1.3,1.6,1.2),CFrame.new(1.35,3.5,0),palette.cloth,Enum.Material.Metal)
 elseif role=="MAGE" then
  shape("ArcaneSpire","Wedge",Vector3.new(1.2,3.8,1.2),CFrame.new(0,4.9,0),palette.base,Enum.Material.SmoothPlastic)
  shape("OrbL","Ball",Vector3.new(.85,.85,.85),CFrame.new(-1.5,3.55,0),palette.accent,Enum.Material.Glass)
  shape("OrbR","Ball",Vector3.new(.85,.85,.85),CFrame.new(1.5,3.55,0),palette.accent,Enum.Material.Glass)
 elseif role=="NINJA" then
  shape("HoodPeak","Wedge",Vector3.new(2.5,1.8,1.4),CFrame.new(0,4.0,-.2),palette.base,Enum.Material.Fabric)
  shape("CrossBladeL","Wedge",Vector3.new(.33,3.1,.45),CFrame.new(-.85,4.2,.5)*CFrame.Angles(0,0,math.rad(-30)),palette.accent,Enum.Material.Metal)
  shape("CrossBladeR","Wedge",Vector3.new(.33,3.1,.45),CFrame.new(.85,4.2,.5)*CFrame.Angles(0,0,math.rad(30)),palette.accent,Enum.Material.Metal)
 elseif role=="TRAPPER" then
  shape("MindCore","Ball",Vector3.new(1.8,1.8,1.8),CFrame.new(0,4.25,0),palette.accent,Enum.Material.Glass)
  shape("PsiWingL","Wedge",Vector3.new(.75,2.6,1.5),CFrame.new(-1.4,4.35,.2),palette.base,Enum.Material.Metal)
  shape("PsiWingR","Wedge",Vector3.new(.75,2.6,1.5),CFrame.new(1.4,4.35,.2),palette.base,Enum.Material.Metal)
 elseif role=="BUILDER" then
  shape("MachinePack","Block",Vector3.new(2.25,2.1,1.3),CFrame.new(0,4.1,.1),palette.base,Enum.Material.Metal)
  shape("ReactorLens","Ball",Vector3.new(1.0,1.0,.35),CFrame.new(0,4.15,-.67),palette.accent,Enum.Material.Glass)
  shape("Antenna","Cylinder",Vector3.new(.2,2.1,.2),CFrame.new(.85,5.55,0),palette.cloth,Enum.Material.Metal)
 elseif role=="BEAST" then
  shape("BeastTotem","Wedge",Vector3.new(2,2.2,1.4),CFrame.new(0,3.8,0),palette.base,Enum.Material.Fabric)
  shape("HornL","Wedge",Vector3.new(.5,2.8,.7),CFrame.new(-1.05,5.0,0),palette.accent,Enum.Material.SmoothPlastic)
  shape("HornR","Wedge",Vector3.new(.5,2.8,.7),CFrame.new(1.05,5.0,0),palette.accent,Enum.Material.SmoothPlastic)
 elseif role=="ZOMBIE" then
  shape("RitualCrown","Cylinder",Vector3.new(.36,2.4,2.4),CFrame.new(0,4.9,0)*CFrame.Angles(0,0,math.rad(90)),palette.accent,Enum.Material.Metal)
  shape("CharmL","Wedge",Vector3.new(.62,2.7,.35),CFrame.new(-1.1,3.7,0),palette.cloth,Enum.Material.Fabric)
  shape("CharmR","Wedge",Vector3.new(.62,2.7,.35),CFrame.new(1.1,3.7,0),palette.cloth,Enum.Material.Fabric)
 end
end

local function decorateAI(model:Model)
 if marked[model] or model:GetAttribute("EGGRUMBLE_BotId")==nil then return end
 local torso=model:FindFirstChild("HumanoidRootPart")
 if not torso or not torso:IsA("BasePart") then return end
 marked[model]=true
 local red=torso.Color.R>torso.Color.B
 local primary=if red then Color3.fromRGB(124,66,62) else Color3.fromRGB(58,91,137)
 local silver=Color3.fromRGB(207,186,140)
 local parent=Instance.new("Folder")
 parent.Name="EGGRUMBLE_BotVisuals"
 parent.Parent=model
 -- AI is moved by PivotTo; unanchored welded armor must follow the moving actor.
 -- Universal soldier armor: leave AI's actual combat role unchanged.
 local function g(name:string,shape:string,offset:CFrame,size:Vector3,color:Color3)
  piece(parent,torso,name,shape,size,offset,color,Enum.Material.Metal,false)
 end
 g("ChestV","Wedge",CFrame.new(0,.3,-.92)*CFrame.Angles(0,math.pi,0),Vector3.new(1.9,1.6,.55),primary)
 for _,side in ipairs({-1,1}) do
  g("Pauldron"..side,"Wedge",CFrame.new(side*1.34,1.03,0)*CFrame.Angles(0,side*math.pi/2,0),Vector3.new(1.05,.75,1.35),silver)
  g("ArmorSkirt"..side,"Wedge",CFrame.new(side*.68,-1.3,.4),Vector3.new(.9,1.45,.43),primary)
 end
 g("HelmetRidge","Wedge",CFrame.new(0,2.73,-.09),Vector3.new(.58,1.0,.95),silver)
 g("BackPlate","Block",CFrame.new(0,.25,.9),Vector3.new(1.7,1.2,.29),primary)
end

local function watchRole(player:Player)
 for _,attribute in ipairs({"P0DPreviewRole","EGGRUMBLE_SelectedRole","EGGRUMBLE_Role"}) do
  player:GetAttributeChangedSignal(attribute):Connect(function() decorateHeroCharacter(player) end)
 end
 local function onCharacterAdded(character:Model)
  -- Roblox CharacterAdded can run before UpperTorso/Torso is inserted.
  -- One bounded delayed recheck prevents missing all V3 costumes after respawn.
  task.defer(function()
   if player.Character==character then decorateHeroCharacter(player) end
  end)
  task.delay(.35,function()
   if player.Parent and player.Character==character then decorateHeroCharacter(player) end
  end)
 end
 player.CharacterAdded:Connect(onCharacterAdded)
 if player.Character then onCharacterAdded(player.Character) end
end

for _,player in ipairs(Players:GetPlayers()) do watchRole(player) end
Players.PlayerAdded:Connect(watchRole)
for _,source in ipairs(workspace:GetChildren()) do connectStandSource(source) end
workspace.ChildAdded:Connect(connectStandSource)
for _,instance in ipairs(workspace:GetDescendants()) do
 if instance:IsA("Model") and instance:GetAttribute("EGGRUMBLE_BotId")~=nil then decorateAI(instance) end
 if instance:IsA("BasePart") and instance.Name:match("^ROLE_[A-Z]+$") then decorateLobbyRoleStand(instance) end
end
workspace.DescendantAdded:Connect(function(instance)
 if instance:IsA("Model") and instance.Name:sub(1,9)=="AI_Actor_" then
  task.defer(function() if instance.Parent then decorateAI(instance) end end)
 elseif instance:IsA("BasePart") and instance.Name:match("^ROLE_[A-Z]+$") then
  task.defer(function() if instance.Parent then decorateLobbyRoleStand(instance) end end)
 elseif instance:IsA("BasePart") and instance.Name=="HumanoidRootPart" then
  local ancestor=instance.Parent
  if ancestor and ancestor:IsA("Model") and ancestor:GetAttribute("EGGRUMBLE_BotId")~=nil then
   task.defer(function() decorateAI(ancestor) end)
  end
 end
end)
print("[EGGRUMBLE ART] 7 hero silhouettes / bot armor overlay source loaded; Studio only; art acceptance pending")
