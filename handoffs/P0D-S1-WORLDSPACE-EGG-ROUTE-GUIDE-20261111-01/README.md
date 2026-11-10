# TRAP RAIDERS / S1 World-space Egg Route Guide (Chat-first source candidate)

- Packet: `P0D-S1-WORLDSPACE-EGG-ROUTE-GUIDE-20261111-01`
- Game/work: `TRAP_RAIDERS` / `p0d-siege-v19`
- Baseline S1 Chat integrator: `35d7d0525388e885aac8281eff2315a59831e0cf`
- Owner: separate FTUE world-space guide lane, **not** the unique `rc/p0d-s1-kids-rc01` writer.
- **Source-ready only**; native Luau parse, 2client, mobile and Roblox Studio **NOT_TESTED**.

`WorldRouteModel.luau` is a client-only pure snapshot-to-route projection. `WorldRouteGuide.client.luau` is a lightweight local `BillboardGui` with one pooled label. During ACTIVE: without an egg it marks the enemy egg; carrying the enemy egg it marks the player's own delivery pad. The marker disappears on results/lobby. It never changes server state, objectives, combat, HP, scores, inventory, rewards, time or paid features.

No AES key, original private game source, remote creation, vendor asset or paid dependency. Exact integration and rollback: `docs/INTEGRATION.md`. Test via `python -m unittest discover -s tests -v` (offline behavioral oracle/static boundary checks; not Luau runtime tests).

The sole Chat integrator in Issue #220 decides whether to include the optional two files in the S1 RC. Do not bypass current V2/V3 contract, independent QA, OWNER approval, or final Studio 2client/mobile evidence. Never push to `main` or `rc/` from this feature lane.