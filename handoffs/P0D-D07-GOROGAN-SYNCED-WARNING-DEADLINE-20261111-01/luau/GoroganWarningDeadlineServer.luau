--!strict
-- Pure D07 server warning stamp reference. Never subscribes, schedules, fires or damages.
-- Caller MUST supply trustworthy Core.STOMP_WARNING and a synchronized server-clock sample.
local M = {}
local function finite(n,lo,hi)
    return type(n)=="number" and n==n and n~=math.huge and n~=-math.huge
        and n>=lo and n<=hi
end
local function id(v)
    return type(v)=="string" and #v>=1 and #v<=64 and v:match("^[%w_%-]+$")~=nil
end
function M.new(config)
    assert(type(config)=="table" and config.enabled==true and config.ownerApproved==true,
        "WARNING_DEADLINE_DISABLED_DEFAULT")
    assert(id(config.matchId) and id(config.eventId),"SERVER_EVENT_IDS_REQUIRED")
    assert(config.stageId=="S1" or config.stageId=="S3","STAGE_DENIED")
    assert(finite(config.epoch,0,1023) and config.epoch%1==0,"EPOCH_INVALID")
    return {matchId=config.matchId,eventId=config.eventId,stageId=config.stageId,
        epoch=config.epoch,lastAttackId=0,lastCoreAt=nil,lastSyncedAt=nil,closed=false}
end
-- warning from *actual* Core.tick STOMP_WARNING, not a table synthesized from Remote input.
-- clock = {coreNow=<same monotonic time domain as warning.windupEnds>,
--          syncedServerNow=<workspace:GetServerTimeNow() at emission>,roundLive=true}
-- Adapter MUST prove provenance and round/epoch after any yielding callback.
function M.stamp(state,warning,clock)
    if state.closed then return nil,"CLOSED" end
    if type(warning)~="table" or warning.kind~="STOMP_WARNING"
        or warning.roundId~=state.matchId or warning.eventId~=state.eventId
        or not finite(warning.attackId,1,3) or warning.attackId%1~=0
        or warning.attackId<=state.lastAttackId
        or not finite(warning.windupEnds,0,1e12)
        or type(clock)~="table" or clock.roundLive~=true
        or not finite(clock.coreNow,0,1e12)
        or not finite(clock.syncedServerNow,0,1e12) then
        return nil,"AUTHORITY_OR_COMMAND_INVALID"
    end
    if (state.lastCoreAt~=nil and clock.coreNow<state.lastCoreAt)
        or (state.lastSyncedAt~=nil and clock.syncedServerNow<state.lastSyncedAt) then
        state.closed=true
        return nil,"CLOCK_REVERSED"
    end
    local remaining=warning.windupEnds-clock.coreNow
    -- Never promise new 2s on late issuance. Require very close to Core's 2s max.
    if remaining<=0 or remaining>2.05 then return nil,"WARNING_NOT_LIVE" end
    state.lastAttackId=warning.attackId
    state.lastCoreAt=clock.coreNow
    state.lastSyncedAt=clock.syncedServerNow
    local issuedAt=clock.syncedServerNow
    return {kind="STOMP_DEADLINE",bossId="GOROGAN",matchId=state.matchId,
        eventId=state.eventId,stageId=state.stageId,epoch=state.epoch,
        attackId=warning.attackId,sentServerTime=issuedAt,
        warningEndsServerTime=issuedAt+remaining},"STAMPED"
end
function M.close(state) state.closed=true end
return M
