-- GQ8_HUD_INTEL_FOG_20261119 - pure display/layout policy.
-- No remote, HP mutation, purchase, or gameplay authority.
local M = {}
local function clamp(v, lo, hi)
    return math.max(lo, math.min(hi, v))
end
local function at(x, y, size, label)
    return {x = math.floor(x + 0.5), y = math.floor(y + 0.5),
        size = math.floor(size + 0.5), label = label}
end

-- Pixel coordinates are inside Roblox safe-area ScreenGui, not raw device pixels.
-- Client creates actual buttons using these anchors. All users may rearrange
-- positions in a future accessibility setting, but cannot change server rules.
function M.layout(w, h, hand)
    assert(type(w) == "number" and type(h) == "number"
        and w >= 320 and h >= 260 and w <= 8192 and h <= 8192)
    local landscape = w / h >= 1.25
    local s = clamp(math.min(w / 851, h / 393), 0.72, 1.2)
    local attack = clamp(66 * s, 50, 72)
    local small = clamp(48 * s, 42, 58)
    local margin = 14
    local xR = w - math.max(margin + attack / 2, 52)
    local yB = h - math.max(margin + attack / 2, 46)
    local mirror = hand == "LEFT" -- swap combat and movement groups together
    local p
    if landscape then
        p = {
            ATTACK = at(xR, yB - 34 * s, attack, "攻撃"),
            JUMP = at(xR + 4 * s, yB - 115 * s, small, "ジャンプ"),
            DODGE = at(xR - 72 * s, yB - 122 * s, small - 4, "回避"),
            INVUL = at(xR - 125 * s, yB - 60 * s, small + 2, "無敵"),
            MUSOU = at(xR - 83 * s, yB + 8 * s, small + 4, "無双"),
            ITEM = at(xR - 80 * s, math.max(64, h * .32), small - 4, "道具"),
            SKILL = at(xR + 1 * s, math.max(64, h * .32), small - 4, "技"),
            CONTEXT = at(xR - 158 * s, yB - 131 * s, small - 8, "調べる"),
            MOVE = at(math.max(77, w * .13), h - 78 * s, clamp(110 * s, 88, 122), "移動"),
            MAP = at(margin + 47 * s, margin + 47 * s, clamp(94 * s, 76, 106), "地図"),
        }
    else
        local x = w - 50
        -- GQ470_FB015_HUD_PORTRAIT_CLEARANCE_REAL69_20261121
        -- On compact portrait screens the old y=h*.18 put MENU buttons
        -- very close to the HP status strip. Reserve a 7px clearance.
        local menuY = clamp(h * .18, 64, 133)
        -- Narrow portrait ITEM shifts outward to protect the combat center.
        local itemInset = if w <= 360 then 45 else 65
        p = {
            ATTACK = at(x, h - 67, 56, "攻撃"),
            JUMP = at(x, h - 138, 46, "ジャンプ"),
            DODGE = at(x - 66, h - 149, 42, "回避"),
            INVUL = at(x - 122, h - 71, 46, "無敵"),
            MUSOU = at(x - 55, h - 35, 46, "無双"),
            ITEM = at(x - itemInset, menuY, 42, "道具"),
            SKILL = at(x + 1, menuY, 42, "技"),
            CONTEXT = at(x - 145, h - 152, 40, "調べる"),
            MOVE = at(66, h - 75, 95, "移動"),
            MAP = at(60, 64, 88, "地図"),
        }
    end
    if mirror then
        for _, item in pairs(p) do
            item.x = math.floor(w - item.x + 0.5)
        end
    end
    -- Top chrome uses the space *beside* the map. At 320-393px this
    -- prevents HP, attributes and map from occupying the same touch region.
    local mapL = p.MAP.x - p.MAP.size / 2
    local mapR = p.MAP.x + p.MAP.size / 2
    local desiredWidth = math.min(w * .55, 480)
    local statusX, statusWidth
    if mirror then
        local rightEdge = mapL - 10
        statusWidth = math.floor(math.min(desiredWidth, rightEdge - 8))
        statusX = math.floor(rightEdge - statusWidth)
    else
        statusX = math.ceil(mapR + 10)
        statusWidth = math.floor(math.min(desiredWidth, w - statusX - 8))
    end
    assert(statusWidth >= 110, "RED_STATUS_NO_SAFE_WIDTH")
    local chrome = {
        status = {x = statusX, y = 9, w = statusWidth, h = 27},
        musouBar = {
            x = math.floor(statusX + statusWidth * .25), y = 37,
            w = math.floor(statusWidth * .58), h = 5,
        },
        map = {x = math.floor(mapL), y = 8,
            w = p.MAP.size, h = p.MAP.size},
    }
    return {
        anchors = p,
        chrome = chrome,
        orientation = landscape and "LANDSCAPE" or "PORTRAIT",
        combatClear = {x0 = w * .27, x1 = w * .71, y0 = h * .20, y1 = h * .79},
        safeAreaRequired = true,
        defaultVisible = {"ATTACK", "JUMP", "DODGE", "INVUL", "MUSOU",
            "ITEM", "SKILL", "MAP"},
        contextOnly = {"CONTEXT"}, -- show only when server prompt can act
    }
