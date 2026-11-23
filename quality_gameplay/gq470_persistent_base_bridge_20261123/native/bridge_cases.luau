-- Diagnostic Native boundary: fake Player Instances and injected Host predicates
-- do NOT authenticate Studio, real Players, real persistence or runtime wiring.
-- All six original donor bodies execute; only GetAsync/Player/Host are fixtures.
local Bridge = require("EGGRUMBLE_PersistentBaseAdmission")
local Store = require("PersistentHatchStore")
local failures, totalReads, totalWrites = 0, 0, 0

local function expect(id, condition)
    print("CHECK\t" .. id .. "\t" .. (if condition then "PASS" else "FAIL"))
    assert(condition, id)
end
local function case(name, run)
    local ok, message = pcall(run)
    print("CASE\t" .. name .. "\t" .. (if ok then "PASS" else "FAIL") .. "\t" .. tostring(message or "ok"))
    if not ok then failures += 1 end
end
local function rejected(expected, value, code)
    return value == nil and code == expected
end
local function player(uid)
    local value = {UserId = uid, Character = {}, IsA = function(_, class) return class == "Player" end}
    fakePlayers[value] = true
    return value
end
local function record(level, revision, xp)
    local raw = Store.blank()
    raw.revision = revision
    raw.progress = {level = level, xp = xp or 0, mastery = {forest_scout = {level = 2, xp = 7}},
        claimedRoundIds = {}, settledCount = 0}
    return raw
end
local function fixture(uid)
    local f = {player = player(uid or 42), round = {phase = "ACTIVE", attributePhase = "ACTIVE"},
        eligible = true, allowed = true, queue = {}, keys = {}, options = {}, reads = 0, writes = 0}
    f.store = {}
    function f.store:GetAsync(key, options)
        f.reads += 1; totalReads += 1
        table.insert(f.keys, key); f.lastOptions = options
        local nextValue = table.remove(f.queue, 1)
        assert(nextValue ~= nil, "unexpected GetAsync")
        if nextValue.pause then nextValue = coroutine.yield("WAIT_GET_ASYNC") end
        if nextValue.fail then error("fixture read unavailable") end
        return nextValue.raw
    end
    function f.store:SetAsync(...)
        f.writes += 1; totalWrites += 1; error("forbidden SetAsync")
    end
    function f.store:UpdateAsync(...)
        f.writes += 1; totalWrites += 1; error("forbidden UpdateAsync")
    end
    f.api = assert(Bridge.new({store = f.store, readOptions = f.options,
        eligible = function(p, fullUid)
            if f.throwEligible then error("eligible unavailable") end
            if p ~= f.player or fullUid ~= p.UserId then return false end
            return f.eligible
        end,
        member = function(p, round)
            if f.throwMember then error("membership unavailable") end
            return f.allowed and p == f.player and round == f.round
                and round.phase == "ACTIVE" and round.retired ~= true
        end}))
    f.account = assert(f.api:bind(f.player))
    function f:read(raw)
        table.insert(self.queue, {raw = raw})
        return self.api:read(self.account)
    end
    function f:fail()
        table.insert(self.queue, {fail = true})
        return self.api:read(self.account)
    end
    function f:start()
        table.insert(self.queue, {pause = true})
        local job, token = {}, self.account
        job.thread = coroutine.create(function() job.result = {self.api:read(token)} end)
        local ok, reason = coroutine.resume(job.thread)
        assert(ok and reason == "WAIT_GET_ASYNC" and coroutine.status(job.thread) == "suspended", tostring(reason))
        return job
    end
    return f
end
local function finish(job, raw, fail)
    local ok, reason = coroutine.resume(job.thread, {raw = raw, fail = fail})
    assert(ok and coroutine.status(job.thread) == "dead", tostring(reason))
    return table.unpack(job.result, 1, 2)
end

