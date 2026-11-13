# P0D HORDE-HEIST-GATE — isolated S2+ gameplay source

**State:** source candidate ONLY. Not selected for S1, not wired into #220 official RC, not Studio tested. Prior design: #219 comment 6847802438. This candidate does not claim a game-level performance improvement.

## One playable hypothesis (once integrated)
A real neutral elite KO on the existing server triggers ONE central shared shortcut:
**2 seconds warning → 10 seconds open → close only when unoccupied.**
Both red and blue can use it; the already-free permanent bypass must remain reachable.
The KO opens a tactical choice in the egg-heist instead of awarding new scores or XP.

## Integration contract (the owner #220 must audit before use)
1. Read #218, #219, #250, #220 current rules. Do not copy this module into S1 simply because it compiles.
2. **Do not create another Game.server, round authority, RemoteEvent, event chooser, KO counter, score, XP, reward, DataStore or client-controlled gate state.**
3. The existing server-only authoritative MusouHorde elite-confirmed death receipt may call `GateRules:onEliteKO(roundId, true, serverNow)` **once**. Client input cannot call it. Confirm the genuine #288 API at a frozen source commit first; no speculative callback name has been wired.
4. The existing Game server owns exactly one `GateRules.new(roundId)` per match and calls `step(roundId, serverNow, occupantCount)` on its existing update cadence. `occupantCount` must be computed by a server spatial query that counts genuine living characters occupying the door's physical volume, not a client report.
5. The existing World/MapBuilder owner must choose an actual collision-free central CFrame and ensure an always-open, accessible alternate path. `GateVisual.create(parent, cframe, auditedCorridorWidth)` creates just a single physical door with legible signage; it does **not** build or validate the bypass.
6. First set `render` once after physical creation and after every step/KO. During OPEN or WAIT_CLEAR `CanCollide=false`. Close only when the server sees zero occupants; **map teardown must follow safe respawn**. Otherwise keep the door passable. Avoid adversarial indefinite occupancy by level design, not by closing onto a player.
7. Red/blue roles share the exact same gate without team keys. Solo/2client, carrying egg, on death, reconnect, round teardown, reset and 600-second timeout must each be tested. Check original castle sidewalls and egg/drop/save rules; a geometric crossing of a solid wall blocks adoption.
8. H0 = no new GateRules/GateVisual (existing source unchanged). H1 = the two modules integrated after source contract inspection, with rollback to immutable H0 source. Actual engine 2client & landscape Android and qualitative owner fun check **REQUIRED**.

## Verified owner API and required physical gameplay gate
The actual #288 V7 `Horde:hit` returns aggregate touched/defeated, **not elite-only KO**. FIRST90 B42 contains **two** authenticated `horde:hit` paths, including evolved ASSAULT. Source-only `EliteKOBridge.luau` checks the elite's original live HP/death receipt by identity and same round, and must be attached to EVERY valid callsite by the original server owner. See [source-locked V2 contract](docs/OWNER_SOURCE_BINDING_AND_FIELD_GATE_V2.md).

An isolated physical door in today's open grass arena is NOT a tactical shortcut. **Do not adopt** until the World/MapBuilder owner defines a collision-safe chokepoint with a completely free alternate path, verifies both teams and all egg paths, and selects the proper corridor width (6–24 studs). Source-only/native CI does not establish real Studio physics.


## V3 physical SEA shortcut design candidate (NOT mounted into Game)

Standalone `src/GateRouteOverlay.luau` now creates two mirror-symmetric **physical** gates (x = -36 / +36, z = -22) and their side barricades in the existing H1 sea corridor, only if actual `H1_FUN_WORLD/SEA_LOW_CAUSEWAY/SEA_ENTRY_RED/SEA_ENTRY_BLUE` are present and source-aligned. It **fails closed without creating parts** if the scene is absent, changed, or already patched. Original Game, MapBuilder, First90, Horde, damage, Remote, XP, egg score, and Studio PlayerScripts remain untouched.

Both doors read the **same** server-owned GateRules state; normal grass/sky detours stay open. The intended choice is a fast (conditional) sea/egg approach versus a longer free bypass. An independent, conservative grid model (1.7-stud avatar clearance) produced symmetric **186 open versus 210 closed** grid steps from own spawn to the enemy egg, and 144 open versus >=174 closed for the sea crossing. These are **2D model distances, not actual Roblox path/time/physics results**. Geometry checks compare original castle walls/pillars and genuine A/B-era H1 sea/sky candidate source locks; no collider insertion into the real game is proven.

This is an **S2+ source experiment** only, not approved product selection or #220 RC integration. For actual adoption the H1 world/source owner must review the overlay, and the sole Game authority must call the two original authenticated B42 PvE hit sites and count occupied door space. Full 2-client Studio + Android + egg carrying + rematch + FUN check remain **NOT_TESTED**. Full [V3 physical routing contract](docs/SEA_ROUTE_GAMEPLAY_V3.md).

## Acceptance status
- Original isolated Luau source: delivered to its own branch, not a real integrated game.
- Independent Python state-oracle: `python -m unittest discover -s tests -v`.
- Native Luau compile + pure state-machine test and real frozen V7/B42 source-contract CI: see `.github/workflows/p0d-s2-shared-elite-gate-20261113.yml` and its exact HEAD workflow result. Source-only gates, **not** real Game integration.
- Rojo actual Place, physical collision, original Game elite KO hook and Roblox Studio/mobile: **NOT_TESTED** until externally proven.
- Business metrics (retention, replay, purchases): **UNKNOWN**.
- Source package may be moved to an isolated S2 experiment by the original server/map owners only after #250 product decision; #220 remains the sole official RC writer.

All seven original jobs remain FREE in the overall design; no paid random loot or power purchases. Existing S1 FIRST90 B42 private trial remains the immediate priority.
