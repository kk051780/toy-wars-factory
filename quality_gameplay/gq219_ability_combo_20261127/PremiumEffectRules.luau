-- Existing #219 V1.3 PREMIUM-003..012. Pure requests, not gameplay authority.
-- Only call inside the existing authoritative Combat transaction. Never accept
-- a client-built context. Combat must validate role-specific attack + premium,
-- ownership, match/cast/actor binding, CD/E, two casts/round, legitimate hits,
-- and atomically reserve/consume receipts. Status/Movement/World/HP own effects.
local M={}
local function finite(x) return type(x)=="number" and x==x and math.abs(x)<math.huge end
local function nonneg(x) return finite(x) and x>=0 end
local function integer(x) return nonneg(x) and x==math.floor(x) and x<=9007199254740991 end
local function index(s) return integer(s) and s<=4 and s+1 or nil end
local function capped(x,cap) if not nonneg(x) or not nonneg(cap) then return nil end return math.min(x,cap) end
local function request(kind,fields)
    fields.kind=kind
    return table.freeze(fields)
end
local echoDelay={0.8,0.9,1,1.1,1.2}
local echoPercent={20,25,30,35,40}
local returnRange={4,6,8,10,12}
local liftHeight={2,3,4,5,6}
local decoyLife={0.7,0.9,1.1,1.3,1.5}
local healFraction={0.01,0.015,0.02,0.025,0.03}
local sealLife={1,1.5,2,2.5,3}
local armorFraction={0.05,0.08,0.11,0.14,0.17}
local armorLife={1,1.25,1.5,1.75,2}
local zoneRadius={3,4,5,6,7}
local zoneLife={2,2.5,3,3.5,4}
local swapRange={3,4,5,6,8}

-- 003: reserve BEFORE the main hit from a single canonical integer budget.
-- Calculate quotient/remainder to avoid large-number multiplication overflow.
function M.reserveEcho(s,budget)
    local i=index(s)
    if not i or not integer(budget) then return nil,"INVALID_BUDGET_OR_STAGE" end
    local q=math.floor(budget/100)
    local r=budget-q*100
    local reserved=q*echoPercent[i]+math.floor(r*echoPercent[i]/100)
    return request("ECHO_RESERVATION",{main=budget-reserved,reserved=reserved,delay=echoDelay[i],maxSecondaryHits=1})
end
-- Combat stores its own reservation, not this returned table as authorization.
-- Used only at original telegraphed location; no recursive effects or new budget.
function M.releaseEcho(s,budget,elapsed,confirmedPrimary,eligibleAtLocation,consumed,remainingCap)
    local p=M.reserveEcho(s,budget)
    if not p or not nonneg(elapsed) or not integer(remainingCap) then return nil,"INVALID_ECHO" end
    if confirmedPrimary~=true or eligibleAtLocation~=true or consumed~=false or elapsed<p.delay then return nil,"ECHO_NOT_ELIGIBLE" end
    local amount=math.min(p.reserved,remainingCap)
    if amount<=0 then return nil,"NO_BUDGET" end
    return request("ECHO_DAMAGE_REQUEST",{maxDamage=amount,maxHits=1,allowRecursive=false})
end

-- 006: select exactly ONE allowed replacement before the existing attack.
-- candidates are the role's canonical, already-unlocked stage-specific options.
function M.replaceAttribute(s,candidates,chosen)
    local i=index(s)
    if not i or type(candidates)~="table" or type(chosen)~="string" or chosen=="" then return nil,"INVALID_ATTRIBUTE" end
    local n=#candidates
    if n<1 or n>i then return nil,"INVALID_CANDIDATE_COUNT" end
    local seen={}
    for k,v in pairs(candidates) do
        if not integer(k) or k<1 or k>n or type(v)~="string" or v=="" or seen[v] then return nil,"INVALID_CANDIDATES" end
        seen[v]=true
    end
    for k=1,n do if type(candidates[k])~="string" then return nil,"INVALID_CANDIDATES" end end
    if not seen[chosen] then return nil,"ATTRIBUTE_NOT_ALLOWED" end
    return request("ATTRIBUTE_REPLACEMENT",{attribute=chosen,maxReactions=1,replaceOriginal=true})
end

