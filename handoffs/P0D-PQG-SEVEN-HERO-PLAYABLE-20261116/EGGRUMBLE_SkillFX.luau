--!strict
-- EGGRUMBLE V3 vivid but bounded 7-job VFX: no heavy lights, textures or assets.
-- 7 distinctive visual grammars; A/B/C alter size, pulse count and color rhythm.
-- 72 short-lived pooled-in-budget emissive objects per server, not a promise of 30fps.
local TweenService=game:GetService("TweenService")
local Debris=game:GetService("Debris")
local SkillFX={}
local ACTIVE_LIMIT=72
local MAX_NEW_PER_PULSE=6
local active=0
local palettes={
 WARRIOR={Color3.fromRGB(255,199,62),Color3.fromRGB(242,73,52)},
 MAGE={Color3.fromRGB(83,201,255),Color3.fromRGB(244,102,43)},
 NINJA={Color3.fromRGB(179,112,255),Color3.fromRGB(61,244,212)},
 TRAPPER={Color3.fromRGB(203,86,252),Color3.fromRGB(117,71,247)},
 BUILDER={Color3.fromRGB(58,248,214),Color3.fromRGB(255,203,67)},
 BEAST={Color3.fromRGB(249,174,55),Color3.fromRGB(249,83,69)},
 ZOMBIE={Color3.fromRGB(102,253,140),Color3.fromRGB(187,69,231)},
}
local function effectPart(parent:Instance,name:string,at:Vector3,size:Vector3,color:Color3,life:number):Part?
 if active>=ACTIVE_LIMIT then return nil end
 active+=1
 local p=Instance.new("Part");p.Name=name;p.Anchored=true
 p.CanCollide=false;p.CanTouch=false;p.CanQuery=false
 p.CastShadow=false;p.Material=Enum.Material.Neon
 p.Size=size;p.Color=color;p.Transparency=.18;p.Position=at;p.Parent=parent
 Debris:AddItem(p,life+.15)
 task.delay(life+.15,function()
  if p.Parent then p:Destroy() end
  active=math.max(0,active-1)
 end)
 return p
end
local function animate(p:Part?,endSize:Vector3,life:number,goalCFrame:CFrame?)
 if not p then return end
 local goal={Size=endSize,Transparency=1}
 if goalCFrame then goal.CFrame=goalCFrame end
 TweenService:Create(p,TweenInfo.new(life,Enum.EasingStyle.Quad,Enum.EasingDirection.Out),goal):Play()
end
local function particleBurst(p:Part?,color:Color3,amount:number)
 if not p then return end
 local emitter=Instance.new("ParticleEmitter")
 emitter.Name="HitSparks"
 emitter.Rate=0;emitter.LightEmission=.6
 emitter.Lifetime=NumberRange.new(.18,.34)
 emitter.Speed=NumberRange.new(9,18)
 emitter.Drag=7
 emitter.SpreadAngle=Vector2.new(130,130)
 emitter.Size=NumberSequence.new({NumberSequenceKeypoint.new(0,.5),NumberSequenceKeypoint.new(1,0)})
 emitter.Transparency=NumberSequence.new({NumberSequenceKeypoint.new(0,.1),NumberSequenceKeypoint.new(1,1)})
 emitter.Color=ColorSequence.new(color)
 emitter.Parent=p
 emitter:Emit(math.min(amount,12))
