--!strict
-- WF13Policy: engine-independent numeric limits for an opt-in server-only gravity zone.
-- Inputs are raw numbers so native Luau can execute this module without Roblox services.
local Policy = {}

Policy.GRAVITY_RATIO = 0.35
Policy.LANDING_SECONDS = 2.0
Policy.LANDING_ASSIST = 0.35
Policy.SAMPLE_SECONDS = 0.08
Policy.MAX_HORIZONTAL = 48
Policy.MAX_RISE = 30
Policy.MAX_FALL = 34
Policy.MAX_DWELL = 18
Policy.SAFETY_DEPTH = 32

local function finite(n: any): boolean
    return type(n) == "number" and n == n and n > -math.huge and n < math.huge
end

function Policy.insideEllipsoid(dx: number, dy: number, dz: number, sx: number, sy: number, sz: number): boolean
    if not (finite(dx) and finite(dy) and finite(dz)
        and finite(sx) and finite(sy) and finite(sz)) then return false end
    if sx <= 0 or sy <= 0 or sz <= 0 then return false end
    local nx, ny, nz = dx / (sx * 0.5), dy / (sy * 0.5), dz / (sz * 0.5)
    return nx * nx + ny * ny + nz * nz <= 1
end

function Policy.upwardForce(mass: number, gravity: number, ratio: number): number
    if not (finite(mass) and finite(gravity) and finite(ratio)) then return 0 end
    if mass <= 0 or gravity <= 0 or ratio < 0.2 or ratio > 0.85 then return 0 end
    return mass * gravity * (1 - ratio)
end

function Policy.landingForce(mass: number, gravity: number, elapsed: number): number
    if not finite(elapsed) or elapsed < 0 or elapsed >= Policy.LANDING_SECONDS then return 0 end
    return Policy.upwardForce(mass, gravity, 1 - Policy.LANDING_ASSIST * (1 - elapsed / Policy.LANDING_SECONDS))
end

function Policy.clampVelocity(vx: number, vy: number, vz: number): (number, number, number)
    if not (finite(vx) and finite(vy) and finite(vz)) then return 0, 0, 0 end
    local horizontal = math.sqrt(vx * vx + vz * vz)
    if horizontal > Policy.MAX_HORIZONTAL then
        local scale = Policy.MAX_HORIZONTAL / horizontal
        vx, vz = vx * scale, vz * scale
    end
    return vx, math.clamp(vy, -Policy.MAX_FALL, Policy.MAX_RISE), vz
end

return Policy
