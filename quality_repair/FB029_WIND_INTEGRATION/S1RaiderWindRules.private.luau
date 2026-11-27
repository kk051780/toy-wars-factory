--!strict
-- FB029: Studio-only server-proved expanded wind bounds.
-- Original H1 public match policy remains 120x65, height 1..12.
-- Use as source-selective MODULE replacement in a private Studio candidate only.
local Wind = {}
Wind.COOLDOWN = 18
Wind.DURATION = 2.5
Wind.SPEED = 27

local function finite(n)
    return type(n) == "number" and n == n and math.abs(n) < 1e7
end

function Wind.canActivate(s)
    if type(s) ~= "table" or s.phase ~= "ACTIVE"
        or (s.team ~= "RED" and s.team ~= "BLUE")
        or s.role ~= "RAIDER" or s.alive ~= true
        or s.carrying == true or s.slowed == true or s.active == true then
        return false
    end
    if not finite(s.now) or (s.lastAt ~= -math.huge and not finite(s.lastAt))
        or not finite(s.x) or not finite(s.y) or not finite(s.z) then
        return false
    end
    if s.now - s.lastAt < Wind.COOLDOWN then return false end

    -- The original server Game must check RunService:IsStudio(), physical grounded
    -- Raycast and actual server world bounds before setting studioArena.
    local maxX, maxZ, maxY = 120, 65, 12
    if s.studioArena == true then
        if not finite(s.arenaMaxX) or not finite(s.arenaMaxZ)
            or not finite(s.arenaMaxY) or s.arenaMaxX < 30 or s.arenaMaxX > 178
            or s.arenaMaxZ < 25 or s.arenaMaxZ > 140
            or s.arenaMaxY < 12 or s.arenaMaxY > 30 then return false end
        maxX, maxZ, maxY = s.arenaMaxX, s.arenaMaxZ, s.arenaMaxY
    end
    if math.abs(s.x) > maxX or math.abs(s.z) > maxZ
        or s.y < 1 or s.y > maxY then return false end
    return true
end

return Wind
