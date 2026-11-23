# RC86 TRAPPER two-endpoint team warp → the one official REAL66 game

Verified historical original: RC86 artifact 14161823401 (`P0D_RC86_SIEGE_V3_STAGE_WEAPONS_UNDEAD_PRIVATE.rbxlx`), script `ServerScriptService/TrapRaidersS1/TrapperWarpService`, SHA-256 `e2ec30532a2c8c8de6cc811dff856c78d15ff6f5bf36942373f913c65af8bfdc` (10,445 bytes). Historical feature was a **two-stage team portal** (40-second life, 3 shared rides, 16-stud separation, 2.5-second rider cooldown), not the same as the V3 TRAPPER's existing one-shot `safeMove(20)`.

**Actual port:** preserve V3's original TRAPPER C short safeMove and add exactly one optional server-authorized pair. First C creates entrance; second C creates exit; ProximityPrompts allow same-team rides in TEAM or owner-only rides in battle royale. No player-supplied destinations or Remote. Server checks real current round, role, team, memberships, castle alive, no eggs, no death/downed/seats, range, wall LOS, anchored floor/slope, arena bounds, destination overlap, session age, cooldown and shared use count. Round/role cleanup removes old portals. Studio-only, no new store/reward/damage/HP writer.

One selected source changes: `ServerScriptService/EGGRUMBLE_SevenRoleCombat` (the preexisting sole role/combat source); original other 64 REAL65 selected routes byte/class/path remain unchanged, and selected one additional RC86 exploration Script stays unchanged in final REAL66 (66/66). Previous #864 wind/#865 six weapons/#869 pickup authorization/#870 reach/#874 exploration/#878 BEAST+WEAPON dojo/#879 Starfall/#882 undead order and existing OFF63 retained.

**Formal promotion contract:** only existing `rc/p0d-s1-kids-rc01`, fresh expected HEAD and nonforce B-writer adoption, exact PR-head Native65+REAL66/Rojo65+REAL66 plus source lock, official same-new-HEAD CI, archived Studio Place and ZIP. No authorship approval waiting, no Work/Codex, no main write, Roblox publish/paid trades/spend OFF.

**Engine reality:** Studio solo+2-client, Android15, child FUN/art and OWNER acceptance are NOT_TESTED / NO_GO. This is an incremental old RC86 behavior port, not proof of complete 48-feature legacy parity. Older original proprietary binary preserved as immutable evidence.

Rollback: the one previous Combat source is copied byte-exact to `TRAPPER_OFF_EXACT_ORIGINAL_COMBAT.luau` in the artifact outside the selected project, and previous official REAL66 git HEAD + original Place remain valid.
