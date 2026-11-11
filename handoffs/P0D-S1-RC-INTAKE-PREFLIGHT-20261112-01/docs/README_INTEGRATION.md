# P0-D S1 RC intake: source-diff preflight (no integration)

This is a **read-only** comparison of the sole official RC author's frozen first project (`35d7d0525388e885aac8281eff2315a59831e0cf`, root `releases/P0D_S1_KIDS_RC01`) against a later source-built S1 candidate with boss/event, spatial warning, team deadlock recovery and first 60-second coach (`b103389e2089f9ff5a08984fe2f8f6f02aa8b1bc`, root `handoffs/P0D-S1-FTUE-ON-D07D08-SPATIAL-LOBBY-20261112-01/candidate`). These are **two pinned Git sources**, not evidence that the user's real Windows Place is identical or Studio-tested.

Observed from GitHub immutable `BUILD_MANIFEST.json` in each source (NOT from guessing filename counts): 15 old entries and 30 candidate entries. There are **11 unchanged exact SHA-256+size entries, 4 changed entries, 15 new entries, and 0 deleted entries.** Full path lists and SHA pins are in `OBSERVED_DIFF.json`. The 4 modified files are `default.project.json`, `src/client/HUD.client.luau`, `src/server/Game.server.luau`, and `tests/test_static_source.py`. The original RC manifest itself contains an illegal extra root `status` field (7 total). The candidate has the exact 6-field canonical PUBLIC_SOURCE_V1 layout. Never copy that old status field into an upgraded manifest.

`tools/rc_intake_preflight.py` only reads JSON files and prints classification to stdout. No network, no git, no writes. It accepts *legacy* seventh-key `status` only in the old input, fails closed on candidate extra keys, deleted files, duplicate/suspicious paths, invalid SHA/digests/sizes, missing source authorization or source drift from the observed fingerprint. **Passing does NOT establish candidate source byte integrity or actual Roblox gameplay.** The other independent QA lane already reported actual 30/30 raw source hash verification on this frozen candidate; only it/sole #220 may declare the corresponding QA gate.

To reproduce after exporting the two immutable manifest files to a local scratch directory:

```sh
python tools/rc_intake_preflight.py --rc /scratch/rc_BUILD_MANIFEST.json --candidate /scratch/ftue_BUILD_MANIFEST.json --expected docs/OBSERVED_DIFF.json
python -m unittest discover -s tests -p 'test_*.py' -v
```

## Sole-integrator next actions (#220 only)
1. Re-read latest #218/#220 comments. The **exclusive RC write claim already belongs to `P0D-CHAT-INTEGRATOR-S1-RC01-A`** (#220 comment `6778052967`); this independent lane must never write or merge `rc/p0d-s1-kids-rc01`.
2. Compare actual RC Git ref **again** before applying anything; if it is not the expected baseline, stop and re-diff.
3. Adopt a complete frozen source candidate atomically in the integrator's own RC branch, never apply an older Game over newer Game. The selected candidate must retain exactly one round/event/damage authority, proper Rojo client paths, authentic D07/D08 corrections, and source-pinned lobby and FTUE. Rebuild official source receipts/lockfile and exact 6-field manifest. D07/D08 explicit activation flags remain false absent owner approval.
4. Run original Python regressions, candidate full assembly, independent RC source QA and native Luau parser against **the actual updated official RC**, not just standalone handoff candidates.
5. After final Chat RC is complete, request one OWNER-directed isolated Windows Roblox Studio two-client/mobile Play/Stop QA. Do not release/publish, enable payments or merge main without separate explicit OWNER authorization.
6. **Publish `game_release_progress_pct` and `score_breakdown` under #220's actual 100-point rubric**, with proof per category and zero for missing official acceptance. This independent diff packet does not assert an overall completion percentage. The verified source coverage (30/30) is a different metric and must not be marketed as 100% game completion.
