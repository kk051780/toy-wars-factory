-- Execute the canonical whole server and observe replicated status property writes.
-- Native Lua harness only: no Roblox network, client rendering or device proof.
local Harness = dofile("tests/roblox_server_harness.lua")
local server = os.getenv("TWF_SERVER_FILE") or "src/ToyWarsServer.server.lua"
local passed, failed = 0, 0

local function check(name, fn)
    local ok, err = pcall(fn)
    if ok then passed = passed + 1; print("PASS "..name)
    else failed = failed + 1; print("FAIL "..name..": "..tostring(err)) end
end

local function eq(actual, expected, label)
    assert(actual == expected, label..": expected "..tostring(expected)..", got "..tostring(actual))
end

local function upvalue(fn, name)
    for i = 1, 40 do
        local key, value = debug.getupvalue(fn, i)
        if not key then break end
        if key == name then return value end
    end
    error("canonical server upvalue missing: "..name)
end

local function fixture(file)
    local h = Harness.new(file)
    local player = h:addPlayer(h:newPlayer())
    local fields = {
        SelectedToy = assert(h:status(player, "SelectedToy")),
        Allies = assert(h:status(player, "Allies")),
        Enemies = assert(h:status(player, "Enemies")),
    }
    return h, player, fields
end

-- The accepted harness models Value assignment but does not synthesize Changed.
-- Count real writes by wrapping the shared instance metatable only for this step.
local function observedStep(h, fields)
    local mt = assert(getmetatable(fields.Allies))
    local original = assert(mt.__newindex)
    local writes = {}
    mt.__newindex = function(object, key, value)
        if key == "Value" then
            for name, field in pairs(fields) do
                if object == field then
                    writes[#writes+1] = {name=name, value=value}
                    break
                end
            end
        end
        return original(object, key, value)
    end
    local ok, err = pcall(function() h.runService.Heartbeat:Fire(0.12) end)
    mt.__newindex = original
    if not ok then error(err) end
    return writes
end

check("idle Heartbeat does not reassign unchanged replicated statuses", function()
    local h, player, fields = fixture(server)
    for tick = 1, 3 do
        local writes = observedStep(h, fields)
        eq(#writes, 0, "idle status writes tick "..tick)
        eq(fields.SelectedToy.Value, "PON", "default selection")
        eq(fields.Allies.Value, 0, "ally count")
        eq(fields.Enemies.Value, 0, "enemy count")
    end
end)

check("one new ally and enemy produce one stable update each", function()
    local h, player, fields = fixture(server)
    local heartbeat = assert(h.runService.Heartbeat.listeners[1]).fn
    local sessions = upvalue(heartbeat, "sessions")
    local simulate = upvalue(heartbeat, "simulate")
    local addEntity = upvalue(simulate, "addEntity")
    local state = assert(sessions[player])
    state.productionTimer = 100
    state.waveBreak = 100
    local ally = assert(addEntity(state, "pon", "ally"))
    local enemy = assert(addEntity(state, "junk", "enemy"))
    local writes = observedStep(h, fields)
    eq(#writes, 2, "first changed-count writes")
    eq(fields.Allies.Value, 1, "one ally")
    eq(fields.Enemies.Value, 1, "one enemy")
    for _, entry in ipairs(writes) do
        eq(entry.value, 1, "never publish transient zero")
        assert(entry.name ~= "SelectedToy", "selection did not change")
    end
    eq(#observedStep(h, fields), 0, "unchanged second step")
    enemy.alive = false
    enemy.model:Destroy()
    writes = observedStep(h, fields)
    eq(#writes, 1, "only enemy count changes after removal")
    eq(writes[1].name, "Enemies", "changed field")
    eq(writes[1].value, 0, "removed enemy")
    eq(fields.Allies.Value, 1, "ally retained")
    assert(ally.alive, "ally remains active")
end)

check("real selection remains authoritative without periodic duplicate writes", function()
    local h, player, fields = fixture(server)
    h.remote.OnServerEvent:Fire(player, "guardon")
    eq(fields.SelectedToy.Value, "GUARDON", "selection callback")
    eq(#observedStep(h, fields), 0, "no redundant selection/count assignments")
end)

local pinned = ".qa/server-before/src/ToyWarsServer.server.lua"
local fh = io.open(pinned, "rb")
if fh then
    fh:close()
    check("pinned old whole server reproduces redundant idle assignments", function()
        local h, player, fields = fixture(pinned)
        local writes = observedStep(h, fields)
        assert(#writes >= 3, "old server must reassign selected/ally/enemy each idle tick")
        eq(fields.Allies.Value, 0, "old ally count")
        eq(fields.Enemies.Value, 0, "old enemy count")
    end)
end
print(string.format("AUTO_STATUS_SNAPSHOT_SUMMARY %d passed / %d failed; canonical whole-server Lua mock", passed, failed))
if failed > 0 then os.exit(1) end
