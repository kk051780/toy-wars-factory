-- Rules supplied byte-for-byte from official f6c9. Native stand-in for Roblox Vector3 only.
local v = {X = 0, Y = 0, Z = 0, __fixtureType = "Vector3"}
local w = {X = 5, Y = 0, Z = 0, __fixtureType = "Vector3"}
local checks = 0
local function verify(ok, label)
    assert(ok, label)
    checks += 1
end
local function holdings(m, a, b, c)
    verify(m.castles.WARRIOR.heldEggs == a and m.castles.NINJA.heldEggs == b and m.castles.MAGE.heldEggs == c,
        "Unexpected actual authoritative holdings")
    verify(Rules.auditEggConservation(m).valid, "Egg conservation failed")
    verify(m.teamDeposits.RED == 0 and m.teamDeposits.BLUE == 0, "Relay changed team deposit counts")
end
local function pick(m, actor, i)
    return Rules.takeFieldEgg(m, actor, "FIELD_" .. i)
end
local function relay(m, a, b, when)
    return Rules.relayEgg(m, a, b, when, true, v, w)
end
local function rejected(m, from, to, when, expected)
    local lastA, lastB = m.eggRelayLastAt[from], m.eggRelayLastAt[to]
    local heldA, heldB = m.castles[from].heldEggs, m.castles[to].heldEggs
    local events, serial, field = #m.events, m.eggRelaySerial, m.fieldEggs
    local ok, err = pcall(relay, m, from, to, when)
    verify(not ok and tostring(err):find(expected, 1, true), "Wrong rejection: " .. tostring(err))
    verify(m.eggRelayLastAt[from] == lastA and m.eggRelayLastAt[to] == lastB, "Rejection moved shared cooldown")
    verify(m.castles[from].heldEggs == heldA and m.castles[to].heldEggs == heldB, "Rejection moved eggs")
    verify(#m.events == events and m.eggRelaySerial == serial and m.fieldEggs == field, "Rejection touched ledger")
end

verify(Rules.RELAY_COOLDOWN_SECONDS == 12, "Wrong f6c9 12-second limit")
local match = Rules.new(Rules.MODE_TEAM, Rules.makeRoster(Rules.MODE_TEAM, {"WARRIOR", "MAGE", "NINJA"}, 3), 24)
Rules.start(match)
holdings(match, 0, 0, 0)
verify(pick(match, "WARRIOR", 12) == 1 and pick(match, "WARRIOR", 11) == 2 and pick(match, "WARRIOR", 13) == 3,
    "Three distinct sender pickups")
verify(pick(match, "NINJA", 14) == 1, "Receiver ordinary pickup")
holdings(match, 3, 1, 0)
local first = relay(match, "WARRIOR", "NINJA", 20)
verify(first.seq == 1 and first.quantity == 1, "First authoritative receipt")
holdings(match, 2, 2, 0)
rejected(match, "WARRIOR", "NINJA", 31.999, "relay cooldown or invalid clock")
local second = relay(match, "WARRIOR", "NINJA", 32)
verify(second.seq == 2 and second.quantity == 1, "Exactly 12.000 seconds should permit transfer")
holdings(match, 1, 3, 0)
rejected(match, "WARRIOR", "NINJA", 45, "relay cannot invent eggs or exceed inventory cap")
holdings(match, 1, 3, 0)

local alternate = Rules.new(Rules.MODE_TEAM,
    Rules.makeRoster(Rules.MODE_TEAM, {"WARRIOR", "MAGE", "NINJA", "BLUE2", "ALLY3"}, 5), 24)
Rules.start(alternate)
verify(pick(alternate, "WARRIOR", 12) == 1 and pick(alternate, "WARRIOR", 11) == 2, "Second scenario donor carry")
verify(pick(alternate, "ALLY3", 13) == 1, "Fresh third ally carry")
relay(alternate, "WARRIOR", "NINJA", 50)
verify(alternate.eggRelayLastAt.ALLY3 == nil, "Third ally clock must be fresh")
rejected(alternate, "WARRIOR", "ALLY3", 55, "relay cooldown or invalid clock")
rejected(alternate, "ALLY3", "WARRIOR", 55, "relay cooldown or invalid clock")
rejected(alternate, "NINJA", "ALLY3", 55, "relay cooldown or invalid clock")
rejected(alternate, "ALLY3", "NINJA", 55, "relay cooldown or invalid clock")
verify(Rules.auditEggConservation(alternate).valid, "Alternate actors egg conservation")
print(string.format("PASS NATIVE_RULES_BOUNDARY %d checks | 4 legitimate pickups | 11.999 rejects | 12.000 accepts | full rejects | cooldown either endpoint", checks))
