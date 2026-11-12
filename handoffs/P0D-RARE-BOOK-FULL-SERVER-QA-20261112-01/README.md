# P0-D Rare discovery notebook — FULL ORIGINAL server code native Luau integration QA

Independent QA issue #239. Parent notebook #236 immutable commit `17e16ae8b323bc5a35aba62981b2b593029939df`; parent animation #232 and original fantasy castles #230. This unique QA branch contains **only tests and documentation**. Original source files and all 3 original strict SHA256 manifests are unchanged.

## Why another test?
Earlier #236 truly executed the original Book/HUD/QAPlan module bodies, including two independent `PlayerGui`s (85 native checks), but **did not execute `RareDiscoveryStudio.server.luau`**. A good server pipeline can fail after the modules pass. This pack tests the entire original server bootstrap, scene builder and moving models *in one actual upstream native Luau interpreter*, using test-only implementations of the **external Roblox engine** API.

It exercises the exact original:
- `RareRealmCatalog.luau` and `RareRealmScene.luau`: 4 original 3D worlds and 115 source Parts.
- `RareEncounterPolicy.luau` and `RareEncounterModels.luau`: actual original 4 model factories and `Model:PivotTo` movement.
- `RareDiscoveryBook.luau`, `RareDiscoveryHUD.luau` and `RareDiscoveryQAPlan.luau`.
- The complete **unmodified original `RareDiscoveryStudio.server.luau`** (test wrapper opts in by overriding its local false flag only in generated test runner, NEVER in any production or original source).

### Native integration checks
Two simulated Roblox Player objects own two separate PlayerGui objects; the full original server registers each, creates real source-made GUI, builds full original 4-world map and 4 moving models sequentially, observes RunService.Heartbeat and real original ProximityPrompt:Triggered listeners. It rejects early prompts, far-distance spurious click, dead player, anchored player, repeated discovery, stale expired prompt. Both players independently discover each of the four distinct original models and their HUDs reach 4/4. Server emits exactly one `TWO_CLIENT_INDEPENDENT_BOOK_4_OF_4` event, eight `NEW_DISCOVERY` and four `CREATURE_EXPIRED` logs. Rejoining a new player starts 0/4. Simulated proper cleanup removes scene.

Six dangerous mutations of **original full server source only** are deliberately introduced in a test-only runtime and must fail: ignore server distance, ignore health, accept anchored player, update the wrong player's UI, award global PASS prematurely with only one player, and print imaginary reward coins.

### What this does NOT prove
**This does NOT run actual Roblox Studio or true physical/network touch input**. Roblox classes and events external to real source are doubles; two simulated Players are NOT 2 real Studio clients. It does not show mobile FPS, camera, actual walking, real physical proximity enforcement by the Roblox engine, child enjoyment, true rare odds, game integration or production release. The original server remains DISABLED and S2+ optional. The only way to complete real engine gate is the OWNER's manual protected unpublished Place Studio 2client/mobile test following #236 README.

No changes to `main`, official S1 RC, previous original Sources, canonical D18 assets, paid features, Roblox Publish, Codex/Windows PC actions, P0ABC lock, or existing automations. No keys.
