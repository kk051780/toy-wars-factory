-- NOT FOR PRODUCTION. Only enable in an OWNER-approved isolated Studio copy.
-- Keep disabled when publishing this source packet; it is not a game startup hook.
local ENABLED = false
if not ENABLED then
    return
end

-- In Studio, place this Script beside MascotPreviewFactory/MascotPreviewCatalog
-- inside a fresh isolated ServerScriptService folder. No dependency on game code.
local Factory = require(script.Parent.MascotPreviewFactory)
local left, leftErr = Factory.Build(workspace, "TRCA-BE-018", CFrame.new(-5, 0, 0))
local right, rightErr = Factory.Build(workspace, "TRCA-ZO-054", CFrame.new(5, 0, 0))
assert(left and right, tostring(leftErr) .. " / " .. tostring(rightErr))
assert(Factory.SetPose(left, "tap"))
assert(Factory.SetPose(right, "win"))
print("P0D_D18_MASCOT_PREVIEW_READY", Factory.GetStatus(left).partCount, Factory.GetStatus(right).partCount)
-- Manually inspect both in Play, then Stop and remove this Script before saving.
