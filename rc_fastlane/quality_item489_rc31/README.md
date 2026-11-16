# GQ V3 RC31 item author parity — ORIGINAL #489 SOURCE, no duplicate implementation

This is **not a new Item gameplay implementation**. The old-round DASH expiry fix written in withdrawn #543 already exists in original #489. The scope here is to **source-select the genuine #489 original Item module** in the existing canonical V3 31-script composer, after the already-adopted #541 neutral and #537 castle improvements, replacing only outdated #482 Item while leaving the other 30 sources and their classes byte-exact.

## Pinned source facts
- Original V3 host #482: `fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9`
- Its **old** Item Git blob: `24a35a2e6004c635456cc6f2288cf13f8365ba27`
- **Existing #489 author:** `03c51bf5c8d12484bd8dc4667b0d3d3841cb4ddd`
- Its **new** Item Git blob: `107046cb0bf81fed9e3cba1699ada31571e44a22`
- Canonical V3 31-source base: **official #541-selected neutral Swarm (original #530 composer plus #541 original source-selection) on [RC e2b6f533c5741a43455c8b0ddb483470457479f7](https://github.com/kk051780/toy-wars-factory/commit/e2b6f533c5741a43455c8b0ddb483470457479f7)
- Pre-existing candidate #517 further adds **HEAL no-waste** using original Item source; this candidate selects the exact #489 base only. #517's separate improvement is not adopted or claimed by this candidate.

## Eight-domain source parity
Character7, field terrain, battle/HP, castle/egg, **the officially selected #541 original neutral Swarm and AI**, lobby/TEAM/BR, ART/score/balance = identical 30/31 source/class. Stage uses **the currently official #541 + #537 composed source project** `artifacts/gq541_official_select/GQ31_SELECTED_537.project.json`, not older pre-#541 or pre-#537 source projects; thus no rollback of the newly adopted neutral or castle repairs. **Items** = original #489 replaces original #482. No new module, second Game/Remote/Store/score/KO, new gameplay design or new round rule. The original #489 restores DASH only when the original session is ACTIVE and the same Player.Character is still attached, handles egg-carrier DASH/SHIELD and checks server LOS via original InteractionGuard.

## Acceptance chain
1. Official V3 31-source composer produces original base ON31 and OFF31; both native+Rojo pass on same PR HEAD.
2. Original #489 checked out at pinned 40-digit commit; full Item Git blob and exact safety anchors enforced.
3. Source selection replaces exactly one existing ITEM and keeps 30 other source **bytes unchanged** in a separate candidate ON31 project; real native 31 and Rojo 31 complete Source/Class equality tested.
4. **Rollback**: build the original GQ31 ON project or omit the selected Item project; no data migration or runtime gate added. Any source drift is RED/fail closed.
5. #220 authenticated sole RC CAS writer must decide adoption against current latest HEAD and preserve 31-script count; this branch does **not** modify official RC directly; its PR-stage canonical artifact uses original #489 as the final source and is marked premerge until the exclusive #220 authenticated CAS writer adopts the PR. A subsequent official push build is the only evidence of official adoption.
6. Studio 2-client / Android 15-min / OWNER #420 art & FUN are distinct NOT_TESTED/NO_GO gates. No main merge, Roblox Publish, Windows execution or spending.

[Scoped SOFT claim](https://github.com/kk051780/toy-wars-factory/issues/218#issuecomment-6914856578). No waiting for an individual former author; source/CAS exclusive ownership is separate.
