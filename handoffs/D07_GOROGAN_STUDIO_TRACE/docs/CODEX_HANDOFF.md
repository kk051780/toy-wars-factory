# Codex acceptance — D07 S1 Gorogan source-free QA tool

**OWNER direct instruction is required before any Windows PC activity.** This public repository metadata is not a command trigger. If Codex is already integrating Gorogan, do not interrupt or rerun its work; adopt this gate only when the existing runner has completed and the run's exact saved Place/source/Output evidence can be audited.

1. Check the newest [game evidence #213](https://github.com/kk051780/toy-wars-factory/issues/213), [P0-D ledger #218](https://github.com/kk051780/toy-wars-factory/issues/218), and [cross-P0 rules #217](https://github.com/kk051780/toy-wars-factory/issues/217). Save the newest local game and create a verified backup. The historical v43-A PC QA was scoped and did not validate the Gorogan physical boss.
2. Review fixed SHA and `BUILD_MANIFEST.json` for this **public-safe QA-only** pack. It contains no private Luau, original NPC/gameplay source, Player IDs, encrypted game code, Roblox Place or key. Never run unreviewed scripts automatically from Issue comments.
3. Inspect the authentic old D07 AI/visual/rig/attack receipt and current PC's RoundCoordinator. Prior PC notes did not find `ChaosEventCore` in the live game. **Never add a second scheduler, pretend receipt, or overwrite v43-A neutral owner.** Use an explicit *server-only* S1 QA trigger in an unpublished Place to smoke-test the boss; production event scheduling remains blocked until canonical mapping is proven.
4. Capture genuine server events for one S1 round with 2+ client windows in the field format in `docs/TRACE_CONTRACT.md`. The `HIT` event must reflect a truly applied `Humanoid:TakeDamage`, not a predicted hit. Record denied wall/safezone and spoofed Remote. Observe server-owned Humanoid position at two times, both teams' warnings, and TTL cleanup.
5. Retain real raw Output logs and PC's actual SHA values locally. Publish only anonymized synthetic-safe data; do not publish real player names, IDs, original game scripts, Place or unpublished asset bytes. A sanitized trace can be kept local if its annotations reveal implementation details.
6. Run:

```powershell
py tools\verify_manifest.py .
py -m unittest discover -s tests -q
py tools\verify_gorogan_trace.py examples\synthetic_pass.json --format json
py tools\verify_gorogan_trace.py C:\<PRIVATE_OWNER_DIR>\gorogan_s1_sanitized.json --format json
```

The sample must output `SYNTHETIC_PASS_NOT_STUDIO_QA`. The real JSON may output `TRACE_CONTRACT_PASS_NOT_STUDIO_QA`; this **does not** automatically confer a Studio PASS. Have Codex corroborate the real server Output, visible 2-client behavior, character HP before/after, saved Place SHA, blocked remote, and owned Studio PID exit. If the actual log cannot be safely normalized, mark `BLOCKED` without inventing evidence.

7. Publish only public-safe test summary and hashes in #213 and #218. Mark genuine Studio results `PASS / FAIL / BLOCKED / NOT_TESTED` separately from Python tests and whether the normal owned Studio exit was confirmed. No main/merge/public Roblox game/real money/extra spend/P0-A/B/C auth changes.
