-- EGG RAID RUMBLE - FREE hatch -> OWNED -> EQUIP -> SCOUT ability policy.
-- PURE SERVER MODULE. No Remote and no DataStore or round authority.
-- Both egg score/carry snapshots and RNG must be provided by canonical server.
local Rules = {}
local ITEMS = {
    starter_scout = { category = "BEAST", rarity = "STARTER", appearance = "plain" },
    forest_scout = { category = "BEAST", rarity = "COMMON", appearance = "forest" },
    star_scout = { category = "BEAST", rarity = "RARE", appearance = "star" },
}
local CLASSES = {
    WARRIOR=true, MAGE=true, NINJA=true, TRAPPER=true,
    BUILDER=true, BEASTMASTER=true, ZOMBIEMASTER=true,
}
local DURATION = 5
local COOLDOWN = 18
local function integer(v)
    return type(v) == "number" and v == math.floor(v)
end
local function okUser(v)
    return integer(v) and v > 0
end
local function player(s, uid)
    if not okUser(uid) then return nil end
    return s.players[uid]
end
local function cloneMap(input)
    local result = {}
    for k,v in pairs(input) do result[k] = v end
    return result
end
function Rules.new()
    return { phase="LOBBY", epoch=0, players={}, rounds={} }
end
function Rules.enroll(s, uid)
    if not okUser(uid) then return false, "INVALID_PLAYER" end
    if not s.players[uid] then
        s.players[uid] = {
            owned={starter_scout=1}, discovered={starter_scout=true},
            equipped="starter_scout", receipts={}, nextUseAt=0, activeUntil=0,
        }
    end
    return true
end
-- Return only data for server-owned DataStore, not a client-provided equip payload.
function Rules.export(s, uid)
    local p = player(s,uid)
    if not p then return nil, "NOT_ENROLLED" end
    return {owned=cloneMap(p.owned), discovered=cloneMap(p.discovered),
        equipped=p.equipped, receipts=cloneMap(p.receipts)}
end
function Rules.restore(s, uid, record)
    if s.phase ~= "LOBBY" then return false, "NOT_LOBBY" end
    if not okUser(uid) or type(record) ~= "table" then return false, "INVALID_SAVE" end
    if type(record.owned) ~= "table" or type(record.receipts) ~= "table" then
        return false, "INVALID_SAVE"
    end
    local owned = {starter_scout=1}
    for k,v in pairs(record.owned) do
        if not ITEMS[k] or not integer(v) or v < 0 or v > 10000 then
            return false, "INVALID_SAVE"
        end
        if v > 0 then owned[k] = v end
    end
    local receipts = {}
    for epoch,item in pairs(record.receipts) do
        if not integer(epoch) or epoch < 1 or not ITEMS[item] then
            return false, "INVALID_SAVE"
        end
        receipts[epoch] = item
    end
    local equipped = record.equipped
    if not ITEMS[equipped] or not owned[equipped] then equipped="starter_scout" end
    local discovered = {starter_scout=true}
    for k in pairs(owned) do discovered[k]=true end
    s.players[uid] = { owned=owned, discovered=discovered,
        equipped=equipped, receipts=receipts, nextUseAt=0, activeUntil=0 }
    return true
end
-- Call exactly once from the canonical Game controller at real MATCH END.
-- eligible user list and contested rare egg holder set must be server certified.
function Rules.finishRound(s, epoch, eligibleUsers, rareEggHolders)
    if s.phase ~= "ACTIVE" or epoch ~= s.epoch then
        return false, "ROUND_NOT_ACTIVE"
    end
    if type(eligibleUsers) ~= "table" or type(rareEggHolders) ~= "table" then
        return false, "INVALID_SNAPSHOT"
    end
    if s.rounds[epoch] then return false, "ALREADY_FINISHED" end
    local eligible, special = {}, {}
    for uid,allow in pairs(eligibleUsers) do
        if not okUser(uid) or type(allow)~="boolean" then return false, "INVALID_SNAPSHOT" end
        if allow and s.players[uid] then eligible[uid]=true end
    end
    for uid,flag in pairs(rareEggHolders) do
        if not okUser(uid) or type(flag)~="boolean" then return false, "INVALID_SNAPSHOT" end
        if flag and eligible[uid] then special[uid]=true end
    end
    s.rounds[epoch] = {eligible=eligible,special=special}
    s.phase="LOBBY"
    return true
end
-- roll is a SERVER SECRET Random:NextInteger(1,10000) result, never a Remote argument.
-- 0.5% rare from a basic egg, 5% if genuine contested rare egg at buzzer.
-- Both rarity tiers are cosmetic sidegrades of identical scout ability/stats.
function Rules.claimFreeHatch(s, uid, epoch, roll)
    local p=player(s,uid)
    if not p then return false, "NOT_ENROLLED" end
    local rnd=s.rounds[epoch]
    if not rnd or not rnd.eligible[uid] then return false, "NOT_ELIGIBLE" end
    if p.receipts[epoch] then return true, p.receipts[epoch], "ALREADY_GRANTED" end
    if not integer(roll) or roll < 1 or roll > 10000 then
        return false, "INVALID_SERVER_ROLL"
    end
    local rareThreshold = rnd.special[uid] and 500 or 50
    local item = roll <= rareThreshold and "star_scout" or "forest_scout"
    p.receipts[epoch]=item
    p.owned[item]=(p.owned[item] or 0)+1
    p.discovered[item]=true
    return true, item, "GRANTED"
end
function Rules.equip(s,uid,item,class)
    if s.phase~="LOBBY" then return false, "LOBBY_ONLY" end
    local p=player(s,uid)
    if not p then return false, "NOT_ENROLLED" end
    if not CLASSES[class] then return false, "UNKNOWN_CLASS" end
    if not ITEMS[item] or not p.owned[item] or p.owned[item] < 1 then
        return false, "NOT_OWNED"
    end
    p.equipped=item
    return true
end
function Rules.startRound(s, epoch)
    if s.phase~="LOBBY" or not integer(epoch) or epoch<=s.epoch then
        return false, "INVALID_EPOCH"
    end
    s.phase="ACTIVE"
    s.epoch=epoch
    for _,p in pairs(s.players) do p.nextUseAt=0; p.activeUntil=0 end
    return true
end
-- Return a permission token only. The owning Game/World adapter spawns a visible,
-- replicated, counterable scout and verifies world position/team before action.
function Rules.requestScout(s, uid, epoch, now)
    if s.phase~="ACTIVE" or s.epoch~=epoch then return false, "STALE_ROUND" end
    local p=player(s,uid)
    if not p then return false, "NOT_ENROLLED" end
    if not integer(now) or now<0 then return false, "INVALID_TIME" end
    if now<p.nextUseAt or now<p.activeUntil then return false, "COOLDOWN" end
    local item=p.equipped
    if not ITEMS[item] or not p.owned[item] then return false, "NOT_OWNED" end
    p.nextUseAt=now+COOLDOWN
    p.activeUntil=now+DURATION
    return true, {ability="SCOUT", duration=DURATION,
        cooldown=COOLDOWN, cosmetic=ITEMS[item].appearance, itemId=item}
end
function Rules.catalog()
    return cloneMap(ITEMS)
end
return Rules
