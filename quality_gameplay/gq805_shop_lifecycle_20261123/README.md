# GQ805: close stale lobby shop overlays during active combat

This is a bounded continuation of original [PR816](https://github.com/kk051780/toy-wars-factory/pull/816), FEATURE `GQ805_3D_SHOP_KIOSK_RUNTIME_20261118`, under [owner requirement805](https://github.com/kk051780/toy-wars-factory/issues/805). It reuses the existing Catalog/View from PR808 and the existing KioskClient. It does not create a second shop, renderer, Remote, wallet or purchase authority.

## Problem and correction

The original KioskClient opens the original ShopView but never retires its ScreenGui. The View has `ResetOnSpawn=false`. Its large opaque window remains when the player's matching TEAM or BATTLE_ROYALE arena becomes ACTIVE. The original shop has DisplayOrder20 and the confirmed-hit/cast presentation has DisplayOrder18. A separate five-body source diagnosis established that the window covers those indicators; it did not establish actual engine input interception or ordering against the main HUD, which also uses DisplayOrder20.

The original code also waits for PlayerGui after validating the prompt and character. If that request becomes stale while waiting, it opens the old request without checking again.

Only `StarterPlayer/StarterPlayerScripts/GQ805_ShopKioskClient.client.luau` changes. The controller now owns a request identity, its GUI and its observation connections. It reads the existing Host's supported mode and corresponding arena phase. It preserves browsing while waiting and after walking away from an already open shop. On ACTIVE, death, elimination or invalidated character/prompt, it retires its own request. After each possible loading boundary it checks the same request, character, Humanoid, root, prompt, proximity and phase. An older request cannot clear a newer request's busy state or GUI.

One Heartbeat observer exists only while a request is pending or open. Manual Close uses the original View's GUI destruction and releases the observer. PlayerGui waiting is bounded to five seconds. The controller does not depend on its own Script.Destroying callback, which Roblox documents as unreliable with deferred destruction. Controller hot replacement is not an engine-tested feature of this slice.

## Locked source boundary

| Item | Before | Proposed after |
|---|---|---|
| Existing KioskClient bytes | 2170 | 5002 (+2832) |
| KioskClient SHA256 | b381bf0e4db6c5382f3621524eb3bc1e20f63b2977f3809c79adab85774b176d | b8651e09ad0caae896e535ae39b74f7fde4b839b13fd33527b6ad5c5e6442b5a |
| Selected scripts | 69 | 69 |
| Other source bodies | 68 | Exact original68 |
| Routes/classes and non-source structure | 69 scripts / 75 instances | Exact same structure |
| Catalog/View | Original4506B / 6116B | Byte-exact originals |

`source_lock.json` pins the full current official69 inventory, project, Place, official artifact and immutable inventory helper. `shop_lifecycle_patch.json` holds one exact-body replacement and its inverse. Whole-body locking makes an intervening KioskClient change fail closed rather than silently overwrite it. The size increase supplies request ownership, lifecycle retirement, current-phase checks and post-yield validation; it adds no gameplay system.

The current build input is official RC `72d620d86761f2aa5da80263a251cc5fa63fecbb` (Bot PR1027), push run [45132949073](https://github.com/kk051780/toy-wars-factory/actions/runs/45132949073), artifact14798134590. Its ZIP is7144237B / SHA256d178f62489f275831da86eaceda8b8ce1fba6a8ccf86366bd86cb8c5507a926b. The actual push artifact has all69 source bodies, project and Place byte-identical to the separately measured H72 PR candidate; the candidate archive is not used as the official input. Relative to historical H93, only BotActors changed to19625B / SHA256c38bcf82df581d2d9f105f9d7843eef0eff8e8bd6315b8520765ee646e1c5051. ACTIVE_RUNTIME remains rich51; this source proposal targets PRIVATE_COMPANION REAL69_UNION22. RUNTIME_UNIFIED remains NO.

The native three-body origin stays H93: `93a1147561a531610ac1609ebc68cc0ecf546623`. The original KioskClient, Catalog and View are byte-identical in H72. The frozen `native/INPUT_LOCK.json` and runner retain H93 as the origin of those three bodies. The current game parent, live-RC fences and official archive are bound separately by the outer lock and workflow. The original H93 lock, grant682 records and publication map remain immutable historical evidence.

The builder retains the exact H93 inventory helper (28443B / SHA2568d5efc7072ee61c331873cda9e642bf8034fdd8bf0e74d97d718af38f1f5e073, Git blob1381f6aeca421f1b28a9c3710177cee56ade6120). CI fetches it from the immutable H93 commit, checks the blob, size and both content hashes, and places it in a separate read-only dependency snapshot. It does not use the changed helper in the H72 checkout or claim that this dependency is the current game parent. Existing helper-drift checks remain enforced before execution.

## Evidence and exact limits

The historical same-body Native execution used the locked fixture with the entire original Catalog/View and either the original or proposed KioskClient, once each. The original retained all38 read-only controls and reproduced24 declared failures across38 scenarios; the proposal passed all38 scenarios. Those original-body, candidate-body, fixture, runner and lock bytes are unchanged. This rebind does not relabel that execution as a new hosted H72 or new source-HEAD run. The suite checks waiting and unrelated arenas, active phase and late replication, manual close/reopen, death/elimination/character replacement,18 controlled yielding cases, old-A/new-B ownership, timeout recovery, module errors and purchase-OFF behavior. Four of the yielding cases are valid controls;14 are stale requests that must not mount.

The runner rejects a baseline timeout or unrelated error. It requires the known exit1/terminal error for the baseline, exit0 and empty stderr for the candidate, the exact case plan and count, and unchanged source/tool inputs. `native/INPUT_LOCK.json` fixes the fixture, original three bodies,38 cases and38 read-only controls. A declared source-head field alone is not an independently authenticated CI receipt.

The H72 rebind was checked against the actual official artifact on 2026-11-23 at07:50:57Z. All11 unchanged overlay fault tests passed with the new lock, and the unchanged builder compiled all69 ON plus69 inverse-OFF sources. Pinned Rojo7.7.1 produced ON832045B / SHA256f2df45e13a9ffa36319be0bd0a80ccd55b3bdcd7321e0ab9c6cd39b32a1443f7 and inverse OFF829213B / SHA256cacc922501717c417c05e60bdf3c32c6d917e3622931401ab45fc8eeed3da3c5. OFF is the complete official H72 Place byte-for-byte, retaining its Bot correction. Other68 bodies, all routes/classes, project and non-source structure are unchanged. The original full H72 artifact, including Bot/HUD and earlier inverse archives, is retained. The local build has no source HEAD and is not hosted CI or Shop RC adoption.

Historical H93 local QA produced ON831490B / SHA2567e50e4fe322bd655eedea695ce2268035f704cb35803391d151684072ebe8bee and inverse OFF828658B / SHA2569cc9068b85893605c5090964fdc27175d9c48372803d65fe52914591fa7e5899. These measurements remain historical and are not the H72 inverse target.

Native uses simulated Roblox instances/events. The require pauses are injected; the actual Catalog/View bodies do not yield. PlayerGui availability and timeout are controlled, not engine timing measurements. Actual rendering, touch hit testing, networking, deferred-event scheduling, Studio Solo/2client, Android15m, ART/FUN and OWNER acceptance remain NOT_TESTED. Every purchase stays disabled and the mount callback stays nil.

The measured teardown is limited to the owned GUI and request: manual close/reopen, GUI destruction/detachment, stale-request retirement and request-owned observer cleanup at the exercised fixture boundaries. The Native fixture does not contain the executing LocalScript Instance and eagerly fires GUI Destroying. Destruction, disabling/re-enabling or hot replacement of that LocalScript, and Deferred Engine behavior, remain NOT_PROVEN; 38/38 PASS is not a universal connection or memory-leak certification. Before any grant, the unissued local scope draft was aligned with the actual #218 request to make this distinction explicit. Original source, cases and acceptance gates were preserved.

## Reproduction

The dedicated workflow checks the actual official parent before and after, verifies the real parent run/artifact, downloads the exact archive, builds Luau commitf46d879e28302a430029304f7f6a162aed66f103/tree2432c996fc9fa73680b5e2cfe172d36114fe3746, verifies pinned Rojo, runs the fault tests, builds ON/OFF and executes both Native variants. It has contents/read and actions/read only. It never updates the canonical producer or a Git ref.

For an offline replay with the authenticated parent archive already available:

```bash
python -B tests/test_gq805_shop_lifecycle_20261123.py -v
python -B quality_gameplay/gq805_shop_lifecycle_20261123/apply_shop_lifecycle.py \
  --base /path/to/extracted-parent --out /path/to/new-output --repo-root /path/to/pinned-h93-helper-snapshot \
  --luau-compile /path/to/fresh-f46/luau-compile --rojo /path/to/pinned-rojo \
  --parent-archive /path/to/original-parent.zip
python -B quality_gameplay/gq805_shop_lifecycle_20261123/native/run_shop_lifecycle.py \
  --source-dir /path/to/extracted-parent/sources \
  --candidate-source /path/to/new-output/ON69/sources/StarterPlayer/StarterPlayerScripts/GQ805_ShopKioskClient.client.luau \
  --luau /path/to/fresh-f46/luau --luau-compile /path/to/fresh-f46/luau-compile \
  --out /path/to/new-native-output
```

The helper snapshot must contain the exact pinned helper at `quality_gameplay/gq470_union22_real69_20261122/compose_union22.py`; the workflow shows the immutable download and validation. Output directories must not already exist. The builder uses the accepted existing inventory verifier without writing bytecode into the input checkout. OFF is derived by reversing the proposed source; it is not merely a copied baseline presented as an inverse test. The original complete parent archive, including its prior rollback artifacts and reports, is retained as `OFF_ORIGINAL_PARENT_ARTIFACT.zip`.

An official parent move requires a coordinated rebind, preservation of the new parent's other sources and a new exact-head check. Do not remove the parent fence to obtain green CI.

## Authority and remaining gates

Source owner/proposed shepherd: CODEX_ROOT_82F2BEB2AB16:/root. Source/test authors: /root and /root/p0_gap. Independent reviewer context: /root/rules_intake. [Request7091284176](https://github.com/kk051780/toy-wars-factory/issues/218#issuecomment-7091284176) retains the original feature and nine isolated PREP paths. The original H93-only grant was registered at8586c940ea073cfe43404e1f48f7694a03bc9744 under metadata682, which was normally released atd325e8edaed2e376d97e15da229f5222e0885bb9. That history does not itself authorize the H72 rebind. The current registry, exact same-claim amendment, its independent review/readback and a separate live SOURCE lease govern publication. This document is not an authorization receipt.

These nine standalone PREP paths do not select the Shop patch in the canonical producer. Adding the six shared canonical paths and their resources requires a separately reviewed same-claim scope amendment and legitimate handoff. They are not part of this slice.

The legal preparation boundary follows the latest [OWNER NO-STALL instruction1011](https://github.com/kk051780/toy-wars-factory/issues/1011). Actual metadata registration, a separate SOURCE lease, source publication with same-head CI/independent review, and a separately scoped single-writer RC transaction remain necessary. The existing Bot/BEAST/Guardian and self-relay priorities remain. Main, Publish, spending, commerce and the five standing automations are outside this change.

After formal intake, the same adopted RC must be checked in Studio: open the lobby shop while waiting, start TEAM/BR, confirm combat feedback remains visible, test respawn and subsequent reentry, and confirm the shop remains read-only. Those engine checks have not been performed here.

API references: [ScreenGui order](https://create.roblox.com/docs/reference/engine/classes/ScreenGui), [Instance wait/destruction](https://create.roblox.com/docs/reference/engine/classes/Instance), [deferred event behavior](https://create.roblox.com/docs/scripting/events/deferred).
