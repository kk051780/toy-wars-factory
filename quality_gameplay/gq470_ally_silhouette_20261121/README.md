# GQ470 FB-015 — teammate silhouettes / actual A-source visual

**Purpose:** make nearby teammates identifiable in the crowded two-team egg-and-castle brawl without filling the HUD or revealing enemy/Assassin stealth through walls. A discrete, desaturated rim follows only up to two nearby touch-device / three desktop, alive, visible allied *player* characters within 45 studs, with occluded depth mode. No bots, parts, damage, HP, scoring, Remote, server, Store or gameplay authority.

**Non-overlap:** #970/#973 existing 16-source art composite, #960 minimap team pins, #957 castle guards, #924 bot overhead labels, #972 self-damage pulse, #968 running dust. **Alternative visual competitor:** PR #976 2-Part/avatar team-crests address the *same player recognition moment*. Do not deploy both; a hard conflict check rejects the #976 client runtime route in the input profile and the B220 exact source packet declares its exclusive alternative. This one new player-only LocalScript has its own selected route `StarterPlayer/StarterPlayerScripts/EGGRUMBLE_AllySilhouette`. It never edits those existing sources.

**Limits:** `TOUCH_MAX_ALLIES=2` / `MAX_ALLIES=3`, scan every 0.75s (no RenderStepped), occluded only, fill invisible, outline 68% transparent, no added Parts or UI, immediate cleanup on death/respawn/team change/stream-out/cloak/reduced-effects (up to 14 scoped event watches per visible ally, all disconnected on clear). A teammate wearing stealth/invisibility is excluded; enemies are never highlighted. ReducedEffects attribute `EGGRUMBLE_ReducedEffects` or optional `GQ470_DisableAllyOutline` disables the cue.

**User value:** friend-or-foe recognition amid dense neutral hordes and visual continuity of a 3D world without another floating Billboard. This is a hypothesis, not measured visual improvement.

**Build:** using exact official PRIVATE REAL69 companion artifact from same-head Actions #44695199140 and official `e80973c354f14a0d0088577f3cc1a875454f0f8f`, `compose_official70.py` leaves all 69 original selected Source/Class bytes unchanged and adds one LocalScript, then the A-only workflow builds OFF69+ON70 via pinned Native Luau and Rojo. Its source-select packet allows #220 to review ONLY the one new source after #910 one-match P0 and #250 value decision, not merge this PR as a whole.

**Rollback:** omit the one LocalScript. OFF69 original Place must remain byte-identical. No change to the existing `rich51` ACTIVE_RUNTIME or the formal RC.

**Status:** source evidence is valid **only** when the latest PR HEAD's same-SHA CI succeeds; Studio solo/2client, actual view obstruction, Android 15min FPS, 32 PC/Android comparison photos, kid FUN, human ART, and OWNER acceptance are **NOT_TESTED**. `ART_NO_GO`, `PRODUCT_NO_GO`, `OWNER_ACCEPTED=0`, `FORMAL_RC_INTEGRATED=NO`. A pass in static or build QA cannot lift these gates. Original route behavior and visual compatibility must be checked in Studio before B final adoption.

## Manual ART420 / P0 retest (not yet performed)

1. First prove the player's **own** avatar is present in the exact chosen PRIVATE Studio Place using **Play (F5), not Run (F8)**. Check movement, jump, camera follow, death/respawn, Output errors. The reported absent-player P0 #364 must remain RED until confirmed in Studio; this optional teammate cue cannot fix initial spawn.
2. With Studio's two-client play test, join RED and BLUE through the actual game UI. Verify teammates nearby show a muted **Occluded-only** outline, while opponents, neutral players, cloaked character/Player, and distant players never show one; test a solid wall, R6 and R15 partially transparent limbs, team changes, humanoid death, repeated respawn and streaming.
3. Turn on `EGGRUMBLE_ReducedEffects` and `GQ470_DisableAllyOutline` while an outline is visible; it must disappear immediately. Confirm at most **2** highlighted allies on a touch device and **3** on non-touch desktop, with no retained instances/watches after leaving range or stream-out. PR #976 team shoulder crests are an exclusive alternative: never enable both at once.
4. If P0 and source acceptability are established, record raw same-camera **8 scenes × PC/low-Android × BEFORE/AFTER = 32** actual images, real human art ratings and 15-minute low-end Android FPS/thermal/no-crash evidence. No screenshots or runtime/owner passes have been collected by this source-only PR.

All statuses remain **NOT_TESTED / ART_NO_GO / MOBILE_NO_GO / FUN_NO_GO / OWNER_NOT_ACCEPTED / NOT_FORMAL_RC** until real evidence and #220 authenticated B non-force CAS, not because Native or Rojo passed.
