# TRAP RAIDERS S1 — Eight-safe full game source review (unpublished)

Date: 2026-11-13 JST. Source-only review branch `review/p0d-s1-v6-eight-safe-hud-snapshot-20261113-01`; **not** the official RC, not a Roblox Studio result, and **not** approval to publish.

## Exact source ancestry and scope
- Sole protected official S1 RC originally and currently pinned to `1263a03701211a652b99b91d2339575dc8104eff`, branch `rc/p0d-s1-kids-rc01`; exclusive writer is #220 `P0D-CHAT-INTEGRATOR-S1-RC01-B`.
- Entire authentic 7-safe full `releases/P0D_S1_KIDS_RC01` source inherited from fixed source commit `6cc131d3de06fe8799d00f475fc446a526e4b2c4`, already independently cross-module native QA at #238, and independent seven-safe physical arena/exit regression QA.
- **Eighth isolated improvement:** exact *full original* `src/client/HUD.client.luau` from independently native-validated #240 fixed Git SHA `82847cb97d06394f8fba5ec5c88e644dce0a336b`, blob `50823390853989ccdda78e28c16ea4757bbe0715`, UTF8 bytes **9549**, SHA256 `ab9155c3e62522cf32f69ba18a042ff3f32c3e6064e483f48147e8c043edeee8`. Original 7-safe HUD blob `b3d3996c40c690e19007a36a847d5b10fc6a1522`, 9017 bytes. No new Remote; keeps Guardian button on right above Attack and all existing client intent actions.
- Prior 7-safe 21-Luau source game code remains byte-identical for all other **20 Luau scripts**, including single authoritative Game.server, monotonic server `snapshotUpdateId`, anti-stale FirstMinuteModel, D07 heartbeat fail-closed (boss OFF), x/z safe respawn, event-order-independent `PlayerRemoving`, Japanese objective signs, Guardian first-minute instructions.
- Only `HUD.client.luau` and its exact `BUILD_MANIFEST.json` hash/size changed inside the release 37-file tree. No code from S2 fantasy worlds, marketplace, rewards or 7 jobs was imported.

## Why the eighth change matters
Server/Coach already reject delayed same-round `SNAPSHOT.updateId` but HUD still accepted packets with an older ordering ID, potentially rewinding player-visible Score, Status, Attack and GuardianTrap button state. The approved candidate adds `lastUpdateId` and accepts only proper newer integer IDs; once versioned it rejects legacy unversioned, fractional, invalid or duplicate IDs. Keeps BOSS_VISUAL independently sequenced and **does not grant HUD control over combat/score**.

## Actual QA gates
- Before native CI, this is an independently prepared **complete 37-file game source** with new 8-safe exact SHA manifest.
- `python3 -B handoffs/P0D-S1-EIGHT-SAFE-HUD-SNAPSHOT-REVIEW-20261113-01/verify_eight_review.py`: source manifest and rules/UX regression with 18 Python `unittest` cases (inherited seven-safe 16 plus two additional HUD checks). Existing authentic release Python tests also run in CI.
- `python3 -B handoffs/P0D-S1-EIGHT-SAFE-HUD-SNAPSHOT-REVIEW-20261113-01/verify_real_rojo.py --place <actual_rojo_output.rbxlx> --receipt <review_receipt.json>`: checks all 21 exact embedded source bytes, classes, expected full Rojo hierarchy, and rejects **13 intentional invalid XML/source mutations** including two fresh HUD stale-data bypasses. Never marks gameplay as tested.
- `.github/workflows/p0d-s1-eight-safe-hud-order-native-rojo-20261113.yml` is a review-only push/workflow_dispatch CI, pinned real Rojo 7.7.1 SHA256 zip, pinned native Luau source `f46d879e28302a430029304f7f6a162aed66f103`, source exact 37 SHA manifest and original 21 code, malformed Luau syntax control, genuine `.rbxlx` build, 14-day non-public artifact. **Do not declare CI success before checking its actual run and logs**.
- Independently verified *input* HUD client native Luau execution: [#240](https://github.com/kk051780/toy-wars-factory/issues/240#issuecomment-6823976405) actual 43/43 checks plus 6 malicious candidate variants, successful CI https://github.com/kk051780/toy-wars-factory/actions/runs/43220513814. That tests the separate original HUD candidate, not 8-way whole-game Roblox Studio.

## Formal release blockers
Only sole #220 may select/merge into protected RC after checking latest exact commit and other chats' claims. Actual Roblox Studio real two-client network / real Android or iOS touch / mobile FPS / child playtest / egg and trap physics and OWNER first-release approval are **NOT_TESTED / NOT_AUTHORIZED**. D07/D08 boss remains disabled, scope must be reviewed before owner final release. Whole S1 global completion = **75/100 last sole-audited**, independent source work does not increase that score. No main/RC/Roblox live/merge/paid/Windows Codex or five automations modified.

Tracking: [#218 shared claims](https://github.com/kk051780/toy-wars-factory/issues/218) · [#220 sole integration](https://github.com/kk051780/toy-wars-factory/issues/220) · [#240 HUD native QA](https://github.com/kk051780/toy-wars-factory/issues/240).
