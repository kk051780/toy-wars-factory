# EGGRUMBLE V3 / independent server-side TEAM–BR combat VFX fairness

Unlike **#503 client FX distance LOD** or closed duplicate #498, this candidate fixes a **server-side cross-mode starvation** in the original 72-live-Part skill emitter. Its parent #482 SkillFX shared one global `active` count across both TEAM and BR, and returned before creating **any** flash/ring/skill silhouette at the >66 active threshold. Concurrent mode A explosions can suppress mode B's real hit cues even though mode B gameplay still deals damage.

## Minimal original-source-selective actual Luau implementation
- NEW `EGGRUMBLE_FXModeFairQuota.luau`: bounded pure Luau ticket allocator (72 global, 12 reserved for opposite mode, 36/36 fresh allocations after both modes emit). Cancels unknown/invalid arena, double release safely, supports per-instance state; no Game, HUD, damage, remote, DataStore, score, economy, AI, castle or lobby.
- NEW `EGGRUMBLE_SkillFX_ModeFair_Overlay.luau`: a **selective copy of original #482 `EGGRUMBLE_SkillFX.luau`**, with only one require/new, lease on Part creation, lease release at the same existing `task.delay` cleanup, and a per-mode preflight instead of the single global preflight. All seven original role geometries, colors, lifetime, actual damage and boss/item logic preserved.
- NEW alternate `EGGRUMBLE_V3_FX_FAIR_22_STUDIO.project.json` maps the original author 21 sources (20 byte-exact unchanged, one selective FX overlay), plus one new helper = **22 sources**. Same server Game, TEAM/BR, 7 roles, field/neutral/castles/eggs/items/lobby. Not a second Game.
- Native Luau tests cover solo cap60, other mode guaranteed 12 headroom, two-mode 36/36 eventual equilibrium, global cap72, timeouts/double release. Actual original SkillFX compile and 22-source Rojo Place source exact are separate CI stages.

## Non-overlap and ownership
This is private **SOURCE_PREP / DRAFT**, SOFT_CLAIM NOT GRANTED. Do not write to #482 author path; request author accept the 4 anchor changes only, then #484 composer builds the newest 26-source (or newer) source-exact composite without overwriting core. #503 owns **client cosmetic distance LOD**, not this server-side cross-match lease. #494/#501 own neutral spawn and fairness, #499 round timer, #500 castle defense, #489 item, #485 ART, #487 SCORE, #220 official authenticated RC write. **Rollback:** restore original #482 SkillFX source blob and remove `FXModeFairQuota` map+file. Entire overlay is source-exact, not certified gameplay.

## Actual gameplay quality acceptance
In unpublished Studio, start TEAM + BR simultaneous 1+15 AI/2+14 AI and spam A/B/C from all 7 jobs. Inspect every mode's FX counts vs 72 global, 60 one-mode, 36-mode steady state, hit marker & critical skill cues, group neutral KO/actual damage unaffected. Repeat start/stop/replays and disposal, ensure no leaks. On 2GB low-end Android 15min verify FPS (median>=30/p10>=25), quality and heat against #420, and independent #470 fun & owner. No mobile/runtime result from native/Place proof; no Roblox publish or monetization.


## Integrated PRIVATE27 source-exact proof (NOT official RC)
The same dedicated workflow now reuses **the original #485 artist composer** and **#484 current26 composer** at fixed SHAs, rather than implementing either again. Immutable inputs:
- Original #482 fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9
- #484 composer+AI 2aeb4fd856657c9298a2763d9204d0c9d9b031cb
- #485 visual ART e86702c906bdf9c71adcdf769ae48a206b26607b
- #487 score 438a406ccfda5563053d783d7561797ccd364361

The new `compose_mode_fair_on_current26.py` validates all 26 original Game/ART/AI/SCORE source hashes against #484's original receipt, then retains **25 byte-exact** and replaces only the originally single `EGGRUMBLE_SkillFX` map with the audited overlay, adds one helper = **27 scripts** (24 server + 3 client). The resulting Rojo Place is only a source candidate, generated without main/official RC mutation. Native/Rojo exact tests must PASS at the same candidate HEAD before any adoption claim. Latest author heads must be re-read before authenticated #220 intake; if they drift, rebuild and revalidate.

A single workflow performs both 22-original-preview and 27-current-composite QA to avoid duplicate CI ownership. Earlier independent current27 workflow was removed before adoption; never use its unverified hash as evidence. **RC adoption, Studio/Android 15min, ART/FUN, and OWNER validation remain NO_GO/NOT_TESTED.**
