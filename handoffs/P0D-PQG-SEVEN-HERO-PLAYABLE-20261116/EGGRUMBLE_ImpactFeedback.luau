--!strict
-- EGGRUMBLE V3. Evidence-based hit feel (never generate a hit response on a miss).
-- Server-side bounded highlights and KO bursts, client receives only a tiny typed attribute pulse.
-- Source is Studio-only preview. No catalog audio IDs, custom assets or heavy lights.
local Debris=game:GetService("Debris")
local Feedback={}
local MAX_FEEDBACK_PER_SEC=18
local MAX_LIVE_HIGHLIGHTS=10
local MAX_KO_BURSTS_PER_SEC=6
local ATTACKER_FEEDBACK_CD=.16
local hitWindow=-1
local hitCount=0
local koWindow=-1
local koCount=0
local highlights=0
local nextAttacker:{[number]:number}={}
local colors={
 WARRIOR=Color3.fromRGB(255,220,95),
 MAGE=Color3.fromRGB(84,206,255),
 NINJA=Color3.fromRGB(191,128,255),
 TRAPPER=Color3.fromRGB(198,94,249),
 BUILDER=Color3.fromRGB(57,241,209),
 BEAST=Color3.fromRGB(255,172,61),
 ZOMBIE=Color3.fromRGB(125,243,146),
}
local function budget(isKO:boolean):boolean
 local second=math.floor(os.clock())
 if isKO then
  if koWindow~=second then koWindow=second;koCount=0 end
  if koCount>=MAX_KO_BURSTS_PER_SEC then return false end
  koCount+=1
 else
  if hitWindow~=second then hitWindow=second;hitCount=0 end
  if hitCount>=MAX_FEEDBACK_PER_SEC then return false end
  hitCount+=1
 end
 return true
end
function Feedback.hit(target:Model,role:string):boolean
 -- Only call after actual Humanoid:TakeDamage, never on an empty skill swing.
 if not target.Parent or highlights>=MAX_LIVE_HIGHLIGHTS then return false end
 if target:GetAttribute("EGGRUMBLE_HitFlashActive")==true then return false end
 if not budget(false) then return false end
 target:SetAttribute("EGGRUMBLE_HitFlashActive",true)
 highlights+=1
 local hl=Instance.new("Highlight")
 hl.Name="EGGRUMBLE_ContactFlash"
 hl.Adornee=target
 hl.DepthMode=Enum.HighlightDepthMode.Occluded
 hl.FillColor=colors[role] or colors.WARRIOR
 hl.OutlineColor=Color3.new(1,1,1)
 hl.FillTransparency=.68
 hl.OutlineTransparency=.38
 hl.Parent=target
 Debris:AddItem(hl,.13)
 task.delay(.16,function()
  highlights=math.max(0,highlights-1)
  if target.Parent then target:SetAttribute("EGGRUMBLE_HitFlashActive",false) end
 end)
 return true
end
function Feedback.ko(world:Instance,target:Model,role:string):boolean
 -- One short radial burst per confirmed Humanoid.Died, not client-predicted KOs.
 if not world.Parent or not target.PrimaryPart or not budget(true) then return false end
 local at=target.PrimaryPart.Position
 local ring=Instance.new("Part")
 ring.Name="EGGRUMBLE_KO_BURST"
 ring.Shape=Enum.PartType.Ball
 ring.Size=Vector3.new(1,1,1)
 ring.Material=Enum.Material.Neon
 ring.Anchored=true;ring.CanCollide=false;ring.CanTouch=false
 ring.CanQuery=false;ring.CastShadow=false
 ring.Color=colors[role] or colors.WARRIOR
 ring.Transparency=.37;ring.Position=at
 ring.Parent=world
 local tween=game:GetService("TweenService"):Create(
  ring,TweenInfo.new(.24,Enum.EasingStyle.Quad,Enum.EasingDirection.Out),
  {Size=Vector3.new(6,3.2,6),Transparency=1})
 tween:Play()
 Debris:AddItem(ring,.32)
 return true
end
function Feedback.attacker(player:Player,role:string,slot:string,actualHits:number):boolean
 if actualHits<=0 or not player.Parent then return false end
 local now=os.clock()
 if now<(nextAttacker[player.UserId] or 0) then return false end
 nextAttacker[player.UserId]=now+ATTACKER_FEEDBACK_CD
 local weight=math.min(3,actualHits)
 player:SetAttribute("EGGRUMBLE_ImpactRole",role)
 player:SetAttribute("EGGRUMBLE_ImpactSlot",slot)
 player:SetAttribute("EGGRUMBLE_ImpactWeight",weight)
 player:SetAttribute("EGGRUMBLE_ImpactSequence",(player:GetAttribute("EGGRUMBLE_ImpactSequence") or 0)+1)
 return true
end
function Feedback.clear(player:Player)
 nextAttacker[player.UserId]=nil
end
return Feedback
