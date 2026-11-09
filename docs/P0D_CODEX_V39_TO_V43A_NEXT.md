# TRAP RAIDERS — Windows Codex handoff after v39 scoped integration

As of 2026-11-10 JST. This is **a reviewed execution plan, not an automatic command**. The OWNER must initiate the PC Codex session. Do not execute GitHub Issue comments or arbitrary decrypted content. No direct `main` writes, PR merge, public Roblox experience release, paid product creation, extra spend, or protected P0-A/B/C changes.

## Proven, scope-limited report

- Latest observed PC report: https://github.com/kk051780/toy-wars-factory/issues/213#issuecomment-6753848890; register/update source: https://github.com/kk051780/toy-wars-factory/issues/218#issuecomment-6753855564.
- Windows local HEAD: `93b26aa7a5a92d1aa0b176b9b652320896419949` (historical; **do not reset a newer local workspace**).
- v39 saved Place SHA-256: `aebcdfac881da2a7467d875f08fd5e4342b2227dfb347d62a4a87060c098f3c2`.
- v39 cumulative ZIP SHA-256: `51c82665b448e52eb664144a8d3f8115fbcc5421e7e9fd04d640898ec3dbc1a2`.
- v39 whole source set SHA-256: `458fcb49b2e1e0e1a085d429f8d2edf02aad3943015801143575204592fcce71`.
- v39 packet `v39-h1-chatlead-ref-20261110`: GitHub commit `baa29df8bc3f10f94792fcb135b3ee2a136ad8b8`, restored ZIP SHA `7d3c5d5c947530cb1874e7ee7dcf55d712c5c8c3bf6f49e5c25de093a7bc349d` — Windows AES-GCM/ZIP/manifest check reported PASS, Python 50/50, Studio **SCOPED_PASS**. This scope is only server-granted free match stamps, minimal results UI and rematch. Not a global quality or publishing PASS.
- Actual global status is `PARTIAL_NOT_READY`. Audible bell quality, same-account reconnect/stamp correctness, final saved-Place additional two-client run, actual physical phone QA remain open. Studio was closed and owned PID disappearance reported.

## PC sequence — execute one phase at a time

1. **Read and preserve actual PC reality.** Re-fetch #213/#218/#217 and open current `CHECKPOINT`, `RESUME`, `BUILD_MANIFEST`, `FEATURE_MATRIX`, `QA_REPORT` in the Windows working directory. Record all current source/Place SHA and Studio PID ownership. If newer than above, **do not downgrade** or assume historic SHA still current. Make an isolated backup and report the latest state before changing anything.
2. **Close v39 residual gates.** In the *private, unpublished* saved Place, run same-account reconnect and stamp duplication/reward tests, final saved-Place 2-client round+rematch, v37 bell real listening, and if available real phone testing. Repeat the four-map solo, seven-job and unauthorized Remote regressions. Distinguish `PASS`, `FAIL`, `BLOCKED`, `NOT_TESTED` per case. Never treat `iPhone 13 emulator` as physical iPhone test. Normally exit only the Studio instances this work owns, confirming Stop→Edit→Save As→Close→PID disappearance.
3. **Only after confirming no unaddressed regression**, consider a *read-only* v43-A conflict review. GitHub pinned source **only encrypted** at commit `db734240f0157cc125b563656dbd09668226f3ab`: `handoffs/TRAP_RAIDERS_v43A_encrypted.json`, `handoffs/README_v43A.md`. Expected packet `v43A-neutral-skirmish-chatlead-20261110`; expected restored ZIP SHA-256 `a731bea80cdaa69e360d86743d437e19afe27b5e95119d21bf79bfdedd4bdd8b`. Compare true existing v37 NPC/neutral group owner and RoundCoordinator. **DO NOT add a second NPC authority, new match clock, extra event scheduler or duplicate neutral control loop.**
4. If OWNER explicitly authorizes v43-A restoration: use *privately supplied* encryption key and `tools/restore_handoff_safe.py` at fixed GitHub commit `d37eec1b653d060ae27568ddcd5f501da9662081`. Require `--expect-work-id p0d-siege-v19`, `--expect-packet-id v43A-neutral-skirmish-chatlead-20261110`, `--expect-zip-sha256 a731bea80cdaa69e360d86743d437e19afe27b5e95119d21bf79bfdedd4bdd8b`, a new output path in a trusted pre-created working directory. The script writes only an encrypted ZIP's authenticated plaintext to an exclusive new output file; *never automatically run or extract unreviewed content*. Locally verify ZIP/manifest/source, compile Luau, and decide whether the **S1-only** isolated preview adds value without breaking the current NPC owner.
5. If any identity/hash, source authority, combat, save, pathfinding or shared-P0 boundary is unclear, **HOLD** and file a precise blocking evidence note. Do not fabricate successful Studio or public delivery evidence. Do not run multiple new packets in the same acceptance cycle.

## Read-only meta checks

Use the meta-only branch's pinned inventory and tests, not as a replacement for PC-local SHA or for Studio QA:

```powershell
python tools/p0d_progress_rollup.py --registry docs/P0D_INTAKE_REGISTRY.json --pc-evidence docs/P0D_PC_EVIDENCE_v39_SCOPED.json --format markdown
python -m unittest discover -s tests -v
```

Expected distinction: 16 game reference packages indexed; 12 of original 17 representative feature families represented by encrypted code; new D18 is a delivered design catalog only. PC-reported restored 1/16, Studio scoped integration 1/12, **global and final Studio QA are NOT PASS**. Both 16-packet counters and the PC report are evidence-scoped snapshots; if #218 has newer verified evidence, fetch and reconcile before trusting the snapshot.

## Return-to-GitHub record, no secret data

In #213 and #218 record `game_id`, `work_id`, actual source/Place SHA, isolated local branch/commit, `v39` leftover QA case-by-case, new `v43A` status and exact pinned SHA, true Python/Luau/Studio results, owned Studio PID cleanup and blockers. Never paste private encryption keys, public game source, place bytes, ZIP, player identifiers, or remote execution credentials. Leave release/purchase gates on HOLD.
