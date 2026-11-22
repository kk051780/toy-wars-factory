# GQ470 FB-015 — REAL69 item ornament visibility (A-only)

Problem found in a real Studio private play: `HEAL/DASH/SHIELD` pickup cores hide after consumption, but the two separate ornaments created by `EGGRUMBLE_EncounterReadabilityArt` do not follow core visibility and falsely appear collectible.

## Actual source fix

From official source-only REAL69 artifact #14610422120 (run #44695199140, formal head `e80973c354f14a0d0088577f3cc1a875454f0f8f`), replace only the existing `decorateFieldItem` block in selected route `ServerScriptService/EGGRUMBLE_EncounterReadabilityArt`. Listen to the original core's `Transparency` and `CanQuery` property changes, initialize visibility even for an inactive item, and disconnect both signals on Destroying.

No new Parts, GUI, frame loop, Remote, inventory, item authority, HP, cooldown, or Store. Preserve original egg crest / vault owners, existing #812 item sculpture and #948 weapon artwork.

## Source evidence, not engine acceptance

- Real original source SHA256: `9ec9982ed0d6e68457712e4e5dd10e7fb608c666adfe2e6904a209f5692a50c9` (21027 bytes).
- Patched source SHA256: `40f4f741be4b71a37085240927dc61fa1a776acceff759f268d97c6d115ec05c` (22046 bytes).
- Exactly 1 of the 69 selected Luau sources changes; 68 untouched. OFF original private Place = 798390 bytes. This is not a claimed ON Place size.
- Local original artifact source lock + 12 tests PASS. Native/Rojo exact-head CI must pass separately to become A-source ready.
- Studio play on this patch, 2client, PC/Android 32 screenshots, 15-minute low-end Android FPS/thermals, human first-3-minute FUN and owner ART acceptance: **NOT_TESTED / NO_GO**.

## B #220 adoption instructions

FEATURE_ID `GQ470_FB015_PICKUP_ORNAMENT_VISIBILITY_REAL69_20261122`; FB-015. A-only source recommendation: `ADOPT_SOURCE_CONDITIONALLY` behind #910 one-match P0, ART17/Horde P0. Actual #250 VALUE_ADOPT and #218 coordinator CLAIM_GRANTED required before the *sole authenticated B #220 writer* may re-GET fresh formal HEAD, source-select the one modified route, perform nonforce expected-SHA CAS, then demand same-head official Native/Rojo/source lock and ZIP/Place bytes.

Do not merge the whole A PR into formal RC, change main, publish, monetize, or treat source CI as Studio ART/FUN success. If formal HEAD moves, rebase, rebuild and re-verify.

## 2026-11-23: fixed original cleanup payload registration

This section registers the existing ART +181 B and +57 B cleanup payload and its original joint review. It introduces no new gameplay implementation. The original README above is retained byte for byte, including its historical source and acceptance statements.

### Fixed payload and provenance

- `current69/EncounterReadabilityArt.cleanup.luau.txt`: original archived `main/runtime/union26/overlays/Art.luau`, **22,284 bytes**, SHA-256 `293eed3bff121484d132ecf7759d189fc3dc6d951412fd60f92f9598341b7837`.
- Current formal ART preimage: **22,046 bytes**, SHA-256 `40f4f741be4b71a37085240927dc61fa1a776acceff759f268d97c6d115ec05c`. The existing four cleanup hunks total +238 B and preserve accepted visibility synchronization, geometry, colors, caps and lifetimes.
- `current69/ORIGINAL_JOINT_REVIEW.json`: original archived `main/reviews/union26/receipt.json`, **232,130 bytes**, SHA-256 `f88b1563c0546ecd40532f1a89c3d3445f1a04b27f89df8db4832185dafa9c2a`.
- Original parent context: `60d92e911c00`; historical composition context: `/root/policy_inventory`. [Original handoff](https://github.com/kk051780/toy-wars-factory/issues/220#issuecomment-7079597551), [ART +181 evidence](https://github.com/kk051780/toy-wars-factory/pull/1010#issuecomment-7078612031), [ART +57 evidence](https://github.com/kk051780/toy-wars-factory/pull/1010#issuecomment-7078831304).
- Original archive SHA-256: `40f0fe23589a886aed4957f87031c45365f2ebe338179b770d6490f0d011bb75` (17,959,164 bytes). Both selected files are copied verbatim. The combined Exploration + ART patch is not added.

The original receipt covers historical **ART + Exploration** after-source execution, including its limited 26/34-body fixtures. It is not an ART-alone run and is not Native CI for this new registration HEAD. The historical reviewer `/root/item_audit` also authored the earlier +57 proposal/full25 fixture; preserve that authorship boundary and the receipt's original flags. This registration does not transform that record into independent approval of those old source fixes. Historical absolute paths and raw results remain unchanged; the receipt alone is not a portable executable bundle.

### Exact registration authority and boundaries

Actual request: [PR1010 comment7087359082](https://github.com/kk051780/toy-wars-factory/pull/1010#issuecomment-7087359082). Actual grant: [#218 comment7087809708](https://github.com/kk051780/toy-wars-factory/issues/218#issuecomment-7087809708), claim `P0D-GQ1010-ART-CLEANUP-20261123-7B6B25AE`, registry commit `bbd45ae5655ec4f24cde4160530b020fe59f68ae`. Owner `CODEX_ROOT_7B6B25AEAA29`; registered independent source-evidence reviewer `/root/current_rules`.

The grant is bound to formal R `dcb501673d7959e4904cf360ef0119917e6aa2e0`. The original evidence comparison base remains `fb5d9b693c48d4ffcce05c3f89d490593e0cecfd`; the historical PR base remains unchanged. [The original official auditor's receipt](https://github.com/kk051780/toy-wars-factory/pull/1020#issuecomment-7087668742) verifies that the intervening 12-path input-retention update preserved all 69 game bodies, project, canonical profile and Place bytes. Registered base-recheck SHA-256: `40bb6cbc719a5c18c0bf48784bf7f7711367083591bc1ce5fa70a0930e8cbc83`.

Only this README append and the two passive files are mutable. The existing workflow, patcher and test Git blobs are fixed. The `.luau.txt` suffix keeps the copied source as evidence; the unchanged historical visibility workflow does not select either new file as a game input. A run triggered by this directory change still tests its historical visibility path and cannot establish current69 cleanup CI.

**PREP_READY=false; registered_source_approval=false; RC_adoption=false.** Registration review is limited to the actual three-file candidate, exact original copies, preserved files, authority and evidence boundaries. Later canonical source adoption requires its own actual exact scope and shared-resource handoff, source/Native/Rojo/intake gates, separate-context review and official-push artifact proof. No RAM, FPS, Studio, multiplayer, Android, ART/FUN or owner-acceptance result is inferred. Exploration source and canonical producer/profile/native/workflow are outside this registration grant.

The current repository policy governs later work; historical approval/ACK wording above is retained as history and is not a new approval requirement introduced by this registration.

### Actual source-write reservation

Source lease: manual CONTROLLER epoch **637**, operation `94e99f5c-4048-47af-bcf3-417576362e2e`, acquire commit `2e5b18c40055abcae8d7962b04f388924bd36909`, work branch `quality/gq470-real69-item-ornament-visibility-20261122-a01`, acquired `2026-11-22T23:55:30Z`, expiry `2026-11-23T00:25:30.000Z`. The three-file commit uses the exact previous source HEAD `f3ac9a5b2742daffb2396c67530db33a64be6779` with non-force expected-SHA CAS. Normal release and registered actual-HEAD review are recorded on the existing PR after the write; this paragraph does not assert either future event.
