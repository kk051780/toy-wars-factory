--!strict
-- TRAP RAIDERS S1 guardian trap: pure numeric server eligibility; no Remote, rewards, or scheduler.
local TrapRules = {}
TrapRules.COOLDOWN = 20
TrapRules.LIFETIME = 25
TrapRules.RADIUS = 5
TrapRules.SLOW_SECONDS = 3
TrapRules.SLOW_RATIO = 0.55
TrapRules.MAX_PER_TEAM = 2
TrapRules.OBJECTIVE_CLEARANCE = 15

local function finite(n)
    return type(n) == "number" and n == n and math.abs(n) < 1e7
end

-- Trap placed AT the server-observed HumanoidRootPart position; client sends no position.
function TrapRules.canPlace(s)
    if type(s) ~= "table" or s.phase ~= "ACTIVE"
        or (s.team ~= "RED" and s.team ~= "BLUE")
        or s.role ~= "GUARDIAN" or s.alive ~= true or s.carrying == true then
        return false
    end
    if not finite(s.now) or (not finite(s.lastAt) and s.lastAt ~= -math.huge) or not finite(s.x)
        or not finite(s.y) or not finite(s.z)
        or type(s.count) ~= "number" or s.count % 1 ~= 0
        or s.count < 0 or s.count >= TrapRules.MAX_PER_TEAM then return false end
    if s.now - s.lastAt < TrapRules.COOLDOWN then return false end
    -- Centre must be clearly inside OWN half, not near boundary or outside play floor.
    if (s.team == "RED" and s.x > -9) or (s.team == "BLUE" and s.x < 9)
        or math.abs(s.x) > 116 or math.abs(s.z) > 55
        or s.y < 2 or s.y > 8 then return false end
    if type(s.avoid) ~= "table" then return false end
    for _, p in ipairs(s.avoid) do
        if type(p) ~= "table" or not finite(p.x) or not finite(p.z) then return false end
        local dx, dz = p.x - s.x, p.z - s.z
        if dx * dx + dz * dz < TrapRules.OBJECTIVE_CLEARANCE ^ 2 then return false end
    end
    return true
end

-- Enemies may evade by jumping over the visible trap disc.
function TrapRules.shouldTrigger(s)
    if type(s) ~= "table" or s.phase ~= "ACTIVE" or s.healthy ~= true
        or s.invulnerable == true or s.enemyTeam == s.trapTeam
        or (s.enemyTeam ~= "RED" and s.enemyTeam ~= "BLUE")
        or (s.trapTeam ~= "RED" and s.trapTeam ~= "BLUE")
        or not finite(s.now) or not finite(s.expiresAt) or s.now >= s.expiresAt
        or not finite(s.x) or not finite(s.z) or not finite(s.enemyX)
        or not finite(s.enemyY) or not finite(s.enemyZ)
        or s.enemyY < 2 or s.enemyY > 7.6 then return false end
    local dx, dz = s.enemyX-s.x, s.enemyZ-s.z
    return dx * dx + dz * dz <= TrapRules.RADIUS * TrapRules.RADIUS
end

function TrapRules.slowSpeed(baseSpeed)
    if not finite(baseSpeed) or baseSpeed <= 0 then return nil end
    return math.max(8, math.floor(baseSpeed * TrapRules.SLOW_RATIO))
end

return TrapRules
