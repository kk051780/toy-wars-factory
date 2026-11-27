local Recipes = require("./ComboRecipes")
local Sequence = require("./ComboSequence")
local checks = 0
local function check(value, label)
    checks = checks + 1
    assert(value, label)
end
local function binding()
    return {actor = "a", round = "r", cast = "c"}
end
local function receipt(b, phase, id, success)
    return {binding = b, actor = b.actor, round = b.round, cast = b.cast, phase = phase, receiptId = id, success = success}
end
local rows, roleCounts, phaseCount, stageCount, holds = Recipes.list(), {}, 0, 0, 0
check(#rows == 21, "fixed count")
for _, row in ipairs(rows) do
    roleCounts[row.role] = (roleCounts[row.role] or 0) + 1
    local a, b = row.parts[1], row.parts[2]
    for s = 0, 4 do
        local p = Recipes.resolve(row.role, a, b, s)
        local reverse = Recipes.resolve(row.role, b, a, s)
        check(p and p.id == row.id and p.stage == s, "direct stage")
        check(reverse and reverse.id == p.id, "reverse pair")
        check(p.proposedEnergy == 80 and p.proposedCooldownSec == 40, "proposed costs")
        check(Recipes.resolve("OTHER", a, b, s) == nil, "role")
        check(Recipes.resolve(row.role, a, a, s) == nil, "same slot")
        check(Recipes.resolve(row.role, a, "COMBO-X001", s) == nil, "unknown")
        check(Recipes.resolve(row.role, a, b .. "|x", s) == nil, "delimiter")
        for _, val in pairs(p.limits) do
            check(type(val) == "number" and val == val and val >= 0 and val < math.huge, "finite limit")
            stageCount = stageCount + 1
        end
        local first = p.receipts[1]
        p.receipts[1] = "MUTATED"
        p.parts[1] = "MUTATED"
        local fresh = Recipes.resolve(row.role, a, b, s)
        check(fresh.receipts[1] == first and fresh.parts[1] == a, "isolated snapshot")
        if s == 0 then phaseCount = phaseCount + #fresh.receipts end
        local bind = binding()
        if fresh.hold then
            if s == 0 then holds = holds + 1 end
            check(Sequence.open(fresh, bind, 30, 0) == nil, "hold blocked")
        else
            local tracker = assert(Sequence.open(fresh, bind, 30, 0))
            local foreign = binding()
            check(not tracker.advance(receipt(foreign, first, "bad", true), 1), "foreign binding")
            local wrong = receipt(bind, first, "bad", true)
            wrong.round = "other"
            check(not tracker.advance(wrong, 1), "foreign round")
            wrong = receipt(bind, first, "bad", true); wrong.actor = "other"
            check(not tracker.advance(wrong, 1), "foreign actor")
            wrong = receipt(bind, first, "bad", true); wrong.cast = "other"
            check(not tracker.advance(wrong, 1), "foreign cast")
            check(not tracker.advance(receipt(bind, "UNKNOWN", "bad", true), 1), "phase jump")
            check(not tracker.advance(receipt(bind, first, "", true), 1), "invalid id")
            check(not tracker.advance(receipt(bind, first, "bad", "true"), 1), "invalid success")
            check(not tracker.advance(receipt(bind, first, "bad", true), 0), "time regression")
            local phases = fresh.receipts
            local expected = {}
            for i, v in ipairs(phases) do expected[i] = v end
            phases[1] = "MUTATED_AFTER_START"
            for i, v in ipairs(expected) do
                local state, phase = tracker.current()
                check(state == "OPEN" and phase == v, "current phase snapshot")
                local e = receipt(bind, v, tostring(i), true)
                check(tracker.advance(e, i + 1), "advance")
                check(not tracker.advance(e, i + 1), "replay")
            end
            check(tracker.current() == "COMPLETE", "complete")
            check(not tracker.abort("LATE"), "terminal")
            for stop = 1, #expected do
                tracker = assert(Sequence.open(Recipes.resolve(row.role, a, b, s), bind, 30, 0))
                for i = 1, stop - 1 do
                    check(tracker.advance(receipt(bind, expected[i], tostring(i), true), i), "prefix")
                end
                check(tracker.advance(receipt(bind, expected[stop], tostring(stop), false), stop), "dependency fail accepted")
                check(tracker.current() == "VOID", "dependency void")
                check(not tracker.advance(receipt(bind, expected[stop], "retry", true), stop), "no retry")
            end
            tracker = assert(Sequence.open(Recipes.resolve(row.role, a, b, s), bind, 30, 0))
            check(tracker.abort("ROUND_END") and tracker.current() == "VOID", "round end")
            check(not tracker.advance(receipt(bind, first, "1", true), 1), "end stops")
            tracker = assert(Sequence.open(Recipes.resolve(row.role, a, b, s), bind, 30, 0))
            check(not tracker.expire(30) and tracker.current() == "VOID", "deadline")
        end
    end
    for _, stage in ipairs({-1, 5, 1.5, math.huge, -math.huge, 0/0, "1", false}) do
        check(Recipes.resolve(row.role, a, b, stage) == nil, "invalid stage")
    end
end
check(phaseCount == 58 and stageCount == 300 and holds == 2, "design totals")
local roles = 0
for _, count in pairs(roleCounts) do roles = roles + 1; check(count == 3, "3 per role") end
check(roles == 7, "7 roles")
local sample = Recipes.resolve("WARRIOR", "WARRIOR-060", "WARRIOR-020", 4)
check(sample.limits.neutralMax == 8 and sample.receipts[1] == "FLIGHT_VALID", "corrected flight")
local lightning = Recipes.resolve("MAGE", "MAGE-041", "MAGE-025", 4)
check(lightning.receipts[1] == "WATER_MARK_VALID" and lightning.telegraphMinSec == nil, "canonical order and unspecified telegraph")
check(Sequence.open(sample, binding(), 0, 0) == nil, "nonpositive deadline")
check(Sequence.open(sample, {}, 30, 0) == nil, "invalid binding")
print("PASS combo source checks", checks)
