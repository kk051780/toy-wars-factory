# FB023 — field item pickups (actual Luau; DRAFT candidate)

**Owner feedback:** place real usable items in the arena; don't introduce a permanent blocking HUD.

**Implementation:** `FieldPickups.server.luau` is a standalone **ServerScript** that must be installed as an actual `ServerScriptService/FieldPickups` instance (not as a ModuleScript). At runtime it spawns three visible world items at arena coordinate centers, raycasts to the ground, presents native touch-capable ProximityPrompts, grants equipped Tools, executes real server-side effects upon `Tool.Activated`, and respawns items 18 seconds after pickup. No Game/Store/egg/KO/HUD file changes; one additive Script only.

| Item | Actual effect | Client experience |
| --- | --- | --- |
| 衝撃ハンマー | Server physics knockback, up to 8 nonfriendly humanoids within 17 studs, **zero** damage/KO/score modification | Visible hand-held metal hammer + expanding impact pulse |
| 疾風の羽根 | 7-second server WalkSpeed boost, capped at 34, expiry restores only if still unchanged by other systems | Equip then tap/click; short blue pulse |
| 守護の護符 | Server ForceField for 4 seconds | Equip then tap/click; short green pulse |

**Safety/fail-closed:** Studio preview enabled by default; non-Studio only if `game.PrivateServerId ~= ""` **and** `workspace.P0D_PRIVATE_FIELD_ITEMS == true` at startup. No public live game activation, additional Remotes, inventory persistence, monetization, team-friendly knockback, new damage/score authority. The pickup pad is noncolliding; team/enemy checks and all activation actions are server-authoritative. The Tool is consumed on use, can be held for later, and one unconsumed copy of each item per player is allowed.

**Quality/release status:** Source-level Python assertions 6/6 PASS locally. Native Luau compile, Rojo path/class installation, RC source-exact overlay, Roblox Studio interaction, multiplayer and Android **NOT RUN**. Treat as `IMPLEMENTED_SOURCE`, **not** `OFFICIAL_RC`, `PRODUCT_GO`, `ART_GO`, or `OWNER_ACCEPTED`. Before official adoption, the #220 integrator must insert it into the up-to-date private RC source manifest, re-run native compiler/source locks, verify instance identity and Studio/Android proximity prompt and effects. Release YELLOW noncritical issues can be tracked but RED source lock/syntax errors remain stop conditions.

**Files owned by this change only:** `quality_repair/FB023_FIELD_PICKUPS/{FieldPickups.server.luau,test_field_pickups.py,README.md}`. Neither the current P0D #476 Game/HUD/Castle sources nor the #471 product-quality scoring engine are edited. Do not create an alternate Game.server or overwrite the latest private 82/83/85-source Place.
