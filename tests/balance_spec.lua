local B = dofile(BALANCE_FILE)
local passed, failed, fuzz = 0, 0, 0
local names = {}
local function check(label, cond)
    if cond then passed = passed + 1; names[#names + 1] = "PASS " .. label
    else failed = failed + 1; names[#names + 1] = "FAIL " .. label end
end
local function eq(a,b) return a == b end
check("pon_registered", B.isUnit("pon"))
check("guardon_registered", B.isUnit("guardon"))
check("tankuru_registered", B.isUnit("tankuru"))
check("junk_not_selectable", not B.isUnit("junk"))
check("unknown_not_selectable", not B.isUnit("hack"))
check("nonnumeric_not_selectable", not B.isUnit(123))
check("pon_price", B.UNITS.pon.cost == 10)
check("guardon_price", B.UNITS.guardon.cost == 28)
check("tankuru_price", B.UNITS.tankuru.cost == 48)
check("pon_buy_success", eq(B.buy("pon", 10, 0), 0))
check("tankuru_buy_success", eq(B.buy("tankuru", 50, 1), 2))
check("buy_denies_insufficient", B.buy("tankuru", 47, 1) == nil)
check("buy_denies_negative", B.buy("pon", -1, 1) == nil)
check("buy_denies_fraction", B.buy("pon", 25.5, 1) == nil)
check("buy_denies_nan", B.buy("pon", 0/0, 1) == nil)
check("buy_denies_infinity", B.buy("pon", math.huge, 1) == nil)
check("buy_denies_hacked", B.buy("junk", 100, 1) == nil)
check("buy_denies_full_field", B.buy("pon", 200, B.MAX_FIELD_UNITS) == nil)
check("buy_denies_invalid_count", B.buy("pon", 200, -1) == nil)
check("upgrade_price1", eq(B.upgradePrice(1), 65))
check("upgrade_price5", eq(B.upgradePrice(5), 1625))
check("upgrade_price6_denied", B.upgradePrice(6) == nil)
check("income_level1", eq(B.incomePerSecond(1), 6))
check("income_level6", eq(B.incomePerSecond(6), 21))
check("income_invalid", B.incomePerSecond(7) == nil)
check("wave1_five_enemies", eq(B.waveSize(1), 5))
check("wave50_capped", eq(B.waveSize(50), 20))
check("wave_over_limit_denied", B.waveSize(51) == nil)
check("hp_damage", eq(B.nextHP(40,40,9),31))
check("hp_floored", eq(B.nextHP(1,40,9),0))
check("hp_over_max_denied", B.nextHP(50,40,5) == nil)
check("hp_negative_damage_denied", B.nextHP(50,50,-1) == nil)
check("coins_reward", eq(B.awardCoins(10,8),18))
check("coins_overflow_capped", eq(B.awardCoins(B.MAX_CASH,8),B.MAX_CASH))
check("coins_negative_reward_denied", B.awardCoins(10,-1) == nil)
check("wave_reward", eq(B.waveReward(1),32))
check("wave_reward_invalid", B.waveReward(-1) == nil)
-- Deterministic numeric stress tests. No Roblox engine simulation is claimed.
math.randomseed(20261024)
for i = 1, 4000 do
    local coins = math.random(0, B.MAX_CASH)
    local count = math.random(0, B.MAX_FIELD_UNITS + 4)
    local unit = ({"pon", "guardon", "tankuru"})[math.random(1,3)]
    local new = B.buy(unit, coins, count)
    if new ~= nil then
        assert(new >= 0 and new <= coins)
        assert(new == coins - B.UNITS[unit].cost)
        assert(count < B.MAX_FIELD_UNITS)
    end
    local hp = math.random(0,200)
    local hurt = math.random(0,300)
    local updated = B.nextHP(hp, 200, hurt)
    assert(updated ~= nil and updated >= 0 and updated <= hp)
    local payout = B.awardCoins(coins, math.random(0,500))
    assert(payout and payout >= coins and payout <= B.MAX_CASH)
    fuzz = fuzz + 1
end
if failed ~= 0 then error("QA failed: " .. failed) end
RESULT_SUMMARY = string.format("PASS %d/%d named + %d deterministic stress cases", passed, passed + failed, fuzz)
RESULT_DETAILS = table.concat(names, "\n")
