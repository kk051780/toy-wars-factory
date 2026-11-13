# P0D independent QA — exact 40+V5 assault attack height H0/H1

2026-11-13 JST. This is an isolated, private, source-only trial, not official RC or Studio play confirmation.

## Frozen baseline and the previous author fixes
- Original #288 40+V5 SHA: 1952154b33422dabc2b4e8ce8eafd8d6df1b6b34
- Author real success CI: https://github.com/kk051780/toy-wars-factory/actions/runs/43386882729
- Original Github Artifact 14019455429, unpublished original Place SHA256 ea2a0c0752bdf4749d948867f13d274d28edfdd155d25aa9af206eb8b833601d
- Original 40 embedded Luau, one Game, one existing Remote. Game blob c118a3ff17397ea69360cd7481a2db51d2c32756. V5 Horde blob 8c147c801e7fa1ff362922d66c9a6fd432fc8b6e.
- Already fixed upstream: true server-clock scout GUARD 5 sec, two ASSAULT attempts spaced2.5 sec within signed 5 sec scout token, red elite 9-stud warning, phone cue geometry. Preserve all these.

## Independent remaining height source risk
Current airborne *visual* scout anchor is actual root position plus4.5 studs vertical. Stage2 ASSAULT feeds same anchor into server-authoritative horde:hit. Real Combat.canSweep allows max5 studs vertical distance. Ground sample root center3.0 above floor and minion center1.65 => visual-origin dy5.85, fails eligibility even if horizontal distance/facing/LOS are fine. Source-conditional risk, not measured Studio miss rate.

## Exact one-hunk candidate
Only one current Game source call changes: before local hits=horde:hit(anchor,currentRoot.CFrame.LookVector,...); after local sweepOrigin=Vector3.new(anchor.X,currentRoot.Position.Y,anchor.Z), then local hits=horde:hit(sweepOrigin,currentRoot.CFrame.LookVector,...). Visual flight unchanged, user root height still checked, no privileges or other 39 script changes.

## Evidence
- Downloaded actual source artifact. H0 XML Place SHA256 ea2a0c0752bd... verified; exact 40 script bodies parsed.
- Local executable Python source and geometry unit tests 30/30 PASS; modified exactly 1 Game source, 39 other Luau byte-identical.
- H1 QA XML Place SHA256 5411cd36750b0bf1765f502ea161b9b483eec459475fa2e3472d4d82802959f9. Original Game GitBlob c118a3..., candidate Game GitBlob 8063e92a2186c0aad16178c99bf0bb92ba395d9e.
- Local H0 and H1 unpublished rbxlx, one-hunk patch, source QA JSON, Japanese H0/H1 test plan are available in conversation files.
- Own GitHub branch now includes tools/patch_v5_assault_height_real40.py with exact source lock and a dedicated .github/workflows/p0d-qa-assault-height-real40-v5.yml. This workflow attempts REAL native compiler40, original Horde native mock50, Combat26, Rojo40 all exact, and publishes a separate private H1 compiled artifact.
- WARNING: New workflow completed run status is NOT VERIFIED. H1 has not yet proven native compilation/Rojo/Studio/Android/fun. Old original H0 native/Rojo success does NOT prove new H1.

## Adoption
On native/Place QA green, request #288 author hunk-level review, #250 explicit PRODUCT_SELECT, and #220 sole RC integration. Two-client and Android must validate real level-ground hit success, no wall/step-through hits, no PvP/score/XP/save changes, guard5sec, max2 assault, first90 FUN. No main, merge, public publishing, paid spend, owner PC/Codex, P0-A/B/C, CAS or automations altered. Official score last75%, FUN_GATE_NO_GO.
