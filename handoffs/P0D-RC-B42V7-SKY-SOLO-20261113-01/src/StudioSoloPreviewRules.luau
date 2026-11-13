--!strict
-- Isolated UNPUBLISHED S1 preview only. No extra Game, remote, match owner.
-- Public server must retain original min 2, BLUE+RED, and empty team ending.
local Solo = {}

function Solo.canStart(isStudio: boolean, count: number,
        red: number, blue: number, minPlayers: number): boolean
    if count >= minPlayers and red > 0 and blue > 0 then
        return true
    end
    -- Only a single genuine Studio test client, never a public server.
    return isStudio == true and count == 1
        and red + blue == 1 and (red == 1 or blue == 1)
end

function Solo.emptyWinner(isStudio: boolean, count: number,
        red: number, blue: number): string?
    if isStudio == true and count == 1 and red + blue == 1 then
        return nil -- don't auto-end private 1-client objective practice
    end
    if red <= 0 then return "BLUE" end
    if blue <= 0 then return "RED" end
    return nil
end

return Solo
