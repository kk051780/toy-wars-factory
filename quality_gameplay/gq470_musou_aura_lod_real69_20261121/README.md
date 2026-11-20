# GQ470 FB-015 — REAL69 Musou aura compact visual slice

## Scope and provenance

- Official base: `rc/p0d-s1-kids-rc01@e80973c354f14a0d0088577f3cc1a875454f0f8f`.
- Verified official 69-source artifact: [run #44695199140](https://github.com/kk051780/toy-wars-factory/actions/runs/44695199140), source `StarterPlayer/StarterPlayerScripts/EGGRUMBLE_MusouAuraClient` (`ModuleScript`, source SHA256 `b2c279371a8fd986b929883290aae58ed9acdafb7cd48f878eae3785e4acccab`).
- Feature ID: `GQ470_FB015_MUSOU_AURA_COMPACT_LOD_REAL69_20261121`. Existing #824 observer author is reused, not replaced; [#218 claim 7052844287](https://github.com/kk051780/toy-wars-factory/issues/218#issuecomment-7052844287). #470 and #420 remain quality owners.
- Only **one source-selected REAL69 module** differs. Nothing is directly merged to the sole formal RC from this A branch. Main is untouched.

## Player-visible source changes (not a rendered claim)

- On-head aura billboard 195×54 → 150×34 px (**51.6% lower nominal rectangle area**), max visible range 160 → 100 studs; lower visual obstruction in crowded team fights.
- State glyph keeps each of the seven original role colors, mode and symbols; fixed 16px type truncates gracefully rather than enlarging over battle targets.
- Occluded-mode outline reduces harsh glow (fill transparency .70 → .84; KAKUHEN .42 → .69; outline .00 → .22). No screen-wide postprocessing, no extra Highlight or light.
- Particle LightEmission .70 → .28, near emission 12/24 → 7/12 per second, lifetime .35–.70 → .25–.48, near phase burst 18/28 → 12/16. Emitter Rate=0 above 95 studs on a trusted snapshot update; near-distance startup burst only. **This does not claim measured FPS**.
- Existing controller refreshes on replicated Musou attribute changes; the distance LOD is refreshed on those state updates, **not continuously on camera movement**. Studio should check fast camera transitions before integration.
- Cosmetic-only: 7 internal role IDs including NINJA remain. No Remote, Game, Host, score, HP, damage, Store, map collision, per-frame camera loop, server authoritative capability, or new world Parts.

## Source gate and rollback

`patch.py` refuses a wrong base-source SHA, anchors all edits, rejects **9 corrupted-source negative cases** and emits the selected changed Luau + report. Dedicated Actions compiles 69 candidate and 69 original selected Luau, builds true candidate and OFF69 Rojo Place, and checks original Place binary byte-for-byte. B packet is **NOT_FORMAL**. Only #220 authenticated B may re-verify the fresh official head, existing #910 playable/ #931 ART6 priority, distinct source/CLAIM, then select this one ModuleScript via expected-SHA nonforce CAS and same-head canonical CI.

## Independent ART gate truth

No genuine old/new screenshot has been collected (**0/32**); Studio Solo/2-client, low-end Android 15-min FPS/heat and first 3-min FUN are **NOT_TESTED**. `ART_NO_GO / MOBILE_NO_GO / FUN_NO_GO / PRODUCT_NO_GO`, OWNER_ACCEPTED=0 until independent #420/#470 review. Outcome is a visual source candidate, not a finished game.