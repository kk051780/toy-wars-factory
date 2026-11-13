-- Original P0D/S2 standalone server policy. This module has no side effects.
-- The sole authoritative Game may call evaluate() within its own atomic
-- no-yield egg transfer transaction. Never expose this state as a client API.
local Relay = {}

Relay.MAX_HORIZONTAL_STUDS = 8
Relay.MAX_VERTICAL_STUDS = 4
Relay.MIN_SECONDS_BETWEEN_PASSES = 12

local function isInt(n)
    return type(n) == "number" and n == n and n % 1 == 0 and math.abs(n) < 1000000000
end

local function isNumber(n)
    return type(n) == "number" and n == n and math.abs(n) < 1000000000
end

local function isPosition(p)
    return type(p) == "table" and isNumber(p.x) and isNumber(p.y) and isNumber(p.z)
end

local function deny(code)
    return false, code
end

-- Input shape is described in INTEGRATION_CONTRACT.md.
-- Trusted world snapshot is exclusively assembled on the server. The request
-- carries ONLY egg ID, recipient ID, round epoch, expected transfer version,
-- and a monotonic client request seq (which must still be rate-limited).
function Relay.evaluate(world, request)
    if type(world) ~= "table" or type(request) ~= "table" then
        return deny("INVALID_INPUT")
    end
    if world.phase ~= "PLAYING" or not isInt(world.roundEpoch) or world.roundEpoch < 1 then
        return deny("ROUND_NOT_PLAYING")
    end
    if not isInt(request.roundEpoch) or request.roundEpoch ~= world.roundEpoch then
        return deny("STALE_ROUND")
    end
    if not isInt(request.actorUserId) or not isInt(request.targetUserId)
        or request.actorUserId == request.targetUserId then
        return deny("INVALID_PARTICIPANTS")
    end
    if type(request.eggId) ~= "string" or #request.eggId < 1 or #request.eggId > 64 then
        return deny("INVALID_EGG_ID")
    end
    if not isInt(request.seq) or request.seq < 1 or not isInt(request.expectedTransferSeq)
        or request.expectedTransferSeq < 0 then
        return deny("INVALID_REQUEST_SEQUENCE")
    end
    if not isNumber(world.nowSec) or world.nowSec < 0 then
        return deny("INVALID_SERVER_CLOCK")
    end
    if type(world.players) ~= "table" or type(world.eggs) ~= "table"
        or type(world.lastAcceptedSeqByUser) ~= "table" then
        return deny("MISSING_AUTHORITY_STATE")
    end

    local lastSeq = world.lastAcceptedSeqByUser[request.actorUserId]
    if lastSeq ~= nil and (not isInt(lastSeq) or request.seq <= lastSeq) then
        return deny("REPLAYED_REQUEST")
    end
    local egg = world.eggs[request.eggId]
    if type(egg) ~= "table" or egg.id ~= request.eggId or egg.phase ~= "CARRIED"
        or egg.carrierUserId ~= request.actorUserId or egg.relayEligible ~= true then
        return deny("NOT_AUTHORIZED_CARRIER")
    end
    if not isInt(egg.transferSeq) or request.expectedTransferSeq ~= egg.transferSeq then
        return deny("STALE_EGG_VERSION")
    end
    if egg.lastRelayAtSec ~= nil then
        if not isNumber(egg.lastRelayAtSec) or egg.lastRelayAtSec > world.nowSec then
            return deny("CLOCK_OR_COOLDOWN_INVALID")
        end
        if world.nowSec - egg.lastRelayAtSec < Relay.MIN_SECONDS_BETWEEN_PASSES then
            return deny("EGG_PASS_COOLDOWN")
        end
    end

    local actor = world.players[request.actorUserId]
    local target = world.players[request.targetUserId]
    if type(actor) ~= "table" or type(target) ~= "table" then
        return deny("PLAYER_MISSING")
    end
    if actor.alive ~= true or target.alive ~= true or actor.stunned == true
        or target.stunned == true or actor.restrained == true or target.restrained == true then
        return deny("PLAYER_NOT_ELIGIBLE")
    end
    if (actor.team ~= "RED" and actor.team ~= "BLUE") or actor.team ~= target.team then
        return deny("WRONG_TEAM")
    end
    if actor.carriedEggId ~= request.eggId or target.carriedEggId ~= nil then
        return deny("CARRIER_INVENTORY_CONFLICT")
    end
    if not isPosition(actor.serverPosition) or not isPosition(target.serverPosition) then
        return deny("UNVERIFIED_POSITIONS")
    end
    local dx = actor.serverPosition.x - target.serverPosition.x
    local dy = actor.serverPosition.y - target.serverPosition.y
    local dz = actor.serverPosition.z - target.serverPosition.z
    if math.abs(dy) > Relay.MAX_VERTICAL_STUDS
        or (dx * dx + dz * dz) > (Relay.MAX_HORIZONTAL_STUDS * Relay.MAX_HORIZONTAL_STUDS) then
        return deny("OUT_OF_PASS_RANGE")
    end
    -- This boolean must be computed by the real Game using a fresh server raycast,
    -- never copied from a client payload or an old cached path check.
    if world.serverLineOfSightClear ~= true then
        return deny("PASS_LINE_OF_SIGHT_BLOCKED")
    end

    -- Single non-mutating receipt. The canonical Game must recheck the same
    -- live state under its own transaction and update egg+players together.
    return true, {
        eggId = egg.id,
        fromUserId = request.actorUserId,
        toUserId = request.targetUserId,
        roundEpoch = world.roundEpoch,
        previousTransferSeq = egg.transferSeq,
        newTransferSeq = egg.transferSeq + 1,
        acceptedRequestSeq = request.seq,
        serverNowSec = world.nowSec,
    }
end

return Relay
