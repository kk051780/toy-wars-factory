--!strict
-- CLIENT-ONLY pure compass presentation policy. No Roblox services, remotes or game authority.
local Compass={}
local function finite(x: any): boolean
    return type(x)=="number" and x==x and x>-10000000 and x<10000000
end
-- Right/up orientation: arrow 0 points toward camera forward, +90 camera right, -90 left.
-- Horizontal projection only; outputs nil if a target or heading is degenerate.
function Compass.angleDegrees(rx: any, rz: any, lx: any, lz: any, dx: any, dz: any): number?
    for _,v in ipairs({rx,rz,lx,lz,dx,dz}) do
        if not finite(v) then return nil end
    end
    local target=dx*dx+dz*dz
    local heading=lx*lx+lz*lz
    local right=rx*rx+rz*rz
    if target<0.25 or heading<0.0001 or right<0.0001 then return nil end
    local rightBearing=rx*dx+rz*dz
    local frontBearing=lx*dx+lz*dz
    if math.abs(rightBearing)+math.abs(frontBearing)<0.000001 then return nil end
    local angle=math.deg(math.atan2(rightBearing,frontBearing))
    if not finite(angle) then return nil end
    return angle
end
function Compass.title(carrying: any): string?
    if type(carrying)~="boolean" then return nil end
    return if carrying then "じぶんの台の方向" else "敵の卵の方向"
end
return Compass
