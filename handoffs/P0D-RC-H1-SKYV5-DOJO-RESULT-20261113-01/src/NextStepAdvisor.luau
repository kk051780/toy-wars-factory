-- TRAP RAIDERS / P0D-BATTLE-DOJO-BRIDGE-001
-- Pure read-only presentation model. Does NOT grant XP, modify DataStore, or own gameplay.
local Advisor = {}

local VALID_SKILL = { beast = true, magic = true, weapon = true, zombie = true, vehicle = true, building = true }
local MAX_LEVEL = 5

local function numberOrZero(v, maxValue)
    if type(v) ~= "number" or v ~= v or v == math.huge or v == -math.huge then
        return 0
    end
    return math.clamp(math.floor(v), 0, maxValue)
end

local function listSkills(supplied)
    local result, found = {}, {}
    if type(supplied) ~= "table" then
        return { "beast", "weapon" } -- compatibility with H1's existing two pads
    end
    for _, skill in ipairs(supplied) do
        if VALID_SKILL[skill] and not found[skill] then
            table.insert(result, skill)
            found[skill] = true
        end
    end
    if #result == 0 then return { "beast", "weapon" } end
    return result
end

function Advisor.build(matchSnapshot, progressSnapshot, options)
    local match = type(matchSnapshot) == "table" and matchSnapshot or {}
    local progress = type(progressSnapshot) == "table" and progressSnapshot or {}
    local opts = type(options) == "table" and options or {}
    local skills = listSkills(opts.availableSkills)
    local levels = type(progress.skillLevels) == "table" and progress.skillLevels or {}
    local targetSkill, lowestLevel = nil, MAX_LEVEL + 1
    for _, skill in ipairs(skills) do
        local lv = numberOrZero(levels[skill], MAX_LEVEL)
        if lv < lowestLevel then
            lowestLevel, targetSkill = lv, skill
        end
    end

    local action, reason
    if progress.canEvolve == true then
        action, reason = "VIEW_EVOLUTION", "進化の条件を達成！次の姿を見てみよう"
    elseif progress.canHatch == true then
        action, reason = "VIEW_HATCH", "獲得した卵を孵化させてみよう"
    elseif targetSkill ~= nil and lowestLevel < MAX_LEVEL then
        action, reason = "VIEW_TRAINING", "次の試合に向けて修行を続けよう"
    else
        action, reason = "PLAY_AGAIN", "もう一度、卵を奪いに行こう"
    end

    return {
        -- Only display values from existing authoritative server snapshots.
        result = match.won == true and "WIN" or (match.won == false and "LOSE" or "PRACTICE"),
        eggsScored = numberOrZero(match.eggsScored, 100),
        neutralDefeats = numberOrZero(match.neutralDefeats, 100000),
        rescues = numberOrZero(match.rescues, 1000),
        action = action,
        actionText = reason,
        suggestedSkill = action == "VIEW_TRAINING" and targetSkill or nil,
        suggestedSkillLevel = action == "VIEW_TRAINING" and lowestLevel or nil,
        friendBonusVisible = opts.sameServerFriendBonus == true,
        autoDismissSeconds = 7,
        dismissible = true,
        readOnly = true,
    }
end

return Advisor
