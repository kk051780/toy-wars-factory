# GQ470 / GQ492: V3 spectator RC32 **PREP**, non-overlap

- **Existing author reused (no gameplay rewrite):** [#492](https://github.com/kk051780/toy-wars-factory/pull/492), immutable HEAD `eb38aa60b69ed0bdd80fb7ea0dd10cf230345c20`, original `EGGRUMBLE_Spectate.client.luau` Git blob `c39b2d3cc481052940b9d11a6fc695261a9b1e40`.
- **Current official starting parent:** `rc/p0d-s1-kids-rc01` HEAD `9466312436d9567db8bb464a57b664d133f6a6cf`, native Rojo31 same-head success 43935111004 and previous S1 same-head success 43935111003. This work **does not write official RC**, main, or original author sources.
- **Only intended delta:** `EGGRUMBLE_EliminatedSpectate` LocalScript from original author, mapped to StarterPlayerScripts in a **private candidate** 32-source Rojo profile. Exactly 31 pre-existing mapped script bytes/class unchanged; one added client script. Zero new server Game/Host/Combat/Remote/Store/score/AI/neutral/item authority.
- **Actual behavior from original author:** On server `EGGRUMBLE_Eliminated=true`, show small castle spectator UI only for the user's match arena; support arrow keys/touch; restore camera on flag reset or arena removal. Existing single Host/RoundReplay remains owner.
- **Separation of eight domains:** character/7 jobs, field/terrain, battle, castle (server), neutral/AI, items, lobby/modes, results/balance all left byte-identical. Only eliminated player's **client camera** is additive. No duplicate level/system.
- **Fail closed:** old source has exact Git blob, 31 unique mapped scripts, correct Host/Rules server classes, no preexisting spectator; exact identical 31 SHA/classes checked before and after selection, Rojo32 true XML Script/Source/Class exact, source OFF = no mapping delta. Native compiles original client. Repo unit tests check duplicate, missing owner, mutation and overwrite refusal.
- **CI:** the canonical workflow is reused **only on the PR branch** for an extra private32 step after the same canonical31 gates. Main official31 artifact remains generated exactly as before. The separate PR-only artifact must never be credited as official RC script, feature adoption, Studio, Android or release readiness.
- **Integration:** #220 sole authenticated writer checks official latest HEAD, future #607 deposit source and all current selected source refs, and either prepares a new zero-collision 32 source profile with nonforce CAS + same-head official CI or marks blocked. Do not wait for individual original author acknowledgement. Do not merge this PR directly into main or canonical branch.
- **Real acceptance still missing:** Studio solo/2-client + castle death, camera return, TEAM/BR isolation, touch safe areas / low-end Android15min, ART/FUN and OWNER accepted. Original #492 client intentionally guards `RunService:IsStudio()`; production support is NOT asserted.

## 2026-11-17 rebase onto next canonical RC
- Parent official now `36400324858cd9f2cdecc72776193c9c8e621f0d`, including sole-writer GQ586 deposit-member check from PR #607. This proposal retains GQ586/previous 31 mapped bytes exactly and adds only #492 spectator LocalScript. New selected base project is `artifacts/gq515_official_select/GQ586_ZOMBIE582_V3_STABLE_NEUTRAL31.project.json`; original isolated preview's earlier parent `946631...` is historical only.

- 2026-11-17 additional latest official parent `63ff99ca8656a85b7aa479cd623c4658dd96c3c4`; three official QA-only commits (#GQ8 scripts and workflow trigger) retained, V3 playable Source 31 unchanged, candidate 31+1 original #492 exact.


## Current 31-script integration-only successor

- This successor uses exactly original #492 LocalScript and original #613 admission code and tests; no new Game, Combat, NPC, Store, Remote, item or castle server authority.
- Fixed starting RC: `89cbeb03d74ddbe3408ef805fed6683ff6abc508` (original #618 real BEAST + original #582 v4 castle leash, GQ611/525).
- **Current base selection:** `GQ618_GUARD582_V4_SELECTED31.project.json`, not the obsolete GQ586-v3 project. All 31 current source/class objects must equal the canonical GQ618_GUARD582_V4 Place exactly. One new LocalScript becomes private32.
- Native compiles all32, executes original #492 lifecycle and 3 mutation negative cases, real Rojo32 compares exact Script Source/Class for all31 and original client. Actual Github Actions must be SUCCESS at fixed PR HEAD before `PREP_READY`.
- Client is guarded by `RunService:IsStudio()`; source selection is for private QA only. Official adoption would require an explicit source/feature flag, RC count32 and publisher-safe review; **do not classify as production-playable**.
- #220 sole authenticated CAS writer and original source QA gates remain; Studio2client/Android/FUN/OWNER are NOT_TESTED. No main, release publishing, payment or Windows changes.


## New formal HEAD follow-up after original GQ615 lobby queue
- Source refresh only: newest authenticated official parent `b0a4b95de5a501173bdbd2ce179e5901d9d78686` with `LOBBY_QUEUE_ETA_615`; selected private32 project is composed from `GQ615_LOBBY_QUEUE_SELECTED31.project.json`, not obsolete prior ZOMBIE-GUARD-only selected project.
- Preserve 31/31 current 31 source/classes including now installed original #615 Host Billboard, #631 Zombie GUARD, #618 Beast, #611 Guard, #525 Item. No reauthoring GQ615 or GQ492. Native32 + Rojo32 full comparison against exact GQ615 canonical Place required after this new HEAD.


## Current official GQ499 deadline composition
- Base accepted RC `b6f80874ecb9320f483bcb87892bc32af387aca3` has 31 current runtime scripts and 32 enabled source flags. Spectator candidate adds one original client only; all original31 including deadline Host preserved byte/class exact.
- Use current `GQ499_DEADLINE_SELECTED31.project.json` and `GQ499_DEADLINE_REAL_ROJO31.rbxlx`, not stale lobby-only base. Studio/Android/FUN still NOT_TESTED.


## New original GQ527 castle bot-siege current RC composition
- Official parent `2291154fd07c8d8af086f76199bf585ff2c725c4`: original 31 scripts, now 33 source flags. One existing BotActors changed by the original #527, after #499 deadline Host; our spectator candidate preserves ALL31 current script bodies and adds only original spectator LocalScript.
- Optional Studio profile base `GQ527_SIEGE_SELECTED31.project.json`; exact live canonical source comparison `GQ527_SIEGE_REAL_ROJO31.rbxlx`. Original #492 remains Studio-only, not public playable, no double gameplay authority.
