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