--!strict
-- EGGRUMBLE V3 neutral death-credit guard: pure policy + server-owned identity.
-- No new horde, KO counter, damage or score authority.
local Fence = {}

-- Pure negative-first decision for native Luau / offline tests.
function Fence.decide(phase: any, winner: any, attackerAlive: any, neutralInCurrentHorde: any, liveSession: any): boolean
    return phase == "ACTIVE"
        and winner == nil
        and attackerAlive == true
        and neutralInCurrentHorde == true
        and liveSession == true
end

-- Invoke only INSIDE the original SwarmCombat h.Died callback; never from clients.
-- The original callback still owns attribution, ImpactFeedback and credit().
function Fence.mayCredit(session: any, id: any, model: any, hordeFolder: any): boolean
    if type(id) ~= "string" or id == "" then return false end
    if not session or not session.rules or not session.rules.castles then return false end
    local castle = session.rules.castles[id]
    if not castle then return false end
    if not model or not hordeFolder or not session.world then return false end
    if hordeFolder.Parent ~= session.world or session.world.Parent == nil then return false end
    if not session.swarm then return false end
    -- A Model from a previous match / separate TEAM-BR arena cannot earn points here.
    if not model:IsDescendantOf(hordeFolder) then return false end
    if model:GetAttribute("EGGRUMBLE_Neutral") ~= true then return false end
    return Fence.decide(session.rules.phase, session.rules.winner, castle.alive,
        true, true)
end

return Fence
