# QA — D07 ライガルド / P0D-D07-LIGARDO-VISUAL-20261110-03

Offline unit/property and Luau source-shape tests: see actual command output; do not infer Studio test from source checks.

## Safety test scope
- Round ID/stage S2/S4/unique event ID/monotonic sequence/phase/remainingMs validation.
- One client decorative spawn per event per round, duplicate rejected, hard <=20 sec lifetime, round-close cleanup.
- No Roblox damage/velocity/Collision/Touch/Query, anchored Roblox Parts only; low-detail and reduced-motion branch.
- ZIP path/duplicate/symlink/manifest checks and AES256-GCM roundtrip and negative ciphertext/wrong key (packaging stage).

## Not tested
`WINDOWS_RESTORE=NOT_TESTED`; `LUAU_PARSE=NOT_TESTED`; `STUDIO_INTEGRATION=NOT_TESTED`; `STUDIO_QA=NOT_TESTED`; `REAL_BOSS_AI=NOT_IMPLEMENTED`; `LIVE_COMBAT_DAMAGE=NOT_IMPLEMENTED`; `MOBILE_FPS=NOT_TESTED`; `PC_BASE_SHA=UNVERIFIED_PC_LOCAL`; `STUDIO_CLOSED_VERIFIED=NOT_TESTED`.

## Integration gate
Read shared Issues #218/#213/#217, latest PC CHECKPOINT/Place SHA, v37 final QA first. Existing boss chooser and boss identifier spellings to be verified in actual Windows code. Isolated draft/source review, real multiplayer Play/Stop then save and normally close owned Studio instance with target PID gone. No production changes.
