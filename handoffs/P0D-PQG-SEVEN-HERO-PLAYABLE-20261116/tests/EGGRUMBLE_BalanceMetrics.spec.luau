--!strict
-- Native Luau regression for isolated balance module; no Roblox engine services.
local B=require("../EGGRUMBLE_BalanceMetrics")
assert(B.neutralBudget(16,"TEAM",3)==128)
assert(B.neutralBudget(16,"BATTLE_ROYALE",3)==96)
assert(B.neutralBudget(16,"TEAM",1)==64)
assert(B.neutralBudget(1,"TEAM",1)==24)
assert(B.neutralBudget(32,"TEAM",3)==144)
assert(B.siegeMultiplier(0,"TEAM",false)==1)
assert(B.siegeMultiplier(900,"TEAM",false)==1)
assert(B.siegeMultiplier(1200,"TEAM",false)==1.25)
assert(B.siegeMultiplier(1200,"TEAM",true)<=1.35)
assert(B.siegeMultiplier(1200,"BATTLE_ROYALE",false)<=1.35)
assert(B.castleParity(1000,50))
assert(not B.castleParity(1000,51))
assert(not B.castleParity(1200,50))
local score=B.score(400,2,1,200,1)
assert(score.ko==700 and score.raid==150 and score.delivery==100)
assert(score.siege==10 and score.elimination==250 and score.total==1210)
local good=B.evaluate({
 {mode="TEAM",seconds=720,maxKo=2000},
 {mode="BATTLE_ROYALE",seconds=900,maxKo=1000},
})
assert(good.releaseReady and good.medianSeconds==810 and good.modeCoverage)
local short=B.evaluate({
 {mode="TEAM",seconds=100},{mode="BATTLE_ROYALE",seconds=200},
})
assert(short.tooShort and not short.releaseReady)
local missing=B.evaluate({
 {mode="TEAM",seconds=800},{mode="TEAM",seconds=1000},
})
assert(not missing.modeCoverage and not missing.releaseReady)
print("EGGRUMBLE_BALANCE_NATIVE_SOURCE_PASS")
