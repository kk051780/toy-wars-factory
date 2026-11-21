# GQ470 FB-015 — Neutral NPC matte contact shadows (A candidate)

Feature `GQ470_FB015_NEUTRAL_CONTACT_SHADOWS_REAL69_20261121` supplies ONE optional **client-only real Luau LocalScript**, reading the existing server-origin `EGGRUMBLE_NeutralSpecies` model attribute. It places at most **6** dark translucent matte cylinders on touch or **10** on PC under currently living nearby neutral models, raycast onto solid dry ground with distance LOD and cleanup on death/despawn/reduced-effects. Scans every 3.8s, local update 0.75–0.95s. No gameplay authority, egg, score, HP, Game, Remote, Store, server script or original REAL69 source edited.

Nonoverlap: #951 changes *SwarmCombat* species meshes (3 Parts); #968 addresses **player** ground footsteps; #985 adds **boss** debris. This script is the **neutral mob dry-ground contact** only. No duplicate adoption with ART16 bundle #970/#983. No claim of improving the actual game until B #220 selects just the one source using fresh official SHA and source-exact nonforce CAS. This branch is **A PREP only**, formal RC remains unchanged.

Source gate: Python negative-mutation safety tests, pinned native Luau original69/candidate70 compile, pinned Rojo exact OFF69 / ON70, exact one-source B handoff and honest 0/32 matched images. This is NOT Studio rendering proof. #910 one-play P0 and #983 primary ART17 beat this optional visual refinement; #218 CLAIM_GRANT and #250 value decision needed before certified B writer adoption.

Acceptance still **NOT_TESTED**: Studio Solo & 2client with 8-species horde; art A/B matched PC/Android screens (0/32); Android 15-minute FPS/heat; initial 3-minute FUN; OWNER. ART/MOBILE/FUN/PRODUCT NO_GO. Rollback: omit one client LocalScript, original 69 sources exact.

Soft claim: https://github.com/kk051780/toy-wars-factory/issues/218#issuecomment-7059240722


## #420 real ART / Android acceptance checklist (NOT COMPLETED)

**Prerequisite:** #910 first validates visible avatar and role → egg theft → home deposit → score → castle verdict → optional replay on actual Studio. This A-private art sample does not fix spawn or authorize formal RC adoption.

1. Capture the standard **8 scenes × PC and low-end Android × BEFORE/AFTER = 32** matched actual camera screenshots and human 1–5 art judgments. In particular inspect the real neutral_swarm scene with eight neutral species materials, battle VFX and readability. Confirm other seven scenes regress nothing.
2. Compare solid level dry floor, 30° dry slope, steep cliff (normal.Y < 0.72), water/non-collidable surface, missing ground. The 0.055-stud thin cylinder should lie in the *actual raycast normal plane*, never float, intersect or reveal an NPC through a wall.
3. Stress the existing 110-neutral swarm, then alternate disjoint closest six/ten living mobs. Instrument **peak** local Part count during churn, not just after cleanup: Touch ≤ 6 and desktop ≤ 10; no leftover parts after KO, despawn, feature OFF, ReducedEffects, avatar respawn, round result or map cleanup.
4. On actual 2–4GB RAM Android, test 15 minutes: median FPS ≥ 30, p10 ≥ 25, thermal FPS degradation ≤ 20%, crashes/OOM = 0; check the 3.8s Workspace:GetDescendants rescan for spikes. Source caps and CI are **not** measured performance.
5. Verify the existing server-authored EGGRUMBLE_NeutralSpecies attribute for eight original NPC species, correct live-Humanoid filtering, no added Remote/HP/AI/score/egg/Game/Store authority, no persistent UI/Neon or collision/query/touch. Compare OFF69 exact and B-selected candidate on the **same official RC HEAD**, if B adoption ever occurs.

**Status**: All 32 actual images missing (0/32). Studio Solo/2client, Android15min and kid first3min FUN NOT_TESTED; OWNER_ACCEPTED=0. This checklist is a future acceptance method, not an ART_GO assertion.
