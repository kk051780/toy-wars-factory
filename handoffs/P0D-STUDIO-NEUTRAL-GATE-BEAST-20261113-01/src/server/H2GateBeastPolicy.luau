--!strict
-- Original P0D optional neutral monster policy. Pure numeric server logic.
-- One match authority: existing original S1 Game.server.luau ONLY.
local P = {}
P.IDLE="IDLE"
P.WARN="WARN"
P.BLOCK="BLOCK"
P.COOLDOWN="COOLDOWN"
P.WARNING_SECONDS = 2
P.MAX_WARNING_SECONDS = 5
P.BLOCK_SECONDS = 5
P.COOLDOWN_SECONDS = 8
P.WAKE_RADIUS = 28

local function finite(n)
    return type(n)=="number" and n==n and math.abs(n) <= 100000000
end

function P.nearBeast(x,y,z,team,alive)
    if not (finite(x) and finite(y) and finite(z)) then return false end
    if team ~= "RED" and team ~= "BLUE" then return false end
    if alive ~= true then return false end
    if y < -2 or y > 17 then return false end
    return x*x + z*z <= P.WAKE_RADIUS*P.WAKE_RADIUS
end

function P.insideGate(x,y,z)
    if not (finite(x) and finite(y) and finite(z)) then return false end
    -- Extra humanoid-body clearance around physical Part x=-1.75..1.75,
    -- z=-11..11, y=0..12: NEVER solidify over a player at this buffer.
    return math.abs(x) < 5 and y >= -2 and y <= 16 and math.abs(z) < 14
end

function P.initial()
    return {phase=P.IDLE,untilAt=0,startedAt=0}
end

function P.solid(s)
    return type(s)=="table" and s.phase==P.BLOCK
end

function P.advance(old,now,nearby,laneClear)
    if type(old)~="table" or not finite(now) or now<0 then return nil end
    if type(nearby)~="boolean" or type(laneClear)~="boolean" then return nil end
    if not (finite(old.untilAt) and finite(old.startedAt)) then return nil end
    if now < old.startedAt then return nil end
    if old.phase==P.IDLE then
        if nearby then
            return {phase=P.WARN,untilAt=now+P.WARNING_SECONDS,startedAt=now}
        end
        return old
    elseif old.phase==P.WARN then
        if now < old.untilAt then return old end
        if laneClear then
            return {phase=P.BLOCK,untilAt=now+P.BLOCK_SECONDS,startedAt=now}
        end
        if now-old.startedAt >= P.MAX_WARNING_SECONDS then
            return {phase=P.COOLDOWN,untilAt=now+P.COOLDOWN_SECONDS,startedAt=now}
        end
        return old
    elseif old.phase==P.BLOCK then
        if now >= old.untilAt then
            return {phase=P.COOLDOWN,untilAt=now+P.COOLDOWN_SECONDS,startedAt=now}
        end
        return old
    elseif old.phase==P.COOLDOWN then
        if now >= old.untilAt then
            return {phase=P.IDLE,untilAt=0,startedAt=now}
        end
        return old
    end
    return nil
end
return P
