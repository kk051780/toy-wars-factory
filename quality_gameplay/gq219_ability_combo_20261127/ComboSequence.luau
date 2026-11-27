-- Pure server-side ordering helper for fixed combo plans. No game authority.
-- Only the existing authoritative server adapter may call open/advance/abort.
-- The private binding must NEVER be sent through a Remote or derived from a client.
-- This helper does not validate actual hits, timers, costs, ownership, effects or movement.
-- The owner of the existing cast must validate those, pay once, and issue the receipt.
local M = {}
local function finite(x)
    return type(x) == "number" and x == x and x > -math.huge and x < math.huge
end
local function validId(x)
    return type(x) == "string" and #x > 0 and #x <= 128
end
function M.open(plan, binding, deadline, now)
    if type(plan) ~= "table" or plan.hold ~= nil then return nil, "HOLD_OR_PLAN" end
    if type(binding) ~= "table" or not validId(binding.actor) or not validId(binding.round) or not validId(binding.cast) then
        return nil, "BINDING"
    end
    if not finite(now) or not finite(deadline) or deadline <= now then return nil, "TIME" end
    if type(plan.receipts) ~= "table" or #plan.receipts < 1 or #plan.receipts > 4 then return nil, "PHASES" end
    local phases = {}
    for i, p in ipairs(plan.receipts) do
        if not validId(p) then return nil, "PHASES" end
        phases[i] = p
    end
    local actor, round, cast = binding.actor, binding.round, binding.cast
    local index, status, lastTime, reason = 1, "OPEN", now, nil
    local seen = {}
    local tracker = {}
    local function close(why)
        status, reason = "VOID", why
    end
    local function checkTime(t)
        if not finite(t) or t < lastTime then return false, "TIME" end
        lastTime = t
        if t >= deadline then close("EXPIRED"); return false, "EXPIRED" end
        return true
    end
    function tracker.current()
        return status, status == "OPEN" and phases[index] or nil, index, reason
    end
    function tracker.abort(why)
        if status ~= "OPEN" then return false, "TERMINAL" end
        close(validId(why) and why or "ABORTED")
        return true
    end
    function tracker.advance(receipt, t)
        if status ~= "OPEN" then return false, "TERMINAL" end
        local ok, err = checkTime(t)
        if not ok then return false, err end
        if type(receipt) ~= "table" or receipt.binding ~= binding or receipt.actor ~= actor or receipt.round ~= round or receipt.cast ~= cast then
            return false, "BINDING"
        end
        if not validId(receipt.receiptId) or seen[receipt.receiptId] then return false, "REPLAY_OR_ID" end
        if receipt.phase ~= phases[index] then return false, "ORDER" end
        if type(receipt.success) ~= "boolean" then return false, "RESULT" end
        seen[receipt.receiptId] = true
        if not receipt.success then close("DEPENDENCY_FAILED"); return true, status end
        index = index + 1
        if index > #phases then status = "COMPLETE" end
        return true, status
    end
    function tracker.expire(t)
        if status ~= "OPEN" then return false, "TERMINAL" end
        return checkTime(t)
    end
    return tracker
end
return M
