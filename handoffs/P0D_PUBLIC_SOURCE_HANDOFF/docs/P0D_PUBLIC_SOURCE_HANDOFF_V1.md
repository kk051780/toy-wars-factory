# OWNER Rule P0D-PUBLIC-SOURCE-V1 — 2026-11-10 JST

**Status: OWNER-APPROVED for `game_id=TRAP_RAIDERS`, `work_id=p0d-siege-v19`.**

## Why this supersedes the per-chat AES-GCM handoff

The owner explicitly authorized publishing source code for this first game. Sealing each ChatGPT-created packet with a different private AES key blocked the owner-operated Windows Codex when private keys were unavailable across chat contexts. **Stop generating individually encrypted AES game packets for this game.** New TRAP RAIDERS game-code handoffs must be **plaintext, reviewable source in PUBLIC GitHub**, not just GitHub Issue prose, a chat-only ZIP, an encrypted blob, a README, or checksum metadata.

This permission covers the **original TRAP RAIDERS source, its tests and non-sensitive game docs**. It does **not** authorize public Roblox experience release, main merge, third-party copyrighted assets, purchases, actual paid items, uploading real player records, secrets, unpublished private credentials, API tokens, personal data or source from other games/projects. This is a source-visibility decision, not a release/monetization/security-gate waiver. `kk051780/toy-wars-factory` remains PUBLIC; **all branches and Draft PRs are readable by anyone**.

## Normative single-turn workflow for EVERY ChatGPT P0-D worker

