-- Native Luau VM assertions, appended after the *actual* authored module.
local P = Pacing
local checks = 0
local function eq(actual, expected, label)
    checks += 1
    assert(actual == expected, label .. ": expected=" .. tostring(expected) .. " actual=" .. tostring(actual))
end
local s = P.new("TEAM:round01")
local function step(state, dt, live, heroes, tickMs, matchId, phase)
    return P.step(state, { matchId = matchId or "TEAM:round01", phase = phase or "ACTIVE",
        dt = dt, live = live, activeHeroes = heroes, tickMs = tickMs })
end
local n, reason = step(s, 0.18, 0, 16, 18)
eq(n, 7, "40/s budget = 7 in first .18 tick")
eq(reason, "READY", "active")
n = step(s, 0.18, 109, 16, 18)
eq(n, 1, "never exceed 110 live")
n,reason = step(s, 0.18, 110, 16, 18)
eq(n, 0, "full actor cap")
eq(reason, "CAP", "full actor reason")
eq(s.credit, 0, "no backlog after cap")
n = step(s, 0.18, 0, 0, 18)
eq(n, 0, "no target")
eq(s.credit, 0, "empty map clears credit")
n = step(s, 0.18, 0, 16, 70)
eq(n, 2, "pressure overload lowers spawn count")
n = step(s, 0.18, 0, 16, 50)
eq(n, 5, "moderate load rate")
n = step(s, 0.18, 0, 16, 18, "BR:old")
eq(n, 0, "foreign epoch")
eq(s.credit, 0, "epoch mismatch clears credit")
n = step(s, 0.18, 0, 16, 18, nil, "FINISHED")
eq(n, 0, "finished match cannot spawn")
eq(s.credit, 0, "closed match clears credit")
for _,bad in ipairs({-1, 111, 3.5, math.huge, 0/0}) do
    n, reason = step(s, 0.18, bad, 16, 18)
    eq(n, 0, "malformed live count rejected")
    eq(reason, "INVALID", "malformed reason")
end
n = step(s, 1.1, 0, 16, 18)
eq(n, 0, "giant catch-up dt rejected")
n = step(s, 0.18, 0, 17, 18)
eq(n, 0, "invalid actor count rejected")
local theoretical = P.new("TEAM:15min")
local total = 0
for _=1, 5000 do
    local issued = P.step(theoretical, {matchId="TEAM:15min", phase="ACTIVE",
        dt=0.18,live=0,activeHeroes=16,tickMs=18})
    total += issued
end
assert(total >= 30000 and total <= 36000 + 1, "15min theoretical supply capacity >= 30k")
checks += 1
print("NEUTRAL_PACING_NATIVE_PASS checks="..tostring(checks).." 15min_supply="..tostring(total))
