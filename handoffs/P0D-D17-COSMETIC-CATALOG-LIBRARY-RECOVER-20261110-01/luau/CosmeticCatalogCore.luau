-- TRAP RAIDERS D17: preview-only cosmetic catalog, no purchases, XP or rewards.
-- Server must construct this module with trusted activePlayer and ownsEntitlement callbacks.
-- Never pass a client-controlled roster/entitlement function or use this module as a shop.
local Catalog = {}

local ORDER = {
    "banner_starter",
    "egg_glow_amber",
    "lobby_plinth_jade",
    "victory_petals",
    "dragon_wave_emote",
}
local ITEMS = {
    banner_starter = {slot = "BANNER", label = "Starter Banner", gate = "STARTER", maxParticles = 0},
    egg_glow_amber = {slot = "EGG_GLOW", label = "Amber Egg Glow", gate = "ENTITLEMENT", maxParticles = 4},
    lobby_plinth_jade = {slot = "LOBBY_PLINTH", label = "Jade Egg Plinth", gate = "ENTITLEMENT", maxParticles = 0},
    victory_petals = {slot = "VICTORY_FX", label = "Victory Petals (Preview)", gate = "PREVIEW_ONLY", maxParticles = 12},
    dragon_wave_emote = {slot = "EMOTE", label = "Dragon Wave (Preview)", gate = "PREVIEW_ONLY", maxParticles = 0},
}
local VALID_SLOTS = {BANNER = true, EGG_GLOW = true, LOBBY_PLINTH = true, VICTORY_FX = true, EMOTE = true}
local MAX_SESSION_PLAYERS = 256

local function validPlayer(playerKey)
    return (type(playerKey) == "number" and playerKey > 0 and playerKey == math.floor(playerKey) and playerKey < 1e16)
        or (type(playerKey) == "string" and #playerKey > 0 and #playerKey <= 64 and playerKey:match("^[%w_%-]+$") ~= nil)
end
local function safeActive(state, playerKey)
    local ok, value = pcall(state.activePlayer, playerKey)
    return ok and value == true
end
local function entitled(state, playerKey, itemId)
    local item = ITEMS[itemId]
    if item == nil or item.gate == "PREVIEW_ONLY" then return false end
    if item.gate == "STARTER" then return true end
    local ok, value = pcall(state.ownsEntitlement, playerKey, itemId)
    return ok and value == true
end
local function publicItem(itemId, item, isOwned)
    return {
        itemId = itemId,
        slot = item.slot,
        label = item.label,
        gate = item.gate,
        owned = isOwned,
        previewable = true,
        maxParticles = item.maxParticles,
        noCombatStats = true,
        purchaseEnabled = false,
        saved = false,
    }
end
function Catalog.new(activePlayer, ownsEntitlement)
    assert(type(activePlayer) == "function", "TRUSTED_ACTIVE_CALLBACK_REQUIRED")
    assert(type(ownsEntitlement) == "function", "TRUSTED_ENTITLEMENT_CALLBACK_REQUIRED")
    return {activePlayer = activePlayer, ownsEntitlement = ownsEntitlement, selected = {}, count = 0}
end
function Catalog.list(state, playerKey)
    if not validPlayer(playerKey) or not safeActive(state, playerKey) then return nil, "NOT_ACTIVE" end
    local out = {}
    for _, itemId in ipairs(ORDER) do
        local item = ITEMS[itemId]
        table.insert(out, publicItem(itemId, item, entitled(state, playerKey, itemId)))
    end
    return out, "OK"
end
function Catalog.preview(state, playerKey, itemId)
    if not validPlayer(playerKey) or not safeActive(state, playerKey) then return nil, "NOT_ACTIVE" end
    if type(itemId) ~= "string" or #itemId > 64 or ITEMS[itemId] == nil then return nil, "INVALID_ITEM" end
    local item = ITEMS[itemId]
    -- Preview is a *view model* only; does not create a Roblox object or grant ownership.
    return publicItem(itemId, item, entitled(state, playerKey, itemId)), "OK"
end
function Catalog.equip(state, playerKey, itemId)
    if not validPlayer(playerKey) or not safeActive(state, playerKey) then return false, "NOT_ACTIVE" end
    if type(itemId) ~= "string" or #itemId > 64 or ITEMS[itemId] == nil then return false, "INVALID_ITEM" end
    local item = ITEMS[itemId]
    if not entitled(state, playerKey, itemId) then return false, "NOT_OWNED" end
    local selected = state.selected[playerKey]
    if selected == nil then
        if state.count >= MAX_SESSION_PLAYERS then return false, "SESSION_CAPACITY" end
        selected = {}
        state.selected[playerKey] = selected
        state.count += 1
    end
    if selected[item.slot] == itemId then return true, "ALREADY_EQUIPPED" end
    selected[item.slot] = itemId
    return true, "EQUIPPED"
end
function Catalog.unequip(state, playerKey, slot)
    if not validPlayer(playerKey) or not safeActive(state, playerKey) then return false, "NOT_ACTIVE" end
    if type(slot) ~= "string" or VALID_SLOTS[slot] ~= true then return false, "INVALID_SLOT" end
    local selected = state.selected[playerKey]
    if selected == nil or selected[slot] == nil then return true, "ALREADY_EMPTY" end
    selected[slot] = nil
    if next(selected) == nil then
        state.selected[playerKey] = nil
        state.count = math.max(0, state.count - 1)
    end
    return true, "UNEQUIPPED"
end
function Catalog.equipped(state, playerKey)
    if not validPlayer(playerKey) or not safeActive(state, playerKey) then return nil, "NOT_ACTIVE" end
    local out = {}
    local selected = state.selected[playerKey] or {}
    for slot, itemId in pairs(selected) do
        -- Revalidate each read: entitlement revocation immediately hides the effect.
        if VALID_SLOTS[slot] and ITEMS[itemId] and ITEMS[itemId].slot == slot and entitled(state, playerKey, itemId) then
            out[slot] = publicItem(itemId, ITEMS[itemId], true)
        end
    end
    return out, "OK"
end
function Catalog.playerLeft(state, playerKey)
    if state.selected[playerKey] ~= nil then
        state.selected[playerKey] = nil
        state.count = math.max(0, state.count - 1)
    end
end
function Catalog.resetSession(state)
    state.selected = {}
    state.count = 0
end
return Catalog
