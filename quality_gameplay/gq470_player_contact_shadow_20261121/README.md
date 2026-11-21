# EGGRUMBLE GQ470 FB-015 — Local grounded avatar contact shadow

## Implemented A-only real game source
One optional `StarterPlayerScripts/EGGRUMBLE_PlayerContactShadow` **LocalScript** (`EGGRUMBLE_PlayerContactShadow.client.luau`) draws a thin dark matte translucent contact disc **only under the player's own living, visible, solid-grounded avatar**. The normal-aligned disc sits on the physically raycast dry floor (including safe slopes), not the camera plane. Neither character nor shadow is made visible if no avatar was spawned. This is not a fix for the P0 player-absent bug.

**Nonoverlap:** #968 creates brief moving footsteps; #993 gives an airborne landing marker; #997 applies contact shadows to neutral NPCs; #975 outlines nearby allies. This feature only handles self-player *grounded* body/terrain separation. No existing selected source or source authority is modified; no new score/HP/egg/AI/Host/Game/Combat/Remote/HUD, no world map remodeling. #218 soft scope notice is **not** CLAIM_GRANTED.

### Runtime budgets and safety
- Exactly **one local noncolliding Part** maximum. SmoothPlastic Cylinder, dark navy grey, ~76% transparent; no Neon, lighting, particles, on-screen GUI, shadow casting, or replicated state.
- 1 dry-ground ray every **0.16s on touch / 0.10s on desktop** while eligible; camera distance ≤55 / ≤75 studs. No frame loop, Workspace descendant enumeration, texture asset, download, or server call.
- Suppress on death, jump, freefall, swim, climb, sit, invisible/stealth attributes, locally hidden head (first-person), spectator camera, noncollidable ground, water, steep faces, or missing ground; immediate cleanup on feature-off / ReducedEffects / CharacterRemoving / script removal.
- OFF rollback: omit just `StarterPlayer/StarterPlayerScripts/EGGRUMBLE_PlayerContactShadow` from private selection; all original REAL69 are unchanged.

### A candidate and formal admission
**BASE_RC**: `e80973c354f14a0d0088577f3cc1a875454f0f8f`
**FEATURE_IDS**: `GQ470_FB015_PLAYER_CONTACT_SHADOW_REAL69_20261121`
**SOURCE_LOCK**: original 69 scripts must remain route/class/source-hash identical; the private candidate adds exactly one LocalScript (REAL70 **source count**, not completion %).
**P0D_PREP_READY_V1**: source-only *candidate* until same-HEAD native/Rojo/actions and B packet are verified.
**ROLLBACK**: remove/unselect one new LocalScript; no persistent data.
**OWNER_FAST_ADMISSION_V2**: `DEFER` until #910 core playable/visible-avatar repair and #983's primary ART17 candidate; independent #250 value acceptance and #218 claim review are not bypassed.

The `compose_official70.py` and dedicated workflow rehydrate the original pinned formal PRIVATE companion from the official same-head artifact; assert all 69 original Luau/class/routes/hashes; build OFF69 byte-exact and ON70 true Rojo Place; compile both with pinned Luau; export a tamper-checked single-source B220 handoff. Such evidence is **SOURCE_QA** only, not a genuine Studio pass. Only #220 authenticated B may apply a selected source to the canonical RC with fresh SHA, nonforce CAS, same-head official CI and rollback. Never merge this entire PREP PR into the official RC or main.

### ART #420 / Product #470 gates — still required
PC old/new and Android low old/new for eight standard scenes = **0/32 observed** so far. Grounded/slope/water/first-person/stealth/spectator/respawn functional behavior requires actual Solo and 2-client Studio test. Low-end Android **15 minutes** measured FPS/heat/touch is not tested. First 3-minute child FUN and OWNER acceptance are not tested. Therefore ART_NO_GO, MOBILE_NO_GO, FUN_NO_GO, PRODUCT_NO_GO, OWNER_ACCEPTED=0. #910 full role→egg→home score→castle victory→optional replay is a higher admission priority.

**Value decision**: ADOPT only if actual matched screenshots show improved avatar-ground readability without terrain clipping or combining badly with #968/#993/#997; otherwise REWORK or REJECT rather than increase visual part count.
