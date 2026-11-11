# S1ロビー再戦デッドロック修正：実Game全体ソース
TRAP RAIDERS / p0d-siege-v19, packet P0D-S1-LOBBY-TEAM-DEADLOCK-PATCHED-GAME-20261111-02.
This is a **full** S1 Game.server.luau source candidate derived from immutable source 35d7d0525388e885aac8281eff2315a59831e0cf; it is not a separate second Game runner.
Changes are EXACTLY four reversible text replacements from prior packet at commit 7693d47180c25c078debba9a5cb0ad294580601f.
Original pure Luau planner is copied with identical bytes from that packet.
Only #220 sole CHAT-INTEGRATOR may optionally replace its one canonical Game.server.luau, add planner alongside it and update its own source manifest/plan/receipt. Do not run a second Game script; do not merge to main; no automatic game publication.
Baseline Game original Git blob SHA1: 0f2c34fe25c00e3251b9ca53952b9ec75400f365; if actual S1 RC has advanced since baseline, STOP: compare four changes and port manually, never overwrite integrated D07/D08/D15 code.
18/18 actual original full-source JS structural checks passed, including exact four replaced anchors and perfect reverse transform back to immutable original; see docs/FULL_SOURCE_DIFF_PROOF.json. This is not native Luau parser QA or actual Studio/phone testing.
No keys, passwords, secrets, payment implementation, or live Roblox release.
