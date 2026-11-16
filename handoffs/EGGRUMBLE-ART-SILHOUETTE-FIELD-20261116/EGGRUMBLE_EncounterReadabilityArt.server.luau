--!strict
-- EGGRUMBLE V3: independent, Studio-only visual language on the original game.
-- P0D ART-A01 scope. DO NOT change neutral HP/KO, egg stock, rewards, mode queues,
-- ProximityPrompts, castle combat, AI nav, ability Remotes, or source actor ownership.
-- No collidable art, new combat scripts, loops, particles, permanent GUIs or monetization.
local RunService=game:GetService("RunService")
local TweenService=game:GetService("TweenService")
local Debris=game:GetService("Debris")
local Players=game:GetService("Players")
if not RunService:IsStudio() then return end

local ROOT_NAME="EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW"
local MAX_DECORATED_NEUTRALS_PER_ARENA=24
local MAX_DECORATED_EGGS_PER_ARENA=28
local MAX_DECORATED_ITEMS_PER_WORLD=12
local MAX_SIMULTANEOUS_KO_BURSTS=8
local MAX_GATE_PIECES=7
local activeNeutrals:{[Instance]:number}={}
local activeEggs:{[Instance]:number}={}
local activeItems:{[Instance]:number}={}
local activeBurst=0
local marked:{[Instance]:boolean}={}
local ceramic=Color3.fromRGB(205,193,160)
local gold=Color3.fromRGB(231,187,103)
local jade=Color3.fromRGB(82,168,131)
local steel=Color3.fromRGB(93,117,142)
local maroon=Color3.fromRGB(137,64,76)
local dark=Color3.fromRGB(64,73,88)

local function previewFor(instance:Instance):Instance?
 local ptr:Instance?=instance
 while ptr do
  if ptr.Name==ROOT_NAME then return ptr end
  ptr=ptr.Parent
 end
 return nil
end

local function arenaFor(instance:Instance):Instance?
 local ptr:Instance?=instance
 while ptr do
  if ptr.Name=="TEAM_Arena" or ptr.Name=="BATTLE_ROYALE_Arena" then
   if ptr.Parent and ptr.Parent.Name==ROOT_NAME then return ptr end
   return nil
  end
  ptr=ptr.Parent
 end
 return nil
end

local function itemPreviewFor(instance:Instance):Instance?
 local ptr:Instance?=instance
 while ptr do
  if ptr.Name=="EGGRUMBLE_ItemPreviewWorld" then return ptr end
  ptr=ptr.Parent
 end
 return nil
end

-- Weld to the actual gameplay part, never add independent world Anchored obstacles.
local function jewel(parent:Instance,anchor:BasePart,name:string,shape:string,
 size:Vector3,offset:CFrame,color:Color3,material:Enum.Material,transparency:number?):BasePart
 local p:BasePart
 if shape=="Wedge" then p=Instance.new("WedgePart")
 else
  local q=Instance.new("Part")
  if shape=="Cylinder" then q.Shape=Enum.PartType.Cylinder end
  if shape=="Ball" then q.Shape=Enum.PartType.Ball end
  p=q
 end
 p.Name="ART_"..name
 p.Size=size
 p.CFrame=anchor.CFrame*offset
 p.Color=color
 p.Material=material
 p.Transparency=transparency or 0
 p.Anchored=false
 p.CanCollide=false
 p.CanTouch=false
 p.CanQuery=false
 p.CastShadow=false
 p.Massless=true
 p.Parent=parent
 local weld=Instance.new("WeldConstraint")
 weld.Part0=anchor
 weld.Part1=p
 weld.Parent=p
 return p
end

