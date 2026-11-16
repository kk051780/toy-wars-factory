--!strict
-- EGGRUMBLE V3: isolated round-local presentation statistic cleanup, not score authority.
-- Only invoked when the original lobby's server-owned queued mode exits to nil.
local Fence = {}
local LIVE_MODES = {TEAM = true, BATTLE_ROYALE = true}
local RESET = {"EGGRUMBLE_Combo", "EGGRUMBLE_BestCombo"}

function Fence.shouldClear(previous: any, current: any): boolean
    return LIVE_MODES[previous] == true and current == nil
end

-- Session KOs, egg score, castle results and player's saved data are untouched.
-- Existing Swarm is the sole producer of these combo values. Boss credit belongs to PR #514.
function Fence.clear(player: any): number
    for _, attribute in ipairs(RESET) do
        player:SetAttribute(attribute, 0)
    end
    return #RESET
end
return Fence