case("PB01_ACCOUNT_AND_UNLOADED", function()
    expect("PB01_BAD_CONSTRUCTOR", rejected("INVALID_ARGUMENT", Bridge.new(nil)))
    local f = fixture()
    expect("PB01_OPAQUE_FROZEN_TOKEN", next(f.account) == nil and table.isfrozen(f.account))
    expect("PB01_BIND_IDEMPOTENT", f.api:bind(f.player) == f.account)
    expect("PB01_NOT_LOADED", rejected("NOT_LOADED", f.api:peek(f.account)))
    local admission = {}
    expect("PB01_NO_UNREADY_ADMISSION", rejected("NOT_LOADED", f.api:admit(f.account, f.round, admission)))
    local ended, code = f.api:endAdmission(f.account, f.round, admission)
    expect("PB01_UNREADY_HAS_NO_ENTRY", ended == false and code == "STALE_ADMISSION")
    expect("PB01_NOT_PLAYER", rejected("INVALID_ARGUMENT", f.api:bind({UserId = 42})))
    expect("PB01_NONPOSITIVE_UID", rejected("INVALID_ARGUMENT", f.api:bind(player(0))))
    expect("PB01_NO_READ_SIDE_EFFECT", f.reads == 0 and f.writes == 0)
end)

case("PB02_LEVELS_FULL_UID_AND_COPY", function()
    local a, b = fixture(42), fixture(100000040)
    local inputA, inputB = record(5, 7, 13), record(20, 9, 21)
    local x, xc = a:read(inputA); local y, yc = b:read(inputB)
    expect("PB02_DISTINCT_LEVELS", xc == "OK" and yc == "OK" and x.level == 5 and y.level == 20)
    expect("PB02_FULL_UID_SNAPSHOT", x.userId == 42 and y.userId == 100000040)
    expect("PB02_POLICY_COLLISION_NOT_KEY", Store.policyUserId(42) == Store.policyUserId(100000040)
        and a.keys[1] == "U_42" and b.keys[1] == "U_100000040")
    expect("PB02_WITHIN_LEVEL_XP", x.xp == 13 and y.xp == 21)
    expect("PB02_ITEM_MASTERY", x.mastery.forest_scout.level == 2 and x.mastery.forest_scout.xp == 7)
    expect("PB02_NESTED_COPY", x.mastery ~= inputA.progress.mastery
        and x.mastery.forest_scout ~= inputA.progress.mastery.forest_scout)
    expect("PB02_DEEP_FROZEN", table.isfrozen(x) and table.isfrozen(x.mastery)
        and table.isfrozen(x.mastery.forest_scout))
    expect("PB02_REJECT_MUTATION", not pcall(function() x.mastery.forest_scout.xp = 99 end))
    inputA.progress.mastery.forest_scout.xp = 6
    expect("PB02_INPUT_NONALIAS", x.mastery.forest_scout.xp == 7 and not table.isfrozen(inputA))
    expect("PB02_OPTIONS_UNCHANGED", a.lastOptions == a.options and not table.isfrozen(a.options))
end)

case("PB03_NORMALIZED_BLANK_NOT_SAVED", function()
    local f = fixture()
    local first, fc = f:read(nil); local savedEquivalent, sc = f:read(Store.blank())
    expect("PB03_BOTH_NORMALIZED_READS", fc == "OK" and sc == "OK" and first.level == 1
        and savedEquivalent.level == 1 and first.revision == 0 and savedEquivalent.revision == 0)
    expect("PB03_NO_RAW_EXISTENCE_CLAIM", first.wasNil == nil and first.isNew == nil
        and first.recordExists == nil and first.defaultOrigin == nil and first.SAVED == nil)
    expect("PB03_FAILURE_DISTINCT", rejected("READ_FAILED", f:fail()))
    expect("PB03_NO_OLD_BLANK_FALLBACK", rejected("READ_FAILED", f.api:peek(f.account)))
    expect("PB03_FAILURE_NO_NEW_ENTRY", rejected("READ_FAILED", f.api:admit(f.account, f.round, {})))
    local value, code = f:read(Store.blank())
    expect("PB03_RECOVERY_EXPLICIT_READ", code == "OK" and value.level == 1 and f.reads == 4)
end)

