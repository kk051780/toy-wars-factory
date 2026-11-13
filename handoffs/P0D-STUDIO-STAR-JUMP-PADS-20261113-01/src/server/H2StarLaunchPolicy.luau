--!strict
-- P0D PRODUCT STUDIO optional H2: one-tap tactical star launch policy.
-- Pure numeric server policy: no Roblox Instances, no Game, no Remote.
local P = {}
P.COOLDOWN = 12
P.MAX_DISTANCE = 10
P.PAD_X = 66
P.PAD_Y = 1
P.PAD_Z = -20
P.SPEED_X = 62
P.SPEED_Y = 72
P.SPEED_Z = 16

local function finite(n)
    return type(n) == "number" and n == n and math.abs(n) <= 1000000
end

function P.canLaunch(s)
    if type(s) ~= "table" then return false end
    if s.team ~= "RED" and s.team ~= "BLUE" then return false end
    if s.pad ~= "RED" and s.pad ~= "BLUE" then return false end
    if s.healthy ~= true or s.grounded ~= true or s.seated == true then return false end
    if not finite(s.now) or (s.lastAt ~= -math.huge and not finite(s.lastAt)) then return false end
    if s.now - s.lastAt < P.COOLDOWN then return false end
    if not finite(s.x) or not finite(s.y) or not finite(s.z) then return false end
    -- Existing S1 Arena bounds + a grounded point near a REAL anchored pad.
    if math.abs(s.x) > 120 or math.abs(s.z) > 65 or s.y < 0 or s.y > 12 then return false end
    local px = if s.pad == "RED" then -P.PAD_X else P.PAD_X
    local dx,dy,dz = s.x-px, s.y-P.PAD_Y, s.z-P.PAD_Z
    return dx*dx + dy*dy + dz*dz <= P.MAX_DISTANCE*P.MAX_DISTANCE
end

function P.velocityFor(pad)
    if pad == "RED" then return {x=P.SPEED_X,y=P.SPEED_Y,z=P.SPEED_Z} end
    if pad == "BLUE" then return {x=-P.SPEED_X,y=P.SPEED_Y,z=P.SPEED_Z} end
    return nil
end
return P
