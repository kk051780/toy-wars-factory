# Legacy RC85/RC86 → V3 single runtime, isolated exploration port

- FEATURE_ID: GQ8_LEGACY_RC85_86_EXPLORATION_INTAKE_20261119
- Source: `EGGRUMBLE_LegacyExplorationBridge.server.luau`
- Formal target: ONLY `rc/p0d-s1-kids-rc01`, maintain latest formal REAL65 and its successor changes.
- Historical original author sources: [RC86 official-provenance private artifact run 43714858562](https://github.com/kk051780/toy-wars-factory/actions/runs/43714858562) 86 original scripts, and [RC91 successor run 43767133429](https://github.com/kk051780/toy-wars-factory/actions/runs/43767133429) 86 original scripts.
- Included behavior: four 4/4 realm discoveries and 6/6 star shards; server-side per-match cosmetic-only progress and brief completion glow in V3 TEAM/BR world.
- Original art/behavior reference: `TrapRaidersS1/RealmHunt` + `TrapRaidersS1/StarShardHunt` (legacy86). New bridge uses actual V3 Host-owned `TEAM_Arena/BATTLE_ROYALE_Arena/TacticalBattlefield`; cannot activate in empty lobby or public servers.
- This is *not* duplicate Game/Remote/Store/HP/Combat. Studio only; no persistent XP/reward, no permanent overlay, no leaderstats or purchases. The quest is optional to any win condition.
- Current real game 65 scripts, #864 legacy Assassin Wind, #836 source QA, #863 late Host watcher, 7 roles and round/session controls MUST remain intact; do not reintroduce legacy Game/HUD/TrapRaiders Remote.
- 10 bounded prompt objects max per arena, 4 landmarks+6 shards, no physical collisions. Require same-mode active player, non-eliminated, alive Humanoid, server-measured 10 stud reach, server Prompt LOS. State per arena epoch; cleaned when arena destroyed.
- Tests: `test_bridge.py` and workflow native pinned Luau. CI pass is *source-only* and not same-HEAD formal 66/66 Rojo proof.
- B writer intake: fresh HEAD, source-selectively add this one Script under ServerScriptService to existing V3 composer, update selected profile to **REAL66 only after actual 66 source build**, verify 65 originals byte-exact (including newer #864 wind and #865 stage weapons), project path/class, Native66/66, Rojo66/66, OFF65 byte-exact, and nonforce expected-SHA CAS. Produce official Place and receipt. Do not just merge the branch and call the game adopted.
- This cannot complete RC85/RC86 full heritage by itself; keep #476/#479/#481 original canonical private sources for independent port; do not claim full lineage inclusion.
- Studio solo/2client, Android15min, ART/FUN/OWNER acceptance: NOT_TESTED, PRODUCT_NO_GO.
- Rollback: omit only `EGGRUMBLE_LegacyExplorationBridge`; retain all actual canonical V3 scripts and previous historical original binaries. Public publish/paid trade: OFF.
