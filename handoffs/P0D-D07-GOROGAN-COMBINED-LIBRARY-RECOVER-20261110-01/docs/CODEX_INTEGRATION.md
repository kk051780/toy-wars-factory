# D07 Gorogan combined runtime — Codex-only integration contract

`P0D-D07-GOROGAN-COMBINED-WIRING-20261110-04`; game `TRAP_RAIDERS`; work `p0d-siege-v19`.

This is **one NEW integration shell** reusing, not copying, previously shipped pure AI, physical rig, attack gate and receipt window. It must be reviewed by the OWNER's Windows Codex against its actual protected local PC source. This is **not** a tested Roblox Place.

## Source prerequisites and why it is necessary

- v40 `ChaosEventCore.luau` from ZIP SHA `05a85a7934f6ae1815c9dd50c81a3ff81c3f8e46c9051fe0f8fea1838b8ed9ec`. Core `ACTIVATE` contains `event`, `matchId`, `kind`, `subtype`, `untilAt` but **not** `eventId`, `stageId` or physical boss spawn. The PC MUST generate a server-unique eventId from an existing round epoch, bind current stage and trusted ground anchor, then call `Combined:start` only with the **actual in-process v40 ACTIVATE object**, no Remote.
- D07 Gorogan AI `GoroganServerAICore.luau` at `80483ad6543fd73dfaf8a21ecf7b58dc2eca75e1`, prior `GoroganServerRuntime.luau` is a reference only and is **NOT** used together with the Combined adapter. Don't attach two heartbeat handlers / two damage pipelines.
- D07 rig ZIP `9ceadcf6d2af1361e92683021e3d174da058b5e4aeeda748f90a8f69309e047c` and commit `e7801615c5b70346dfaec189f195a65f5b597ec9`, from which `GoroganRigDriver.luau`, `GoroganDamageBoundary.luau`, `GoroganAttackReceiptWindow.luau` are required as sibling ModuleScripts.
- D07 client display `GoroganVisualPolicy` / `GoroganVisualPrefab` / local adapter at `5128e288c7bd119a470c253a9792f4d829c569ec`, fed **server** `TRAP_BossVisualEvent` snapshots. The client visual is separate from physical hitboxes. `START` / `STOMP` / `END` only.

## Mandatory true server callback provenance

The PC integrator must construct `Combined.new({integrationApproved=true, ...})` **server-only**, supplying real Driver, Gate, Window instances and all required callbacks. In particular:

- `isCanonicalActivation` must validate the **identity of the real v40 output** in RoundCoordinator (not a client-controlled `kind=BOSS` table). `mintServerEventId` binds to canonical match epoch and can only mint once per round. `getStageId`, `getCurrentRoundId`, `getGroundAnchor`, `getNow` and `isRoundActive` come from existing **server** APIs.
- Driver `currentRound/isEventActive/isValidStageAnchor/isSafeTerrain/serverOnlyFolder` must be reviewed against real S1 map, `workspace` ownership, trusted ground, and correct Motor6D/R6 geometry. Do not force movement by teleport if PathfindingService fails.
- Gate `resolvePlayerFromTrustedId/isRealRoundEvent/isActiveCombatant/isSafeZone/isDamageImmune/getBossPosition` must source current server roster and Humanoid. `getAttackCenter` must use `window:center`. `isCanonicalAttackReceipt` must use `window:attests`. Never replace either with `return true` or client-provided fields. `raycastIgnore` may include the boss rig, but must **not** include world collision/walls. Gate rechecks raycast before `Humanoid:TakeDamage`.
- The adapter's `Core.tick` result is the **only** place where `window:openFromCoreResult` is invoked. `window:close` runs even on callback failure and on stop. It will issue damage at most once per Core `STOMP_RESOLVE`; the Gate has its own player/attack dedupe.
- Navigation receives the exact server-monotonic `now` missing from the old `GoroganServerRuntime.requestNavigation(position,reason)` reference. Core/driver timestamps must use same `getNow` clock. ComputeAsync may yield: adapter prevents overlapping heartbeats and rejects if the round/event changed while awaiting a route.
- If callback missing, noncanonical event, stale round, broken rig, invalid roster, nonmonotonic clock or damage callback raises, this adapter fails closed / destroys the rig. **Do not** silently report success or re-roll boss in the same round.

## Mandatory PC one-slice Studio acceptance

The v43-A latest **true PC report** [#213 #6758415195](https://github.com/kk051780/toy-wars-factory/issues/213#issuecomment-6758415195) confirms scoped 2/3client pass and Studio closure, but game remains `PARTIAL_NOT_READY` and saved-Place reboot QA is still open. Prioritize saved-Place reboot test before any boss. Then read-only verify the real PC does not already contain a ChaosEventCore or independent event picker; PC report said canonical `ChaosEventCore` was **not present** in current game source. Adding it must first be explicitly designed as a **single server chooser**, and it must not displace existing world weather or v43-A ownership.

If dependencies actually pass, load this optional adapter in an unpublished **S1-only** Place; validate genuine server event, ServerScriptService modules, real R6 motor/walking, server-network-owned NPC, path blockage, warning seen on 2 clients, actual one-hit 8HP cap, safezone/wall exclusion, round close and rematch cleanup, 7 job/egg regression, iPhone emulator FPS, Studio-owned-PID close. If any criterion fails, record BLOCKED/FAIL, do not claim full runtime success. No second scheduler, duplicate damage writer, exploit of P0-A/B/C gates, main merge, publish, purchase or spending.

## Known limitations

No access to PC's latest local Source/Place contracts; `Luau` compiler and Roblox Studio have **not** run on this package. It uses Luau syntax and checks with Python offline/static tests. `integrationApproved` is a local interlock **not a cryptographic proof**. Old samples' R6 rig geometry and network ownership remain runtime risks. We deliberately omit arbitrary automatic registration in `RunService.Heartbeat`; PC RoundCoordinator owns timing.
