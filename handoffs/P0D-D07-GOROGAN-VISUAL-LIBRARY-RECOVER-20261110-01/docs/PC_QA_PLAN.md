# S1/S3 Studio QA plan (future Windows Codex only)

1. Read newest #218, #213, #217 and newest local PC checksum/manifest; abort on unexpected local generation. Work solely on an unpublished duplicate Place.
2. Restore AES-GCM packet with a private OWNER-supplied key using the approved fail-closed v2 restore helper from `d37eec1b653d060ae27568ddcd5f501da9662081`, specifying expected ZIP SHA and packet_id and work_id. Independently verify manifest and every file SHA. Never log secret or upload source to PUBLIC GitHub.
3. Run Luau parse/type check for each module, inspect client module and server adapter code. Ensure approved v40 canonical boss ID mapping BOSS_GOROGAN→GOROGAN, server-owned single-event choice, server attributes really exist. The optional script must remain OFF if contract is absent.
4. In isolated S1, run valid externally triggered boss visual: gold core, moss, distinct left/right arms, red neon warning ring, 2s warning, active, optional STOMP phases <=3, END clear. Compare lowDetail and reducedMotion. Spawn should be physically non-colliding and not interfere with Raycasts. No Humanoid or attack/HP effects should be created by visual prefab.
5. Negative tests: wrong match/seq, replayed START, stale EventID, S2, NaN/out-of-bounds position, death/disconnect, 2 client join/leave, reset after round end; no ghost model persists. Server must not fire once after round end.
6. Performance: measure S1/S3 and iPhone landscape emulator at low detail + normal under 2 client; 20s samples, not 3-second cherry-pick. No physical phone assertion unless tested.
7. Stop Play, Save, Quit only Studio process opened for this job, verify PID gone. Update QA_REPORT, CHECKPOINT, RESUME, FEATURE_MATRIX and sha. Issue only sanitized result/hashes (not private Luau/Place/key).

Required distinction: offline Python tests are **not** runtime Studio proof; visual appearance must be reviewed in actual Roblox 3D before claims of success.
