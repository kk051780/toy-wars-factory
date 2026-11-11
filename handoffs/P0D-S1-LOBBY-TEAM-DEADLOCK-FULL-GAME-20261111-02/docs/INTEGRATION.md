# Exact S1 full-source integrator intake (only #220 RC writer)
Source root in this packet: src/server/Game.server.luau (full original patched single authority) and src/server/LobbyTeamRecovery.luau (pure ModuleScript).
Original base: 35d7d0525388e885aac8281eff2315a59831e0cf, Game Git blob 0f2c34fe25c00e3251b9ca53952b9ec75400f365.
1. Compare newest integrated RC Game source with original. If different, STOP: this full file cannot be copied verbatim; manually port only the four approved deltas.
2. If identical, copy the two source files into the *sole* releases/P0D_S1_KIDS_RC01/src/server folder, replacing the existing Game source and adding its sibling ModuleScript. Existing Rojo default.project.json maps src/server; DO NOT mount another Game.
3. Preserve server ownership for all Team/round/event/combat/egg/score/damage and ensure no other LocalScript tries to modify the team. The new lobby planner does not create a second Remote.
4. Rebuild canonical PUBLIC_SOURCE_V1 manifest, fixed source SHA/receipt and run the existing S1 static/gameplay independent QA.
5. Native Studio test: 2RED+0BLUE LOBBY changes to 1v1, 4RED+0BLUE to 2v2, 1 user never begins, COUNTDOWN with last blue departing and 2 reds -> LOBBY (not false ACTIVE win); ACTIVE/RESULTS teams unchanged; spawn relocation and no stale carry.
6. If false positives or device issues, restore original Game Git blob, remove planner, refresh manifest and run full tests.
Native Luau parse and Roblox 2client/mobile Studio QA NOT_TESTED by this author. Full file source verification is not actual playable match verification.
