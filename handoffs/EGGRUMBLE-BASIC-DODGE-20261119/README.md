# GQ828 successor: genuine free normal attack + grounded dodge (Real59 → Real60 candidate)

OWNER: Issue #828. No author ACK wait. Parent **official** private EGGRUMBLE V3 Real59 RC HEAD `38d11f0bf311491ba76fe03f818948e5d4b06889` (PR #829 already merged). Exact official private parent Place artifact run `44401178585` (SUCCESS), artifact ID `14473365566`.

**Status:** Actual candidate source-selected, not promoted to canonical RC. This candidate preserves 57/59 original selected sources unchanged, modifies ONLY the existing single original ServerScriptService `EGGRUMBLE_SevenRoleCombat` ModuleScript and original StarterPlayerScripts `EGGRUMBLE_HudIntelRuntime` LocalScript, and adds exactly ONE pure server `EGGRUMBLE_BasicMobilityPolicy` ModuleScript. Total=60. It does not create any second Combat/Host/Swarm/HP/KO/Remote/Score/Store instance.

## What actually changed
- **Normal attack (all seven jobs):** one owner-created `EGGRUMBLE_BASIC_ATTACK` server Tool in the real existing SevenRoleCombat. Damage, LOS, team authorization, original 13 pre-hit invulnerability filters, neutral Swarm KO and existing impact feedback are reused through `neutralAndBotHit` (no direct new `:TakeDamage` calls). Pure role specs: 8–13 base damage, short range, 0.40–0.56 second cooldown. No status ailments or damage multipliers invented. Low stat values are **balancing proposals** until real match tests.
- **Grounded dodge (all seven jobs):** one owner-created `EGGRUMBLE_DODGE_STEP` Tool. Server-rejects egg carriers, seats, water/air, downed/eliminated, old mode, wrong role, stale avatar/tool and abuse under role-specific 3.0–4.1s cooldown. Only reuses original `safeMove` obstacle/raycast/landing-ground checks and never writes HP/damage or confers invulnerability. Max forward step 7–10 studs. No paid power.
- **Actual HUD:** main ATTACK button now calls `EGGRUMBLE_BASIC_ATTACK` (falls back to truthful `技A` if not provisioned), true DODGE button calls `EGGRUMBLE_DODGE_STEP`; independent A/B/C selected skill-use moves to existing `CONTEXT` reserved position so it cannot overlap DODGE. The native Roblox movement/jump remain unchanged, and the genuine server MUSOU/INVUL buttons, Fog map, HP/status and map art remain unchanged.

## Native / Source / Rojo acceptance
CI `.github/workflows/p0d-gq828-basic-dodge-real60.yml` sources the *physical exact same-official-head Real59 private Place* and its receipt, then runs `compose_real60.py` with source-exact-match anchors, no patching an obsolete original Combat, checks one Combat and same damage-site count, compiles actual 60 and actual 59 source files with pinned Luau, executes seven-job policy positive and three malicious mutants, builds candidate Real60 + OFF59 with pinned Rojo 7.7.1 and source/class compares both places. Fails closed if official HEAD moves.

