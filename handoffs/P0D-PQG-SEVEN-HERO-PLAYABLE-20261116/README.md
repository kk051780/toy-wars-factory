# P0D Seven Hero Playable Studio Slice — SOURCE, not official RC

OWNER instruction (2026-11-16): "ゲーム品質ゲートとして、各キャラを作り上げて".

## What is implemented as actual Luau

`SevenHeroArena.server.luau` is a **Studio-only**, opt-in ServerScriptService preview, additive to (not replacing) the official Game/Store/egg/Remote source. It creates **7 selectable 3D hero stands**, **three Roblox Tools per selected job**, **12 respawning training dummies with actual Humanoid damage**, and server-side abilities/effects. No network assets, no external IP characters, no new charges.

| Internal role ID kept | Visible role | A / B / C implemented as runnable Studio behavior |
| --- | --- | --- |
| WARRIOR | 戦士 | strike / earthquake AoE / large battle shockwave |
| MAGE | 魔法使い | ranged magic / AoE thunder + ally healing / falling meteor |
| NINJA | 暗殺者 | dash hit / temporary speed + transparency / extended strike dash |
| TRAPPER | 超能力者 | gravity hit / short levitation + swap of two training enemies / temporary two-point portal |
| BUILDER | マッドサイエンティスト | energy shot / tracking autonomous turret / 3D mobile UFO demonstration and blast |
| BEAST | 魔獣使い | beast impact / AI-companion summon with follow and target damage / giant beast |
| ZOMBIE | 呪術師 | damage + short slow curse / three attacking undead units / oversized dark creature |

The display names are the new OWNER-approved direction; internal IDs remain unchanged to minimize migration risk. Abilities target **test dummies only** for safe preview and **do not demonstrate finished real PvP**.

## Try privately in Roblox Studio

1. On an isolated Studio copy (never the production place), create a **Script** in ServerScriptService.
2. Paste the complete file `SevenHeroArena.server.luau` into that Script.
3. Enter **Play**. Find the seven job stands about 42 studs from the existing SpawnLocation; a flat test floor and twelve red test dummies appear.
4. Use the stand ProximityPrompt to choose a job. Equip a Tool from the backpack (or Android hotbar): A=basic, B=special, C=signature. Each can be activated against the training dummies, which respawn.
5. Stop Play to remove all prototype entities. Script is inert outside Studio because of `RunService:IsStudio()`.

## Safety / honest test status

- Preview **works only when installed into a Studio test place**; GitHub code existence is not a Studio test record.
- No source was added to the canonical RC, no normal merge or game Publish, no DataStore writes, no real network Remotes, no game economy modifications.
- No source-exact Rojo/native Lua compiler, Studio 2-client, Android FPS/Art/FUN or OWNER acceptance has run for this slice yet. It remains **SOURCE_WIP / ENGINE_UNKNOWN / RC_NOT_INTEGRATED**.
- This is a playable mechanics scaffold, **not** the finished art/style/animations, enemy-team AI, map, egg capture or advanced skill trees. Role-specific full product quality remains NO_GO.
- Follow the existing Game/HUD/SevenJobs author PR #297/#303/#305 and latest private role fixes #476/#481 for all shared integration paths. No edits to another writer's path. #220's authenticated RC writer alone decides any source-selective official adoption.

## Next concrete source integration order

(1) Lock existing author source-IDs and map all 7 roles/21 skills; (2) author-integration into genuine Game/Tool/HUD for real server role authority and mobile; (3) add physical character models, locomotion and hit animations at #420 art quality; (4) test opponent interaction, anti-permaCC, egg carrier, death/rejoin/respawn, AI/rideable, missiles/vehicle controls and anti-P2W; (5) source exact QA → authenticated RC CAS → real Studio/Android/competitive/OWNER verification.

Roll back by removing the single preview Script, which removes all spawned prototype objects on next Play.