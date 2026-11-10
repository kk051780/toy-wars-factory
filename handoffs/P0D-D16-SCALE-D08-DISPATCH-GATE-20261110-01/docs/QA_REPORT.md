# Offline QA report — D16 scale D08 dispatch gate

- Type: new source-only reference; disabled, `approvedByOwner` and `visualRendererReady` both false unless explicitly configured by the OWNER Windows Codex.
- Python behavioral oracle + static Luau text contract: **54/54 PASS** (`python -m unittest discover -s tests -q`).
- Tested logical paths: default-off, missing approval/renderer/mapping, explicit synthetic mapping, giant target/mini roster, duplicate replay, typed D08 envelope, wrong phase/kind/subtype, expiry and early cleanup, wrong match/stage/epoch, round/roster mutation mid-yield, invalid clock/user IDs, reset/stop, no second scheduler.
- This is **not** an interpreter execution of the `.luau` file. Native Luau parse = NOT_TESTED; ROBLOX Studio = NOT_TESTED; Windows Codex source comparison and PC intake = NOT_TESTED; 2client/3client/mobile = NOT_TESTED; real UI/physics effect = NOT_IMPLEMENTED; original encrypted D16 ZIP source recovery = BLOCKED.
- No actual GitHub or Studio publication should be inferred from offline unit tests. A separate immutable pinned GitHub packet and 100% remote byte/SHA readback are required for PUBLIC_SOURCE_V1 delivery.
