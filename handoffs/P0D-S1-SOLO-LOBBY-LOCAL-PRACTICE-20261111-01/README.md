# P0D-S1-SOLO-LOBBY-LOCAL-PRACTICE-20261111-01

## Purpose

When TRAP RAIDERS S1 has only one user online, the actual source-built game remains in `LOBBY` because `Config.MinPlayers=2`. The HUD hides its real attack button unless `ACTIVE`; new players can have nothing to do. This optional **client-only** practice toy shows a yellow local, noncolliding dummy and a separate `れんしゅう たたく！` button while the authoritative server snapshot says `LOBBY` with exactly one player. Hit count is local-only, capped at 99; NO rewards, coins, XP, scores or leaderboard. Countdown or match phase promptly destroys the dummy and hides the UI.

**This is a completed source candidate, not integrated into S1 RC.** S1 official completeness belongs only to #220 CHAT-INTEGRATOR.

## Contents

- `src/LobbyPracticeModel.luau` — pure fail-closed local state model for server snapshot gate, cooldown, range/facing and local counter.
- `src/LobbySoloPractice.client.luau` — one optional LocalScript that listens on the EXISTING `TrapRaidersS1Remote`, creates no Remote, and neither sends server actions nor changes match authority.
- `tests/test_lobby_practice.py` — Python reference oracle and static content assertions only. These do **not** run native Luau/Studio.
- `docs/INTEGRATION.md` — precise Rojo mapping, preflight and release/rollback rules.
- `BUILD_MANIFEST.json` — canonical PUBLIC_SOURCE_V1 file hashes and lengths.

Nothing uses third-party IP/assets or secret IDs. The package intentionally includes no studio Place binaries, scripts touching other P0s or paid item catalogs.

## Test

`python -m unittest discover -s tests -v`

## Safety

`script.Parent`/shared module belongs to the **client**; visual instances are created locally and never used by server combat, hit detection or scoring. `Workspace` visibility is local only. They may be removed without changing map or session state. Code is optional/disabled until #220 integrates. Roblox native Luau parse, two-client device testing and phone landscape remain `NOT_TESTED`.
