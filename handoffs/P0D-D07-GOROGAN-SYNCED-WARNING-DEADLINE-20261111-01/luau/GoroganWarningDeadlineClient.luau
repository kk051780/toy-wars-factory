--!strict
-- Pure D07 UI time projection, NO extra RemoteEvent/Heartbeat subscription.
-- Caller must read workspace:GetServerTimeNow() (not client os.clock) and genuine
-- existing visual lifecycle state. Never prolong a windup past server deadline.
local M={}
local function finite(n,lo,hi)
    return type(n)=="number" and n==n and n~=math.huge and n~=-math.huge
        and n>=lo and n<=hi
end
local function id(v)
    return type(v)=="string" and #v>=1 and #v<=64 and v:match("^[%w_%-]+$")~=nil
end
function M.new(matchId,eventId,stageId,epoch)
    assert(id(matchId) and id(eventId),"VISUAL_IDS_INVALID")
    assert(stageId=="S1" or stageId=="S3","STAGE_INVALID")
    assert(finite(epoch,0,1023) and epoch%1==0,"EPOCH_INVALID")
    return {matchId=matchId,eventId=eventId,stageId=stageId,
        epoch=epoch,lastAttackId=0,lastNow=nil,deadline=nil,closed=false}
end
-- From existing trusted server-only FireClient channel, not client-to-server input.
-- active = ORIGINAL GoroganVisualPolicy.state.active, never packet.claimedActive.
function M.accept(state,packet,syncedNow,active)
    if state.closed then return nil,"CLOSED" end
    if active~=true then state.closed=true;return nil,"VISUAL_ENDED" end
    if not finite(syncedNow,0,1e12) or (state.lastNow~=nil and syncedNow<state.lastNow) then
        state.closed=true;return nil,"CLOCK_INVALID"
    end
    state.lastNow=syncedNow
    if type(packet)~="table" or packet.kind~="STOMP_DEADLINE"
        or packet.bossId~="GOROGAN" or packet.matchId~=state.matchId
        or packet.eventId~=state.eventId or packet.stageId~=state.stageId
        or packet.epoch~=state.epoch or not finite(packet.attackId,1,3)
        or packet.attackId%1~=0 or packet.attackId<=state.lastAttackId
        or not finite(packet.sentServerTime,0,1e12)
        or not finite(packet.warningEndsServerTime,0,1e12) then
        return nil,"INVALID_IDENTITY_OR_REPLAY"
    end
    local duration=packet.warningEndsServerTime-packet.sentServerTime
    if duration<=0 or duration>2.05
        or packet.sentServerTime>syncedNow+0.2 then return nil,"BAD_SERVER_DEADLINE" end
    -- Consume valid attack receipts even if already expired; never revive old telegraph.
    state.lastAttackId=packet.attackId
    state.deadline=packet.warningEndsServerTime
    if syncedNow>=state.deadline then return nil,"LATE_EXPIRED" end
    local remaining=math.min(2,state.deadline-syncedNow)
    return {remainingSeconds=remaining,serverDelaySeconds=math.max(0,syncedNow-packet.sentServerTime),
        warningEndsServerTime=state.deadline,attackId=state.lastAttackId},"RENDER_REMAINING"
end
-- Render caller may poll without a second frame/event connection.
function M.remaining(state,syncedNow,active)
    if state.closed or active~=true or not finite(syncedNow,0,1e12)
        or state.deadline==nil then return 0 end
    if state.lastNow~=nil and syncedNow<state.lastNow then return 0 end
    state.lastNow=syncedNow
    return math.max(0,math.min(2,state.deadline-syncedNow))
end
function M.close(state) state.closed=true;state.deadline=nil end
return M
