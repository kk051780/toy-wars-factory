--!strict
-- P0D H1 release safety: review-only staging. DO NOT ENABLE LIVE until #220 OWNER approval.
-- Source-local immutable flags: no attributes, remote messages, client inputs, or economy can enable production.
local ReleaseGate = {}
local LIVE_ENABLE = false -- intentionally disabled for all published games
local APPROVED_GAME_ID = 0 -- OWNER must explicitly authorize a positive UniverseId
local APPROVED_PLACE_ID = 0 -- OWNER must explicitly authorize a positive PlaceId

local function validId(x: any): boolean
    return type(x) == "number" and x == x
        and x > 0 and x < 1000000000000000 and x % 1 == 0
end

function ReleaseGate.canRun(isStudio: any, gameId: any, placeId: any): boolean
    if isStudio == true then return true end
    if isStudio ~= false then return false end
    return LIVE_ENABLE == true
        and validId(APPROVED_GAME_ID) and validId(APPROVED_PLACE_ID)
        and validId(gameId) and validId(placeId)
        and gameId == APPROVED_GAME_ID and placeId == APPROVED_PLACE_ID
end

return ReleaseGate