end

-- Use only verified server replicated snapshots. Never synthesize READY, HP,
-- invulnerability, musou charge or a skill entitlement from local timers.
function M.display(snapshot)
    if type(snapshot) ~= "table" or snapshot.serverAuthoritative ~= true then
        return {
            state = "SYNCING", hpText = "--/--", musouCharge = 0,
            phase = "NONE", statuses = {},
            buttons = {INVUL = false, MUSOU = false, ITEM = false, SKILL = false},
        }
    end
    local hp = math.floor(clamp(tonumber(snapshot.hp) or 0, 0, 100000))
    local maxHp = math.floor(clamp(tonumber(snapshot.maxHp) or 1, 1, 100000))
    hp = math.min(hp, maxHp)
    local remainInvul = clamp(tonumber(snapshot.invulRemaining) or 0, 0, 24)
    local remainMusou = clamp(tonumber(snapshot.musouRemaining) or 0, 0, 20)
    local charge = clamp(tonumber(snapshot.musouCharge) or 0, 0, 1)
    local phase = "NONE"
    if remainInvul > 0 then
        phase = "INVUL"
    elseif snapshot.invulArmed == true then
        phase = "ARMED"
    elseif remainMusou > 0 then
        phase = snapshot.musouPhase or "MUSOU"
    end
    local status = {}
    if type(snapshot.statuses) == "table" then
        for _, entry in ipairs(snapshot.statuses) do
            if type(entry) == "table" and type(entry.label) == "string"
                and type(entry.priority) == "number" then
                table.insert(status, {label = string.sub(entry.label, 1, 20),
                    priority = entry.priority, icon = entry.icon or "!"})
            end
        end
    end
    table.sort(status, function(a, b)
        if a.priority == b.priority then return a.label < b.label end
        return a.priority > b.priority
    end)
    local visible = {}
    for i = 1, math.min(3, #status) do visible[i] = status[i] end
    local egg = snapshot.carryingEgg == true
    local down = snapshot.downed == true or hp == 0
    local blocked = egg or down
    return {
        state = down and "DOWN" or "READY",
        hp = hp, maxHp = maxHp, hpText = tostring(hp) .. "/" .. tostring(maxHp),
        statuses = visible, hiddenStatusCount = math.max(0, #status - 3),
        attribute = snapshot.attribute or "NONE",
        phase = phase,
        invulRemaining = remainInvul,
        musouRemaining = remainMusou,
        musouCharge = charge,
        buttons = {
            INVUL = snapshot.invulReady == true and not blocked and remainMusou <= 0
                and remainInvul <= 0 and snapshot.invulArmed ~= true,
            MUSOU = snapshot.musouReady == true and not blocked
                and remainInvul <= 0 and snapshot.invulArmed ~= true and remainMusou <= 0,
            ITEM = snapshot.hasEquippedItem == true and not down,
            SKILL = snapshot.hasEquippedSkill == true and not down,
        },
    }
end

function M.menuItems(kind, owned)
    -- Explicitly supplied server-owned loadout; no purchasing on selection.
    if kind ~= "ITEM" and kind ~= "SKILL" then return {} end
    local out = {}
    if type(owned) ~= "table" then return out end
    for _, item in ipairs(owned) do
        if type(item) == "table" and item.kind == kind
            and item.serverOwned == true and type(item.id) == "string" then
            table.insert(out, {id = item.id, label = item.label or item.id,
                enabled = item.usable == true, cooldown = item.cooldown or 0})
        end
    end
    return out
end

return M