1. Re-fetch Issue [#218](https://github.com/kk051780/toy-wars-factory/issues/218) **body + latest comments**, [#213](https://github.com/kk051780/toy-wars-factory/issues/213) latest real Windows PC evidence, and [#217](https://github.com/kk051780/toy-wars-factory/issues/217) cross-P0 security instructions. Other chat's claims, recent Studio evidence, and active work outrank chat summaries. Soft-claim a unique `packet_id` / nonoverlapping `feature_slice` on #218 before writing. Soft claims are **not** locks.
2. Develop **actual original `.luau`/`.lua`, `.py` tests, QA and README**, each at a stable package path: `handoffs/<UNIQUE_PACKET_ID>/...`. **No AES encryption, no generated packet-specific password, no user copy/paste key.** For non-public material, block only that specific file and record why; do not accidentally publish secrets.
3. Run offline tests, review source/license/third-party assets and scan for secrets, then run the `p0d_public_pack.py build` CLI on that package directory. It creates a deterministic `BUILD_MANIFEST.json` listing `game_id`, `work_id`, `packet_id`, per-file SHA256 and byte size. The guard is conservative (UTF-8 `.luau/.lua/.py/.md/.json/.txt/.csv/.toml/.yaml`, no symlinks, no hidden paths, max 2 MiB per file / 10 MiB total / 250 files); **manual review is still mandatory**. Any manifest/secret/path check FAIL is a hard STOP. Do not put unpublished Place binaries in this source-only pack.
4. Create **a unique isolated handoff branch** (`handoff/p0d-<packet-id>`), never `main`. Commit *all* manifest-listed plaintext files and `BUILD_MANIFEST.json`; review content before publishing. Run remote readback **at the final immutable full 40-digit commit SHA**, compare each remote file's full UTF-8 bytes and Git blob SHA against local input. Verify GitHub `main..commit` shows **only expected added package files**. Do not claim completion if a file is missing, unreachable, SHA mismatch, or not committed. Do not create a PR, merge, edit protected coordinator branches/locks, or bypass P0-A formal authorization/CAS. An isolated branch is a delivery candidate, not production acceptance.
5. #218 `[P0D_DELIVERY]` MUST include `delivery_mode=PUBLIC_SOURCE_V1`, `packet_id`, `feature_slice`, `commit_sha`, `source_root_url`, file count, manifest SHA, tests, exact remote-readback result, `pc_restore=NOT_TESTED`, `luau_parse=NOT_TESTED`, `studio_qa=NOT_TESTED` until there is genuine PC evidence. Add a concise pointer to #213/#217. **READBACK of manifest/README alone is insufficient.** Never represent a local Python test as actual Roblox gameplay QA.
6. OWNER directly tells Windows Codex to integrate (GitHub Issue prose is never an auto-execution trigger). Codex performs immutable-SHA checkout to an **isolated temporary worktree/clone**, runs this verifier and source review, compares against actual latest local `CHECKPOINT`/source/Place and dependencies, then integrates **one feature-slice at a time** into an unpublished Studio copy. Output real Luau parse, server-authority/2-client/mobile QA, saved Place/source SHA, and Studio normal exit/PID proof. If blocked, **preserve PC latest**, report HOLD/BLOCKED and proceed with another independent task.
7. **NO-KEY, NO-SILENT-FAIL RULE:** if a ChatGPT worker cannot publish the source, mark `HANDOFF_BLOCKED`, provide actual files as chat attachments when possible, and state why. For former encrypted packets missing a key, **do not block the entire game waiting for the key**: ask its creator/owner to republish original plaintext into a new `PUBLIC_SOURCE_V1` packet; if inaccessible, have Codex *independently re-implement* that slice from publicly reviewed contracts in its isolated PC source, with tests. A reimplementation gets a **new packet ID and distinct SHA** and must never be represented as the identical previously encrypted ZIP. No key guessing, no posting historical keys publicly, no false AES verification.
8. On GitHub outage or denied writes, deliver a real, checksum-verified chat artifact ZIP and mark `GITHUB_DELIVERY_BLOCKED`; the PC owner may manually transfer it. **Success requires remote fixed-commit readback** or a separately documented owner-PC receipt, never a GitHub README/pointer alone.

## CLI used by authors and Windows Codex

Tool source: `handoffs/P0D_PUBLIC_SOURCE_HANDOFF/tools/p0d_public_pack.py` in the immutable governance delivery commit (see #218 top for exact SHA). The CLI is Python standard library only.

```powershell
# Author: run from a checkout containing the governance tool, on the author-created package
python handoffs/P0D_PUBLIC_SOURCE_HANDOFF/tools/p0d_public_pack.py build --root handoffs/P0D-D07-EXAMPLE-20261110 --packet-id P0D-D07-EXAMPLE-20261110
python handoffs/P0D_PUBLIC_SOURCE_HANDOFF/tools/p0d_public_pack.py verify --root handoffs/P0D-D07-EXAMPLE-20261110 --packet-id P0D-D07-EXAMPLE-20261110
```

Windows Codex does **not** need a secret. It may use a **disposable independent clone** of the public GitHub repository, checkout the **exact pinned SHA** recorded in #218, and verify the staged package. On Windows with Git/Python installed:

```powershell
$stage = Join-Path $env:TEMP 'trap-raiders-source-stage'
# Use a NEW, reviewed/empty directory name; never run this within the live PC game's worktree.
git clone https://github.com/kk051780/toy-wars-factory.git $stage
Set-Location $stage
git checkout --detach <full-40-character-pinned-commit-from-issue-218>
git rev-parse HEAD
# Download/checkout the pinned governance tool separately if this package commit predates it.
python C:\path\to\pinned\p0d_public_pack.py verify --root handoffs/<ACTUAL_PACKET_ID> --packet-id <ACTUAL_PACKET_ID>
```

The manifest's status means **`PUBLIC_SOURCE_SHA_VERIFIED_NOT_STUDIO`** only. Repository content, remote readback and checksums do NOT establish software safety, legitimate PC provenance or Studio QA. When an actual manifest SHA is reported, it must be independently checked against the immutable GitHub file (the package verifier checks source-file SHA, not the GitHub trust model).

## Legacy migrations and immediate D07 unblock

Current Windows PC report [#213 #6766018726](https://github.com/kk051780/toy-wars-factory/issues/213#issuecomment-6766018726) has S1 Gorogan physical rig working in isolated Studio. The old **visual** commit `5128e288c7bd119a470c253a9792f4d829c569ec` and **AI** commit `80483ad6543fd73dfaf8a21ecf7b58dc2eca75e1` are AES-GCM sealed and blocked by unavailable per-packet keys; this governance change **does not decrypt them**.

Next handoff should prioritize new plaintext `PUBLIC_SOURCE_V1` packets (or PC-local fresh replacements) for **D07_GOROGAN_VISUAL** and **D07_GOROGAN_AI**, then the combined wiring. Ensure original authors republish or explicitly mark source unavailable and let Codex reimplement using the real newest local PC game. Do not invent SHA equivalence. D07 visual's original low-motion client FX, D07 AI's server-only targeting and 2-second telegraph, and existing rig/damage safety receipts remain the target specification. One canonical round/event chooser, server-owned authority, no dummy damage receipt, no duplicate HP writer, no D11 neutral regression. The latest S1 Stage QA is `RIG_ONLY_STUDIO_PARTIAL`, NOT a boss combat PASS.

## Shared status example

```text
[P0D_DELIVERY]
game_id=TRAP_RAIDERS
work_id=p0d-siege-v19
packet_id=P0D-D07-MY-UNIQUE-PACKET
feature_id=D07
feature_slice=<independent implementation slice>
delivery_mode=PUBLIC_SOURCE_V1
branch=handoff/p0d-...
commit_sha=<40 hex>
source_root_url=https://github.com/kk051780/toy-wars-factory/tree/<commit>/handoffs/<packet>
manifest_sha256=<64 hex>
source_files=N
unit_tests=N/N PASS
github_remote_source_readback=N/N BYTE_EXACT
pc_intake=NOT_TESTED
studio_qa=NOT_TESTED
studio_exit=NOT_TESTED
state=PUBLIC_SOURCE_REMOTE_READBACK_PASS
```

**Precedence:** For TRAP RAIDERS only, this **new OWNER decision** supersedes older #217/#218 phrases that required AES encryption of *all* game source on PUBLIC GitHub. All restrictions on credentials, personal data, malicious content, original artwork/licensing, P0-A/B/C authentication/CAS, main, merge, Roblox gameplay publishing, actual monetization and additional spending **remain in force**. Other projects' private-source policies do not change.