end
function SkillFX.emit(parent:Instance,role:string,slot:string,origin:Vector3,forward:Vector3,center:Vector3,radius:number)
 local palette=palettes[role];if not palette or not parent.Parent then return end
 if active>ACTIVE_LIMIT-MAX_NEW_PER_PULSE then return end
 local f=Vector3.new(forward.X,0,forward.Z)
 if f.Magnitude<.05 then f=Vector3.new(0,0,-1) else f=f.Unit end
 local right=Vector3.new(-f.Z,0,f.X)
 local primary=palette[1]
 local secondary=if slot=="A" then palette[2] else palette[1]
 local life=if slot=="C" then .72 elseif slot=="B" then .57 else .36
 local scale=if slot=="C" then 1.4 elseif slot=="B" then 1.1 else .85
 local head=effectPart(parent,"FX_"..role.."_"..slot.."_FLASH",center,Vector3.new(2,2,2),primary,life)
 if head then
  head.Shape=Enum.PartType.Ball
  animate(head,Vector3.new(radius*1.45*scale,2.4,radius*1.45*scale),life)
  particleBurst(head,secondary,if slot=="C" then 12 else 5)
 end
 -- Shared readable impact ring, kept thin so enemies and environment stay visible.
 local ring=effectPart(parent,"FX_"..role.."_RING",center+Vector3.new(0,.3,0),
  Vector3.new(.8,.22,.8),secondary,life*.9)
 if ring then
  ring.Shape=Enum.PartType.Cylinder
  ring.CFrame=CFrame.new(ring.Position)*CFrame.Angles(0,0,math.pi/2)
  animate(ring,Vector3.new(.3,radius*1.45,radius*1.45),life*.9)
 end
 if role=="WARRIOR" then
  -- Three sweeping sword wave edges; their crossed slash silhouette identifies 武神.
  for i=-1,1 do
   local at=center+right*i*2+Vector3.new(0,2,0)
   local p=effectPart(parent,"WarGod_FlyingSlash",at,Vector3.new(.22,3,radius*.7),primary,life)
   if p then
    p.CFrame=CFrame.lookAt(at,at+f)*CFrame.Angles(0,0,i*.28)
    animate(p,Vector3.new(.08,5,radius*1.7),life,CFrame.lookAt(at+f*6,at+f*10))
   end
  end
 elseif role=="MAGE" then
  for i=1,3 do
   local a=i*math.pi*2/3
   local at=center+Vector3.new(math.cos(a)*radius*.55,1.5,math.sin(a)*radius*.55)
   local p=effectPart(parent,"Mage_CrystalStorm",at,Vector3.new(1.2,3,1.2),secondary,life)
   if p then p.CFrame=CFrame.new(at)*CFrame.Angles(.4*i,.2*i,.25*i)
    animate(p,Vector3.new(.15,6,.15),life,CFrame.new(at+Vector3.new(0,5,0))*CFrame.Angles(1,1,1)) end
  end
 elseif role=="NINJA" then
  for i=1,3 do
   local at=origin+f*i*3+right*(i-2)*2+Vector3.new(0,1.7,0)
   local p=effectPart(parent,"Assassin_ShadowAfterimage",at,Vector3.new(1.4,4,.25),secondary,life)
   if p then
    p.CFrame=CFrame.lookAt(at,at+f)*CFrame.Angles(0,0,i*.3)
    animate(p,Vector3.new(.15,5,.07),life,CFrame.lookAt(at+f*5,at+f*10))
   end
  end
 elseif role=="TRAPPER" then
  for i=1,3 do
   local a=i*math.pi*2/3
   local at=center+right*math.cos(a)*radius*.65+f*math.sin(a)*radius*.65+Vector3.new(0,2,0)
   local p=effectPart(parent,"Esper_PsiOrbit",at,Vector3.new(2.3,2.3,2.3),secondary,life)
   if p then
    p.CFrame=CFrame.new(at)*CFrame.Angles(a,.5,a)
    animate(p,Vector3.new(.12,.12,.12),life,CFrame.new(center)*CFrame.Angles(a*3,a*3,0))
   end
  end
 elseif role=="BUILDER" then
  for i=-1,1 do
   local at=origin+Vector3.new(0,2.3,0)+right*i*2+f*4
   local p=effectPart(parent,"MadScientist_RailShot",at,Vector3.new(.35,.35,5),secondary,life)
   if p then
    p.CFrame=CFrame.lookAt(at,at+f)
    animate(p,Vector3.new(.07,.07,15),life,CFrame.lookAt(at+f*11,at+f*18))
   end
  end
 elseif role=="BEAST" then
  for i=-1,1 do
   local at=center+right*i*radius*.38+Vector3.new(0,2.8,0)
   local p=effectPart(parent,"Beast_FangClaw",at,Vector3.new(1.1,5,.9),secondary,life)
   if p then
    p.CFrame=CFrame.lookAt(at,at+f)*CFrame.Angles(.5,i*.25,.4*i)
    animate(p,Vector3.new(.12,8,.2),life,CFrame.new(at+f*5)*CFrame.Angles(.8,i*.25,.6*i))
   end
  end
 elseif role=="ZOMBIE" then
  for i=-1,1 do
   local at=center+right*i*radius*.4+Vector3.new(0,1.3,0)
   local p=effectPart(parent,"CurseMaster_SoulFlame",at,Vector3.new(1.6,3,1.6),secondary,life)
   if p then p.Shape=Enum.PartType.Ball
    animate(p,Vector3.new(.4,7,.4),life,CFrame.new(at+Vector3.new(0,6,0))) end
  end
 end
 -- Each ultimate gets exactly ONE additional signature monument; total <=6 Parts/pulse.
 -- C is legible even among mobs and still bounded by the shared 72-part budget.
 if slot=="C" then
  local signatureNames={
   WARRIOR="ULTIMATE_WarGod_DivineHalo",
   MAGE="ULTIMATE_Mage_StormPillar",
   NINJA="ULTIMATE_Assassin_ShadowCross",
   TRAPPER="ULTIMATE_Esper_GravitySingularity",
   BUILDER="ULTIMATE_Scientist_OverdriveCore",
   BEAST="ULTIMATE_Beast_TitanShadow",
   ZOMBIE="ULTIMATE_Curse_SoulGate",
  }
  local tower=effectPart(parent,signatureNames[role] or "ULTIMATE_Unknown",
   center+Vector3.new(0,4,0),Vector3.new(2,4,2),secondary,.66)
  if tower then
   local final=Vector3.new(5,10,5)
   if role=="WARRIOR" then
    tower.Shape=Enum.PartType.Cylinder
    final=Vector3.new(1,16,16)
    tower.CFrame=CFrame.new(tower.Position)*CFrame.Angles(0,0,math.pi/2)
   elseif role=="MAGE" then
    final=Vector3.new(3,21,3)
   elseif role=="NINJA" then
    final=Vector3.new(16,.2,3)
    tower.CFrame=CFrame.lookAt(tower.Position,tower.Position+f)*CFrame.Angles(0,0,math.pi/4)
   elseif role=="TRAPPER" then
    tower.Shape=Enum.PartType.Ball
    final=Vector3.new(.4,.4,.4)
    tower.Size=Vector3.new(10,10,10)
   elseif role=="BUILDER" then
    final=Vector3.new(4,4,16)
    tower.CFrame=CFrame.lookAt(tower.Position,tower.Position+f)
   elseif role=="BEAST" then
    final=Vector3.new(12,18,6)
   elseif role=="ZOMBIE" then
    tower.Shape=Enum.PartType.Cylinder
    final=Vector3.new(.6,14,14)
    tower.CFrame=CFrame.new(tower.Position)*CFrame.Angles(0,0,math.pi/2)
   end
   animate(tower,final,.66)
  end
 end
end
function SkillFX.active():number return active end
return SkillFX
