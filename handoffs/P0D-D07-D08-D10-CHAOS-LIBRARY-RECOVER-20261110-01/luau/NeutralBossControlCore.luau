--!strict
-- TRAP RAIDERS v40/v41: one neutral raid boss, optional bounded direction.
-- NO direct damage/egg state/character teleport/physics authority in this module.
local Core = {}
local function okId(v): boolean
    return type(v)=="string" and #v>0 and #v<=96 and string.match(v,"^[%w_%-]+$")~=nil
end
local function finite(t): boolean
    return type(t)=="number" and t==t and t~=math.huge and t~=-math.huge
end
function Core.new(matchId: string)
    assert(okId(matchId), "MATCH_INVALID")
    return {matchId=matchId, lastAt=0, phase="NEUTRAL", controlledBy=nil,
        expiresAt=0, commandUsed={}, bossPresent=false, bossId=nil}
end
function Core.spawn(state, bossId: string, now: number)
    assert(finite(now) and now>=state.lastAt, "TIME_INVALID")
    if state.bossPresent or state.phase=="DONE" or (bossId~="GOROGAN" and bossId~="RAIGALD") then
        return false, "SPAWN_REJECTED"
    end
    state.bossPresent, state.bossId, state.lastAt = true,bossId,now
    return true,"SPAWNED"
end
-- Caller must check actual OWNER server roster and item inventory. The `proof` table is
-- not an authentication token and must never be populated from RemoteEvent client data.
function Core.command(state, now: number, userId: number, team: string, proof)
    if not finite(now) or now<state.lastAt then return false,"TIME_REJECTED" end
    state.lastAt=now
    if not state.bossPresent or state.phase=="DONE" then return false,"BOSS_NOT_PRESENT" end
    if state.controlledBy and now<state.expiresAt then return false,"ALREADY_CONTROLLED" end
    if not (team=="BLUE" or team=="RED") or type(userId)~="number" or userId<1 or userId%1~=0 then return false,"IDENTITY_REJECTED" end
    if type(proof)~="table" or proof.matchId~=state.matchId or proof.team~=team
        or proof.userId~=userId or proof.serverRosterConfirmed~=true or proof.alive~=true
        or proof.hasRelicOrFreeTamerSkill~=true or proof.inNeutralZone~=true or proof.carryingEgg==true then
        return false,"SERVER_EVIDENCE_REQUIRED"
    end
    if state.commandUsed[userId] then return false,"ONE_COMMAND_PER_USER" end
    state.commandUsed[userId]=true
    state.controlledBy=team
    state.expiresAt=now+7
    state.phase="DIRECTED"
    return true,"DIRECTED"
end
function Core.tick(state,now:number,matchActive:boolean)
    if not finite(now) or now<state.lastAt then return false,"TIME_REJECTED" end
    state.lastAt=now
    if not matchActive then
        state.phase,state.controlledBy,state.bossPresent="DONE",nil,false
        return true,"CLEANUP"
    end
    if state.phase=="DIRECTED" and now>=state.expiresAt then
        state.phase,state.controlledBy="NEUTRAL",nil
        return true,"RETURNED_NEUTRAL"
    end
    return true,"NO_CHANGE"
end
return Core