case("PB04_CORRUPT_UNSAFE_AND_EXCEPTION", function()
    local f = fixture()
    local dojo = Store.blank(); dojo.dojo = {}
    local dojoV4 = Store.blank(); dojoV4.dojoV4 = {}
    expect("PB04_LEGACY_DOJO", rejected("CORRUPT_RECORD", f:read(dojo)))
    expect("PB04_LEGACY_DOJOV4", rejected("CORRUPT_RECORD", f:read(dojoV4)))
    local unsafe = Store.blank(); unsafe.revision = 9007199254740992
    expect("PB04_UNSAFE_REVISION", rejected("INVALID_PROFILE", f:read(unsafe)))
    local explosive = setmetatable({}, {__index = function() error("donor validation exception") end})
    expect("PB04_DONOR_ERROR", rejected("DONOR_ERROR", f:read(explosive)))
    expect("PB04_ERROR_IS_CURRENT", rejected("DONOR_ERROR", f.api:peek(f.account)))
    local value, code = f:read(record(5, 1))
    expect("PB04_EXCEPTION_RELEASES_TICKET", code == "OK" and value.level == 5)
    local max = fixture(); local raw = Store.blank(); raw.revision = 9007199254740991
    local maximum, mc = max:read(raw)
    expect("PB04_MAX_SAFE_REVISION", mc == "OK" and maximum.revision == 9007199254740991)
end)

case("PB05_ADMISSION_FIXED_DURING_READS", function()
    local f = fixture(); local loaded = assert(f:read(record(5, 1)))
    local admission = {}; local fixed, code = f.api:admit(f.account, f.round, admission)
    expect("PB05_ADMISSION_COPY", code == "OK" and fixed ~= loaded and fixed.mastery ~= loaded.mastery)
    local pending = f:start()
    expect("PB05_PENDING_PEEK", rejected("READ_PENDING", f.api:peek(f.account)))
    expect("PB05_PENDING_GET_FIXED", f.api:get(f.account, f.round, admission) == fixed)
    expect("PB05_PENDING_SAME_ADMIT_FIXED", f.api:admit(f.account, f.round, admission) == fixed)
    expect("PB05_READ_FAILURE", rejected("READ_FAILED", finish(pending, nil, true)))
    expect("PB05_FAILURE_SAME_ADMIT_FIXED", f.api:admit(f.account, f.round, admission) == fixed)
    local later = assert(f:read(record(20, 2)))
    expect("PB05_NEW_READ_OLD_ADMISSION", later.level == 20 and f.api:get(f.account, f.round, admission).level == 5)
    f.player.Character = {}
    expect("PB05_RESPAWN_SAME_ADMISSION", f.api:get(f.account, f.round, admission) == fixed)
    expect("PB05_CONFLICT", rejected("ADMISSION_CONFLICT", f.api:admit(f.account, f.round, {})))
    expect("PB05_HOST_TOKENS_NOT_FROZEN", not table.isfrozen(f.round) and not table.isfrozen(admission)
        and not table.isfrozen(f.player))
end)

case("PB06_FINISHED_AND_STALE_CLEANUP", function()
    local f = fixture(); assert(f:read(record(5, 1))); local old = {}
    assert(f.api:admit(f.account, f.round, old))
    f.round.phase = "FINISHED" -- attribute remains ACTIVE; no delayed close has run.
    expect("PB06_FINISHED_GET_REJECTED", rejected("STALE_ADMISSION", f.api:get(f.account, f.round, old)))
    expect("PB06_FINISHED_ADMIT_REJECTED", rejected("STALE_ADMISSION", f.api:admit(f.account, f.round, old)))
    expect("PB06_ACCOUNT_READ_RETAINED", f.api:peek(f.account).level == 5 and f.round.attributePhase == "ACTIVE")
    f.eligible = false
    expect("PB06_CLEANUP_WITHOUT_ELIGIBILITY", f.api:endAdmission(f.account, f.round, old) == true)
    f.eligible = true; f.round = {phase = "ACTIVE"}; local fresh = {}
    assert(f.api:admit(f.account, f.round, fresh))
    local removed, why = f.api:endAdmission(f.account, f.round, old)
    expect("PB06_STALE_END_NO_CLEAR", removed == false and why == "STALE_ADMISSION"
        and f.api:get(f.account, f.round, fresh).level == 5)
    f.eligible = false
    expect("PB06_REMOVE_WITHOUT_ELIGIBILITY", f.api:remove(f.account) == true)
end)

