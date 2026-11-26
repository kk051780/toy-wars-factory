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


## 2026-11-23: fixed original Router60ce payload registration

This append registers an existing repaired Router and its original review. It introduces no new gameplay implementation, producer, patch, fixture or test. The old README and its historical SOURCE_WIP/claim wording above remain byte-exact; the actual grant below authorizes only this passive evidence registration.

### Original bytes and distinct preimages

- `current69/EGGRUMBLE_BotPathRouter.luau.txt`: **12,555 bytes**, SHA-256 `60ce79cacfc44cb73f2d1f0e84b24ce23e01a5020712b26718c8ab3672c77b12`.
- `current69/ROUTER_REVIEW.json`: **74,409 bytes**, SHA-256 `d0775bc4c4bfc0edd8be11b8d3fa4c5b21bb1b9df96409d1e879212045dc5c45`.
- Original scope: [#218 comment7077307346](https://github.com/kk051780/toy-wars-factory/issues/218#issuecomment-7077307346). Original author/follow-on lineage: [PR536 comment7077568194](https://github.com/kk051780/toy-wars-factory/pull/536#issuecomment-7077568194).
- Reused original archive: `EGGRUMBLE_QualityGate_20261122_bf89c1781045.zip`, **60,374,944 bytes**, SHA-256 `626d5275dd6197dc3f7e423f872e89e5a1d104f818a63bcede9fd6ac391642a2`. The selected source/review members match their complete public pins. This archive is not relabeled as a different older published ZIP.
- Historical PR parent is `cdf4fe5f231c998532963c5c16d9525d20a69e7e`; historical PR base is `d2f3ed1a47558fdaf07be0181c83c698bdb2ce34`. Its original one-line overlay is not the copied 60ce full source.

The final historical **bef → 60ce +204 B** patch repairs delayed-start waypoint handling. It is not the full formal-R patch. The formal Router is **7,614 bytes**, SHA-256 `92d44fd4635878fdfbbf1d8f3db691537ae348472dd5770f82421f78b00d5f52`; formal92d → 60ce is **+4,941 B** and includes the existing body-sweep, overlap, support and corner-preservation lineage. No partial patch is added or used as a substitute for the full source.

The original review uses its historical 15-source/Host context and controlled Native fixtures. Its source pins, absolute evidence paths, raw failures and approval/adoption flags are copied verbatim. This JSON alone is not a portable executable bundle or a new-HEAD run. Additional source-bound c38/60ce death/respawn and terminal/replay evidence is recorded in [the existing PR484 QA comment7086580046](https://github.com/kk051780/toy-wars-factory/pull/484#issuecomment-7086580046). These records preserve their exact executed bodies and do not claim all69, Studio physics or current-HEAD CI.

### Actual authority and acceptance boundary

Request: [PR536 comment7087483099](https://github.com/kk051780/toy-wars-factory/pull/536#issuecomment-7087483099). Actual grant: [#218 comment7087809708](https://github.com/kk051780/toy-wars-factory/issues/218#issuecomment-7087809708), claim `P0D-GQ536-ROUTER-PAYLOAD-20261123-7B6B25AE`, registry commit `bbd45ae5655ec4f24cde4160530b020fe59f68ae`. Owner `CODEX_ROOT_7B6B25AEAA29`; registered independent source-evidence reviewer `/root/gameplay_audit`.

Grant base R is `dcb501673d7959e4904cf360ef0119917e6aa2e0`; original evidence-comparison base `fb5d9b693c48d4ffcce05c3f89d490593e0cecfd` and historical PR base remain unchanged. [Official push verification](https://github.com/kk051780/toy-wars-factory/pull/1020#issuecomment-7087668742) proves all game/profile/Place bytes identical across that input-retention-only movement. Registered common base-recheck SHA-256 is `40bb6cbc719a5c18c0bf48784bf7f7711367083591bc1ce5fa70a0930e8cbc83`; Router peer recheck SHA-256 is `49a4a71fc30be944eaa8efe2421094fd2b660adc3aa5e70bf5c4ba21b6413dc0`.

The cumulative PR scope is eight paths: this README and the two passive copies are mutable; the old workflow, two harness generators, source patcher and source test retain their five original Git blobs. `.luau.txt` is passive evidence and is not selected as executable Source by the unchanged workflow. The old hosted CI still tests its historical one-line/private26 path; its green result cannot become 60ce/current69 runtime proof.

**PREP_READY=false; registered_source_approval=false; RC_adoption=false.** No label06e Bot source is included, and the existing 0A2 Bot successor is unchanged. Canonical producer/profile/verifier/native/test paths, the shared workflow, BotActors and other gameplay bodies are outside this grant. Later canonical adoption requires its own exact grant, shared-resource handoff, same-HEAD gates, registered separate-context review and official RC push/artifact verification. Studio, multiplayer, Android and ART/FUN remain unverified.

Current repository policy governs subsequent work. The old ACK language above is retained as historical text and is not a newly imposed prior-author approval requirement.

### Actual source-write reservation

Source lease: manual CONTROLLER epoch **652**, operation `0d0e5aba-d689-43fa-a906-bf9f74504bfa`, acquire commit `28d3f361e9639a34e4f196e12ec52eb44df80525`, work branch `quality/gq-v3-bot-route-fullstep-20261116`, acquired `2026-11-23T01:09:40Z`, expiry `2026-11-23T01:39:40.000Z`. The three-file commit uses the exact previous source HEAD `cdf4fe5f231c998532963c5c16d9525d20a69e7e` with non-force expected-SHA CAS. Normal release and registered actual-HEAD review are recorded on the existing PR after the write; this paragraph does not assert either future event.
