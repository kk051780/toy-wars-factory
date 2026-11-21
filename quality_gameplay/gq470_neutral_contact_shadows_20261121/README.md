# GQ470 FB-015 — Neutral NPC matte contact shadows (A candidate)

Feature `GQ470_FB015_NEUTRAL_CONTACT_SHADOWS_REAL69_20261121` supplies ONE optional **client-only real Luau LocalScript**, reading the existing server-origin `EGGRUMBLE_NeutralSpecies` model attribute. It places at most **6** dark translucent matte cylinders on touch or **10** on PC under currently living nearby neutral models, raycast onto solid dry ground with distance LOD and cleanup on death/despawn/reduced-effects. Scans every 3.8s, local update 0.75–0.95s. No gameplay authority, egg, score, HP, Game, Remote, Store, server script or original REAL69 source edited.

Nonoverlap: #951 changes *SwarmCombat* species meshes (3 Parts); #968 addresses **player** ground footsteps; #985 adds **boss** debris. This script is the **neutral mob dry-ground contact** only. No duplicate adoption with ART16 bundle #970/#983. No claim of improving the actual game until B #220 selects just the one source using fresh official SHA and source-exact nonforce CAS. This branch is **A PREP only**, formal RC remains unchanged.

Source gate: Python negative-mutation safety tests, pinned native Luau original69/candidate70 compile, pinned Rojo exact OFF69 / ON70, exact one-source B handoff and honest 0/32 matched images. This is NOT Studio rendering proof. #910 one-play P0 and #983 primary ART17 beat this optional visual refinement; #218 CLAIM_GRANT and #250 value decision needed before certified B writer adoption.

Acceptance still **NOT_TESTED**: Studio Solo & 2client with 8-species horde; art A/B matched PC/Android screens (0/32); Android 15-minute FPS/heat; initial 3-minute FUN; OWNER. ART/MOBILE/FUN/PRODUCT NO_GO. Rollback: omit one client LocalScript, original 69 sources exact.

Soft claim: https://github.com/kk051780/toy-wars-factory/issues/218#issuecomment-7059240722
