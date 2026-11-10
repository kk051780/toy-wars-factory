# P0-D OWNER policy V2 — CHAT-FIRST COMPLETE BUILD, CODEX FINAL-ONLY

**Effective:** 2026-11-11 JST · **Game:** TRAP_RAIDERS · **work_id:** p0d-siege-v19  
**Overrides:** The older P0-D rule to send each small packet to Windows Codex for immediate Studio acceptance.  
**Does not override:** PUBLIC_SOURCE_V1, owner-only production release, no spending, no unapproved merge or main write, P0-A/B/C authentication/CAS/independent review, normal Studio cleanup, and the five existing Automations. Other P0 tracks remain as previously governed.

## Decision

**ChatGPT parallel workers own development through a reproducibly assembled, near-final *whole-game* release candidate.** They produce actual Luau, authored gameplay/assets, Roblox project mapping, test source, design/contracts, and offline QA. A separate **CHAT-INTEGRATOR** owns a single isolated `rc/` build plan and composes all approved pinned sources into one reproducible, inspectable, complete project without accessing Windows. An independent **CHAT-QA** checks integration, mocks/contracts and gameplay rules, records gaps, and returns defects to the original feature owners. **Codex is not a per-packet gate and consumes no quota for routine feature integration.**

**Windows Codex role:** On the OWNER's direct instruction, once the CHAT-INTEGRATOR declares a near-final **release candidate** with a real self-contained source/project and full offline receipt, use the PC once per RC revision to preserve latest PC checkpoint and Place, import the complete candidate, perform native Luau/Roblox Studio 2+ client/mobile/normal exit QA, record actual failures, and return a defect list. If needed ChatGPT fixes the integrated source and submits an RC delta for the next *bounded final* PC session. This is not a promise that one attempt is guaranteed to pass.

**Exception:** If an untestable engine/API capability is a hard blocker for the entire product and waiting would multiply rework, OWNER may request *one focused smoke test* from Codex (especially DataStore, multi-client authority, physics/network ownership, asset loading, mobile performance). This is not an invitation to resume per-feature PC acceptance.

## What the recent evidence proves — and does not

- Windows original-source readback passed **21/21 exact sources and 321 manifest files**; separate new D16 originals have since been published. This validates transport and source integrity, not user-facing gameplay.
- Previous S1 D07 Studio work had native parsing, require smoke, actual boss movement, two-client attack, mobile-emulator scoped success and normal Studio exit, **but was only PARTIAL**, including unequal warning duration (~0.93s vs ~1.96s), inconsistent negative test, cleanup timing. `PARTIAL_NOT_READY` remains true. See #213 `6776360480` and #218 `6776369402`.
- Most Python unit / SHA tests passing is good evidence that **routine per-packet PC checks are low-yield**. It cannot prove Luau engine syntax, genuine 2client correctness, performance, saving, or Roblox production readiness. Those remain final gates.

## Operating lanes (exclusive branch ownership)

| Lane | Product | Write scope | Output | Can call Codex? |
|---|---|---|---|---|
| CHAT-PLAN | gameplay canon, stage/balance, child usability, minimum release scope | own design branch/packet | locked minimum-first playable spec, acceptance matrix | No |
| CHAT-FEATURE-N | parallel feature assets, Luau, tests, source contracts | *one* unique feature packet/branch | immutable full-source SHA and manifest | No |
| CHAT-INTEGRATOR | **single designated release writer**; cross-pack API adapters, project mapping, selection of one source per system | only unique `rc/<release_id>` or isolated handoff branch | full source tree, entrypoint, project mapping, lockfile, deterministic build ZIP and receipts | No |
| CHAT-QA | independent negative tests, balance simulations, source contract and regression audit | separate QA branch only | objective PASS/FAIL and issue list | No |
| WINDOWS-CODEX | latest real PC/Place backup, complete RC import, true Studio multiplayer/mobile/shutdown and logs | owner-approved isolated local workspace only | PASS/FAIL with measured evidence, no automatic publish | **Only direct OWNER request at near-final RC** |

Different feature chats may work concurrently on separate paths without a global single-writer lock; only the integration-owned candidate tree requires serialization/one writer. Reading someone else's latest work is encouraged; changing that person's branch or their claim is prohibited.

## Shared artifact contract for every feature chat

