# RC85/RC86 legacy Crystal Canyon and Meteor 4th route: ONE cumulative V3 RC

## Concurrent integration resolved without losing features

The owner's only official branch is \`rc/p0d-s1-kids-rc01\`. PR **#879** has independently and successfully *already integrated* \`STARRY_PATH_V1\` (ten timed star slabs, two switches, 16s/7s, occupied player safety) into the EXISTING \`EGGRUMBLE_RealmBattleCore\` script of the current formal REAL66. It is NOT correct to create second star stones, a new Star owner, or rewind the official branch to the older pre-#879 parent.

**This PR now ports ONLY missing original RC85/RC86 \`WCS_F01_C01\` and \`METEOR_FOURTH_V1\`.** One new *environment-only* Studio Script builds an elevated canyon with the always-open safe route, two Mojuron gate switches, timed 14s shortcut/cooldown4s, symmetric 6-step access, and the independent meteor 55s quiet +5s warning +22s physical fourth bridge. The existing #879 STAR path is REQUIRED as an explicit dependency and *reused*, not replicated. Four physical routes exist in the same canyon: safe bridge at z=30, managed gate at z=15, existing #879 ten-star path at z=0, weather meteor at z=-17. Star path center shares existing Realm location (floor center, +12 vertical, -175 Z relative). ORIGINAL tactical floor is not destroyed or replaced.

## Real old source evidence
The prior CI artifact RC85 ID **14158848286** contained 85 genuine Luau source bodies; RC86 ID **14161823401** contained 86. Source XML was extracted for original modules:
- \`TrapRaidersS1/WCS_CrystalCanyon\` source SHA256 \`17ee851bda13076effdd81de68346f83b8d82366ec7b09de4f7cd938a1b78198\`, 2 banks, 2 mole triggers, safety bank, 14s open, 4s cooldown, return steps.
- \`TrapRaidersS1/StarfallPath\` SHA256 \`f88ec4005a5cb611a2f5acfd7eb67309f2de3799a2f51ebe6208bc2ee3670b35\`, 10 stones and 16s bridge, **already included via PR #879**.
- \`TrapRaidersS1/MeteorFourth\` SHA256 \`d4894535eec6f1bb40c1e17a9626e1bcd98a00307ad0db858c4073e6b92b4bd2\`, fourth route 55+5+22s; this PR source-selectively adapts it to the single current V3 game, only after original #879 star exists.

## Source selection / no loss
Current official REAL66 has 65 existing V3 scripts and one RC86 4-Realm/6-StarShard exploration bridge. PR #879 modifies a single existing Realm source; this patch **does not overwrite it**. \`compose_real67.py\` consumes the *just-generated* same-head formal REAL66 project+receipt, confirms **all original 65 byte-exact SHA** and the 66th original exploration script byte-exact. It then adds exactly ONE new non-Game script:
\`ServerScriptService/EGGRUMBLE_LegacyCanyonRoutes\` class \`Script\`.
All prior 66 script routes, bodies, classes, lineage and existing field/castle/lobby/Combat/Swarm/Item/Dojo/Realm features are unchanged. No additional Game/Store/score/HP/Remote, no currency, no monetization. Both TEAM and BR maps, player-alive + selected mode + actual server wall LOS gates, no bridge closure while anyone occupies, no 20-second permanent disarm or second star scene.

The official workflow now compiles all **67/67** actual Luau sources with pinned Native, builds verified Rojo67, checks exact previous official 66 against OFF66 rebuilt, retains original OFF65/OFF63 chain; fresh current parent CAS, PR-head green, formal same-head green and artifact bytes before reporting adopted. \`test_runtime_contract.py\` rejects duplicate star sources and checks time/authorization gates. CI compile does **not** prove actual Roblox client runtime.

## Still not fully migrated
These two unique old-S1 feature flags close only the physical old WCS+meteor gap. **Do not count already-adopted #879 STARRY_PATH twice.** Old RC85/86 still have 48 flags with partial semantic parity. Twin-biome creatures/evolution/mastery, first-90 onboarding, exact Gorogan 3D etc require source-level integration and actual Studio tests. Real two-client, Android15min, visual art, FUN/OWNER remain NOT_TESTED/NO_GO. Never create another official RC branch, change main, publish, spend, use Work/Codex or wait for original author acknowledgement.
