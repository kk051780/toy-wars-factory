# TRAP RAIDERS S1 — Lobby Team Deadlock Recovery (keyless)

Packet `P0D-S1-LOBBY-TEAM-DEADLOCK-RECOVERY-20261111-01` · `TRAP_RAIDERS / p0d-siege-v19`.

Independent original source-ready **optional** server gameplay bugfix for sole RC integrator #220. Public plaintext; no AES, password, secret token, proprietary Roblox assets or remote IDs.

## Root cause in actual source-built S1

At initial source commit `35d7d0525388e885aac8281eff2315a59831e0cf`, `Game.server.luau` only assigns teams on join. After a match, if two people remain on the same team (both opposing players quit), `LOBBY` never transitions to `COUNTDOWN` until someone new joins. During an existing `COUNTDOWN`, losing all players on one side when 2+ remain can permit a one-sided `resetRound()`; the next tick then declares an empty-side defeat.

## Files

- `src/LobbyTeamRecovery.luau`: pure deterministic strict Luau minimal team reassignment planner. It has no event loop, no Remote, and no gameplay authority by itself.
- `tools/apply_game_patch.py`: SHA-locked source transform targeting only the original canonical `Game.server.luau`; **always** writes to a separate new path. Sole integrator reviews and merges the generated diff, not this chat.
- `tests/test_team_recovery.py`: pure Python reference oracle and adversarial validation of planner cases and exact patch markers; not native Luau execution.
- `docs/INTEGRATION.md`: precise Rojo mapping, game contract, rollback, and final Roblox QA cases.
- `docs/OFFLINE_TEST_LOG.txt`: actual isolated Python results.
- `BUILD_MANIFEST.json`: exact six-key canonical `P0D_PUBLIC_SOURCE_V1` manifest; source SHA256+sizes.

No edits to `main`, `rc/p0d-s1-kids-rc01`, Windows Codex, live Roblox, store, any P0-A/B/C controls, or existing Automations. Only the #220 integrator may include this in a complete RC. No claim of Studio/2client/phone execution or full game completion.
