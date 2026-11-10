# S1 actual-source assembly plan — SNAPSHOT ONLY, NOT FINAL RC
P0D / TRAP_RAIDERS / p0d-siege-v19 / 2026-11-11 JST

**Read before use:** This plan and compatible assembler are pinned to the *actual* initial S1 source snapshot [35d7d0525388e885aac8281eff2315a59831e0cf](https://github.com/kk051780/toy-wars-factory/tree/35d7d0525388e885aac8281eff2315a59831e0cf/releases/P0D_S1_KIDS_RC01/). They do not establish Studio PASS or complete game release. The current source lacks original D07 boss, D08 canonical event, D11 neutral and other planned gameplay.

This standalone, isolated handoff branch descends from the immutable source game commit, so the checked-out branch contains the game's `releases/P0D_S1_KIDS_RC01/src`, `default.project.json`, `docs/OFFLINE_TEST_LOG.txt` plus these original handoff files. Do not run against the latest local Windows Place. Do not overwrite an existing output dir.

## Real assembly command (run in an isolated clone, not an active PC worktree)
```bash
python handoffs/P0D_S1_SOURCE_PLAN_SNAPSHOT_20261111_01/tools/chat_rc_assemble.py \
  --plan handoffs/P0D_S1_SOURCE_PLAN_SNAPSHOT_20261111_01/SOURCE_PLAN_S1_SNAPSHOT.json \
  --source-root releases/P0D_S1_KIDS_RC01 \
  --out /tmp/P0D_S1_SOURCE_SNAPSHOT_ASSEMBLED
```

The source snapshot plan lists 6 **real** source/project paths and one real offline-log SHA. The Python source assembler is a byte-for-byte copy of the author's compatible source at commit f5caa9876c6f3eba3ed41787794e6047c6ef8b70, not a new game implementation. The single genuine `Game.server.luau` unit declares `authorities=["round","event_chooser","damage"]`. `event_chooser` currently refers to the existing ***cosmetic alarm***. Do NOT treat that as already implementing D08 original! After D08 is integrated, #220 must re-assign actual authority and remove duplicate selectors.

## Handoff and gates
1. On a clean checkout of this handoff commit, run the command above. The tool may generate `CHAT_RC_RECEIPT.json` **only for this limited initial source snapshot**. The file is NOT included in this package and must not be represented as final assembled game QA.
2. If this exact full-source run fails, return explicit blocker evidence to this source/tool lane, not to PC Codex; do not falsify receipts.
3. The #220 sole-writer CHAT-INTEGRATOR takes or revises the plan for a true complete RC only after original D07/D08 and selected S1 gameplay have been integrated; pin that later RC's actual fresh SHA and manifest, not these historic paths.
4. Run independent static actual RC audit, dynamic real-play trace, then OWNER directly requests one final Windows Studio QA; no intermediate per-pack Codex.
5. Do not claim revenue proof from a source tree. Initial public launch and paid features need separate OWNER consent. No main write/merge/game publication, paid, P0-A/B/C CAS or 5 automation modifications.

The source owner reports 80/80 *previously run* offline source tests. This packet verified the frozen exact log content and source hashes, but did **not** rerun the 80 gameplay tests or execute the Python assembler against the actual checked-out S1 source. The copied Python assembler's own previous author-lane suite has been re-run as 34/34 PASS separately, which is not equivalent to actual S1 assembly.
