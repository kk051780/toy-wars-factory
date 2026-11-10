# P0-D S1 CHAT independent release-source & project-wiring gate

`game_id=TRAP_RAIDERS` · `work_id=p0d-siege-v19` · packet `P0D-S1-RC-SOURCE-WIRING-VERIFIER-20261111-01`

**Purpose.** Read-only, self-contained, stdlib Python independent check for the one Chat-integrated S1 game RC. It verifies that *actual* `src/`, `assets/`, `default.project.json`, `CHAT_RC_RECEIPT.json` and the *exact plan file used for assembly* agree byte-for-byte; every Rojo `$path` exists, maps to a real script/asset, and every `.luau`/`.lua` source is in the project tree. It blocks bad server/client placement, duplicate canonical authority declarations, symlinks, case-colliding filenames/folders, plan tamper, untracked code and deceptive Studio/publication PASS claims.

## Usage

Requires no keys, packages, network, or Windows. **Run only after** the #220 CHAT-INTEGRATOR produces the actual RC directory and preserves the original source-plan JSON outside the project:

```bash
python3 tools/verify_rc_wiring.py \
  --rc /path/to/P0D-S1-KIDS-RC01-assembled \
  --plan /path/to/P0D_CHAT_RELEASE_PLAN_V1.json
python3 -m unittest discover -s tests -v
```

The first command prints a JSON receipt and returns exit code 0 only on the narrowly scoped artifact/wiring PASS; returns 2 with a defect otherwise. It **never edits the RC**, runs game code, launches Studio or performs network requests. If the actual RC or plan has not been delivered, classify integration `RC_PENDING`; **synthetic test success is NOT release readiness**.

## Ownership / integration contract

- #220 `P0D-CHAT-INTEGRATOR-S1-RC01-A` alone writes `rc/p0d-s1-kids-rc01` and assembles game runtime, source plan and `CHAT_RC_RECEIPT.json`.
- This packet **never changes game logic or an RC branch**. It only audits exact source artifacts and Rojo file placement. Source schema follows the published Chat-first V2 assembler (`P0D_CHAT_RELEASE_PLAN_V1` and `P0D_CHAT_SOURCE_ASSEMBLY_RECEIPT_V1`).
- A **separate** independently claimed S1 QA lane owns multiplayer/egg/castle/combat/replay/boss-warning *scenario* QA, not this packet. The owners must combine both QA receipts before any `CHAT_RC_READY` decision.
- The actual S1 gameplay and all native Luau parser, Studio 2client/mobile, latency, physics, DataStore, asset loading and Studio normal-exit tests are **NOT_TESTED** by this verifier. They remain required for owner-directed final Windows QA.
- Does not certify compliance with copyright/security policy for source *contents*. Exact hashes and mapping cannot establish game correctness; `PASS_SOURCE_WIRING_ONLY` must never be relabeled `STUDIO_PASS`.

## Safety

Public TRAP_RAIDERS plaintext source permission only. No main changes, PR merges, production Roblox publication, purchases/spending or P0-A/B/C protected controls/Automations.

## Added V1.1: pre-RC real-source snapshot gate (2026-11-11)

The sole integration writer currently publishes the **in-progress** source under
`releases/P0D_S1_KIDS_RC01/`, with `BUILD_MANIFEST.json` in the
`P0D_PUBLIC_SOURCE_V1` schema rather than the **final**
`P0D_CHAT_RELEASE_PLAN_V1` + `CHAT_RC_RECEIPT.json` pair. To avoid waiting
for the RC, run an *additional narrowly scoped* independent check now:

```bash
python3 tools/verify_source_snapshot.py \
  --source-root /path/to/repo/releases/P0D_S1_KIDS_RC01
```

This checks actual game source bytes/SHA256/size against the project's current
manifest; Rojo `$path` mapping and script side; missing, untracked, symlink,
case-collision and false status claims. An output of
`PASS_SOURCE_SNAPSHOT_ONLY__NOT_FINAL_RC` is **not** the independent final
RC acceptance, is **not** gameplay scenario verification, and does **not**
authorize Codex, Studio PASS, or Roblox publication. The strict final-RC
checker above stays unchanged and must run on the assembled RC with its exact
source plan after the integration writer has finished.

Both tools are read-only and work with stdlib Python. The snapshot tool is a
separate new acceptance target for early source hygiene, not a way to bypass
the Chat-first V2 assembly and true runtime tests.

## V1.2 independent hardening: plural canonical authorities and duplicate Rojo mount

The single-writer integrator may select the separate, optional compatible release assembler
from commit `f5caa9876c6f3eba3ed41787794e6047c6ef8b70`.
That assembler permits ONE actual `Game.server.luau` unit to declare
`"authorities": ["round", "event_chooser", "damage"]`, without creating fake
second authorities. This independent gate now validates the full source-plan roles,
checks the assembler's attested `source_units[].authorities` against each unit,
rejects ambiguous singular/plural fields, duplicate/unknown roles, stale or forged
receipts, and rejects any executable source mounted under more than one Rojo
`$path` (which would load the same script twice).

Original V2 singular `authority` files and legacy V2 receipts remain supported.
The separate compatible assembler is an optional author-owned SOURCE candidate;
these offline tests do not prove the fork's native Roblox behavior or certify
that the game has truly only one runtime event/round/damage writer.

## V1.3 — Strict original PUBLIC_SOURCE_V1 compatibility and real S1 defect

`verify_source_snapshot.py` now checks **the official handoff schema**, not merely
source-byte consistency. It enforces exactly six canonical root keys, including
`packet_id`, the exact canonical JSON encoding and sorted file entries, exact
`path`/`size`/`sha256` per file, the original 250-file / 2 MiB per file / 10 MiB
package limits, UTF-8 text, allowlisted public-source extensions, hidden and
credential-style names, and high-confidence secret patterns. Its old acceptance
condition was too permissive: it accepted the S1 initial source manifest at
`35d7d0525388e885aac8281eff2315a59831e0cf` despite an additional root
`status` key that the official `p0d_public_pack.py verify` rejects. That finding
is documented in `docs/ACTUAL_S1_SCHEMA_FINDING.md`.

The **old** result "15/15 files SHA match + 3/3 Rojo paths" remains a valid
statement about those subchecks, **but the full early snapshot gate now must
return `FAIL_SOURCE_SNAPSHOT` / `PUBLIC_SOURCE_MANIFEST_SCHEMA_MISMATCH`** until
#220's sole integration author regenerates the canonical manifest. No direct
patch is made to another chat's RC branch.

The in-progress S1 is not the final RC. Separate `verify_rc_wiring.py` still
requires the final original `P0D_CHAT_RELEASE_PLAN_V1` and authentic
`CHAT_RC_RECEIPT.json`. Neither a manifest fix nor the synthetic QA test suite
proves boss integration, native Luau compilation, Roblox multiplayer, Studio,
first-player retention or OWNER release approval.
