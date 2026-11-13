-- Pure real Luau CLI tests. The generator embeds the original SHA-locked
-- EggRelayPolicy source before this file and assigns local Relay.
-- No fake Roblox engine pass is claimed.
local tests = 0

local function deepCopy(v)
    if type(v) ~= "table" then return v end
    local out = {}
    for k, value in pairs(v) do
        out[k] = deepCopy(value)
    end
    return out
end

local function eq(a, b)
    if type(a) ~= type(b) then return false end
    if type(a) ~= "table" then return a == b end
    for k, v in pairs(a) do
        if not eq(v, b[k]) then return false end
    end
    for k in pairs(b) do
        if a[k] == nil then return false end
    end
    return true
end

local function fixture()
    local world = {
        phase = "PLAYING",
        roundEpoch = 7,
        nowSec = 100,
        lastAcceptedSeqByUser = {[1] = 4},
        serverLineOfSightClear = true,
        eggs = {
            E2 = {
                id = "E2", phase = "CARRIED", carrierUserId = 1,
                relayEligible = true, transferSeq = 3, lastRelayAtSec = 80,
            },
        },
        players = {
            [1] = {
                alive = true, stunned = false, restrained = false,
                team = "RED", carriedEggId = "E2",
                serverPosition = {x = 0, y = 0, z = 0},
            },
            [2] = {
                alive = true, stunned = false, restrained = false,
                team = "RED", carriedEggId = nil,
                serverPosition = {x = 8, y = 0, z = 0},
            },
        },
    }
    local request = {
        actorUserId = 1, targetUserId = 2, roundEpoch = 7,
        eggId = "E2", seq = 5, expectedTransferSeq = 3,
    }
    return world, request
end

local function check(name, expected, change)
    local world, request = fixture()
    if change then change(world, request) end
    local beforeWorld, beforeRequest = deepCopy(world), deepCopy(request)
    local allowed, receipt = Relay.evaluate(world, request)
    if expected == "ACCEPT" then
        assert(allowed == true, name .. ": unexpectedly denied " .. tostring(receipt))
        assert(type(receipt) == "table", name .. ": no receipt")
        assert(receipt.eggId == request.eggId and receipt.toUserId == request.targetUserId,
            name .. ": receipt mismatch")
        assert(receipt.fromUserId == request.actorUserId, name .. ": actor mismatch")
        assert(receipt.roundEpoch == world.roundEpoch, name .. ": round mismatch")
        assert(receipt.previousTransferSeq == 3 and receipt.newTransferSeq == 4,
            name .. ": transfer version mismatch")
        assert(receipt.acceptedRequestSeq == request.seq, name .. ": request sequence mismatch")
    else
        assert(allowed == false, name .. ": should be blocked")
        assert(receipt == expected,
            name .. ": expected " .. expected .. ", got " .. tostring(receipt))
    end
    assert(eq(world, beforeWorld), name .. ": policy mutated world state")
    assert(eq(request, beforeRequest), name .. ": policy mutated caller request")
    tests += 1
end

check("valid team-to-teammate pass", "ACCEPT")
check("billion scale Roblox player IDs", "ACCEPT", function(w, r)
    local actor, target = 5000000123, 5000000456
    w.players[actor] = w.players[1]
    w.players[target] = w.players[2]
    w.players[1] = nil
    w.players[2] = nil
    w.lastAcceptedSeqByUser[actor] = w.lastAcceptedSeqByUser[1]
    w.lastAcceptedSeqByUser[1] = nil
    w.eggs.E2.carrierUserId = actor
    r.actorUserId = actor
    r.targetUserId = target
end)
check("above maximum exact integer user ID", "INVALID_PARTICIPANTS", function(_, r)
    r.actorUserId = 9007199254740992
end)

check("classic/5 egg ID independent", "ACCEPT", function(w, r)
    local egg = w.eggs.E2
    w.eggs.E2 = nil
    egg.id = "N1"
    w.eggs.N1 = egg
    w.players[1].carriedEggId = "N1"
    r.eggId = "N1"
end)
check("limit exactly eight horizontal", "ACCEPT", function(w)
    w.players[2].serverPosition.x = 8
end)
check("limit exactly four vertical", "ACCEPT", function(w)
    w.players[2].serverPosition.y = 4
end)
check("cooldown exactly 12", "ACCEPT", function(w)
    w.eggs.E2.lastRelayAtSec = 88
end)
check("no previous pass time", "ACCEPT", function(w)
    w.eggs.E2.lastRelayAtSec = nil
end)

