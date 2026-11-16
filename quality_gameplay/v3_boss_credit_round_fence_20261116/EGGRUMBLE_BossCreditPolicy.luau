--!strict
-- Pure source-only policy. Game/Remote/score authorities remain unchanged.
local Policy = {}
local MATCH_MODE = {TEAM = true, BATTLE_ROYALE = true}
function Policy.shouldReset(previousMode: any, currentMode: any): boolean
    -- Only real mode boundary events reset the session-bound boss counter.
    -- A repeated notification or a malformed value must never erase a real KO.
    if previousMode == currentMode then return false end
    local previousValid = previousMode == nil or MATCH_MODE[previousMode] == true
    local currentValid = currentMode == nil or MATCH_MODE[currentMode] == true
    return previousValid and currentValid
end
return Policy