case("PB07_R2_R3_OLD_R1_ORDER", function()
    local f = fixture(); local r1, r2 = f:start(), f:start()
    expect("PB07_TWO_ONLY", rejected("READ_BUSY", f.api:read(f.account)) and f.reads == 2)
    local second, code = finish(r2, record(5, 12))
    expect("PB07_R2_ACCEPTED", code == "OK" and second.revision == 12)
    local r3 = f:start()
    expect("PB07_OLD_HIGH_REVISION_STALE", rejected("STALE_READ", finish(r1, record(20, 99))))
    expect("PB07_R3_STILL_PENDING", rejected("READ_PENDING", f.api:peek(f.account)))
    local third, tc = finish(r3, record(20, 13))
    expect("PB07_R3_ACCEPTED_UNTAINTED", tc == "OK" and third.revision == 13 and f.reads == 3)
end)

case("PB08_STALE_TICKET_RELEASES_OWN_SLOT", function()
    local f = fixture(); local r1, r2 = f:start(), f:start()
    assert(finish(r2, record(5, 12))); local r3 = f:start()
    expect("PB08_OLD_R1_STALE", rejected("STALE_READ", finish(r1, record(20, 99))))
    local r4 = f:start()
    expect("PB08_R3_R4_FILL_TWO", rejected("READ_BUSY", f.api:read(f.account)) and f.reads == 4)
    expect("PB08_R3_SUPERSEDED_BY_R4", rejected("STALE_READ", finish(r3, record(20, 13))))
    local latest, code = finish(r4, record(20, 14))
    expect("PB08_R4_ACCEPTED", code == "OK" and latest.revision == 14)
end)

case("PB09_REMOVE_REBIND_OLD_COMPLETION", function()
    local f = fixture(); local oldAccount = f.account; local old1, old2 = f:start(), f:start()
    expect("PB09_REMOVE_INVALIDATES", f.api:remove(oldAccount) == true)
    f.account = assert(f.api:bind(f.player))
    expect("PB09_SAME_PLAYER_FRESH_TOKEN", f.account ~= oldAccount)
    local new1, new2 = f:start(), f:start()
    expect("PB09_OLD_COMPLETION_STALE", rejected("STALE_READ", finish(old2, record(20, 99))))
    expect("PB09_OLD_TICKET_NOT_NEW_CAPACITY", rejected("READ_BUSY", f.api:read(f.account)) and f.reads == 4)
    expect("PB09_OTHER_OLD_COMPLETION_STALE", rejected("STALE_READ", finish(old1, nil, true)))
    expect("PB09_OLD_TOKEN_PERMANENTLY_STALE", rejected("STALE_ACCOUNT", f.api:peek(oldAccount)))
    expect("PB09_OLD_READ_CALL_STALE", rejected("STALE_ACCOUNT", f.api:read(oldAccount)))
    expect("PB09_NEW_OLDER_READ_STALE", rejected("STALE_READ", finish(new1, record(5, 1))))
    local value, code = finish(new2, record(20, 2))
    expect("PB09_NEW_ACCOUNT_ACCEPTED", code == "OK" and value.revision == 2)
    local removed, why = f.api:remove(oldAccount)
    expect("PB09_OLD_REMOVE_NO_CLEAR", removed == false and why == "STALE_ACCOUNT"
        and f.api:peek(f.account).level == 20)
end)

case("PB10_LATEST_FAILURE_NO_FALLBACK", function()
    local f = fixture(); assert(f:read(record(5, 1)))
    local r1, r2 = f:start(), f:start()
    expect("PB10_LATEST_FAILURE", rejected("READ_FAILED", finish(r2, nil, true)))
    expect("PB10_OLD_SUCCESS_STALE", rejected("STALE_READ", finish(r1, record(20, 99))))
    expect("PB10_PEEK_STILL_FAILED", rejected("READ_FAILED", f.api:peek(f.account)))
    expect("PB10_ADMISSION_STILL_FAILED", rejected("READ_FAILED", f.api:admit(f.account, f.round, {})))
    local value, code = f:read(record(5, 2))
    expect("PB10_RECOVERY_NOT_TAINTED_BY_99", code == "OK" and value.revision == 2)
end)

