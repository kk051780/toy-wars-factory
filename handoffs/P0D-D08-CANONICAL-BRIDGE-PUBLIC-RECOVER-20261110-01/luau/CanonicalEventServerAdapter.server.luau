--!strict
-- Disabled-by-default PC integration EXAMPLE. Never add as a second server event chooser.
-- This file does nothing until the OWNER PC integrator wires true RoundCoordinator,
-- trusted single RNG, the reviewed v40 ChaosEventCore and exact event consumers.
local ENABLE_AFTER_PC_SINGLE_CHOICE_AUDIT = false
if not ENABLE_AFTER_PC_SINGLE_CHOICE_AUDIT then return end

-- Required PC integration mapping (do not guess / do not enable before review):
-- local v40 = require(ServerScriptService:WaitForChild("ChaosEventCore"))
-- local bridge = require(ServerScriptService:WaitForChild("CanonicalEventBridge"))
-- local instance = bridge.new(v40, {
--   enabled = true,
--   readRound = function() return RoundCoordinator.getAuthoritativeRoundSnapshot() end,
--   serverRoll = function(matchId, epoch) return ServerOwnedRng:NextInteger(0, 99) end,
--   onWarning = function(e) return GenuineVisualEventEmitter.warn(e) end,
--   onBossActivate = function(e) return ApprovedD07ServerBoss.activate(e) end,
--   onWeatherActivate = function(e) return ApprovedSingleWeatherRuntime.activate(e) end,
--   onCleanup = function(e) return ApprovedSingleEventCleanup.cleanup(e) end,
--   approvedRaigaldAsLigardo = false,
-- })
-- Genuine server tick invokes instance:tick(); genuine match shutdown instance:stop().
-- Event consumers must recheck current roundId+epoch and NEVER act on RemoteEvent data.
