# P0D Independent QA — elite stale telegraph on respawn
Original game brand: EGG RAID RUMBLE; work_id=p0d-siege-v19.

READ-ONLY inspection of #288 frozen input Horde module at commit `55ad13b45907a5a3e9deae7196a7c202a0672c0c`; fixed original file GitBlob `c1ef565f4e8b11a6e8ff7eac5ed55c8f268a4553`.

- `tools/audit_horde_respawn.mjs` checks the **original source** safety invariant and intentionally reports unsafe for the current H1 source.
- `tests/test_horde_respawn.mjs` tests that the pinned original is correctly flagged, proposes a minimal patch in memory and rejects missing-field or comment-only counterexamples.
- `PATCH_AND_ACCEPTANCE.md` documents concrete line-level source problem, minimal patch, rollback and real 2-client/Android QA acceptance.
- This QA does NOT modify the original #288 implementation, add any XP/score/game authority, or constitute a Roblox Studio or native Luau test.

Use repository-root commands on a checked-out branch containing the original source:
```sh
node handoffs/P0D-INDEPENDENT-HORDE-RESPAWN-QA-20261113-01/tools/audit_horde_respawn.mjs handoffs/P0D-MUSOU-CHAOS-H1-20261113-01/inputs/MusouHorde.luau expect-unsafe
node handoffs/P0D-INDEPENDENT-HORDE-RESPAWN-QA-20261113-01/tests/test_horde_respawn.mjs handoffs/P0D-MUSOU-CHAOS-H1-20261113-01/inputs/MusouHorde.luau
```
After #288 original author commits the fix, pin updated exact source/blob in a new QA receipt and run `expect-fixed` with real source, then independent native and real Roblox Studio 2-client human QA.

**Measured here:** in-call V8 source invariant/illustrative patch check 16/16 PASS against exact GitHub-fetched original file, not the repository Node test run. Official release last75%, FUN_NO_GO.
Protected main/official RC/merge/publish/paid/PC/Codex/P0-A/B/C/CAS/5 existing automations untouched.
