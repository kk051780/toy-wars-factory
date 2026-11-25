# RC31 existing original #536 AI BotPathRouter full-step obstacle gate

**Purpose: RC-only source integration of EXISTING original author PR #536, not new gameplay code.** Preserve exactly the current official canonical 31-game source, 7 playable roles, field, genuine combat, castles/eggs, original Swarm+StoneGiant+AI, original #489 Item, TEAM/BR lobby, and ART/SCORE/balance. Replace only one existing BotPathRouter source by calling the already-written existing author #536 `source_patch.overlay` at immutable author HEAD.

Original source parent **#484** `6b52eaf1f2725496277998fe0c5532b7a8fcaab5`, BotPathRouter Git blob `d9841bb874659129cae6c930bce302ff6936ac4a`. Author **#536** `cdf4fe5f231c998532963c5c16d9525d20a69e7e`, source patch Git blob `651d4c6e92bfe8595eeadb438b594797bd473e77`. Original #536 CI [#43845671792 success](https://github.com/kk051780/toy-wars-factory/actions/runs/43845671792): native full-step raycast and original Router.navigate harness; own author code is not reimplemented here.

Geometry: original anchored AI may travel 30 × .3 = 9 studs per step, but the server raycast checks min(8, step) studs. Existing original #536 one-line authored repair raycasts the entire intended displacement. This is a source-model geometry defect, **not Studio-reproduced**.

## RC source-select sequence
1. Existing official V3 #530 composer, #541 neutral Swarm, #537 castle Host, #540 respawn stealth, #539 lobby world, #489 FieldItemPickups selected exactly as currently official (single each).
2. Immutable original #536 patch checked out at fixed Git commit; own script Git blob checked, and it itself verifies original #484 BotPathRouter blob and exact one-hunk rollback. No second BotPathRouter/AI/Game/Store/Remote.
3. `select_original536_route.py select --base EXISTING31 --author PINNED536 --out GQ536_ON31`: checks all **other30 script bytes identical**, existing original router exactly pinned. OFF = the original official selected31 (including #489 and all previous author revisions).
4. Compile **all selected31 native Luau**; real Rojo7.7.1 builds true unpublished Place and checks **31/31 script Source/Class** and all other 30 same bytes. Python regression tests pin both immutable sources, reject drift, idempotent and base overwrite.
5. Only authenticated #220 sole non-force expected-SHA CAS writer may admit to official RC branch. Official **new HEAD** push same-head V3 and legacy CI must pass, real .rbxlx bytes/SHA and GitHub ZIP bytes recorded. No main, no Roblox Publish, no payment, no Windows work.
6. Studio 2-client, 1+15AI, Android 15min, #420 ART/FUN, OWNER final approval remain NOT_TESTED/NO_GO. No claim to a better game simply because native code/Place compiled.

[Scope claim](https://github.com/kk051780/toy-wars-factory/issues/218#issuecomment-6915790526). #555 nearest eligible human BotActors is an independent change in a *different* AI script and is NOT implemented or claimed here.
