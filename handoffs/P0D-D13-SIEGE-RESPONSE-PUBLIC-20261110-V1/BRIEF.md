# P0-D D13 Siege Response — single-slice Codex brief
Game: TRAP_RAIDERS / work_id: p0d-siege-v19 / Packet: P0D-D13-SIEGE-RESPONSE-20261110-A

Objective: defend existing egg castle against gate diversion and flank infiltration with *reassignment of existing guards*, never spawn a new NPC or strengthen health/damage. Smallest target: existing S1 two routes (FRONT and FLANK).

Inputs must originate from authoritative RoundCoordinator/physics/LoS on SERVER. Adapter must reject client-supplied claimed gate hits, egg, LoS, team, positions, clock or round ID. Call standalone `SiegeResponseDecisionCore.step` only from the trusted adapter. `intents` are planning commands, not completed motion. Integrator must pathfind on foot, decline invalid paths, preserve original NPC ownership and log outcomes. Never teleport a guard or persist tracking through walls.

No modification of existing v37 egg / bell / 3-sec beacon / 6-sec teammate marker. Never duplicate v43-A neutral ownership. No new boss, vehicle, cosmetic progression, map or paid mechanism. Do not unconditionally integrate before v37 stored SHA final QA and v39-H1. S1 A/B: original guards vs guarded response, at same NPC count.
