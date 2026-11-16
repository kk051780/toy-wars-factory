# EGGRUMBLE V3 — boss defeat round-scope fence (isolated GQ)
2026-11-16 • #470 game-quality writer • packet `GQ-V3-BOSS-KO-ROUND-FENCE-20261116` • #218 SOFT claim `6907126516`.

## Proven gap / what really changes
Original #482 fixed HEAD `fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9`, source `EGGRUMBLE_LobbyCastleModesPreview.server.luau` increments real winner's `EGGRUMBLE_BossDefeats` when StoneGiant dies. Original `EGGRUMBLE_RoundReplay.resetHuman` never resets that Player attribute. Thus a session's counter may carry into the next TEAM/BR lobby and round. This is a static source finding, not a real Studio reproduction.

These **two new, optional, Studio-only Luau sources** are wired only in the **isolated 23-source project JSON**. The server observer tracks already-server-owned `EGGRUMBLE_QueuedMode` and zeroes the boss counter at each real mode boundary. It never clears a non-nil running mode during late script startup; the first unqueued player is initialized to zero. Actual boss damage, boss session membership, neutral KO, character state, castle, item, lobby, UI, score, original 21 Luau sources remain byte-identical. No Remote, DataStore, purchase, Roblox Publish or extra Game authority.

## Safety & validation
- #482 original 21 source paths unchanged; 2 new scripts = 23 in this private alternate Rojo mapping.
- GitHub Python negative/positive contract tests and a *native Luau* 13-transition policy harness in the own workflow. Successful source checks do not imply Roblox Studio gameplay success.
- If the original author repairs this gap first, pinned original blob tests fail closed and this overlay must be discarded.
- **OFF / rollback:** build the original `EGGRUMBLE_V3_STUDIO.project.json` rather than this alternate mapping; exclude both independent scripts. No original files are edited.
- **CLAIM status:** soft-not-granted; author #482 should approve only the source-selective behavior and resolve overlap. #220 alone may run authenticated CAS into official RC after latest-source rebase, SourceLock, same-HEAD native/Rojo, exact Place and ZIP evidence. Do not merge blindly.
- **Studio acceptance:** TEAM solo (1+15) and BR (2+14), kill StoneGiant, result, return to lobby, new mode, verify boss counter starts 0; verify no reset mid-round; disconnect/rejoin; Android15min/FPS; #420 ART/FUN; OWNER. All **NOT_TESTED** as of source delivery.
- **Status:** SOURCE candidate only; official RC integration 0, product/ART/FUN/MOBILE gates NO_GO.
