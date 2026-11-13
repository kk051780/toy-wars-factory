--!strict
-- UNPUBLISHED Studio-only solo practice guard. No extra Game/Remote or public rules.
-- IMPORTANT: latch whether the round STARTED solo. A 2-client match that later
-- loses one team must still finish; it cannot silently convert into practice.
local Solo = {}

function Solo.canStart(isStudio: boolean, count: number,
        red: number, blue: number, minPlayers: number): boolean
    if count >= minPlayers and red > 0 and blue > 0 then
        return true
    end
    return isStudio == true and count == 1
        and red + blue == 1 and (red == 1 or blue == 1)
end

function Solo.isSoloRound(isStudio: boolean, count: number,
        red: number, blue: number): boolean
    return isStudio == true and count == 1
        and red + blue == 1 and (red == 1 or blue == 1)
end

function Solo.emptyWinner(isStudio: boolean, startedSolo: boolean,
        count: number, red: number, blue: number): string?
    -- Round-latched only; joining or disconnecting never changes the mode.
    if isStudio == true and startedSolo == true
        and count == 1 and red + blue == 1
        and (red == 1 or blue == 1) then
        return nil
    end
    if red <= 0 then return "BLUE" end
    if blue <= 0 then return "RED" end
    return nil
end

return Solo
