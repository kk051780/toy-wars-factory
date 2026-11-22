--!strict
-- Native Luau test; requires the selected module in the same test directory.
local B=require("./EGGRUMBLE_BalanceMetrics")
local normal=B.evaluate({
 {mode="TEAM",seconds=720,maxKo=150},
 {mode="BATTLE_ROYALE",seconds=900,maxKo=90},
})
assert(normal.releaseReady and normal.overlongCount==0)
assert(normal.longestRoundSeconds==900)
assert(normal.medianSeconds==810 and not normal.tooLong)
-- Original source incorrectly returned releaseReady=true (median 1110 inside
-- 360..1200) despite a BR game overrunning the 20-minute absolute maximum.
local runaway=B.evaluate({
 {mode="TEAM",seconds=720,maxKo=150},
 {mode="BATTLE_ROYALE",seconds=1500,maxKo=90},
})
assert(runaway.medianSeconds==1110)
assert(runaway.overlongCount==1)
assert(runaway.longestRoundSeconds==1500)
assert(runaway.tooLong and not runaway.releaseReady)
-- Exactly 20m is allowed; per-mode coverage and other metrics remain intact.
local boundary=B.evaluate({
 {mode="TEAM",seconds=1200,maxKo=150},
 {mode="BATTLE_ROYALE",seconds=900,maxKo=90},
})
assert(boundary.releaseReady and boundary.overlongCount==0)
assert(boundary.maxKo==150 and boundary.modeCoverage)
-- The change cannot transform an all-TEAM sample into fake full mode coverage.
local oneMode=B.evaluate({
 {mode="TEAM",seconds=720},
 {mode="TEAM",seconds=900},
})
assert(not oneMode.releaseReady and not oneMode.modeCoverage)
print("GQ_V3_BALANCE_OUTLIER_NATIVE_PASS")
