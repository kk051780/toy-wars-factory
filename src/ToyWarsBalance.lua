--!strict
-- TOY WARS FACTORY v1.2: shared rules. No Roblox API calls; tested in native Lua 5.4.
-- Initial numbers are test hypotheses; not final PvP balance.
local B = {}

B.UNITS = {
    pon = {name = "PON", cost = 10, hp = 40, damage = 9, range = 5.5, speed = 8.5, cooldown = 0.9, reward = 0},
    guardon = {name = "GUARDON", cost = 28, hp = 108, damage = 6, range = 5.6, speed = 5.3, cooldown = 1.2, reward = 0},
    tankuru = {name = "TANKURU", cost = 48, hp = 70, damage = 19, range = 17.0, speed = 4.0, cooldown = 2.1, reward = 0},
    curebo = {name = "CUREBO", cost = 32, hp = 56, damage = 3, range = 6.0, speed = 4.9, cooldown = 1.4, reward = 0, repairAmount = 8, repairRange = 12, repairCooldown = 3.0},
    junk = {name = "JUNK", cost = 0, hp = 38, damage = 6, range = 5.4, speed = 6.0, cooldown = 1.4, reward = 8},
}
B.PLAYABLE_IDS = {"pon", "guardon", "tankuru", "curebo"}
B.MAX_WAVE = 50
B.MAX_FIELD_UNITS = 20
B.MAX_LEVEL = 6
B.MAX_CASH = 999999

local function isInteger(n)
    return type(n) == "number" and n == n and n ~= math.huge and n ~= -math.huge and n == math.floor(n)
end

function B.isUnit(id)
    return type(id) == "string" and id ~= "junk" and B.UNITS[id] ~= nil
end

function B.getUnit(id)
    if type(id) ~= "string" then return nil end
    return B.UNITS[id]
end

function B.canBuy(id, coins, activeCount)
    if not B.isUnit(id) then return false, "invalid_unit" end
    if not isInteger(coins) or coins < 0 or coins > B.MAX_CASH then return false, "invalid_coins" end
    if not isInteger(activeCount) or activeCount < 0 then return false, "invalid_count" end
    if activeCount >= B.MAX_FIELD_UNITS then return false, "field_full" end
    if coins < B.UNITS[id].cost then return false, "not_enough_coins" end
    return true, "ok"
end

function B.buy(id, coins, activeCount)
    local allowed, reason = B.canBuy(id, coins, activeCount)
    if not allowed then return nil, reason end
    return coins - B.UNITS[id].cost, "ok"
end

function B.upgradePrice(level)
    if not isInteger(level) or level < 1 or level >= B.MAX_LEVEL then return nil, "invalid_level" end
    return level * level * 65, "ok"
end

function B.incomePerSecond(level)
    if not isInteger(level) or level < 1 or level > B.MAX_LEVEL then return nil, "invalid_level" end
    return 6 + (level - 1) * 3, "ok"
end

function B.waveSize(wave)
    if not isInteger(wave) or wave < 1 or wave > B.MAX_WAVE then return nil, "invalid_wave" end
    return math.min(3 + 2 * wave, B.MAX_FIELD_UNITS), "ok"
end

function B.nextHP(current, maxHP, damage)
    if not isInteger(current) or not isInteger(maxHP) or current < 0 or maxHP < 1 or current > maxHP then
        return nil, "invalid_hp"
    end
    if not isInteger(damage) or damage < 0 or damage > 100000 then return nil, "invalid_damage" end
    return math.max(0, current - damage), "ok"
end

function B.awardCoins(current, reward)
    if not isInteger(current) or current < 0 or current > B.MAX_CASH then return nil, "invalid_coins" end
    if not isInteger(reward) or reward < 0 then return nil, "invalid_reward" end
    return math.min(B.MAX_CASH, current + reward), "ok"
end

function B.waveReward(wave)
    if not isInteger(wave) or wave < 1 or wave > B.MAX_WAVE then return nil, "invalid_wave" end
    return 24 + wave * 8, "ok"
end

return B

