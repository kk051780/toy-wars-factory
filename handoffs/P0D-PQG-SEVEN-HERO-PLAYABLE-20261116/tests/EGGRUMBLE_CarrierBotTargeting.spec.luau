--!strict
-- Native Luau regression for the V3 class-skill / egg-objective / bot combat seam.
-- The original actor owns team, HP, 11-stud range, LOS and cooldown.
local Policy = require("../EGGRUMBLE_CarrierBotTargeting")
local checks = 0
local function check(value:boolean, reason:string)
    assert(value, reason)
    checks += 1
end

-- Policy is identical in the TEAM and BR host; egg ownership is server side.
for _,mode in ipairs({"TEAM", "BATTLE_ROYALE"}) do
    local now = 100
    check(Policy.canStrike(0, 0, now), mode .. " ordinary exposed target")
    check(not Policy.canStrike(0, now + 3, now), mode .. " WIND stealth when empty")
    check(Policy.canStrike(1, now + 3, now + .2), mode .. " carrier after WIND")
    check(Policy.canStrike(3, now + 3, now + .2), mode .. " full egg pouch")
    check(not Policy.canStrike(0, now + 3, now + .3), mode .. " still stealth after depositing")
    check(Policy.canStrike(0, now + 3, now + 3), mode .. " expiry inclusive")
    check(Policy.canStrike(0, now + 3, now + 3.1), mode .. " expiry after")
    check(Policy.canStrike(2, now + 1000, now), mode .. " carried egg wins over extreme stealth")
end
check(Policy.canStrike(0, nil, 100), "unbuffed missing attribute")
check(Policy.canStrike(0, "bad", 100), "malformed stealth cannot make invisible")
check(Policy.canStrike(0, 0/0, 100), "nan stealth cannot make invisible")
check(Policy.canStrike(0, math.huge, 100), "infinite stealth cannot make invisible")
check(Policy.canStrike(0, -math.huge, 100), "negative infinite stealth cannot make invisible")
check(Policy.canStrike(nil, 1000, 100), "missing authoritative egg count cannot grant immunity")
check(Policy.canStrike(0/0, 1000, 100), "corrupt authoritative egg count cannot grant immunity")
check(not Policy.canStrike(0, 104, 103.99), "normal stealth remains effective until expiry")
print("CARRIER_BOT_TARGET_NATIVE_PASS " .. tostring(checks) .. " checks")
