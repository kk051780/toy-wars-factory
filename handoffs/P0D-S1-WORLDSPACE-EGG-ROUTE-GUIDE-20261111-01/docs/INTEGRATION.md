# Sole #220 CHAT-INTEGRATOR integration + QA contract

## Exact source baseline (read-only)

- `releases/P0D_S1_KIDS_RC01/src/server/MapBuilder.luau` at `35d7d0525388e885aac8281eff2315a59831e0cf`: `TRAP_RAIDERS_S1/{RED,BLUE}_CASTLE/{RED,BLUE}_EGG`, `{RED,BLUE}_SCORE_PAD` are actual Part names.
- `src/server/Game.server.luau`: existing `TrapRaidersS1Remote` sends `SNAPSHOT` with `serial`, `phase`, `team`, `carrying` every 0.5s. The one existing server processes egg pickup/delivery; no round/event/damage changes needed.
- This packet does not assume the latest Windows local Place and is not the original PC source recovery.

## Optional additive mount only by unique RC writer

1. Copy `src/WorldRouteModel.luau` to S1 RC `src/shared/WorldRouteModel.luau`.
2. Copy `src/WorldRouteGuide.client.luau` to RC `src/client/WorldRouteGuide.client.luau`.
3. Keep the existing `TrapRaidersHUD` StarterPlayerScripts mount exactly once. Add one new, uniquely named Rojo project entry under `StarterPlayer/StarterPlayerScripts`:

```json
"TrapRaidersWorldRoute": {"$path": "src/client/WorldRouteGuide.client.luau"}
```

4. Keep `ReplicatedStorage.TrapRaidersShared` mapped to `src/shared` exactly once. Never make a second `TrapRaidersS1Remote` or another server round authority. Update RC source-lockfile/BUILD_MANIFEST, exact plan, receipt, tests using the #220 sole-owner workflow; run independent RC static + dynamic QA.
5. Optional feature is disabled simply by omitting both files and the one project entry. There is **no global toggle, server branch, or new network protocol**.

## User-facing behavior and failure handling

| Server-owned snapshot | Local 3D marker | Code lookup |
|---|---|---|
| ACTIVE RED not carrying | BLUE egg | `BLUE_CASTLE/BLUE_EGG` |
| ACTIVE BLUE not carrying | RED egg | `RED_CASTLE/RED_EGG` |
| ACTIVE RED carrying BLUE egg | RED score pad | `RED_CASTLE/RED_SCORE_PAD` |
| ACTIVE BLUE carrying RED egg | BLUE score pad | `BLUE_CASTLE/BLUE_SCORE_PAD` |
| LOBBY / COUNTDOWN / RESULTS | hidden | no part lookup |
| Malformed/stale/wrong-team egg snapshot | ignored | does not create route |
| Map part not replicated yet | temporarily hidden | retry at next 0.5s server snapshot |

Does not offer enemy-player reveal, teleport, private inventory, DataStore, chat, link, monetization, or screen-covering popups. A single local BillboardGui is reused; max distance 220 studs, with 8-stud vertical offset. On tiny landscape phones the marker might need smaller text or occlusion changes: **physical mobile QA required**, not assumed.

## Release QA that MUST remain NOT_TESTED here

Native Roblox Luau parse/Play, actual mobile landscape safe-area/overlap/FPS, 2client RED/BLUE asymmetric target selection, team disconnection/rejoin, late map replication, egg capture/drop/reset, anti-exploit, true D07 boss, D08 canonical events, round end, Studio closed. Offline Python tests cover only the pure projection specification and static integration boundaries.

## Rollback

Remove `src/shared/WorldRouteModel.luau`, `src/client/WorldRouteGuide.client.luau`, and `TrapRaidersWorldRoute` from Rojo. No server state migration, cleanup jobs, or external assets. Rebuild and revalidate exact source/hash receipt. Neither this handoff nor a GitHub Issue comment is a PC Codex command or Roblox publish permission.
