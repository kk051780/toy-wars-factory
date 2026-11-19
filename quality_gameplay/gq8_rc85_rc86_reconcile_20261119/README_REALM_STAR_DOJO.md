# RC85/RC86 → formal V3 REAL65: non-duplicated exploration + dojo

**Formal RC is ONE Git branch**: \`rc/p0d-s1-kids-rc01\`. Its source label REAL65 means 65 actual selected Luau routes, not percentage complete or proof that all old S1 flags have transferred.

## Original files, not just issue titles

Actual original CI artifact \`14158848286\` (RC85 85 sources) and \`14161823401\` (RC86 86 sources), plus verified RC86 wall-LOS \`14177514150\`. These artifacts contain exact source-lock and old \`RC_FEATURE_LOCK\` (48 enabled flags). Core three inputs:
- \`ServerScriptService/TrapRaidersS1/RealmHunt\`: 4 distinct SKY/SEA/EMBER/STAR discoveries, per-player counters, cosmetic-only, no 2nd Game/Store.
- \`ServerScriptService/TrapRaidersS1/StarShardHunt\`: 6 session-only collectible fragments, no currency/save, originally placed on old Starry Path.
- \`ServerScriptService/TrapRaidersS1/DojoRules\` + \`LobbyDojoIsland\`: real physical lobby and pure skill policy \`BEAST\` / \`WEAPON\`, levels 1..5, level costs 10/15/20/25 XP, 180s per skill, real friends training together 1.5x XP, PvE-only 5% per level capped 20%.

PR #868 **already implemented and native/Rojo verified** a separate \`EGGRUMBLE_LegacyExplorationBridge.server.luau\` REAL66 *candidate*, but its extra 66th server Script is NOT selected in the official REAL65 composer. Do **not** enable that 66th candidate *as well* as this Realm port: duplicate quest landmarks/markers would result. Reuse its verified design, source markers and guard tests, and port discovery into original V3 Realm owner instead, preserving the selected **65 of 65** original source route contracts.

## Implementation, exact existing owners (NO SECOND GAME)

\`port_realm_shards_dojo65.py\` is a post-#870 source-locked overlay. All 65 original route bytes/class are checked against the official receipt before edits; exactly 3 *already-modified* selected routes are changed; the other 62 stay exact. No new script/remote/HP/KO/Store/round/egg/score authority.

1. **Current \`EGGRUMBLE_RealmBattleCore\`** already owns TEAM and BR physical arena discovery, sea/sky aircraft/subsea, and storm world. It now additionally places four reachable 3D landmark prompts and six small star fragments in the same current arena; uses the Realm script's own server-side current-mode/valid-castle/elimination/humanoid eligibility and original wall-safe prompt path. Per-current-mode/round player attribute counters only; no source spawns independent old S1 world. Attributes cleaned when arena destroyed. Cosmetic-only; 10 objects per arena, no persistence or gacha.
2. **Current \`GQ8_LobbySocialPlaza\`** already owns physical Studio-only social scene. Adds a walkable little dojo with two real practice pads; server authorizes proximity and no active TEAM/BR queue. 1-second *server-measured* progress only while standing on chosen pad; 180s bounded per skill, level1→5 with the original cost table. 1.5x if *genuine Roblox friends* are co-training, cached per pair to avoid repeated friend API work. PlayerRemoving clears session profile; no DataStore/paid boost/UI-guide.
3. **Current \`EGGRUMBLE_SevenRoleCombat\`** consumes the server-only dojo rank ONLY in existing \`neutralAndBotHit\`'s neutral Swarm damage amount. PvP player, castle, bot, guardian, summon and egg authority remain unchanged. An actual BEAST role consumes BEAST rank; other players' verified basic M1 consumes WEAPON rank. No client action to set levels and max multiplier 1.20.

A source QA marker includes all 3 old flag candidates:
- \`REALM_HUNT_V1\` → adapted functional 4/4 Realm collectibles.
- \`STAR_SHARDS_V1\` → adapted functional 6/6 collectible shards (old \`STARRY_PATH\` 10-stone physical route *not* thereby included).
- \`FB007_LOBBY_DOJO_PHYSICAL_V1\` → adapted 2 real training stations, exact original Dojo XP rules, bounded +20% neutral-only PvE.
Formal bridge source \`EGGRUMBLE_LegacyExplorationBridge\` remains repository-only reference; no duplicate selected Script.

### Non-loss validation and hard limits

1. Reproduce the original deterministic official selected sources with previous #864 wind + #865 RC86 weapon pickups + #869 15 item prompt aliases + #870 neutral-only wall-safe reach. Apply this helper once after those original overlays.
2. Recheck all 65 \`route/class/path/sha256/bytes\`, 9 existing patched route owners unchanged (the same existing 3 already in 9), exact OFF63, pinned actual Luau Native 65/65, pinned Rojo 65/65, official same-head artifact and .rbxlx. Do not merge if CI not GREEN at fresh PR HEAD and current official base.
3. Real Studio (1/2 clients), Android15min, player-perceived art/FUN, 4+6 accessible terrain navigation, physical dojo friend co-training, neutral PvE damage only and no PvP, post-join/rejoin cleanup: NOT_TESTED until actually run in Roblox. No public publish, Work/Codex, paid transactions, main changes.
4. **Remaining old RC85/86 48-flag semantic feature audit is open**: \`STARRY_PATH\`, original CrystalCanyon bridge and meteor, twin biomes + 4 original NPC species and bond training, saved PvE mastery/beast evolution, original 3D castle/Gorogan, six-skill durability, first-90 onboarding, etc. The source being 65 is not proof all are done.

Regression-first changes only, no author acknowledgement needed, use certified #220 same-head CAS/nonforce. This artifact is an independent real functional increment, NOT permission to declare the entire legacy cumulative project finished.
