--!strict
-- EGGRUMBLE V3: one physically present War God transformation per living character.
-- Server-owned and tied to its character lifetime. Three crest motifs, two shoulder
-- flames and one back halo; no paid power, lighting spam or unlimited Part creation.
local RunService=game:GetService("RunService")
local Debris=game:GetService("Debris")
local Mantle={}
local MAX_ACTIVE_MANTLES=8
local PART_LIMIT_PER_MANTLE=6
local live:{[number]:any}={}
local num=0
local gold=Color3.fromRGB(255,214,73)
local flame=Color3.fromRGB(246,112,52)
local function make(parent:Model,root:BasePart,name:string,shape:Enum.PartType,
 size:Vector3,off:CFrame,color:Color3):Part
 local p=Instance.new("Part")
 p.Name=name
 p.Shape=shape
 p.Size=size
 p.Color=color;p.Material=Enum.Material.Neon
 p.Transparency=.35;p.CastShadow=false
 p.CanCollide=false;p.CanQuery=false;p.CanTouch=false
 p.Massless=true;p.Anchored=false
 p.CFrame=root.CFrame*off
 p.Parent=parent
 local joint=Instance.new("WeldConstraint")
 joint.Name="DivineFixedOffset";joint.Part0=root;joint.Part1=p;joint.Parent=p
 return p
end
local function clear(id:number)
 local old=live[id]
 if not old then return end
 live[id]=nil
 num=math.max(0,num-1)
 if old.deadConnection then old.deadConnection:Disconnect() end
 if old.model and old.model.Parent then old.model:Destroy() end
 if old.highlight and old.highlight.Parent then old.highlight:Destroy() end
 if old.char and old.char.Parent then old.char:SetAttribute("EGGRUMBLE_DivineVisualActive",false) end
end
function Mantle.cancel(player:Player)
 clear(player.UserId)
 local c=player.Character
 if c then
  c:SetAttribute("EGGRUMBLE_KamiUntil",0)
  c:SetAttribute("EGGRUMBLE_DivineVisualActive",false)
 end
end
function Mantle.activate(player:Player,duration:number):boolean
 assert(RunService:IsStudio(),"Private Studio-only divine mantle")
 Mantle.cancel(player)
 local char=player.Character
 local h=char and char:FindFirstChildOfClass("Humanoid")
 local root=char and char:FindFirstChild("HumanoidRootPart")::BasePart?
 if not char or not h or h.Health<=0 or not root then return false end
 duration=math.clamp(duration,.2,6)
 local untilTime=os.clock()+duration
 -- Buff is on this CHARACTER (not persistent Player), so death/respawn cannot inherit it.
 char:SetAttribute("EGGRUMBLE_KamiUntil",untilTime)
 if num>=MAX_ACTIVE_MANTLES then return true end
 num+=1
 local model=Instance.new("Model")
 model.Name="EGGRUMBLE_DivineMantle"
 model.Parent=char
 local parts=0
 local function ornament(name:string,shape:Enum.PartType,size:Vector3,offset:CFrame,color:Color3)
  if parts>=PART_LIMIT_PER_MANTLE then return end
  parts+=1
  make(model,root,name,shape,size,offset,color)
 end
 ornament("DivineCircleBack",Enum.PartType.Cylinder,Vector3.new(.18,5.5,5.5),
  CFrame.new(0,1.1,1.1)*CFrame.Angles(0,0,math.pi/2),gold)
 ornament("DivineFlameLeft",Enum.PartType.Ball,Vector3.new(1.2,2.3,1),
  CFrame.new(-1.6,1.6,.2),flame)
 ornament("DivineFlameRight",Enum.PartType.Ball,Vector3.new(1.2,2.3,1),
  CFrame.new(1.6,1.6,.2),flame)
 ornament("DivineSealSun",Enum.PartType.Ball,Vector3.new(1.3,1.3,.4),
  CFrame.new(0,3,1.2),gold)
 ornament("DivineSealMoon",Enum.PartType.Ball,Vector3.new(.7,.7,.35),
  CFrame.new(-1.8,2.65,1.1),gold)
 ornament("DivineSealStar",Enum.PartType.Ball,Vector3.new(.7,.7,.35),
  CFrame.new(1.8,2.65,1.1),gold)
 local hlt=Instance.new("Highlight")
 hlt.Name="EGGRUMBLE_WarGodGlow"
 hlt.Adornee=char
 hlt.DepthMode=Enum.HighlightDepthMode.Occluded
 hlt.FillColor=gold;hlt.OutlineColor=flame
 hlt.FillTransparency=.84;hlt.OutlineTransparency=.48
 hlt.Parent=char
 local token={}
 live[player.UserId]={model=model,highlight=hlt,char=char,token=token}
 live[player.UserId].deadConnection=h.Died:Connect(function()
  local entry=live[player.UserId]
  if entry and entry.token==token then
   clear(player.UserId)
   if char.Parent then char:SetAttribute("EGGRUMBLE_KamiUntil",0) end
  end
 end)
 char:SetAttribute("EGGRUMBLE_DivineVisualActive",true)
 task.delay(duration,function()
  local entry=live[player.UserId]
  if entry and entry.token==token then
   clear(player.UserId)
   -- Keep buff expiry tied to its own character, never change a respawned avatar.
   if char.Parent then char:SetAttribute("EGGRUMBLE_KamiUntil",0) end
  end
 end)
 return true
end
return Mantle
