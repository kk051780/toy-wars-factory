# P0 #431 — Live-safe castle art, Stage 1 (source QA only)

This package contains a **new** `P0DLiveCastleArt.server.luau` Script, distinct from the seven older Studio-only source overlays. It is a reversible prototype, NOT a tested/published production release.

## Why the old seven Studio arts cannot just be enabled

The true original `Game` calls `MapBuilder.build(Config)` unconditionally and builds `TRAP_RAIDERS_S1` with two existing team towers each. The Studio-only parent `Owner361CastleBattlefield` goes further: resizes `GrassArena` from 250×142 to 370×294, repositions physical boundary walls and adds collidable scenery. Unconditionally removing its Studio guard would change gameplay map collision/paths in production. Old `CastleDetailArt` and `FantasyWorldArt` additionally depend on the Studio-expanded scene, so changing only their guards would not load them.

This patch **does not touch** any of those original sources. It uses only MapBuilder's original towers, producing 36 large, low-cost non-colliding roof/banner parts, zero shadows, zero lights, zero UI, zero remotes, no heartbeat. It may improve production-visible castle silhouette, but actual rendering and its aesthetic quality remain unproven.

## Private Studio-only functional preview (not a production parity certificate)

1. Open candidate `P0D_LIVE_CASTLE_SAFE_PRIVATE81.rbxlx` in Roblox Studio as a local test, without publishing. Save a local backup before editing.
2. Open Explorer → `ServerScriptService` → `TrapRaidersS1` → `P0DLiveCastleArt`. Set a **Boolean Script Attribute** `EnablePrivatePreview` to `true`. Do this **before** pressing Play.
3. Start a private Solo session. Check `Workspace.TRAP_RAIDERS_S1.P0D_LIVE_SAFE_CASTLE_ART_V1`. Expected: `ActualArtPartCount=36`, `AdditionalCollisionCount=0`, `AdditionalLightCount=0`, `SourceQAOnly=true`.
4. Inspect near original team towers at approximately x=±115, z=±35. Verify the original egg/core/score objectives, walking and attack all behave as before. Do not infer quality merely from the attribute count; inspect actual roof shapes and occlusion.
5. Stop. Restore `EnablePrivatePreview=false` (or remove attribute) to recover the original Studio preview without modifying the 80 authored scripts. The optional prototype source can be removed entirely to roll back.

**Major limitation:** In ordinary Studio Play, the old Studio-only overlays can still run, including `Owner361CastleBattlefield`. Enabling this preview adds the new castle ornament *on top of those old Studio visuals* and **cannot simulate a true non-Studio game**, even if the script creates its folder. For a real 1:1 live-vs-Studio comparison the OWNER must separately authorize a private production-like engine test; no ChatGPT branch/PR here has permission to publish Roblox or change the player's Windows PC.

## Evidence and sign-off

- Source exact RC80 parent: `1bf25e7e83a38ecbbef588309edd7217b9f39c67`.
- Source-only candidate: 81 Luau sources; all original 80 byte-identical. Single added Script.
- Real Rojo Place compiled and verified via PR CI; original Game, HUD and Owner361CastleBattlefield Instance-to-Source identities match.
- Screenshot evidence 0/32; real low-end Android 15m median>=30/p10>=25 not tested; first-3-minutes kid FUN >=4/5 not tested.
- Gate: `LIVE_ART_NO_GO / ART_NO_GO / MOBILE_NO_GO / FUN_NO_GO`, `OWNER_ACCEPTED=0`.
- Remaining P0: the other seven ART groups and the normal nonStudio Parent world still differ from the Studio experience.

Keep PR isolated. Only B #220 may source-selectively adopt through current-head non-force CAS; no regular PR merge, main change, Roblox Publish, purchases or unauthorized computer use.