Native proof SUCCESS: [run 44403176104](https://github.com/kk051780/toy-wars-factory/actions/runs/44403176104), genuine Real60 Place **639,726 bytes**, Source/Class hash `222b5797f5742b8d03160f1d1dc425c954a8ec98e667084a39b222d1b5c2a86d`. Original OFF59 Source/Class SHA `bde044295bc286df9f42a98dd351ac09aac1389b063136cb08fe2fbcde7ca327`. Candidate artifact ID `14473632087`; compressed archive size **383,787 bytes**. Do not compare this ZIP to the original 59 with mismatched included files. Current legitimate formal RC has 59 selected sources; 60 is candidate only.

## Explicit acceptance not yet demonstrated
Roblox Studio actual 2-client input, mobile touch (including left-hand), keyboard/controller, 15-minute low-end Android FPS, visual old-vs-new battle art, exact server role Tool lifecycle across deaths and new rounds, anti-cheat under high latency, actual PvP balance and fun are all **NOT_TESTED**. Static Native tests do not establish real in-game usability or artistic acceptance. A real Android start->castle->attack/dodge->pickup->Musou/Invul->death->respawn->leave round script should be tested. Basic VFX uses the original `ImpactFeedback` path; no newly invented full-screen particles.

## Sole-writer RC handoff
Only #220 authenticated B writer may adopt this new source profile into one `rc/p0d-s1-kids-rc01` through fresh non-force expected-SHA CAS; on resulting **new same official HEAD** rerun its canonical 60 Native/Rojo/OFF59 gate and record ZIP/Place/hash. If another newer profile such as Real61 (trade) or Real56 (counter) is adopted first, reconcile its source lineage and composition rather than replacing its new features with old Real59. No main merge, Roblox publish, Robux or new Work/Codex use. Source rollback is OFF59 exactly. No individual author approval required to continue. Candidacy != user acceptance.

## Source ownership and merge exclusion
Never overwrite any newer #841 counter, #842/#843 trade-composite, #825 MUSOU/INVUL source or original Combat except the scoped patch shown here. If original Combat now contains another basic/dodge Tool, FAIL and reconcile; don't attach duplicate attack loops. The extra normal attack has no new RemoteEvent nor damage/score authority; the only one is original SevenRoleCombat / Swarm.


## SUCCESSOR 2026-11-19: CURRENT Real62→Real63 (supersedes Real59→60 above)

The official lineage advanced twice while this feature was built: first #844 fixed the single original Host source class to runnable `Script` at official HEAD `5a47e96f6b4766a9c59dd06b111bea53b73bd5ca`; then #842 adopted exactly three original trade preview/journal/escrow source routes, preserving active Host, at latest official HEAD `b15db4b9ad1f1f4c1f02fb0976eb3c2f6db8a6ff` (**Real62**). This source feature has been rebased onto that TRUE latest formal 62-source lineage with a non-force two-parent developer-branch reconciliation. The official sole RC is not yet modified by this feature.

**Now correct:** Real62 62 original source/class instances, +1 pure BasicMobilityPolicy, exactly two original singleton owner source *patches* (`EGGRUMBLE_SevenRoleCombat` and existing `EGGRUMBLE_HudIntelRuntime`) => genuine **Real63**, 60/62 original source instances byte-for-byte unchanged, with Host still executable `Script` and all three original Trade/Journal/Escrow modules preserved byte-exact. New field eggs/Fog and all previous 7-job MUSOU/INVUL remain intact. No second damage or store authority.

The currently active Real63 preselection contract is:
- `handoffs/EGGRUMBLE-BASIC-DODGE-20261119/compose_real63.py`
- `rc_fastlane/EGGRUMBLE_V3_REAL63_BASIC_DODGE.json`
- `.github/workflows/p0d-gq828-basic-dodge-real63.yml` (private candidate)
- `.github/workflows/p0d-rc-eggrumble-v3-real63-basic-dodge.yml` (formal after authorized nonforce CAS)

The older Real60 workflows/manifest are historical/manual only and MUST NOT replace newer 62-source official content. Exact official Real62 physical source parent: Actions run `44404334603` SUCCESS, artifact ID `14473628619`, official commit `b15db4b9ad1f1f4c1f02fb0976eb3c2f6db8a6ff`.

Earliest genuine private Real63 Native/Rojo/Off62 candidate SUCCESS: [run 44404983954](https://github.com/kk051780/toy-wars-factory/actions/runs/44404983954), source count 63, actual Place **662,117 bytes**, place/source-class hash `243d502ecf43f3151ab81ee81c6ec61c02ee181fbd9cc877288452e3e88d66d3`, exact OFF62 source-class hash `52ddbbdbd8370bcda6720c468c74f19dcdf706391bb58e0bd8197c57570a5e84`, candidate artifact ID `14472869066` (ZIP 397,094 bytes). Newest PR-head CI after branch reconciliation and formal-style PR gate still required. Formal RC adoption is not proven by this old successful candidate run.

**Real-world GO remains NO:** no actual Roblox Studio 2-client combat/physics test, Android 15 min, attack hit-feel, input overlap screenshots or FUN/ART acceptance. All new moves are free, do not process real purchases and never write `main` or publish. Only the designated sole #220 writer should advance the official branch by nonforce expected-SHA CAS, rechecking that its SHA is still the latest and preserving any further newer approved sources. Then run exact NEW official HEAD gate plus artifact readback before claiming RC_INTEGRATED.
