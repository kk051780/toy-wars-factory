# TRAP RAIDERS — final Windows Studio evidence acceptance gate

**Source-only, keyless QA helper. NOT a Roblox Studio result.**

OWNER-selected sole integrator: #220 lane RC01-B. Official frozen release source commit: `5dc6c958ea5549b1e859d6d250e6179e731181fb`. Rojo-built, *not runtime-tested*, official Place SHA-256: `f5c0b56cc7d3bbc2d92190dd95cb94f4dfa490f7949f2440655799c5893684a7`. Latest source-native S1 gameplay/independent QA passed on exact original Game; official project completion score currently **75/100**, with actual Roblox Studio, 2client, physical mobile, D07 boss and human first play all still **NOT_TESTED**.

## What the gate does

`validate_studio_receipt.py` takes a **future** OWNER-directed PC Codex evidence receipt and a local evidence folder. It rejects wrong source/Place/manifest hashes, overwritten newer owner PC backups, nonexistent or duplicate client IDs, missing mobile performance, missing or failed gameplay scenarios, missing honest evidence bytes, invalid evidence hashes/path traversal/symlinks, unsafe publication, and hidden/unsupported boss deferrals. It requires all 23 core scenarios, plus 3 D07 boss scenarios when enabled. This exact S1 current source has D07/D08 flags deliberately OFF, so **this gate will block an OFF-boss receipt until a separate authenticated OWNER scope decision and revised acceptance policy**. A syntactically valid GitHub comment link is NOT proof of OWNER consent.

The tool can check **local-file bytes and claims**, but it cannot cryptographically authenticate that Roblox Studio actually produced those logs. Do not use a synthetic passing unit-test fixture to certify real gameplay. The OWNER and release integrator must review raw real Studio logs/screenshots, identities, project imports and source evidence. Never publish based on this validator alone.

## One-batch OWNER Windows Codex process — NOT EXECUTED HERE

1. **Before import**, backup newest Windows PC Place, original source, HEAD, CHECKPOINT/RESUME, protect ownership and compute SHA256 of Place and backup checkpoint. Preserve PC current state (may differ from Chat-sourced RC).
2. Fetch **only** immutable official release commit `5dc6c958ea5549b1e859d6d250e6179e731181fb`, verify `releases/P0D_S1_KIDS_RC01/BUILD_MANIFEST.json` SHA256 `81cd35eb89593f6e84ccbc3d9dca1cadda4a06edfee488afc7375eaee6864311`, 32 recorded source bytes and Rojo project. The official built Place is available as [review-only Actions artifact](https://github.com/kk051780/toy-wars-factory/actions/runs/43109365409) (temporary; re-build from pinned source if expired).
3. **Only after OWNER directly instructs Windows Codex**, create a new isolated unpublished test Place, import full RC once, preserve other projects, start Studio. Capture real test 2 client sessions for **each** scenario ID from `example_not_tested.json`; test both mobile touch and desktop, actual client/server authority, capture and win loop, stale remote rejection, FPS, save/reopen, exit.
4. D07 boss must be tested with **real** warning-to-hit timing, damage receipt and removal before it counts; in current RC both boss flags are OFF. Do not enable blindly. If OWNER explicitly elects to defer the boss from initial S1, update #220's documented scope/criteria first; this version of gate remains blocked until that decision is genuinely reviewed and code/policy updated.
5. Save evidence **locally**, not on public GitHub. Do not include player real names, private local filesystem paths, credentials, recordings of identifiable children, or personal data in public comments. Use a sanitary machine receipt with `scenarios[].status` PASS/FAIL/NOT_TESTED, `scenarios[].evidence[]` {path, sha256, size} linked to local logs under `--evidence-root`, and actual session/backup data. Keep raw logs securely.
6. Run `python validate_studio_receipt.py receipt.json --evidence-root <local-evidence-folder>`. Exit 0 means **evidence-shape-and-byte PASS only**; exit 2 means BLOCKED. Even status PASS does **not** permit release. OWNER explicitly approves first Roblox publication separately.

## Current real status

- Chat code: Rojo full source 20/20 scripts; native original `Game.server.luau` 62 assertions and 5 deliberate bad mutations rejected, native boss modules in simulated services; no actual two-client Roblox Studio.
- Current source scoreboard 75/100 for PRELAUNCH, not probability of successfully launching.
- Current actual Studios receipt: **NOT CREATED / NOT_TESTED**. The JSON template deliberately fails the validator; no synthetic success is advertised.
- A new official RC commit or source modification requires a **fresh** pin and independent QA before this tool may accept results. Never change `main`, publish Roblox, introduce paid items/spend, touch P0-A/B/C protected controls or the five scheduled automations.

Canonical tracking: [#218](https://github.com/kk051780/toy-wars-factory/issues/218) / [#220](https://github.com/kk051780/toy-wars-factory/issues/220) / [#213](https://github.com/kk051780/toy-wars-factory/issues/213).
