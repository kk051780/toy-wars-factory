-- #765 lane4. Server-only elemental access policy; not a RemoteEvent, HP, damage or Store authority.
-- All context, registry and grant tables MUST be constructed and owned by existing authoritative Host/Item server.
local M = {}
local LEVELS = {
 WARRIOR={FIRE=1,EARTH=7,DIVINE=25},
 MAGE={ICE=1,FIRE=5,LIGHTNING=12},
 NINJA={WIND=1,ICE=9,LIGHTNING=15},
 TRAPPER={LIGHTNING=1,EARTH=7,FIRE=15},
 BUILDER={EARTH=1,WATER=7,ICE=14},
 BEAST={WATER=1,WIND=7,FIRE=15},
 ZOMBIE={EARTH=1,ICE=9,CURSE=20},
}
local STARTER={WARRIOR="FIRE",MAGE="ICE",NINJA="WIND",TRAPPER="LIGHTNING",
 BUILDER="EARTH",BEAST="WATER",ZOMBIE="EARTH"}
local ELEMENT={FIRE=true,WATER=true,ICE=true,WIND=true,EARTH=true,LIGHTNING=true,DIVINE=true,CURSE=true}
local function finite(n)
 return type(n)=="number" and n==n and n~=math.huge and n~=-math.huge
end
local function validContext(ctx)
 return type(ctx)=="table" and ctx.serverOwned==true
  and ctx.activeMatch==true and ctx.currentAvatar==true
  and type(ctx.sessionId)=="string" and #ctx.sessionId>0
  and LEVELS[ctx.role]~=nil and finite(ctx.now) and ctx.now>=0
  and finite(ctx.level) and ctx.level>=1 and ctx.level<=500 and ctx.level%1==0
end
function M.starter(role)
 return STARTER[role]
end
function M.unlockLevel(role,element)
 local levels=LEVELS[role]
 return levels and levels[element] or nil
end
function M.pickupSpec(element)
 if not ELEMENT[element] then return nil end
 -- Upper attributes are a brief taste, not an unearned permanent final form.
 if element=="DIVINE" or element=="CURSE" then return {duration=10,charges=1} end
 return {duration=24,charges=2}
end
-- A pickup is minted in the existing Item server, never from a client claim.
-- registry[pickupId] must already exist from server-spawned world objects.
-- A given world pickup can be used exactly once globally, even across teams.
function M.issuePickup(ctx,pickupId,element,registry,grants)
 if not validContext(ctx) then return false,"INVALID_SERVER_CONTEXT" end
 if not ELEMENT[element] or type(pickupId)~="string" or #pickupId==0 then
  return false,"INVALID_PICKUP" end
 if type(registry)~="table" or type(grants)~="table" then return false,"INVALID_STORAGE" end
 local record=registry[pickupId]
 if type(record)~="table" or record.available~=true
  or record.element~=element or record.sessionId~=ctx.sessionId then
  return false,"UNVERIFIED_OR_TAKEN_PICKUP" end
 local required=M.unlockLevel(ctx.role,element)
 if required and ctx.level>=required then return false,"ALREADY_UNLOCKED" end
 local spec=M.pickupSpec(element)
 -- No yield between marking a verified pickup as taken and publishing the grant.
 record.available=false
 grants[element]={element=element,sessionId=ctx.sessionId,role=ctx.role,
  issuedAt=ctx.now,expiresAt=ctx.now+spec.duration,charges=spec.charges,pickupId=pickupId}
 return true,"PICKUP_GRANTED"
end
-- Call once AFTER existing Host/Combat confirms a real, valid cast.
-- The same call validates and consumes a temporary charge; there is no separate
-- check/consume race and no extra server damage/HP authorization.
function M.authorizeAndConsume(ctx,element,grants)
 if not validContext(ctx) then return false,"INVALID_SERVER_CONTEXT" end
 if not ELEMENT[element] then return false,"UNKNOWN_ELEMENT" end
 local required=M.unlockLevel(ctx.role,element)
 if required and ctx.level>=required then return true,"LEVEL" end
 if type(grants)~="table" then return false,"NO_PICKUP_GRANT" end
 local grant=grants[element]
 if type(grant)~="table" or grant.element~=element or grant.sessionId~=ctx.sessionId
  or grant.role~=ctx.role or not finite(grant.issuedAt) or not finite(grant.expiresAt)
  or not finite(grant.charges) or grant.charges%1~=0
  or grant.charges<1 or grant.charges>2 or grant.issuedAt>ctx.now then
  return false,"INVALID_GRANT" end
 if grant.expiresAt <= ctx.now then return false,"PICKUP_EXPIRED" end
 grant.charges=grant.charges-1
 if grant.charges==0 then grants[element]=nil end
 return true,"PICKUP"
end
return M
