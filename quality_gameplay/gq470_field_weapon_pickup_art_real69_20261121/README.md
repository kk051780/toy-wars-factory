# GQ470 FB015 — REAL69 field weapon pickup silhouettes (A-only PREP)

- Unique isolated source: existing ServerScriptService/EGGRUMBLE_FieldItemPickups (ModuleScript), 1/69 changed; all other 68 selected original Luau scripts byte-exact.
- Owner visual feedback FB-015/#364; design #219; art/Android/FUN #420; quality implementer #470. Independent soft claim: https://github.com/kk051780/toy-wars-factory/issues/218#issuecomment-7052478788
- Official source base only: rc/p0d-s1-kids-rc01@e80973c354f14a0d0088577f3cc1a875454f0f8f, real official private companion Studio artifact #14610422120 / workflow run #44695199140. Revalidate at authenticated B admission.
- Source SHA256 old 8fbf9187267df800c5c4a6379b1e2e3db0de4c363854a805c40c378bd0bb9658, candidate 3db8b5dadb8017f0ae01c53092d3ed53d408076ee2dc3a8bb88a8d9a364824e8, byte count 14656->15826.

## Real player-visible delta

The six original world weapon pickups SUN_BLADE/WIND_SPEAR/THUNDER_BOW currently use only one generic shaft on a square base. Add one angled matte WedgePart facade to each, with distinct color, dimensions and orientation, so the sword blade, spear tip and bow limb are recognizable at range. Exactly +6 ephemeral world Parts maximum for six sites. All six facets are Anchored and CanCollide/CanTouch/CanQuery false. Each facet uses the same world-item Folder lifecycle as original visuals; its Transparency is synchronized with original shaft when collected and after 15-second respawn. There is no new performance loop, GUI, Remote, Store, purchase or effect authority.

Original HEAL/DASH/SHIELD consumable models, physical interaction/base Part, 18s weapon buff, damage multiplier/reach, cooldown, per-round session and anti-egg-carrier restrictions, itemStop cleanup, ProximityPrompt and TEAM/BR server LOS authority remain untouched.

## Source-only verification and admission

Dedicated workflow gq470-field-weapon-art-real69-prep.yml pins true GitHub author HEAD (not synthetic merge), downloads exact formal REAL69 source ZIP, confirms original 69 SHA256 values, applies only FIELD_WEAPON_REAL69.patch with zero fuzz, validates only one changed script and all 68 others byte-exact, and rejects eight source mutation negatives. It compiles all 69 candidate + all 69 OFF Luau with pinned native compiler, builds both real Rojo Place files, compares OFF Place byte-for-byte with formal original, and preserves existing legacy48 inventory source evidence. An artifact includes one selected Luau, B220 handoff manifest, report, old/new private Place.

B #220 is solely authorized for fresh nonforce CAS into single official RC after #910 P0 and higher priority existing ART composite; A CI success is not permission to merge blindly. Full rollback of one existing source through OFF69_SOURCE_EXACT.

BEFORE_AFTER_32=0/32; Studio solo/2client NOT_TESTED; Android15min NOT_TESTED; ART/MOBILE/FUN_NO_GO, OWNER_ACCEPTED=false, formal RC not adopted. This candidate does not claim actual quality or fun without measured Studio/mobile evidence. No main, publish, payments, force or Work.