local function deathCue(neutral:Model)
 -- The neutral Humanoid's real death is the only trigger, never a fake 10,000-KO counter.
 if activeBurst>=MAX_SIMULTANEOUS_KO_BURSTS then return end
 local root=neutral.PrimaryPart
 if not root or not root.Parent then return end
 local nearHuman=false
 for _,player in ipairs(Players:GetPlayers()) do
  local character=player.Character
  local pr=character and character:FindFirstChild("HumanoidRootPart")::BasePart?
  if pr and (pr.Position-root.Position).Magnitude<=125 then
   nearHuman=true;break
  end
 end
 if not nearHuman then return end
 activeBurst+=1
 local ring=Instance.new("Part")
 ring.Name="ART_TrueNeutralKOCue"
 ring.Shape=Enum.PartType.Cylinder
 ring.Size=Vector3.new(.17,2.4,2.4)
 ring.CFrame=CFrame.new(root.Position-Vector3.new(0,1.1,0))*CFrame.Angles(0,0,math.rad(90))
 ring.Material=Enum.Material.Glass
 ring.Color=jade
 ring.Transparency=.2
 ring.Anchored=true
 ring.CanCollide=false
 ring.CanTouch=false
 ring.CanQuery=false
 ring.CastShadow=false
 -- Transient cue is outside the dead model so Debris owns its guaranteed cleanup.
 ring.Parent=previewFor(neutral) or workspace
 TweenService:Create(ring,TweenInfo.new(.21,Enum.EasingStyle.Quad,Enum.EasingDirection.Out),{
  Size=Vector3.new(.17,7.2,7.2),Transparency=1
 }):Play()
 Debris:AddItem(ring,.25)
 task.delay(.28,function() activeBurst=math.max(0,activeBurst-1) end)
end

local function decorateNeutral(neutral:Model)
 if marked[neutral] or neutral:GetAttribute("EGGRUMBLE_Neutral")~=true then return end
 if neutral.Name~="HordeSoldier" then return end
 local arena=arenaFor(neutral)
 local root=neutral:FindFirstChild("HumanoidRootPart")
 local head=neutral:FindFirstChild("Head")
 local hum=neutral:FindFirstChildOfClass("Humanoid")
 if not arena or not root or not root:IsA("BasePart") or not head or not head:IsA("BasePart") or not hum then return end
 if (activeNeutrals[arena] or 0)>=MAX_DECORATED_NEUTRALS_PER_ARENA then return end
 marked[neutral]=true
 activeNeutrals[arena]=(activeNeutrals[arena] or 0)+1
 local art=Instance.new("Folder")
 art.Name="EGGRUMBLE_NeutralArt_VisualOnly"
 art.Parent=neutral
 -- Each small low-rank neutral gets two distinctive LOW-POLY armor masses,
 -- not a full-size boss or twenty separate particle emitters.
 jewel(art,root,"TornMantle","Wedge",Vector3.new(1.85,.75,1.15),
  CFrame.new(0,.7,.45)*CFrame.Angles(0,math.pi,0),dark,Enum.Material.Fabric)
 jewel(art,head,"BoneCrest","Wedge",Vector3.new(.68,.78,1.0),
  CFrame.new(0,.61,0),ceramic,Enum.Material.SmoothPlastic)
 local fired=false
 hum.Died:Connect(function()
  if fired then return end
  fired=true
  deathCue(neutral)
 end)
 neutral.Destroying:Connect(function()
  activeNeutrals[arena]=math.max(0,(activeNeutrals[arena] or 1)-1)
  marked[neutral]=nil
 end)
end

local function decorateEgg(egg:BasePart)
 if marked[egg] then return end
 local arena=arenaFor(egg)
 if not arena then return end
 if not (egg.Name:match("^FieldEgg_%d+$") or egg.Name:match("^ReleasedEgg_")) then return end
 if (activeEggs[arena] or 0)>=MAX_DECORATED_EGGS_PER_ARENA then return end
 marked[egg]=true
 activeEggs[arena]=(activeEggs[arena] or 0)+1
 -- The pickup remains the original ProximityPrompt host and the sole egg authority.
 local trim=Instance.new("Folder")
 trim.Name="EGGRUMBLE_EggVisual_VisualOnly"
 trim.Parent=egg
 jewel(trim,egg,"GoldenCradle","Cylinder",Vector3.new(.16,4.35,4.35),
  CFrame.new(0,-1.5,0)*CFrame.Angles(0,0,math.rad(90)),gold,Enum.Material.Metal)
 jewel(trim,egg,"TopGem","Wedge",Vector3.new(1.1,.85,1.1),
  CFrame.new(0,1.54,0),jade,Enum.Material.Glass,.12)
 egg.Destroying:Connect(function()
  activeEggs[arena]=math.max(0,(activeEggs[arena] or 1)-1)
  marked[egg]=nil
 end)
