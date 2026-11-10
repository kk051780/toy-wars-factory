-- Isolated, UNPUBLISHED Studio-only smoke test; placement must be adapted by Codex.
-- Do not keep this script in production ServerScriptService.
local Core = require(script.Parent.SessionStampCore)
local View = require(script.Parent.SessionStampViewModel)
local state = assert(Core.newState(123456))
local function round(id, won, contributes)
    return {
        kind = "SERVER_FINALIZED_ROUND", matchId = id,
        userId = 123456, stageId = "S1", jobId = "TRAPPER",
        completed = true, won = won, contributed = contributes,
        roundSeconds = 60, activeSeconds = 35, meaningfulServerActions = 2,
    }
end
local a, one = Core.apply(state, round("smoke-001", false, false))
assert(one.status == "AWARDED_SESSION_ONLY" and one.awarded == 1)
local b, duplicate = Core.apply(a, round("smoke-001", true, true))
assert(b == a and duplicate.status == "DUPLICATE_FINALIZATION")
local c, win = Core.apply(b, round("smoke-002", true, false))
assert(win.awarded == 2 and c.stamps == 3)
assert(#win.unlocks == 1 and win.unlocks[1] == "FREE_EGG_BANNER")
local ui = View.fromRewardView(Core.view(c), win)
assert(ui.sessionOnly and ui.saved == false and ui.totalStamps == 3)
assert(ui.saveLabel == "This session only - not saved")
print("TRAP_RAIDERS_V39_SESSION_STAMP_SMOKE_PASS")
