-- P0D-D13: pure, server-adapter-only reference; no NPC creation, movement, Remote, or Studio calls.
-- CRITICAL: the caller MUST construct events from verified server-owned gate/LoS/egg state.
-- A client Remote payload, even with a `serverOwned=true` flag, is NOT an authorized event.
local Director = {}
local GUARD_COOLDOWN = 2
local MAX_RETASK = 2
local MAX_IDS = 128
local WATCH_DURATION = 4
local ALERT_DURATION = 7
local CHASE_DURATION = 4
local VALID = {gate_damage=true, guard_los=true, egg_picked=true, egg_carrier_los=true,
    egg_dropped=true, round_end=true}
local DEST = {gate_damage="FRONT", guard_los="FLANK", egg_picked="EXIT", egg_carrier_los="EXIT"}
local NEXT_STATE = {gate_damage="WATCH", guard_los="ALERT", egg_picked="ALERT",
    egg_carrier_los="CHASE"}
local SEVERITY = {CALM=0, RESET=0, WATCH=1, ALERT=2, CHASE=3}

function Director.new(roundId)
    assert(type(roundId)=="string" and #roundId>0, "roundId required")
    return {roundId=roundId, lastTime=-1, closed=false, teams={}, seen={}, seenOrder={}}
end

local function teamState(state, teamId)
    local t = state.teams[teamId]
    if not t then
        t = {mode="CALM", untilTime=0, lastRetask={}}
        state.teams[teamId] = t
    end
    return t
end

local function expire(t, now)
    if now >= t.untilTime then
        t.mode = "CALM"
        t.untilTime = now
    end
end

local function countPosts(guards, defenderTeam)
    local counts = {EGG=0, FRONT=0, FLANK=0, RESERVE=0, EXIT=0}
    for _,g in ipairs(guards) do
        if g.team == defenderTeam and g.alive == true and counts[g.post] ~= nil then
            counts[g.post] += 1
        end
    end
    return counts
end

local function plan(t, now, defenders, defenderTeam, target)
    local counts = countPosts(defenders, defenderTeam)
    local out = {}
    local candidates = {}
    for _,g in ipairs(defenders) do
        if g.team == defenderTeam and g.alive == true and g.movable == true and
            type(g.id) == "string" and type(g.post) == "string" and
            g.post ~= target and counts[g.post] ~= nil and
            now - (t.lastRetask[g.id] or -100000) >= GUARD_COOLDOWN then
            local reserve = g.post == "RESERVE"
            -- Never abandon the final guard from egg-room/front/flank/exit route.
            if reserve or counts[g.post] > 1 then
                table.insert(candidates, {id=g.id, post=g.post, priority=reserve and 0 or 1})
            end
        end
    end
    table.sort(candidates, function(a,b)
        if a.priority ~= b.priority then return a.priority < b.priority end
        return a.id < b.id
    end)
    for _,g in ipairs(candidates) do
        if #out >= MAX_RETASK then break end
        if g.post == "RESERVE" or counts[g.post] > 1 then
            counts[g.post] -= 1
            -- Intents only: integration adapter must pathfind/walk and can reject them.
            table.insert(out, {guardId=g.id, fromPost=g.post, toPost=target})
            t.lastRetask[g.id] = now
        end
    end
    return out
end

-- Event fields: id, roundId, defenderTeam, type. Values originate only from a trusted server adapter.
-- No target player ID or world position is carried in an output intent (prevents wall-tracking).
function Director.step(state, now, event, defenders)
    assert(type(state)=="table" and type(defenders)=="table", "invalid state or defenders")
    if type(now)~="number" or now ~= now or now == math.huge or now == -math.huge or now < 0 or now < state.lastTime then
        return {status="REJECT_TIME", intents={}}
    end
    if type(event)~="table" or type(event.id)~="string" or #event.id==0 or
        type(event.defenderTeam)~="string" or #event.defenderTeam==0 or
        event.roundId ~= state.roundId or not VALID[event.type] then
        return {status="REJECT_EVENT", intents={}}
    end
    if state.closed then return {status="CLOSED", intents={}} end
    if state.seen[event.id] then return {status="DUPLICATE", intents={}} end
    state.lastTime = now
    state.seen[event.id] = true
    table.insert(state.seenOrder, event.id)
    if #state.seenOrder > MAX_IDS then
        state.seen[table.remove(state.seenOrder,1)] = nil
    end
    if event.type=="round_end" then
        state.closed=true
        state.teams={}
        return {status="ENDED", intents={}, mode="CALM"}
    end
    local t=teamState(state,event.defenderTeam)
    expire(t,now)
    if event.type=="egg_dropped" then
        t.mode="RESET"
        t.untilTime=now
        return {status="RESET", intents={}, mode=t.mode}
    end
    local proposed=NEXT_STATE[event.type]
    if SEVERITY[proposed] >= SEVERITY[t.mode] then
        t.mode=proposed
    end
    local dur=WATCH_DURATION
    if event.type=="guard_los" or event.type=="egg_picked" then dur=ALERT_DURATION end
    if event.type=="egg_carrier_los" then dur=CHASE_DURATION end
    t.untilTime=math.max(t.untilTime,now+dur)
    local intent=plan(t,now,defenders,event.defenderTeam,DEST[event.type])
    return {status="ACCEPTED", mode=t.mode, intents=intent, untilTime=t.untilTime}
end
return Director