check("round already ended", "ROUND_NOT_PLAYING", function(w)
    w.phase = "RESULT"
end)
check("invalid current epoch", "ROUND_NOT_PLAYING", function(w)
    w.roundEpoch = 0
end)
check("request old round", "STALE_ROUND", function(_, r)
    r.roundEpoch = 6
end)
check("request future round", "STALE_ROUND", function(_, r)
    r.roundEpoch = 8
end)
check("self pass", "INVALID_PARTICIPANTS", function(_, r)
    r.targetUserId = 1
end)
check("invalid egg ID", "INVALID_EGG_ID", function(_, r)
    r.eggId = ""
end)
check("oversized egg ID", "INVALID_EGG_ID", function(_, r)
    r.eggId = string.rep("X", 65)
end)
check("zero request sequence", "INVALID_REQUEST_SEQUENCE", function(_, r)
    r.seq = 0
end)
check("bad version", "INVALID_REQUEST_SEQUENCE", function(_, r)
    r.expectedTransferSeq = -1
end)
check("NaN server clock", "INVALID_SERVER_CLOCK", function(w)
    w.nowSec = 0 / 0
end)
check("no canonical egg table", "MISSING_AUTHORITY_STATE", function(w)
    w.eggs = nil
end)
check("duplicate request seq", "REPLAYED_REQUEST", function(_, r)
    r.seq = 4
end)
check("older request seq", "REPLAYED_REQUEST", function(_, r)
    r.seq = 3
end)
check("egg already dropped", "NOT_AUTHORIZED_CARRIER", function(w)
    w.eggs.E2.phase = "DROPPED"
end)
check("egg delivered", "NOT_AUTHORIZED_CARRIER", function(w)
    w.eggs.E2.phase = "VAULT"
end)
check("egg not eligible", "NOT_AUTHORIZED_CARRIER", function(w)
    w.eggs.E2.relayEligible = false
end)
check("actor not true carrier", "NOT_AUTHORIZED_CARRIER", function(w)
    w.eggs.E2.carrierUserId = 42
end)
check("egg transfer already occurred", "STALE_EGG_VERSION", function(_, r)
    r.expectedTransferSeq = 2
end)
check("cooldown remaining", "EGG_PASS_COOLDOWN", function(w)
    w.eggs.E2.lastRelayAtSec = 89
end)
check("future cooldown timestamp", "CLOCK_OR_COOLDOWN_INVALID", function(w)
    w.eggs.E2.lastRelayAtSec = 101
end)
check("missing target user", "PLAYER_MISSING", function(w)
    w.players[2] = nil
end)
check("dead actor", "PLAYER_NOT_ELIGIBLE", function(w)
    w.players[1].alive = false
end)
check("dead receiver", "PLAYER_NOT_ELIGIBLE", function(w)
    w.players[2].alive = false
end)
check("sender restrained", "PLAYER_NOT_ELIGIBLE", function(w)
    w.players[1].restrained = true
end)
check("receiver stunned", "PLAYER_NOT_ELIGIBLE", function(w)
    w.players[2].stunned = true
end)
check("enemy teammate", "WRONG_TEAM", function(w)
    w.players[2].team = "BLUE"
end)
check("sender inventory no longer holds egg", "CARRIER_INVENTORY_CONFLICT", function(w)
    w.players[1].carriedEggId = "OTHER"
end)
check("receiver already holds an egg", "CARRIER_INVENTORY_CONFLICT", function(w)
    w.players[2].carriedEggId = "N1"
end)
check("invalid position", "UNVERIFIED_POSITIONS", function(w)
    w.players[1].serverPosition = {x = 0, y = nil, z = 0}
end)
check("too far horizontal", "OUT_OF_PASS_RANGE", function(w)
    w.players[2].serverPosition.x = 8.01
end)
check("too far vertical", "OUT_OF_PASS_RANGE", function(w)
    w.players[2].serverPosition.y = 4.01
end)
check("blocking wall", "PASS_LINE_OF_SIGHT_BLOCKED", function(w)
    w.serverLineOfSightClear = false
end)
check("missing server raycast", "PASS_LINE_OF_SIGHT_BLOCKED", function(w)
    w.serverLineOfSightClear = nil
end)

assert(tests == 41, "native assertions count changed: " .. tostring(tests))
print("P0D_EGG_RELAY_NATIVE_POLICY_41_CASES_PASS")
