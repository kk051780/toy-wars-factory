# Exact official MapBuilder runtime QA — P0-D S1

Independent keyless test scope `P0D-S1-OFFICIAL-RC-REAL-MAPBUILDER-GEOMETRY-NATIVE-20261112-04`.

The final prelaunch S1 `Game.server.luau` gameplay QA intentionally used test-only **MapBuilder geometry** for its server combat loop. This package tests the missing piece: the **actual unchanged official MapBuilder source** from frozen official commit `5dc6c958ea5549b1e859d6d250e6179e731181fb`.

- `src/server/MapBuilder.luau`: **Git blob** `d2127b8c20c8abd880a21f84aeeb706feeb14ce8`.
- `src/shared/Config.luau`: **Git blob** `ef10e4288e4732588116cd3e55d3d871ca803ff4`.
- `tools/run_original_mapbuilder_native.py` fetches those exact original game source bytes from Git, locks both original Git blob SHA1 values, and executes their full actual Luau bodies using official upstream native Luau at `f46d879e28302a430029304f7f6a162aed66f103`. Only global `Instance`, `workspace`, `Vector3`, `CFrame`, color and GUI types are faked.
- It checks 27 real Parts, three folders, four initially disabled interactions, both mirrored castles, egg/delivery/spawn/arena coordinates, anchored/non-collidable/queryable objective properties, single world folder, prevention of duplicate game world, and absence of accidental Remote/Game authority creation.
- A native Luau mutation runner must reject six deliberately bad variants of the *original source* (prompts active in lobby, eggs misplaced, spawn misplaced, unanchored parts, accidental touch triggers, colliding egg). The real game bytes are NEVER edited; tests mutate temporary memory only.

**Interpretation:** a successful test validates the actual authored MapBuilder constructor and source geometry against a simple faithful instance containment/type fake. It is **not** Roblox Studio, physics/pathfinding, 2-client map traversal, mobile QA, first-minute human testing or release approval. It cannot grant additional official release points without the #220 sole integrator's evidence audit.

This package does NOT replace the actual S1 MapBuilder or author new map art (other chat #219/#222 mission). No main, official RC, merge, Roblox publishing, Windows Codex, charge, protected P0-A/B/C or scheduled automation changes.