end

local function decorateFieldItem(item:BasePart)
 if marked[item] then return end
 local kind=item.Name:match("^ITEM_%d+_(%u+)$")
 if kind~="HEAL" and kind~="DASH" and kind~="SHIELD" then return end
 local world=arenaFor(item) or itemPreviewFor(item)
 if not world then return end
 if (activeItems[world] or 0)>=MAX_DECORATED_ITEMS_PER_WORLD then return end
 marked[item]=true
 activeItems[world]=(activeItems[world] or 0)+1
 local trim=Instance.new("Folder")
 trim.Name="EGGRUMBLE_FieldItemVisual_VisualOnly"
 trim.Parent=item
 -- Three SHAPES and colors, not three unreadable identical neon balls:
 -- healing = cross, dash = swept wing, shield = guarded crest.
 local roleColor=if kind=="HEAL" then jade elseif kind=="DASH" then steel else maroon
 jewel(trim,item,"GroundHalo","Cylinder",Vector3.new(.14,3.6,3.6),
  CFrame.new(0,-1.3,0)*CFrame.Angles(0,0,math.rad(90)),roleColor,Enum.Material.Metal)
 if kind=="HEAL" then
  jewel(trim,item,"RemedyCross","Block",Vector3.new(.55,1.8,.4),
   CFrame.new(0,1.3,0),ceramic,Enum.Material.SmoothPlastic)
 elseif kind=="DASH" then
  jewel(trim,item,"WingTip","Wedge",Vector3.new(1.65,1.4,.42),
   CFrame.new(0,1.3,0)*CFrame.Angles(0,0,math.rad(24)),gold,Enum.Material.Metal)
 else
  jewel(trim,item,"GuardDiamond","Wedge",Vector3.new(1.45,1.45,.38),
   CFrame.new(0,1.3,0)*CFrame.Angles(0,0,math.rad(45)),ceramic,Enum.Material.Slate)
 end
 item.Destroying:Connect(function()
  activeItems[world]=math.max(0,(activeItems[world] or 1)-1)
  marked[item]=nil
 end)
end

local function decorateVault(part:BasePart)
 if marked[part] then return end
 if part.Name~="EggVault" and part.Name~="OwnEggDeposit" then return end
 if not arenaFor(part) then return end
 marked[part]=true
 local art=Instance.new("Folder")
 art.Name="EGGRUMBLE_CastleEggStationArt_VisualOnly"
 art.Parent=part
 local isVault=part.Name=="EggVault"
 jewel(art,part,"StationBadge","Cylinder",Vector3.new(.15,2.9,2.9),
  CFrame.new(0,part.Size.Y/2+.6,0)*CFrame.Angles(0,0,math.rad(90)),
  if isVault then gold else jade,Enum.Material.Metal)
 -- Distinguish enemy-vault theft from your own deposit through shape and color.
end

