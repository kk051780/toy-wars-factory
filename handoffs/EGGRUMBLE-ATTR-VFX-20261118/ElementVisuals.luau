-- BATTLE-ATTR-VFX / #765 lane 2. Replicated ModuleScript; client presentation ONLY; never grants damage or an attribute.
-- Use only after an existing server-authoritative cast/HIT/shield signal.
-- One invisible anchor and at most eight short Beams per event, no neon-box spam.
local Visual = {}

-- Distinct silhouettes: readable without color. Coordinates are a normalized camera-plane trace.
local SHAPES = {
 FIRE     = {color={255,117,44}, points={{-.6,-.6},{-.25,.0},{-.5,.25},{0,1},{.15,.25},{.5,.65},{.3,-.2},{.65,-.6}}},
 WATER    = {color={57,176,255}, points={{-.9,.1},{-.6,.55},{-.25,.55},{0,.1},{.3,-.35},{.6,-.35},{.9,.1}}},
 LIGHTNING= {color={255,221,73}, points={{-.3,1},{.2,.35},{-.2,.1},{.3,-.25},{-.1,-.45},{.35,-1}}},
 WIND     = {color={173,242,186}, points={{-.8,-.4},{-.3,-.7},{.4,-.55},{.8,-.1},{.6,.45},{0,.7},{-.5,.4},{-.1,.1}}},
 EARTH    = {color={185,136,81}, points={{-.75,-.55},{-.6,.4},{-.15,.85},{.15,.15},{.55,.65},{.8,-.55},{.2,-.85},{-.75,-.55}}},
 ICE      = {color={185,227,255}, points={{0,1},{0,-1},{0,0},{-.8,.5},{.8,-.5},{0,0},{.8,.5},{-.8,-.5}}},
 DIVINE   = {color={255,239,166}, points={{0,1},{.7,.7},{1,0},{.7,-.7},{0,-1},{-.7,-.7},{-1,0},{-.7,.7},{0,1}}},
 CURSE    = {color={187,104,230}, points={{-.8,.8},{-.25,.25},{-.6,-.15},{0,-.7},{.6,-.15},{.25,.25},{.8,.8},{.3,.85}}},
}
local KINDS={WEAPON=true, ATTACK=true, SHIELD=true}
local OUTCOMES={NORMAL=true, ADVANTAGE=true, RESIST=true, IMMUNE=true}
local active = {}
local MAX_ACTIVE=8
local MAX_BEAMS=8
local function finite(x)
 return type(x)=="number" and x==x and x~=math.huge and x~=-math.huge
end
function Visual.describe(element,kind,outcome,lowEnd)
 local shape=SHAPES[element]
 if not shape or not KINDS[kind] or not OUTCOMES[outcome] then return nil end
 local beamCount=math.min(#shape.points-1,lowEnd and 4 or MAX_BEAMS)
 local duration=if kind=="WEAPON" then .42 elseif kind=="SHIELD" then .9 else .62
 local weight=if outcome=="ADVANTAGE" then .18 elseif outcome=="RESIST" then .07
  elseif outcome=="IMMUNE" then .045 else .12
 return {element=element,kind=kind,outcome=outcome,color=shape.color,
  silhouette=shape.points,beamCount=beamCount,duration=duration,width=weight,
  pulse=outcome=="ADVANTAGE" and 2 or 1,drawSlash=outcome=="IMMUNE"}
end
function Visual.capacity()
 return MAX_ACTIVE,MAX_BEAMS
end

-- Reuse the actual camera basis; this displays a graphic cue near an already confirmed event.
-- This function MUST only be called on a client; no RemoteEvent, TakeDamage, XP, or HP writes.
function Visual.render(element,kind,outcome,position,lowEnd)
 local d=Visual.describe(element,kind,outcome,lowEnd)
 if not d or typeof(position)~="Vector3" then return false end
 if not (finite(position.X) and finite(position.Y) and finite(position.Z)) then return false end
 local RunService=game:GetService("RunService")
 if not RunService:IsClient() then return false end
 local camera=workspace.CurrentCamera
 if not camera then return false end
 local Debris=game:GetService("Debris")
 local holder=Instance.new("Part")
 holder.Name="EGG_AttributeCue_"..d.element
 holder.Transparency=1;holder.Anchored=true
 holder.CanCollide=false;holder.CanTouch=false;holder.CanQuery=false
 holder.Size=Vector3.new(.1,.1,.1)
 holder.CFrame=CFrame.new(position)
 holder.Parent=workspace
 active[#active+1]=holder
 while #active>MAX_ACTIVE do
  local oldest=table.remove(active,1)
  if oldest then oldest:Destroy() end
 end
 local right=camera.CFrame.RightVector
 local up=camera.CFrame.UpVector
 local scale=if kind=="SHIELD" then 2.7 elseif kind=="WEAPON" then 1.1 else 2.1
 local rgb=d.color
 local color=ColorSequence.new(Color3.fromRGB(rgb[1],rgb[2],rgb[3]))
 local function beamBetween(ax,ay,bx,by,width)
  local a=Instance.new("Attachment")
  a.Position=(right*ax+up*ay)*scale
  a.Parent=holder
  local b=Instance.new("Attachment")
  b.Position=(right*bx+up*by)*scale
  b.Parent=holder
  local beam=Instance.new("Beam")
  beam.Attachment0=a;beam.Attachment1=b
  beam.FaceCamera=true;beam.LightEmission=.65;beam.LightInfluence=0
  beam.Width0=width;beam.Width1=width
  beam.Color=color
  beam.Parent=holder
 end
 for i=1,d.beamCount do
  local p=d.silhouette[i];local q=d.silhouette[i+1]
  beamBetween(p[1],p[2],q[1],q[2],d.width)
 end
 -- IMMUNE has an extra slash in regular mode; low-end always honors the strict 4-beam budget.
 if d.drawSlash and not lowEnd and d.beamCount<MAX_BEAMS then
  beamBetween(-.9,-.9,.9,.9,d.width)
 end
 Debris:AddItem(holder,d.duration)
 return true
end
-- Server-confirmed original V3 cast ID mapping: #482 Mage A/B/C, Warrior C mantle, Zombie C curse.
-- No speculative element for other seven-role skills; return nil until a verified server tag exists.
local KNOWN_CASTS={
 MAGE={A="ICE",B="FIRE",C="LIGHTNING"},
 WARRIOR={C="DIVINE"},
 ZOMBIE={C="CURSE"},
}
function Visual.elementForServerCast(signature,serverRole)
 if type(signature)~="string" or type(serverRole)~="string" then return nil,nil end
 local role,slot,seq=string.match(signature,"^([A-Z]+):([ABC]):(%d+)$")
 if not role or role~=serverRole or #seq>10 then return nil,nil end
 local n=tonumber(seq)
 if not n or n<1 or n>2147483647 then return nil,nil end
 local element=KNOWN_CASTS[role] and KNOWN_CASTS[role][slot]
 return element,n
end

return Visual
