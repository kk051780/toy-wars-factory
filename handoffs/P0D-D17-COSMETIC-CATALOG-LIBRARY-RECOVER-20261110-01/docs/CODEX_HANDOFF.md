# Owner Windows Codex integration brief — D17 catalog only

1. Read #218 newest claims + #213 latest PC report; ensure no new conflicting scope. This packet is **not** the D17 privacy-metrics oracle and should not run purchase/telemetry APIs.
2. Verify PC's latest legitimate local CHECKPOINT/RESUME/BUILD_MANIFEST, Place and Luau source SHA. Preserve the newer cumulative Place; never overwrite with reference ZIP.
3. Download the encrypted JSON from the immutable GitHub commit; obtain private key directly from OWNER in chat; use vetted `restore_handoff_safe.py` pinned at `d37eec1b653d060ae27568ddcd5f501da9662081`, supply expected zip SHA/work_id/packet_id and a fresh owner-controlled directory. Do not reveal key in logs or GitHub.
4. Examine source/manifest and offline tests; do Luau compile/type review; no asserted Studio QA from Python test PASS.
5. After v37 and v39 prerequisite QA, S1 only: plug `Catalog.list` and `Catalog.preview` into the **existing** lobby without duplicate screens. Preview metadata may be shown by UI but no asset ID is sent by Remote. Do not equip unless verified server entitlement exists. On logout call `playerLeft`, on true server restart `resetSession`.
6. Security QA: client-forged `owned=true`, fake product ID or fake win must not grant item; two players cannot see each other's equipment; repeating equip is idempotent; revoked entitlement hides currently selected item; 256-cap and cleanup; iPhone landscape 3-second FPS isn't long-term phone QA.
7. Only after verified physical UI render and private QA: record SHA of Place/ZIP, feature matrix, output errors, Play→Stop→Save→owned Studio process exit. Report to #213 and #218, distinguish `WINDOWS_RESTORE`, `LUAU_PARSE`, `STUDIO_INTEGRATED`, `STUDIO_QA`.
8. No publication, Robux/test purchases, DataStore, main/merge, expense, P0-A/B/C infrastructure changes.