case("PB11_REVISION_AND_MASTERY_EQUALITY", function()
    local f = fixture(); local a = record(5, 10)
    a.progress.mastery.starter_scout = {level = 1, xp = 1}
    assert(f:read(a))
    local b = record(5, 10)
    b.progress.mastery = {starter_scout = {level = 1, xp = 1}, forest_scout = {level = 2, xp = 7}}
    local same, sc = f:read(b)
    expect("PB11_VALUE_EQUAL_DIFFERENT_TABLES", sc == "OK" and same.revision == 10)
    local conflict = record(5, 10); conflict.progress.mastery.starter_scout = {level = 1, xp = 1}
    conflict.progress.mastery.forest_scout.xp = 6
    expect("PB11_MASTERY_LEAF_CONFLICT", rejected("REVISION_CONFLICT", f:read(conflict)))
    expect("PB11_CONFLICT_NOT_PUBLIC_OLD", rejected("REVISION_CONFLICT", f.api:peek(f.account)))
    expect("PB11_LOWER_REVISION_REJECTED", rejected("REVISION_REGRESSION", f:read(record(5, 9))))
    local recovered, rc = f:read(b)
    expect("PB11_REJECTION_DID_NOT_POLLUTE_BASE", rc == "OK" and recovered.mastery.forest_scout.xp == 7)
    expect("PB11_DELETED_RECORD_NOT_RESET", rejected("REVISION_REGRESSION", f:read(nil)))
    local advanced, ac = f:read(record(20, 11))
    expect("PB11_HIGHER_REVISION_ACCEPTED", ac == "OK" and advanced.level == 20)
end)

case("PB12_ELIGIBILITY_AND_MEMBERSHIP_FAILURE", function()
    local f = fixture(); local job = f:start(); f.eligible = false
    expect("PB12_COMPLETION_RECHECK", rejected("INELIGIBLE", finish(job, record(5, 1))))
    f.eligible = true
    expect("PB12_FAILED_RECHECK_NO_PENDING_STUCK", rejected("INELIGIBLE", f.api:peek(f.account)))
    assert(f:read(record(5, 2))); f.eligible = "truthy"
    expect("PB12_ELIGIBLE_EXACT_TRUE", rejected("INELIGIBLE", f.api:read(f.account)) and f.reads == 2)
    f.eligible = true; f.throwEligible = true
    expect("PB12_ELIGIBILITY_EXCEPTION_REJECTED", rejected("INELIGIBLE", f.api:bind(f.player)))
    f.throwEligible = false; local entry = {}; assert(f.api:admit(f.account, f.round, entry))
    f.throwMember = true
    expect("PB12_MEMBERSHIP_EXCEPTION_REJECTED", rejected("STALE_ADMISSION", f.api:get(f.account, f.round, entry)))
    expect("PB12_CLEANUP_NOT_BLOCKED_BY_CALLBACK", f.api:endAdmission(f.account, f.round, entry) == true)
end)

case("PB13_CONCRETE_PLAYER_SAME_UID", function()
    local f = fixture(); local oldAccount, oldPlayer = f.account, f.player
    local old = f:start(); f.player = player(oldPlayer.UserId)
    f.account = assert(f.api:bind(f.player))
    expect("PB13_NEW_INSTANCE_NEW_ACCOUNT", f.account ~= oldAccount)
    expect("PB13_OLD_INSTANCE_NOT_ELIGIBLE", rejected("INELIGIBLE", finish(old, record(20, 99))))
    local value, code = f:read(record(5, 1))
    expect("PB13_FULL_UID_NOT_ACCOUNT_IDENTITY", code == "OK" and value.userId == 42 and value.level == 5)
    expect("PB13_OLD_REMOVE_PRESERVES_NEW", f.api:remove(oldAccount) == true and f.api:peek(f.account) == value)
    expect("PB13_NEW_ROUND_NO_OLD_AUTHORITY", rejected("STALE_ADMISSION", f.api:admit(f.account, {phase = "ACTIVE"}, {})))
end)

case("PB14_NO_SAVING_WRITES", function()
    expect("PB14_ZERO_WRITES", totalWrites == 0)
    expect("PB14_ACTUAL_DONOR_READS_EXECUTED", totalReads > 40)
end)
print("METRIC\tGetAsync\t" .. totalReads)
print("METRIC\tSavingWrites\t" .. totalWrites)
assert(failures == 0, tostring(failures) .. " failed cases")
