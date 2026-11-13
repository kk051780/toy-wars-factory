--!strict
-- TRAP_RAIDERS S2+: one shared central gate after a trusted neutral elite KO.
-- Pure state machine only. One Game.server.luau remains the round/KO/score authority.
local GateRules = {}
GateRules.__index = GateRules

local WARNING_SECONDS = 2
local OPEN_SECONDS = 10

local function isValidTime(value)
    return type(value) == "number" and value == value
        and value > -math.huge and value < math.huge and value >= 0
end

local function validCount(value)
    return type(value) == "number" and value == math.floor(value)
        and value >= 0 and value <= 128
end

function GateRules.new(roundId: string)
    assert(type(roundId) == "string" and #roundId > 0, "roundId required")
    return setmetatable({
        roundId = roundId,
        phase = "LOCKED",
        triggered = false,
        warningUntil = nil,
        openUntil = nil,
        lastNow = 0,
    }, GateRules)
end

function GateRules:_validRequest(roundId, now)
    if roundId ~= self.roundId or not isValidTime(now) or now < self.lastNow then
        return false
    end
    self.lastNow = now
    return true
end

-- Call only from existing server-owned Horde elite KO receipt, never a Remote.
-- Returns true only for the first authentic KO in the current round.
function GateRules:onEliteKO(roundId: string, isElite: boolean, now: number): boolean
    if not self:_validRequest(roundId, now) then
        return false
    end
    if isElite ~= true or self.triggered or self.phase ~= "LOCKED" then
        return false
    end
    self.triggered = true
    self.phase = "WARNING"
    self.warningUntil = now + WARNING_SECONDS
    self.openUntil = now + WARNING_SECONDS + OPEN_SECONDS
    return true
end

-- occupants comes from server-only overlap query around the physical door.
-- A player standing within the door prevents it closing onto that player.
-- The safe permanent alternate route must remain present independently.
function GateRules:step(roundId: string, now: number, occupants: number): boolean
    if not validCount(occupants) or not self:_validRequest(roundId, now) then
        return false
    end
    if self.phase == "WARNING" and now >= self.warningUntil then
        self.phase = now < self.openUntil and "OPEN" or
            (occupants > 0 and "WAIT_CLEAR" or "CLOSED")
    end
    if self.phase == "OPEN" and now >= self.openUntil then
        self.phase = occupants > 0 and "WAIT_CLEAR" or "CLOSED"
    end
    if self.phase == "WAIT_CLEAR" and occupants == 0 then
        self.phase = "CLOSED"
    end
    return true
end

function GateRules:snapshot()
    local passable = self.phase == "OPEN" or self.phase == "WAIT_CLEAR"
    return {
        roundId = self.roundId,
        phase = self.phase,
        passable = passable,
        triggered = self.triggered,
        warningUntil = self.warningUntil,
        openUntil = self.openUntil,
    }
end

-- The existing Game server should create a NEW rules instance for next round.
-- Do not reset while players are in the doorway: remove round map after respawn.
return GateRules
