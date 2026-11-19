# ORIGINAL RC85→RC86→REAL66 : physical WCS canyon, Starfall path, Meteor 4th route

**SOLE FORMAL RC:** \`rc/p0d-s1-kids-rc01\`. In official source profile \`REAL66\`, the oldest S1 RC85/86 physical WCS/Starfall/Meteor lane trio is still not selected. THIS PR ports that one distinct physical world feature into the same V3 TEAM and BATTLE_ROYALE arenas by **one new environmental-only server Script** (candidate source profile REAL67). It does *not* merge old S1 Game/HP/Store/Remote/score scripts or select a second actual Game.

## Source locked historical originals (not from vague concept descriptions)

Old actual private RC85 \`P0D_FB026_NECROMANCER_SIEGE_CUMULATIVE_PRIVATE85.rbxlx\` 85 Lua source scripts (CI artifact **14158848286**), RC86 \`P0D_RC86_SIEGE_V3_STAGE_WEAPONS_UNDEAD_PRIVATE.rbxlx\` 86 scripts (artifact **14161823401**) were downloaded and old-world Source XML extracted and compared. Original source fingerprints SHA256:

| Old real script | Original source SHA256 | Useful behavior |
|---|---|---|
| \`TrapRaidersS1/WCS_CrystalCanyon\` | \`17ee851bda13076effdd81de68346f83b8d82366ec7b09de4f7cd938a1b78198\` | Two banks, always-on safe bridge, 2 Moguron prompts, 14-second gate and four-second cooldown, crystal scenery and fall-return stairs |
| \`TrapRaidersS1/StarfallPath\` | \`f88ec4005a5cb611a2f5acfd7eb67309f2de3799a2f51ebe6208bc2ee3670b35\` | TEN physical glowing star steps at z=-35, two symmetric server-checked switches, 16-second open and seven-second cooldown, do-not-close-on-player |
| \`TrapRaidersS1/MeteorFourth\` | \`d4894535eec6f1bb40c1e17a9626e1bcd98a00307ad0db858c4073e6b92b4bd2\` | DISTINCT fourth lane z=-17, 55s quiet, 5s warning, 22s temporary bridge, cap12 real parts and postpone closure if occupied |

The original old S1 sources used old \`TRAP_RAIDERS_S1\` workspace anchors, \`P0D_STARRY_PATH\`, and \`P0D_CrystalCanyonAnchor\`, which are NOT active in the V3 Arena. Directly copying them would silently disarm. The port changes *only* the world locator (V3 Host \`EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW/TEAM_Arena\` and \`BATTLE_ROYALE_Arena\`, each existing anchored collidable 890x1050 \`TacticalBattlefield\`) and makes a safe elevated bridge/stair scene over the retained original map. No replacing or clearing the tactical battlefield. The old 3 policy flags are retained in \`LegacyFlags\`.

## Actual new Script (one and only unique environmental runtime)

\`EGGRUMBLE_LegacyCanyonRoutes.server.luau\`: Studio-only; attaches to the existing canonical lobby and future per-round arena even if the lobby appears late (no 20s disarm). Each arena gets one idempotent \`GQ8_RC85_WCS_StarMeteor\` Model with original 2 banks + safe bridge + 2 shore access stairs + 2 Mogurons + 10 timed Star stones + independent 8-part Meteor bridge. Players can use both sides, either mode; all prompts check server-owned current mode, living human, cast-out/elimination and actual LOS with \`RespectCanCollide\`, *not* client-only prompt visibility. No second Game/Combat/Swarm/HP/KO/egg/reward/Store/DataStore/Remote. Arena destroyed = scene gone and task loops retire. Both ephemeral paths wait for zero living players before closure; original always-safe bridge never disappears. No permanent HUD/tutorial overlay.

### Source non-loss contract and test

- \`compose_real67.py\` reads exactly the official composer \`artifacts/real66\` project, selected 66 route/class/bytes, exact \`REAL66_LEGACY_INTAKE_RECEIPT.json\` and exact parent Place. It asserts original 65 exact source digests and the previously adopted **one 66th RC86 Realm4/StarShards6 Script**, then adds only new \`ServerScriptService/EGGRUMBLE_LegacyCanyonRoutes\` **Script**. All existing 66 paths and source bytes are unchanged. Existing Dojo/social/Combat 2 owners, Wind, weapons, LSS/Realm storm, normal two-mode Host all remain byte-exact.
- Same-PR-head official workflow composes 66 unchanged then composes 67. A true pinned native Luau CLI compiles 67/67, true Rojo 7.7.1 rebuilds REAL67, \`rehydrate\` verifies selected 67 route/classes and original OFF66 build is Rojo-rebuilt byte-exact. Existing OFF63 and OFF65 checks also still run. All source changed and test execution must PASS before any formal-branch merge, fresh SHA + nonforce PR; then repeat official same-head Actions and report exact ZIP and .rbxlx bytes.
- \`test_runtime_contract.py\` enforces old time rules and server LOS, two symmetric routes, player-safe closure and no Game/Store/Remote/paid APIs. **Static tests are not engine playtests**.

### Remaining failures and launch gates
This one RC85/RC86 historical three-feature family is still only compiled/linked, **not** verified by actual Studio 1/2-client. Check both TEAM/BR map accessibility, stairs without jump exploit, bridge collision and actual occupancy under client lag, 55+5s meteor cycle, old V3 castle/bot/egg routes unobstructed, Android rendering and device FPS before removing Studio-only. Product ART/FUN/OWNER are NOT_TESTED and **NO_GO**. Do not claim “all original 48 flags integrated”: remaining long-tail (twin biomes/creatures/bond, saved mastery/evolution, six-skill durability, exact Gorogan, old first90, etc.) require semantic verification, one at a time, without S1/Game duplications.

No Work, Codex, separate official RC, public Publish, main changes, monetization or original-author approval wait.
