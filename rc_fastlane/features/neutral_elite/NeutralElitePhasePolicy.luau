--!nocheck
-- P0D-017 neutral elite + strong boss phase preview. Pure server policy.
-- No heartbeat, damage/HP/XP/score/egg/Store writer, Remote or RNG.
-- The original Game -> MusouHorde exclusively owns all actual mob HP and hits.
local Elite={}
Elite.VERSION="P0D017_NEUTRAL_ELITE_PHASE_POLICY_V1"
Elite.KINDS={
    GOROGAN={name="遺跡巨人ゴロガン",range=12,windup=2.0,recovery=5.0,visual="GROUND_SHOCK"},
    RAIGALD={name="嵐竜ライガルド",range=18,windup=3.0,recovery=7.0,visual="STORM_ARC"},
}
Elite.MAX_ONE_PER_ROUND=1
local function finite(n)
    return type(n)=="number" and n==n and n>=0 and n<math.huge
end
local function validRound(v)
    return type(v)=="number" and v==math.floor(v) and v>=1 and v<=1000000000
end
function Elite.spawn(roundId,kind,now,roundActive,existing)
    if not validRound(roundId) or not Elite.KINDS[kind] or not finite(now)
        or roundActive~=true then
        return nil,"INVALID"
    end
    if existing and existing.live and existing.roundId==roundId then
        return nil,"MAX_ONE"
    end
    return {roundId=roundId,kind=kind,phase="READY",readyAt=now,
        live=true,attackCount=0}, "CREATED"
end
local function cancel(s,now)
    s.phase="RECOVERY"
    s.readyAt=now+1.5
    return {kind="CANCEL",reason="TARGET_UNSAFE"}
end
function Elite.step(s,roundId,now,distance,visible,roundActive)
    if not s or s.live~=true or not validRound(roundId)
        or s.roundId~=roundId or not finite(now)
        or roundActive~=true or not Elite.KINDS[s.kind] then
        if s and s.live and (s.roundId~=roundId or roundActive~=true) then
            s.live=false -- no carryover between games
        end
        return {kind="INACTIVE"}
    end
    local cfg=Elite.KINDS[s.kind]
    local safe=finite(distance) and type(visible)=="boolean"
    if s.phase=="READY" then
        if now<s.readyAt or not safe or visible~=true or distance>cfg.range then
            return {kind="NONE"}
        end
        s.phase="TELEGRAPH"
        s.readyAt=now+cfg.windup
        return {kind="WARN",visual=cfg.visual,seconds=cfg.windup,range=cfg.range}
    elseif s.phase=="TELEGRAPH" then
        if not safe or visible~=true or distance>cfg.range then
            return cancel(s,now)
        end
        if now<s.readyAt then return {kind="NONE"} end
        s.phase="RECOVERY"
        s.readyAt=now+cfg.recovery
        s.attackCount+=1
        -- Only original authoritative Horde may turn this into a hit.
        return {kind="REQUEST_HORDE_STRIKE",visual=cfg.visual,
            range=cfg.range,sequence=s.attackCount,roundId=roundId}
    elseif s.phase=="RECOVERY" then
        if now<s.readyAt then return {kind="NONE"} end
        s.phase="READY"
        return {kind="READY"}
    end
    s.live=false
    return {kind="INACTIVE"}
end
function Elite.close(s,roundId)
    if not s or s.roundId~=roundId or s.live~=true then return false end
    s.live=false
    s.phase="CLOSED"
    return true
end
function Elite.canStartAgain(s,roundId)
    return s==nil or (s.roundId~=roundId)
end
return Elite
