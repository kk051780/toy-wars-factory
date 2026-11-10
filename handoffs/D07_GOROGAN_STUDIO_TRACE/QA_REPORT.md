# QA report — public-safe D07 S1 synthetic trace verifier

- Offline Python unittest: **72/72 PASS**; manifest hashes/size **12/12 PASS**; synthetic affirmative and intentional duplicate-hit rejection confirmed.
- Scope: **source-free Python validator only**; no Luau VM, Windows restore or real Roblox Studio run.
- Expected positive: synthetic fixture returns `SYNTHETIC_PASS_NOT_STUDIO_QA`.
- Expected negative: repeated same-player hit returns `DUPLICATE_OR_INVALID_HIT_TARGET` with nonzero exit.
- Validations include strict JSON parsing; schema/game/work/round; S1 unpublished server-only trigger; source/Place/log hash metadata; >=2 clients; canonical event receipt; Pathfinding MoveTo/actual observed movement; 2-second telegraph; <=3 attacks; <=8HP/server LOS; no old round or fake Remote damage; <=14s cleanup; owned Studio exit *claims*.
- Unresolved: authentic server log provenance, physical R6 rig, Roblox pathing, visual warning visibility, true HP delta, client frame rate, real mobile, actual Place/source/Output SHA, real Studio PID close.
- **Do not use this synthetic test verdict as a public release condition.** Global game status remains PARTIAL_NOT_READY.

See `docs/TRACE_CONTRACT.md` for evidence limitations and `docs/CODEX_HANDOFF.md` for owner-PC validation process.
