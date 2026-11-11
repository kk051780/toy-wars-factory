# S1 original objective prompt visual guard — optional, NOT INSTALLED

Baseline immutable `35d7d0525388e885aac8281eff2315a59831e0cf`:
- Game source: `releases/P0D_S1_KIDS_RC01/src/server/Game.server.luau` blob SHA1 `0f2c34fe25c00e3251b9ca53952b9ec75400f365`
- Map source: `releases/P0D_S1_KIDS_RC01/src/server/MapBuilder.luau` blob SHA1 `d2127b8c20c8abd880a21f84aeeb706feeb14ce8`
- Rojo project: `releases/P0D_S1_KIDS_RC01/default.project.json` blob SHA1 `9035dba279830bda1305ccdcd66fcbf94795fe33`

In the baseline, `setObjectiveEnabled(true)` globally enables available eggs and BOTH score pads. Server `Rules.canSteal/canScore` rejects impossible actions, yet unrelated native prompt UIs can be displayed. For first-time young players this is confusing; it is not a game-authority bug. Source-game panel/map/FX modules remain untouched here.

## OWNER S1 CHAT-INTEGRATOR opt-in recipe ONLY

1. Check your NEWEST `rc/p0d-s1-kids-rc01`, original PC/Place provenance and other prompted UI code. If another client changes `ProximityPrompt.Style` or your map name/snapshot schema changed, SKIP until reviewed; no silent ownership overwrite.
2. Copy `src/PromptContextModel.luau` to RC `src/client/PromptContextModel.luau`; copy `src/PromptContextGuard.client.luau` to RC `src/client/PromptContextGuard.client.luau`.
3. Under existing `StarterPlayerScripts` tree in `default.project.json`, ADD these unique mappings, retaining existing `TrapRaidersHUD` and any other scripts:

```json
"TrapRaidersPromptPolicy": {"$path": "src/client/PromptContextModel.luau"},
"TrapRaidersPromptGuard": {"$path": "src/client/PromptContextGuard.client.luau"}
```

4. Keep `Game.server.luau`, `S1Rules.luau`, `MapBuilder.luau`, the existing Remote and server ProximityPrompt `.Enabled` UNCHANGED. Client-only `Style.Custom` suppresses built-in UI; `Style.Default` restores it for a context-relevant objective. ProximityPrompt.Triggered may still be reached by other inputs; server must independently revalidate. It does.
5. Source QA: check valid Rojo mapping (module sibling of LocalScript), singleton Game authority, no second Remote, no unexpected clients writing objective/score, no clobbering other Custom UI. Update real RC manifest/plan/receipt if adopted. Independent QA #220 static/gameplay must evaluate the actual RC.
6. OWNER-directed final Studio 2-client and mobile QA only near final RC: For each team, check BOTH egg steal prompts, score pads when not carrying, picked-up egg, own egg stolen, countdown/results reset, respawn, visible timing and touch. Ensure HUD and optional world-space route module are unaffected. In particular test fast local `Style` changes while server is simultaneously setting `.Enabled` and mobile touch HoldDuration=0.35.
7. Rollback by removing exactly these TWO client project mappings/files. No server/gameplay migration. Client script restores only prompts it owned when it is destroyed.

## Explicit limitations / why fail-closed

- `SNAPSHOT` does not expose an explicit `ownEggHome` boolean. The guard reads the existing own egg's replicated `.Transparency`, which baseline writes 0 at base, 1 when stolen. If the state is unknown, scoring prompt stays visually suppressed; the actual server Rules remain ultimate authority. The world map may not yet be replicated; waits until next snapshot (0.5s) before touching a prompt.
- This is NOT a guaranteed hack/cheat prevention system and MUST NOT be treated as server authorization. A modified Roblox client can change any locally rendered UI. Backend access already checks actual phase/team/distance/egg owner and carrying status.
- `Style.Custom` documented to suppress default native UI at https://create.roblox.com/docs/reference/engine/enums/ProximityPromptStyle . Native Luau/Studio mobile/2-player execution are NOT_TESTED; Python scenario oracle verifies logical expectations and static boundaries, not Roblox runtime.
- Does not install paid items, analytics, new prompts, Remote messages, overlays, player data, monetization or cause any production release.
