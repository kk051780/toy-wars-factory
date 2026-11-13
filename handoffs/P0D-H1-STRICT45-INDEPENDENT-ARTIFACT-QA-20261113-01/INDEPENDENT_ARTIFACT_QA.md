# P0D H1 Strict 45 — independent **actual binary** artifact audit

2026-11-13 JST | P0D-FUN-H1-001 | P0D-LOBBY-TRAINING-001
Scope: QA READ-ONLY, entirely separate from #220's sole official RC writer.
This audit did NOT run Roblox Studio and did NOT change game source.

## Source and artifact actually examined

- Source fixed SHA `646cd9bd18b3428235ada06a763f9c5ac65b6883`.
- Original author SUCCESS workflow `43415851018`, job `131853431871`, artifact `14030858994`: https://github.com/kk051780/toy-wars-factory/actions/runs/43415851018/artifacts/14030858994
- The real `.zip` was downloaded through the authorized GitHub connector and its ZIP CRC examined; **no remote build inferred from Issue text**.
- Actual ZIP SHA256: `55e32af239f0c6ce94db56b65880345f406692720751225b06e0897cb156a186`.
- The ZIP contains `EGG_RAID_RUMBLE_H1_DOJO_SKYV5_STRICT4_PRIVATE.rbxlx` (432,510 bytes), `SOURCE_LOCK.json`, `PRIVATE_PLACE_RECEIPT.json`, and three native QA text files.
- Actual Place binary SHA256: `96dada63baa2b99e321b5f9eb35a0f335aa22925212e66a8a9b32c48cf5ffd2d`; matched the original author report and the actual embedded PLACE_RECEIPT.
- Real XML parsed with Python `xml.etree.ElementTree`: **45** embedded Luau sources: 2 Script, 6 LocalScript, 37 ModuleScript.
- Independently recalculated every source's Git blob SHA1 from actual XML Source UTF-8 bytes and compared its Counter against the complete 45-entry `SOURCE_LOCK.json` hash Counter: **45/45 EXACT PASS**, including duplicated hashes if any (multiset equality, not merely distinct count).
- Verified exactly one each of (Script,Game), (Script,H1FunWorld), (ModuleScript,DojoRules), (ModuleScript,StudioSoloPreviewRules), (LocalScript,P0DStudioTrialAudit).
- Verified actual V5 H1FunWorld Git blob `7a90affd4eb7eebcdfba39d833a2875ff665d5cf`, original strict audit blob `ee96518a7eeaaaba98d2a8e2aff6dad780fae8c7`, original DojoRules blob `120bac439c979310c9ddeb2fcf2ffa002b6d1add`.
- Confirmed exactly one physical named route for `SKY_GROUND_BOOT_RED`, `SKY_GROUND_BOOT_BLUE`, `SKY_SCORE_DOCK_RED`, `SKY_SCORE_DOCK_BLUE`; original Game single OnServerEvent registration and Dojo single tick.
- ZIP lock explicitly `studio_1client=NOT_TESTED`, `studio_2client=NOT_TESTED`, `android=NOT_TESTED`, `owner_fun=NOT_TESTED`, `official_rc_adopted=false`, `published=false`, `paid=false`.

## Deliberate negative test, all 3/3 rejected

Using temporary copies of the **actual downloaded ZIP**, rebuilt with consistent ZIP CRC:
1. Mutate one byte of the actual Place V5 path name while leaving the author SHA constant -> `PLACE_SHA256_MISMATCH` rejection.
2. Replace just the expected World blob SHA in SOURCE_LOCK with a forged all-zero SHA -> rejected.
3. Falsely change the lock's `studio_2client` from `NOT_TESTED` to `PASS` -> `FAKE_STUDIO_PASS` rejection.

The independent auditor is a simple Python stdlib script that performs ZIP/Place SHA, complete source-lock multiset and unique authority checks. No claim of Luau/engine execution is made in this separate audit; the author's own pinned native/Rojo CI success is independently confirmed by the actual completed workflow job steps.

## Current decision and next acceptance

**SOURCE_ARTIFACT_INDEPENDENT_AUDIT=PASS; ROBLOX_ENGINE_1CLIENT/2CLIENT/ANDROID/FUN=NOT_TESTED.**
This private H1 variant is not #250 formal product-selected and is NOT official #220 RC adopted. The last official S1 score 75/100 and owner FUN_NO_GO stand unchanged. The prior separate experimental branch `experiment/p0d-h1-dojo-sky-v5-unified-20261113-01` is **SUPERSEDED** as it lacks this preferred build's strict V4 observer; do not duplicate or promote it.

The next acceptance is OWNER manually opening the genuine private Place on Windows Roblox Studio in a backed-up isolated unpublished Place, verifying actual egg carry→walk the 4 V5 ramps→sky→own-score, negative carry reset, dojo passive XP, 2 clients/disconnect, then Android and human FUN. #219 PRODUCT_DRI and #250 must select product; only #220 sole RC writer may later update official RC with source/authority lock and independent full RC QA. No main/merge/publish/paid/Windows Codex automatic/extra spending/CAS/P0ABC/five automation changes.
