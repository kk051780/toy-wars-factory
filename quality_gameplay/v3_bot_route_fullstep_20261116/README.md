# GQ V3 full-step wall clearance — independent source-locked repair

**Status:** SOURCE_WIP / soft claim requested at #218 comment 6912964714 / NOT CLAIM_GRANTED / official RC adopted 0.

**Author source:** existing #484 HEAD `6b52eaf1f2725496277998fe0c5532b7a8fcaab5`, BotPathRouter blob `d9841bb874659129cae6c930bce302ff6936ac4a`. Original #482 and current #484 retain all real Game, role, AI and scene authority.

## Exact defect

Current original `Router.navigate` can request `PATH_TRAVEL_SPEED * dt = 30 * .3 = 9 studs` in one step but the `routeClear` ray only checks `math.min(8,diff.Magnitude)`. A wall at 8.5 studs therefore lies inside the attempted move but beyond the server's validation ray, allowing a potentially colliding anchored AI `PivotTo` to pass through.

This is a **deterministic source-model geometric gap**, NOT a claim of observed Studio or Android behavior.

## Actual implementation

`source_patch.py` generates a private author-source-exact 1-line Router:
- OLD: `workspace:Raycast(at,diff.Unit*math.min(8,diff.Magnitude),p)`
- NEW: `workspace:Raycast(at,diff.Unit*diff.Magnitude,p)`

Everything else stays byte-for-byte unchanged. The existing `RaycastParams.RespectCanCollide=true`, waypoint path, max 2 asynchronous computes, TEAM+BR namespace, movement speed and all other authors remain untouched.

`make_native_ray_harness.py` extracts the **real authored** `routeClear` function and executes both versions in actual native Luau with a deterministic collidable wall at 8.5 studs, plus near-wall, open-field, short-step and two-mode parity checks. This is not Studio physics or real-device performance measurement.

## Eight-domain no-overlap

| Domain | Preserved |
| --- | --- |
| Character | Seven jobs, hero HP/roles/skills unchanged |
| Field | All routes/water/ground parts unchanged; only ray coverage of requested AI step |
| Battle | HIT, damage and KO unchanged |
| Castle | Physical castles, siege, eggs and team wins unchanged |
| Neutral | Swarm, boss and KO pacing unchanged |
| Item | HEAL/DASH/SHIELD and field placement unchanged |
| Lobby | TEAM/BATTLE_ROYALE queues, selection, replay unchanged |
| Balance | 30stud/s, up to .3s step, PathFinding concurrency 2 unchanged |

## Safety and integration

- Source original #484 Git blob must match and replacement must be exactly one hunk.
- Flag OFF / rollback = use unmodified #484 Router. No new controller or Remote.
- Flag ON only after #218 CLAIM_GRANTED, #484 author ACK, exact latest source rebase, native+Rojo SourceExact, no RED.
- Only #220 authenticated sole writer may take source-selective change via non-force expected-SHA CAS into official `rc/p0d-s1-kids-rc01`, then record same-HEAD CI, canonical ZIP/Place bytes and feature registry.
- Studio 2-client, 15min Android, art/FUN comparison and OWNER accepted remain NO_GO until observed.
- No main, author branches, canonical RC, publish, charges or Windows operations changed by this draft.

**Not a continuation of closed duplicate #534.** Current #484 already fixed CreatePath exception recovery; this slice concerns **separate raycast length** only.
