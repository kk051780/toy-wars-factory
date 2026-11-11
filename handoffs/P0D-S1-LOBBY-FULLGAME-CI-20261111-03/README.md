# P0-D S1 actual full-Game lobby patch: offline CI gate

Packet: `P0D-S1-LOBBY-FULLGAME-ACTUAL-REPLAY-CI-20261111-03`. Scope: strictly read-only source validation of the *previously* delivered full Game candidate. No new gameplay script, match authority, main/RC branch modification, merge or Roblox publication.

Pinned full candidate: `c609f622f7820efb2b7ee7270d30368644484f34` under `handoffs/P0D-S1-LOBBY-TEAM-DEADLOCK-FULL-GAME-20261111-02/`.

Original S1 Game: `35d7d0525388e885aac8281eff2315a59831e0cf` (`Game.server.luau` git blob `0f2c34fe25c00e3251b9ca53952b9ec75400f365`). Original earlier lobby-only planner and 66 Python tests: `7693d47180c25c078debba9a5cb0ad294580601f`.

The branch-scoped workflow at `.github/workflows/p0d-s1-lobby-fullgame-ci-20261111.yml` checks out three *fixed* immutable commits and runs:

1. 3 original full Game source-integrity Python tests originally published but previously NOT_RUN.
2. 9 additional new Python tests covering SHA256, Git blob SHA1, source authority, original planner identity, byte-exact four disjoint source hunks, negative tampering, both PUBLIC_SOURCE_V1 manifests.
3. Prior exact original 66/66 Python simulator and negative tests.
4. Manifest verifier for this CI helper packet.

The workflow uses a GitHub-hosted public-repo Linux runner, `permissions: contents: read`, no secrets, no project mutation, no paid cloud calls, no Roblox Studio. A passing result does **not** mean the Luau source compiled in Roblox Studio or a game with two clients was played. Only the #220 sole S1 Chat integrator may adopt/reject the fix and arrange final OWNER-directed Studio validation.
