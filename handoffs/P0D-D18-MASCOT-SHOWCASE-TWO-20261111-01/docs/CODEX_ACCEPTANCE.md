# Windows Codex: source intake / optional isolated Studio test (OWNER action only)

## Before any work
1. Re-read issue #218 top + latest comments, actual #213 OWNER PC S1 safety QA, and #217 authorization. Latest real Windows PC HEAD/Source/Place/CHECKPOINT/RESUME outranks this independent prototype. If current D07 boss safety QA is still incomplete, **do not interrupt it**.
2. Fetch the `packet_id` at its full immutable SHA, verify **all manifest-listed file bytes** plus `BUILD_MANIFEST.json` with `p0d_public_pack.py verify`; compare GitHub commit `main..commit` scope. Never merge, publish, add paid items, spend, edit others' branches, or bypass P0-A CAS/independent review. Keep the downloaded source in a new staging worktree outside game PC source.
3. Preserve real newest Place + scripts + manifest SHA/backups. If you cannot prove your test Studio is isolated from the OWNER's other open Studio instances, **HOLD**; do not operate someone else's session.

## Optional dry-run in a separate unpublished Place
1. Create new `ServerScriptService/D18PreviewIsolated` folder. Insert sibling `ModuleScript` instances `MascotPreviewCatalog`, `MascotPreviewFactory`; insert `Script` named `ShowcaseDemo` with source. Verify native Luau parse and `require` **before** setting `local ENABLED = true` in this **local test Script only**. Do not edit the handoff canonical source.
2. Use a blank floor around y=0 and manual landscape viewport. `Play`: two distinct models only; count deer **21** Parts and greeter **16** Parts; no preexisting gameplay actor or character was touched; model names/attributes match IDs; 0 touching/collision/raycast query interaction, all anchored and nonblocking. Verify both appear with recognizable antlers/door and lighthouse hat/uneven boots/flag at both near and far camera distance.
3. Invoke `SetPose` manually for idle/tap/win/loss and `SetLod` near/far; observe visible part counts 21->17->21 and 16->12->16, no leaked parts. Invalid ID, invalid origin, invalid pose and foreign model must be rejected; `Destroy` must remove exactly models owned by the Factory. Check no client remote, no purchases, no reward state, no DataStore, no errors. Record Output + screenshots and local FPS/p95 frame time; not a synthetic 2-client gameplay PASS.
4. Mobile emulator landscape: evaluate silhouette readability and UI occlusion, color contrast in grayscale, performance on target low-end device emulation, no text clipping or interaction blockage. Real physical phone is separate `NOT_TESTED` until measured.
5. `Stop` -> `Edit` -> delete demo + preview models and test scripts -> save **a separate isolated local test Place** and its full SHA -> normal close of ONLY the Studio instance started for this preview; verify target PID/instance/lock vanished. Never close other Studio sessions.

## Decision and reporting
- If integration/source ownership conflicts with current D17 collection display, **NO-OP**. Do not create duplicate catalog/free entitlement or event scheduler.
- Offline tests are *not* native Luau parse. Studio native parse, Play/Stop, screenshots, mobile emulator, FPS, normal exit must each be separately evidenced. If not run, mark `NOT_TESTED` rather than PASS.
- Do not claim a real gameplay collectible without trusted D17 ownership and D06 free stamp; this packet contains **no unlocking logic**.
- Main / merge / Roblox publish / monetization / unapproved spend: **HOLD**.
