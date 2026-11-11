# Original Game.server + MapBuilder integrated native QA

This source-only independent test tests the previously unproven boundary between the real S1 server match controller and the real map instance constructor. Current sole-integrator official RC is fixed to commit `5dc6c958ea5549b1e859d6d250e6179e731181fb`; this packet **does not change that branch**.

Original byte-for-byte official RC Git blobs enforced before native execution:

- `Game.server.luau` `3d3c5934e110099517fc4a7eb5aa914fcd52f145`
- `MapBuilder.luau` `d2127b8c20c8abd880a21f84aeeb706feeb14ce8`
- `S1Rules.luau` `5652b5b43d753c2fcbd27b6c040a34a3642f71ee`
- `LobbyTeamRecovery.luau` `db1a369133550bc8356a4ee3ac22b97fcb1b46c4`
- `Config.luau` `ef10e4288e4732588116cd3e55d3d871ca803ff4`

The checker is derived from independent native original-Game lifecycle test `c5966c68326ec085c199c1e3bf69daf320852f4a` and replaces **only the test's fabricated MapBuilder** with the actual pinned original MapBuilder Luau body. It uses test-only Roblox external `Instance` / `workspace` / `Vector3` / `CFrame` / `Players` / remote / clock / humanoid service objects. The original game authority, map builder and rules bodies are not modified or persisted; Roblox `require` imports are redirected to already-executed exact original module return values within the temporary test fixture.

Tests check that real MapBuilder constructs 27 Parts, 3 Folders, 4 server-owned prompt handles, castle/egg/pad/spawn symmetry; that the same physical-part tables are passed to the actual original Game authority; and that real prompt signals perform enemy egg theft, own egg restrictions, delivery, 2-score win, rematch, server melee, replay and cooldown rejection. Deliberately change two real map source lines in temporary memory to demonstrate the checker detects wrong egg location and an active lobby prompt, plus five existing unsafe actual Game/Rules mutations.

Official Luau interpreter pinned to `f46d879e28302a430029304f7f6a162aed66f103`. All test GitHub Actions results reflect native Luau running with external Roblox API mocks — **not** Roblox Studio, real engine physics, mobile, real two-client network delivery, actual player comprehension or launch eligibility.

No main/RC code edits, merges, Roblox publish, payments, PC Codex commands, protected P0-A/B/C controls or scheduled automations.
