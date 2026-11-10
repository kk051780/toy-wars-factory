# Offline P0-D chat assembly plan (`P0D_CHAT_RELEASE_PLAN_V1`)

This is a **local build gate**, not a release certificate. To invoke:

```bash
python -m unittest discover -s tests -v
python tools/chat_rc_assemble.py --plan path/to/release_plan.json --source-root path/to/verified_keyless_source_staging --out path/to/NEW_never_existing_directory
```

The plan is JSON. Required top-level identity: `format`, `game_id`, `work_id`, `release_id`, `phase="CHAT_BUILD_READY"`, `studio_status="NOT_TESTED"`, `publish_approved=false`, `units`, `capabilities`, `offline_checks`. `units` are a list of verified actual individual files of this form:

```json
{
  "unit_id": "example_round_core",
  "source_commit": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "source_path": "verified_packet/src/RealRoundCore.luau",
  "target_path": "src/server/RealRoundCore.luau",
  "sha256": "<the actual 64-character SHA-256 of that source file>",
  "authority": "round",
  "variant_family": "d01_round_core",
  "variant_kind": "original",
  "depends_on": []
}
```

The above SHA values are **illustrative placeholders**, not a real runnable release plan. Each source must be staged from its real immutable GitHub source commit, with manifest/receipt verified separately, and `sha256` calculated from actual byte content. The CLI never retrieves from GitHub, launches Codex, or edits production. Use `target_path="default.project.json"` for a real Roblox Studio/Rojo object-tree mapping. Unity of subsystem responsibility must be verified by source review as well as by the mechanical tool. Assets must be real, original, or reproducibly authored; no unavailable marketplace dependencies unless explicitly documented as an engine-test blocker.

Allowed singular `authority` values are `round`, `event_chooser`, `damage`, `persistence`, `reward`, `matchmaker`, or `none`. The same non-none authority may be assigned to exactly one unit per candidate; multiple source files can reference that authority without themselves claiming to own it. `variant_family` must be unique among selected units where applicable, with `variant_kind` original/cleanroom/new. Choose the original or fallback **once**, never both. Any graph cycle or missing dependency is a hard fail. The build rejects unpinned commits, modified/missing files, symlinks/path traversal, overlapping output filenames, forged Studio PASS or publish authorization.

Minimum S1 declaration names (each requires **real authored implementation and independent source inspection**, not merely a checkmark): `match_lifecycle`, `team_spawn`, `input_mobile`, `capture_objective`, `combat_damage`, `victory_defeat`, `client_hud`, `map_art`, `entrypoint`. Each offline evidence item has `test`, `status=PASS`, `log_path` and `sha256` verified from actual log bytes. The gate checks only the presence/integrity of claims and files — **it cannot prove functionality, completed artwork, Roblox networking or suitability to publish**.

The assembler returns a new isolated source directory with all selected bytes and final `CHAT_RC_RECEIPT.json` listing immutable source identities. A second independent reviewer must compare it against the acceptance matrix. The PC is invoked only for the complete candidate or a clearly declared near-final integrated milestone, not per feature.
