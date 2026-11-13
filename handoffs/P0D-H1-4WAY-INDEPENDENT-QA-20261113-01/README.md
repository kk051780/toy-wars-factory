# Independent H1 four-way actual .rbxlx cross-contract QA

[Owner source #255](https://github.com/kk051780/toy-wars-factory/issues/255) builds the complete sky/sea + moving-neutral + RAIDER Wind/Guardian trap + D18 dragon client-guide source, frozen git 1498c2d344ede2d9da6c2bfdd025ebc1a15ec48b. Our independent #257 QA **never edits that source**.

Original successful artifact ZIP SHA256 292dfe59542e2f6ea8e35f95617e2337e7e7554c54b02b2cd278bfbae80910ce; exact original unpublished .rbxlx (216457 bytes) SHA256 c930ecaeb09a6da365e6bc7ee8ec68b86096f32e9c82844e9af07c27ae0deac9. Direct actual XML inventory 28 real scripts; eight Git blobs proven including D18 assets and correct wall-safe overlay.

This QA reads **actual Rojo game XML** (not a design JSON) and enforces script class distribution 2 server/4 client/22 module, one S1 Game/Remote/round authority, egg cancel of Wind, Guardian trap counter, only current two live roles, D07/D08 OFF, D18 read-only ordered SNAPSHOT to real enemy egg/own score pad, no new creature damage/rewards/economy, six connected passable-by-source geometry routes that avoid all castle wall bounding boxes, original egg and pad objective, plus 16 intentionally unsafe source mutations rejected. Does **not** prove physical physics, touch FPS, client performance, route-length fun, or child comprehension.

On checked-out source branch:
```sh
python3 handoffs/P0D-H1-WOW-4WAY-20261113-01/tools/assemble.py --verify
python3 handoffs/P0D-H1-WOW-4WAY-20261113-01/tools/assemble.py --assemble
rojo build handoffs/P0D-H1-WOW-4WAY-20261113-01/dist/TRAP_RAIDERS_H1_WOW_STUDIO_ONLY/default.project.json -o /tmp/h1_4way.rbxlx
python3 handoffs/P0D-H1-4WAY-INDEPENDENT-QA-20261113-01/independent_h1_xml.py --place /tmp/h1_4way.rbxlx
```
The separate CI workflow pins Rojo 7.7.1 SHA256 and rebuilds source. **No official RC/main/publish/paid/automations changes**. Last sole S1 75/100, owner FUN_GATE NO_GO until genuine H0/H1 private 2client/mobile and human comparison.
