# TRAP RAIDERS S1 — D07/D08 + spatial warning + lobby recovery COMPOSED SOURCE

**2026-11-12 JST | `TRAP_RAIDERS` | `p0d-siege-v19` | `P0D-S1-KIDS-RC01`**

**Actual modified single Game.server source exists in `candidate/`, but D07/D08 source flags remain OFF, native Luau and Roblox Studio have NOT been tested, and OWNER has not approved public release.** This is a handoff packet for sole #220 CHAT-INTEGRATOR, not a release or a duplicate runtime deployed to the user's actual place.

## What is genuinely in this one source tree

This package composes the previously separated parts into a single **28-file public-source S1 Rojo game tree**, using exact original immutable source origins:

1. Base corrected real D07/D08 v40 canonical event/game and physical Gorogan callback/damage modules, including the two independent fixes to legitimate original Studio negative `Player.UserId` and D08 successful NORMAL/BOSS event retirement. Source commit `ff291d7a5e6dc53e841552d1abc3cbdf9a805f48`.
2. A server-authenticated STOMP attack-center packet via the ONE existing S1 Remote and a separate passive 8-segment local visual ring, with replay lock after END/TTL in the same epoch. This visual is NOT a source of damage, collision, coins or immunity.
3. EXACTLY the four unchanged `LobbyTeamRecovery` Game.server source replacements previously developed in original lobby author source `c609f622f7820efb2b7ee7270d30368644484f34`, with original planner Git blob `db1a369133550bc8356a4ee3ac22b97fcb1b46c4`. The original author source transformation `7693d47180c25c078debba9a5cb0ad294580601f` was independently executed on (a) the original initial game and proved byte-exact with the original author's patched Game, then (b) the prior corrected S1 game; its inverse restores the exact prior corrected S1 Game. Rebalancing occurs ONLY in LOBBY and COUNTDOWN refuses an empty team; the same single Game still owns round, egg, HP, event and damage.
4. Two proof bundles `lobby-evidence/` (8 exact Git blobs including the original 66 Python tests, original patch tool and official manifest) and `overlay-evidence/` (7 original reviewed D07/D08 source/docs/tests Git blobs, including 34-case Python test). Both are copied byte-exact into this source handoff so test reproduction does NOT depend on undocumented adjacent chat branches.
5. `SOURCE_PLAN_LOBBY.json` declares exactly **19 source/project units**, one unique Game server Script owning round+event+damage with a new explicit dependency on `LobbyTeamRecovery`. All 19 source SHAs pin the real immutable canonical candidate Git commit `421e01b9ea5fca5b009649521cc478402001dada`.
6. Source/game source manifest includes 28 unchanged-or-reviewed original files, six strict `P0D_PUBLIC_SOURCE_V1` keys with SHA256 file sizes. Manifest SHA256 `bda047cf81e386bbf3bab4f6fc1384236408a33230129c861e34f2c30b78af1b`.

## Actual CI evidence, never confuse offline source checks with Studio

- [GitHub Actions real Python composite 238-test run](https://github.com/kk051780/toy-wars-factory/actions/runs/43058146952): **SUCCESS**.
- 80/80 current game `unittest` cases using the new composite Game folder; 58/58 S1 original Game + D07/D08 source + local spatial visual + exact 4-hunk lobby merge; 66/66 the original lobby author's actual Python tests from frozen evidence; 34/34 the original independent D07/D08 correction author's actual Python tests.
- Actual official public-source verifier: `PUBLIC_SOURCE_SHA_VERIFIED_NOT_STUDIO` 28/28 SHA256 file checks.
- [Separate actual Python 19-source assembler CI](https://github.com/kk051780/toy-wars-factory/actions/runs/43058892465): **SUCCESS**, source/project bytes 19/19 exact SHA256 and actual Python-generated receipt SHA256 `4114d8b8206cbbc778fbd7ebacf025b01ba2fe3b7f3d24fe890dfc89819c0066` committed at `CHAT_RC_RECEIPT.json`; original formal `P0D_PUBLIC_SOURCE_V1` verifier 28/28 PASS in the SAME assembler job. Source plan checksum `6e9f4e690eaec9e190aefd3a9f41ce19be8f478a9ef5581ebc666edcac4be3c1`. Reproduce using `python3 handoffs/P0D_S1_SOURCE_PLAN_SNAPSHOT_20261111_01/tools/chat_rc_assemble.py --plan handoffs/P0D-S1-D07D08-SPATIAL-LOBBY-COMPOSITE-20261112-01/SOURCE_PLAN_LOBBY.json --source-root handoffs/P0D-S1-D07D08-SPATIAL-LOBBY-COMPOSITE-20261112-01/candidate --out /tmp/s1_d07d08_lobby_assemble`. This tool does NOT compile/run native Luau, Roblox physics, actual Place or mobile UI.

## Native acceptance gates still required before the real game is ready

- #220 **sole** integrated release writer must compare this packet to the LATEST unique RC source and any other already-selected game work (lobby, objective prompt context, first 60s coach, D15 traps, D11 neutral, collection, commercial LiveOps). DO NOT wholesale merge other author branches or overwrite independent modifications. Current original protected `rc/p0d-s1-kids-rc01` was not edited here.
- Both current server flags `CANONICAL_S1_ENABLED=false`, `D07_D08_RELEASE_REVIEW_APPROVED=false`. D07/D08 are **NOT enabled** at runtime. This remains so until owner review and successful native two-client Studio/real mobile QA.
- D08's WEATHER 10% choice has no S1 approved weather runtime; it must stay fail-closed rather than inventing gameplay. D07 physical lifetime 14 seconds vs event 17 seconds remains a safety/cleanup gate. The client STOMP ring will display less than 2s if the network is late and cannot be relied upon for server damage or fair reaction time. Long-running match serial >=1024 also needs native-verified handling. Whole-game independent QA is still pending the FINAL sole #220 RC SHA.
- Owner-controlled Windows Codex should run the **final consolidated** native Roblox Studio Play/Stop, two clients, mobile touch and normal exit only when source is near launch, not once per Chat-authored piece.
- No main or #220 RC changes, merge, Roblox live publication, added expenses, changes to other P0A/B/C CAS or any of the five existing ChatGPT automations were made by this lane.
