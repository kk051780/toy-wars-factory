# P0-D D14 CART motion (original reference)

A cart **server-owned motion policy for fixed, authored rails**, rather than a true player-driven physics vehicle. Safe, enjoyable first milestone: two crew members use prior D14 `VehicleSeatCore` ownership; ONLY the canonical driver may request NEXT; server controls route positions, team/round, rate, time and model movement. It does not change egg ownership, HP, win conditions, paid items, speed buffs, or PvP hitboxes.

* **NO CART 3D/MODEL/CLIENT VISUALS IN THIS PACKET.** The earlier other-chat D14 `CART/RAFT VISUAL` reference owns that work. This packet returns pure server rail position/heading snapshots for a future carefully reviewed visual adapter. Real player movement/seat/raft/physics remains PC integration work.
* Path has 2–24 server-authored nodes, 6–80 studs apart, max speed 16stud/s, max 2000 coordinate. A fixed leg is completed before awaiting a new canonical driver command; no teleport, one unauthorized command cannot start movement. dt >100ms stops rather than jumping forward, no catchup.
* Existing D14 seat ledger remains the ONLY authoritative seat system. Server callbacks must get Round/Team/Driver/Alive/Carrier/Snare from canonical state; never from RemoteEvent payload. On driver leaving, NPC hijack, death, egg carrying, snare, round end: halt; on match end destroy cosmetic cart.

## Scope & unknowns

**REAL ROBLOX STUDIO/LUAU PARSE = NOT_TESTED.** Python reference oracle tests simulate policy, not a Luau VM or multiplayer. No true wagon physics/steering/pathfinding/boat buoyancy. World terrain collision, visual compatibility with separate D14 client cart, mobile UX, two players physically riding, server network replication and positional coordinate agreement must be checked by OWNER Codex in isolated Studio. Never integrate into true PC's newer saved place without snapshot protection.