-- POST-hit effects. Server's one-time receipt is checked here only as a
-- defensive contract; host must bind it to a real accepted hit and consume it.
-- No yield; no authority writes; no Instances, timers, Remote, XP or score.
function M.planAfterHit(id,s,c)
    local i=index(s)
    if not i or type(c)~="table" or c.confirmedHit~=true or c.consumed~=false or c.active~=true then return nil,"INVALID_HIT_CONTEXT" end
    if id=="PREMIUM-004" then
        if c.explicitReturn~=true or c.selectionOpen~=true or c.safeOrigin~=true or c.canMove~=true or c.carryingEgg~=false then return nil,"RETURN_NOT_ALLOWED" end
        local limit=capped(returnRange[i],c.moveCap)
        if not limit or not nonneg(c.distance) or c.distance<=0 or c.distance>limit then return nil,"RETURN_RANGE" end
        return request("RETURN_TO_VALIDATED_ORIGIN",{maxDistance=limit})
    elseif id=="PREMIUM-005" then
        if c.targetKind=="PLAYER" then
            if c.legalPush~=true then return nil,"PUSH_NOT_ALLOWED" end
            return request("EXISTING_PUSH_DIRECTION_ONLY",{noLift=true,noNewCC=true})
        end
        if c.targetKind~="NEUTRAL" or c.safeLanding~=true or c.resistant~=false or not integer(c.targetCap) then return nil,"LIFT_NOT_ALLOWED" end
        local height=capped(liftHeight[i],c.liftCap)
        local count=math.min(i,c.targetCap)
        if not height or height<=0 or count<=0 then return nil,"NO_LIFT_BUDGET" end
        return request("NEUTRAL_LIFT_REQUEST",{maxTargets=count,maxHeight=height,extraDamage=0})
    elseif id=="PREMIUM-007" then
        if c.safeVisualPoint~=true or c.decoyActive~=false then return nil,"DECOY_NOT_ALLOWED" end
        return request("VISUAL_DECOY_REQUEST",{duration=decoyLife[i],maxDecoys=1,collision=false,hasAI=false,canAttack=false,grantsVision=false})
    elseif id=="PREMIUM-008" then
        if c.healAllowed~=true or not finite(c.maxHP) or c.maxHP<=0 or not nonneg(c.hp) or c.hp<=0 or c.hp>c.maxHP or not nonneg(c.healedRoundFraction) or c.healedRoundFraction>0.06 or not nonneg(c.healCap) then return nil,"HEAL_NOT_ALLOWED" end
        -- Ledger tracks actual heal/maxHP at time of the heal in existing HP authority.
        local remaining=math.max(0,0.06-c.healedRoundFraction)
        local amount=math.min(healFraction[i]*c.maxHP,remaining*c.maxHP,c.maxHP-c.hp,c.healCap)
        if amount<=0 then return nil,"NO_HEAL_ROOM" end
        return request("SELF_HEAL_REQUEST",{maxAmount=amount,maxRoundFraction=0.06})
    elseif id=="PREMIUM-009" then
        if c.targetKind~="PLAYER" or c.targetEligible~=true or c.targetUsedThisRound~=false then return nil,"SEAL_NOT_ALLOWED" end
        return request("OPTIONAL_EFFECT_MARK_REQUEST",{duration=sealLife[i],maxMitigation=0.2,maxUses=1})
    elseif id=="PREMIUM-010" then
        if c.invincible~=false or c.otherMitigation~=false then return nil,"ARMOR_NOT_ALLOWED" end
        local fraction=capped(armorFraction[i],c.mitigationCap)
        if not fraction or fraction<=0 then return nil,"NO_MITIGATION_ROOM" end
        return request("FRONTAL_ARMOR_REQUEST",{duration=armorLife[i],maxMitigation=fraction,maxUses=1,reflectDamage=0})
    elseif id=="PREMIUM-011" then
        if c.safeFloor~=true or c.zoneActive~=false then return nil,"ZONE_NOT_ALLOWED" end
        local fraction=capped(0.08,c.mitigationCap)
        local radius=capped(zoneRadius[i],c.radiusCap)
        if not fraction or fraction<=0 or not radius or radius<=0 then return nil,"NO_ZONE_BUDGET" end
        return request("TACTICAL_ZONE_REQUEST",{radius=radius,duration=zoneLife[i],maxMitigation=fraction,maxZones=1,collision=false})
    elseif id=="PREMIUM-012" then
        if c.targetKind~="NEUTRAL" or c.targetAlive~=true or c.resistant~=false or c.bothPositionsSafe~=true or c.canMove~=true or c.carryingEgg~=false then return nil,"SWAP_NOT_ALLOWED" end
        local limit=capped(swapRange[i],c.moveCap)
        if not limit or not nonneg(c.distance) or c.distance<=0 or c.distance>limit then return nil,"SWAP_RANGE" end
        return request("ATOMIC_NEUTRAL_SWAP_REQUEST",{maxDistance=limit,maxTargets=1})
    end
    return nil,"UNKNOWN_OR_WRONG_PHASE"
end

-- 009: only a real, optional effect FROM marked enemy TO original caster.
-- No basic/physical attack, movement, ultimate/invincibility or time effects.
function M.sealMitigation(s,ctx)
    local i=index(s)
    if not i or type(ctx)~="table" or ctx.eligibleOptionalEffect~=true or ctx.protectedKind~=false or ctx.sameMarkedSourceAndCaster~=true or ctx.consumed~=false or not nonneg(ctx.elapsed) or ctx.elapsed>=sealLife[i] or not nonneg(ctx.amount) or not nonneg(ctx.mitigationCap) then return nil,"SEAL_INELIGIBLE" end
    local fraction=math.min(0.2,ctx.mitigationCap)
    if fraction<=0 or ctx.amount<=0 then return nil,"NO_MITIGATION_ROOM" end
    return request("OPTIONAL_EFFECT_REDUCTION",{maxReduction=ctx.amount*fraction,maxUses=1})
end

-- 010: existing damage authority applies the reduction ONCE and never reflects.
function M.armorMitigation(s,ctx)
    local i=index(s)
    if not i or type(ctx)~="table" or ctx.legitimateHit~=true or ctx.frontal~=true or ctx.invincible~=false or ctx.otherMitigation~=false or ctx.consumed~=false or not nonneg(ctx.elapsed) or ctx.elapsed>=armorLife[i] or not nonneg(ctx.amount) or not nonneg(ctx.mitigationCap) then return nil,"ARMOR_INELIGIBLE" end
    local fraction=math.min(armorFraction[i],ctx.mitigationCap)
    if fraction<=0 or ctx.amount<=0 then return nil,"NO_MITIGATION_ROOM" end
    return request("FRONTAL_DAMAGE_REDUCTION",{maxReduction=ctx.amount*fraction,maxUses=1,reflectDamage=0})
end
return table.freeze(M)
