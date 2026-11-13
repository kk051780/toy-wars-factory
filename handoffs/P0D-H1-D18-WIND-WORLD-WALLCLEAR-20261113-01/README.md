# P0D H1 — FIRST COHESIVE D18 MASCOT + WIND + SKY/SEA + WALL-CLEAR PRIVATE GAME SOURCE

This branch produces **one actual complete unpublished game Rojo project** from canonical sources, not three disconnected packs:
- #252 full S1 25-source composite `3c537a551e173fffaf0e1039c90d04250313c6d8`: original match, egg stealing, HUD, Guardian trap, server-owned RAIDER wind, original #232 moving whale/pegasus, sky/sea overlay. All **24 source files except old H1FunWorld** remain SHA-identical.
- #253 review-only corrected H1 world Luau **exact blob cc764b9caaa293ff747489e02e607af4502ddca4** source origin `2494fa855d77e1ef6dd2c5f8b8d21fbef90fc44a`; copied into OWN local full-game source. Added two sea entry connectors and moved sky ramps/sea route away from source-defined solid side walls.
- #219 D18 Batch8 `TRCA-BE-063 熔炉の角竜` via **exact** previously compiled catalog / LocalScript / Rules blobs pinned by SHA in `BUILD_MANIFEST.json` from `bce72bd3b36f5a331afc939ede6a7779fb9545b9`. Runs only within Roblox Studio and gives read-only client prompt/short golden direction to real enemy egg or current team's score pad.

## Ownership, acceptance, risks
- This branch is **not** #220 protected `rc/p0d-s1-kids-rc01` and does NOT rewrite #248/#251/#252/#253/previous #219 assets or `main`. No publishing, merger, real spending or Codex remote operation. Studio-only H1.
- Source-only geometry math checks castle-wall intrusion, endpoint connectivity/slope and map bounds. **Zero source-defined overlaps does not prove Roblox avatar physics, egg carrying, performance, trap counterplay, child fun or release quality.**
- Original `S1` only **two live roles RAIDER/GUARDIAN**, not planned seven. No new damage/game/round/server reward authority, Remote, DataStore or paid features.
- Original H0 eight-safe game `3120b9d3c0a5ec58c9f2613c5d186f3493b54f83` remains rollback, as does separately vetted #252 combined H1.
- Order for #220 intake after **independent QA**: validate exact 28 source locks and source collisions; build real unpublished Place; owner private 2 clients physically take both sky and sea from either team, actual egg pick/carry/return/drop, Wind vs Guardian trap and both visible neutral creatures; check dragon prompt on Android touchscreen and E key, stale snapshots; measure FPS and Output, no false hint/no overlap, compare H0 vs this H1 human play before any RC adoption. No model/game publish by this branch.
- If player movement can't traverse path, or if cloud art blocks visibility, rollback source to original H0 and revise; don't call SOURCE PASS gameplay PASS.

## Provenance/Tests
`python tools/verify_unified.py` plus `python -m unittest discover -s tests -p 'test_*.py' -v`; CI builds pinned real Rojo 7.7.1, validates 28 scripts inside full .rbxlx and native Luau compile/guide tests. Source integrity manifest contains exact Git blob and UTF8 bytes for every Luau source. Artifacts Studio only.
