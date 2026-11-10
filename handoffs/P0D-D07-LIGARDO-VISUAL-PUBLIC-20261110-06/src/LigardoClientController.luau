-- Bind ONLY to a real server-origin boss visual RemoteEvent supplied by the PC integrator.
-- The server MUST map its canonical v40 BOSS_* event into boss="LIGARDO" and S2/S4.
-- Do not create another event picker, spawn a real NPC, or accept any client damage intent.
local RunService = game:GetService("RunService")
local Policy = require(script.Parent.LigardoVisualPolicy)
local Builder = require(script.Parent.LigardoVisualBuilder)
local M = {}
function M.mount(remote, roundId, parent, lowDetail, reducedMotion)
    assert(typeof(remote) == "Instance" and remote:IsA("RemoteEvent"), "server remote")
    assert(typeof(parent) == "Instance", "local visual parent")
    local state = Policy.new(roundId)
    local view, origin
    local clockZero = os.clock()
    local warningStarted = nil
    local conn = {}
    local function cleanup()
        if view then Builder.destroy(view); view = nil end
    end
    conn.message = remote.OnClientEvent:Connect(function(payload)
        if type(payload) ~= "table" then return end
        local act = Policy.snapshot(state, payload, os.clock())
        if act.kind == "SPAWN" then
            -- Read-only visual position. Its actual source/authority must be validated by PC server.
            local p = payload.visualCenter
            if typeof(p) ~= "Vector3" or p.X ~= p.X or p.Y ~= p.Y or p.Z ~= p.Z or
                math.abs(p.X) > 4096 or math.abs(p.Y) > 4096 or math.abs(p.Z) > 4096 then
                Policy.close(state)
                return
            end
            cleanup()
            origin = p
            warningStarted = os.clock()
            view = Builder.build(parent, lowDetail == true)
            Builder.update(view, origin, "TELEGRAPH", 0, reducedMotion == true)
        elseif act.kind == "DESPAWN" then
            cleanup()
        end
    end)
    local accumulator = 0
    conn.frame = RunService.RenderStepped:Connect(function(dt)
        accumulator += dt
        if accumulator < 0.08 then return end  -- <=12.5 updates/s, mobile bounded.
        accumulator = 0
        local now = os.clock()
        if Policy.tick(state, now).kind == "DESPAWN" then cleanup() end
        if view and origin then
            local shownPhase = state.phase
            -- Local glowing charge is capped at 2s. This is NOT authoritative attack timing.
            if shownPhase == "TELEGRAPH" and warningStarted and now - warningStarted >= 2 then
                shownPhase = "IDLE"
            end
            Builder.update(view, origin, shownPhase, now - clockZero, reducedMotion == true)
        end
    end)
    function conn.close()
        Policy.close(state)
        cleanup()
        if conn.message then conn.message:Disconnect(); conn.message = nil end
        if conn.frame then conn.frame:Disconnect(); conn.frame = nil end
    end
    return conn
end
return M
