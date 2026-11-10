-- TRAP RAIDERS D14 reference only. Authoritative server supplies every fact.
-- Pure policy: no Instance, RemoteEvent, Humanoid, mover physics, or DataStore.
local Motion = {}
local MAX_NODES = 24
local MAX_COORD = 2000
local MAX_EDGE = 80
local MIN_EDGE = 6
local MAX_SPEED = 16

local function finite(n)
    return type(n) == "number" and n == n and n ~= math.huge and n ~= -math.huge
end
local function dist(a, b)
    local x, y, z = b.x - a.x, b.y - a.y, b.z - a.z
    return math.sqrt(x*x + y*y + z*z)
end
local function copy(p)
    return {x=p.x, y=p.y, z=p.z}
end
local function interpolate(a, b, t)
    return {x=a.x+(b.x-a.x)*t, y=a.y+(b.y-a.y)*t, z=a.z+(b.z-a.z)*t}
end
function Motion.checkRoute(route)
    if type(route) ~= "table" or type(route.id) ~= "string" or
       not string.match(route.id, "^[A-Za-z0-9_%-]+$") or #route.id > 48 then
        return false, "BAD_ROUTE_ID"
    end
    if type(route.nodes) ~= "table" or #route.nodes < 2 or #route.nodes > MAX_NODES then
        return false, "NODE_COUNT"
    end
    if not finite(route.speed) or route.speed < 2 or route.speed > MAX_SPEED then
        return false, "SPEED_LIMIT"
    end
    for i, p in ipairs(route.nodes) do
        if type(p) ~= "table" then return false, "BAD_POSITION" end
        for _, axis in ipairs({"x", "y", "z"}) do
            if not finite(p[axis]) or math.abs(p[axis]) > MAX_COORD then
                return false, "BAD_POSITION"
            end
        end
        if i > 1 then
            local length = dist(route.nodes[i-1], p)
            if length < MIN_EDGE or length > MAX_EDGE then return false, "EDGE_RANGE" end
        end
    end
    return true, "OK"
end
function Motion.new(route, roundId, teamId)
    local valid, why = Motion.checkRoute(route)
    if not valid then return nil, why end
    if type(roundId) ~= "string" or #roundId < 1 or #roundId > 80 then return nil, "ROUND_ID" end
    if teamId ~= "BLUE" and teamId ~= "RED" then return nil, "TEAM_ID" end
    local snapshot = {
        routeId=route.id, roundId=roundId, teamId=teamId,
        leg=1, progress=0, moving=false, ended=false, lastCommand=0,
        position=copy(route.nodes[1]), direction={x=route.nodes[2].x-route.nodes[1].x, y=route.nodes[2].y-route.nodes[1].y, z=route.nodes[2].z-route.nodes[1].z},
    }
    return snapshot, "OK"
end
function Motion.requestNext(state, route, facts)
    if state.ended then return false, "ENDED" end
    if type(facts) ~= "table" or facts.roundId ~= state.roundId or facts.teamId ~= state.teamId then
        return false, "WRONG_ROUND_TEAM"
    end
    -- All values below are injected by trusted server adapter, not Remote payload.
    if facts.isCurrentDriver ~= true or facts.alive ~= true or facts.carrier == true or
       facts.mounted ~= true or facts.isTrapped == true then
        return false, "DRIVER_AUTH"
    end
    if not finite(facts.sequence) or facts.sequence % 1 ~= 0 or facts.sequence <= state.lastCommand then
        return false, "REPLAY"
    end
    if state.moving then return false, "ALREADY_MOVING" end
    if state.leg >= #route.nodes then return false, "ROUTE_END" end
    state.lastCommand = facts.sequence
    state.moving = true
    return true, "OK"
end
function Motion.step(state, route, dt, facts)
    if state.ended then return state.position, "ENDED" end
    if not finite(dt) or dt < 0 or dt > 0.1 then
        state.moving = false
        return state.position, "BAD_DT_STOP"
    end
    if not facts or facts.roundId ~= state.roundId or facts.teamId ~= state.teamId or
       facts.active ~= true or facts.driverStillValid ~= true or
       facts.alive ~= true or facts.mounted ~= true or facts.carrier == true or facts.isTrapped == true then
        state.moving = false
        return state.position, "AUTH_STOP"
    end
    if not state.moving then return state.position, "STOPPED" end
    local a, b = route.nodes[state.leg], route.nodes[state.leg+1]
    if not b then state.moving=false; return state.position, "ROUTE_END" end
    local legLen = dist(a, b)
    state.progress = math.min(1, state.progress + dt * route.speed / legLen)
    state.position = interpolate(a,b,state.progress)
    state.direction = {x=b.x-a.x, y=b.y-a.y, z=b.z-a.z}
    if state.progress >= 1 - 1e-9 then
        state.progress = 1
        state.position = copy(b)
        state.leg += 1
        state.progress = 0
        state.moving = false -- explicit per-leg command; no client-selected path
        return state.position, "LEG_COMPLETE"
    end
    return state.position, "MOVING"
end
function Motion.stop(state)
    state.moving = false
    return state.position
end
function Motion.endRound(state)
    state.moving = false
    state.ended = true
    return state.position
end
return Motion