local function decorateModeGate(gate:BasePart)
 if marked[gate] then return end
 if gate.Name~="TEAM_PORTAL" and gate.Name~="BATTLE_ROYALE_PORTAL" then return end
 if not previewFor(gate) then return end
 marked[gate]=true
 local team=gate.Name=="TEAM_PORTAL"
 local c=if team then maroon else steel
 local art=Instance.new("Folder")
 art.Name="EGGRUMBLE_ModeGateFrame_VisualOnly"
 art.Parent=gate
 local n=0
 local function g(name:string,shape:string,sz:Vector3,off:CFrame,color:Color3)
  if n>=MAX_GATE_PIECES then return end
  n+=1
  jewel(art,gate,name,shape,sz,off,color,Enum.Material.Metal)
 end
 -- Distinct silhouette and no new billboard:
 -- TEAM: low fortress battlements. BR: taller three-point crown.
 for _,side in ipairs({-1,1}) do
  g("Upright"..side,"Wedge",Vector3.new(1.4,11.8,2.7),
   CFrame.new(side*5.15,0,.3)*CFrame.Angles(0,math.rad(side*90),0),c)
 end
 g("GateLintel","Block",Vector3.new(12.2,1.3,2.6),
  CFrame.new(0,6.18,.25),ceramic)
 if team then
  for _,side in ipairs({-1,1}) do
   g("Battlement"..side,"Block",Vector3.new(2.5,2.2,2.7),
    CFrame.new(side*3.65,7.73,.3),c)
  end
 else
  for _,side in ipairs({-1,1}) do
   g("CrownSpike"..side,"Wedge",Vector3.new(2.2,3.4,2.6),
    CFrame.new(side*3.65,8.16,.3),c)
  end
 end
 g("PortalMedallion","Cylinder",Vector3.new(.16,2.4,2.4),
  CFrame.new(0,6.9,-1.28)*CFrame.Angles(0,0,math.rad(90)),gold)
end

local DEFENSE_COLORS:{[string]:Color3}={
 HARDENED=ceramic,REPAIR=jade,TURRET=gold,TRAP=maroon,SENSOR=steel
}
local function decorateDefense(stand:BasePart)
 if marked[stand] or not previewFor(stand) then return end
 local id=stand.Name:match("^DEFENSE_(%u+)$")
 if not id or not DEFENSE_COLORS[id] then return end
 marked[stand]=true
 local art=Instance.new("Folder")
 art.Name="EGGRUMBLE_DefenseModuleVisualOnly"
 art.Parent=stand
 jewel(art,stand,"ModuleDisc","Cylinder",Vector3.new(.22,2.2,2.2),
  CFrame.new(0,stand.Size.Y/2+.5,0)*CFrame.Angles(0,0,math.rad(90)),
  DEFENSE_COLORS[id],Enum.Material.Metal)
 -- Only the original server rules determine a module's defensive power.
end

local function process(instance:Instance)
 -- The authored 9-pickup field-item preview runs independently from the V3 lobby.
 -- Both visual-only variants are supported with the SAME isolated script.
 if instance:IsA("BasePart") and instance.Name:match("^ITEM_%d+_%u+$") then
  decorateFieldItem(instance)
  return
 end
 if not previewFor(instance) then return end
 if instance:IsA("Model") and instance.Name=="HordeSoldier" then
  task.defer(function() if instance.Parent then decorateNeutral(instance) end end)
 elseif instance:IsA("BasePart") then
  if instance.Name=="HumanoidRootPart" and instance.Parent and instance.Parent.Name=="HordeSoldier" then
   local m=instance.Parent
   task.defer(function() if m:IsA("Model") then decorateNeutral(m) end end)
  elseif instance.Name=="Head" and instance.Parent and instance.Parent.Name=="HordeSoldier" then
   local m=instance.Parent
   task.defer(function() if m:IsA("Model") then decorateNeutral(m) end end)
  elseif instance.Name:match("^FieldEgg_%d+$") or instance.Name:match("^ReleasedEgg_") then
   decorateEgg(instance)
  elseif instance.Name=="EggVault" or instance.Name=="OwnEggDeposit" then
   decorateVault(instance)
  elseif instance.Name=="TEAM_PORTAL" or instance.Name=="BATTLE_ROYALE_PORTAL" then
   decorateModeGate(instance)
  elseif instance.Name:match("^DEFENSE_%u+$") then
   decorateDefense(instance)
  end
 end
end

for _,instance in ipairs(workspace:GetDescendants()) do process(instance) end
workspace.DescendantAdded:Connect(process)
print("[EGGRUMBLE ART] true-KO cues, capped small-neutral silhouettes, egg visibility and 2 gate shapes / Studio only")