1. Always read **Issue #218 opening override + latest comments**, the current `rc/` release plan, #213 actual PC evidence, and #217 protected cross-P0 controls.
2. Declare a `SOFT_CLAIM`: exact `game_id`, `work_id`, `feature_slice`, `author_lane`, input source SHA, own output path, compatible interface version, and dependencies. Resolve any overlap before writing.
3. Build **actual source**. At minimum supply editable Luau (`.luau`), Python oracle/negative/contract tests where relevant, source-reachable assets or deterministic 3D generators, README, QA with limitations, and `BUILD_MANIFEST.json` with SHA/size.
4. Publish to a **unique public isolated branch** only for OWNER-approved TRAP_RAIDERS; verify immutable commit 40-hex SHA and **all** remote file bytes/hash. No private keys, credentials, user data, unauthorized third-party assets, or other games.
5. Notify the integration owner with entrypoint/export shape, callbacks, ownership rules, side effects, `ServerScriptService`/`ReplicatedStorage`/client placement, time units, replication boundaries, alternate variant family and exact source commit. No blanket “integration done” or Studio PASS.
6. The integration owner either selects the packet, marks `NOT_SELECTED` with a reason, or returns an actionable contract defect. **Do not queue an individual Codex acceptance**.

## Release workflow and statuses

`DESIGN_LOCKED` → `CHAT_FEATURES_DELIVERED` → `CHAT_ASSEMBLED` → `CHAT_QA_PASS` → `CHAT_RC_READY` → `OWNER_DIRECT_WINDOWS_FINAL_QA` → (`RC_DEFECTS_TO_CHAT` → `CHAT_RC_READY`) → `OWNER_RELEASE_APPROVAL` → `RELEASED`.

The independent `CHAT_RC_READY` build must contain (a) the *single* chosen real runtime modules (not a pile of independent demos), (b) a loadable project map and actual map/asset source, (c) a canonical event chooser and round/damage/reward authority, (d) explicit end-to-end placement/wiring and module requirements, (e) target core game loop and mobile controls, (f) a tested offline build and independent QA receipt, and (g) a defect matrix including engine-only unknowns. A generic packet ZIP, code snippets, a mock-only demo, or a static `PASS` statement alone is **not** a complete game.

**Release scope to reach children sooner:** Target a genuinely playable *S1 first experience* before polishing all 648 collectible concepts. S1 requirements: spawn / teams, mobile input, objective or egg capture, defender response/combat, HP & win/lose and reset, functioning map and UI, multiplayer persistence strategy and safe failure behavior. Keep S2–S4 and extra cosmetic modes in clearly selected/disabled development tracks unless approved as an explicit first-version requirement. A scoped private test release still needs OWNER permission and native Studio acceptance; code-on-GitHub does not automatically publish a Roblox place.

## Acceptance evidence and runtime boundary

- **Offline chat:** source bytes, SHA/manifest, package precedence (original vs fallback one only), one RNG/event chooser, one damage/XP/entitlement authority, API/time/identity compatibility, cross-module test, scenario/mocks, build repeatability, script/asset layout, independent QA; optionally native Luau CLI if actually available, clearly label tool/version.
- **Final Windows:** reconcile with latest actual PC HEAD and saved Place *without clobbering newer local changes*; native Luau parse/require, real Roblox multi-client (hostile remote/dup attempts, boss warning/damage/escape, round change, game over/restart, DataStore failure), touch + mobile FPS/camera/HUD, cold reopen, Studio normal exit and owned PID, QA trace/Place SHA.
- **Owner sign-off:** only after true final measured QA with launch criteria; no autonomous merge/main write, Roblox production publish, products/paid/spend. A PC failure returns to Chat, **not** to per-feature Codex loops.

## Commands and artifacts

`tools/chat_rc_assemble.py` accepts a locally staged pinned-source directory and a `P0D_CHAT_RELEASE_PLAN_V1` lockfile to generate an **isolated, byte-verified source tree** and a `CHAT_RC_RECEIPT.json`. It requires nine S1 capability declarations, singleton round/event/damage authority, pinned commit/hash for every source file, no source-path traversal/symlinks, no duplicate destinations, no competing original/cleanroom variants, a valid `default.project.json`, and hashed offline QA logs. It **will not** set `STUDIO_PASS`, publish, or change PC/`main`. Read `docs/RC_PLAN_SCHEMA.md` and `docs/CODEX_FINAL_HANDOFF.md` before use.

## No more quota-triggered stalls

Chat feature production does not stop while Codex hits daily/weekly limits. The integration lane maintains a **single fixed release manifest + dependency graph**, a canonical open-defect list and all source hashes in GitHub; capped chats hand over their code via the shared ledger and fixed commits. New ChatGPT conversations can pick up immediately. Conversely, ChatGPT quotas and context limits do still exist; the process reduces dependence on Codex but does not eliminate all usage limits.
