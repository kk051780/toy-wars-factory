# GQ470 FB-015 — teammate silhouettes / actual A-source visual

**Purpose:** make nearby teammates identifiable in the crowded two-team egg-and-castle brawl without filling the HUD or revealing enemy/Assassin stealth through walls. A discrete, desaturated rim follows only up to three nearby, alive, visible allied *player* characters within 45 studs, with occluded depth mode. No bots, parts, damage, HP, scoring, Remote, server, Store or gameplay authority.

**Non-overlap:** #970/#973 existing 16-source art composite, #960 minimap team pins, #957 castle guards, #924 bot overhead labels, #972 self-damage pulse, #968 running dust. This one new player-only LocalScript has its own selected route `StarterPlayer/StarterPlayerScripts/EGGRUMBLE_AllySilhouette`. It never edits those existing sources.

**Limits:** `MAX_ALLIES=3`, scan every 0.75s (no RenderStepped), occluded only, fill invisible, outline 68% transparent, no added Parts or UI, cleanup on death/despawn/team change/leave and reduced-effects flag. A teammate wearing stealth/invisibility is excluded; enemies are never highlighted. ReducedEffects attribute `EGGRUMBLE_ReducedEffects` or optional `GQ470_DisableAllyOutline` disables the cue.

**User value:** friend-or-foe recognition amid dense neutral hordes and visual continuity of a 3D world without another floating Billboard. This is a hypothesis, not measured visual improvement.

**Build:** using exact official PRIVATE REAL69 companion artifact from same-head Actions #44695199140 and official `e80973c354f14a0d0088577f3cc1a875454f0f8f`, `compose_official70.py` leaves all 69 original selected Source/Class bytes unchanged and adds one LocalScript, then the A-only workflow builds OFF69+ON70 via pinned Native Luau and Rojo. Its source-select packet allows #220 to review ONLY the one new source after #910 one-match P0 and #250 value decision, not merge this PR as a whole.

**Rollback:** omit the one LocalScript. OFF69 original Place must remain byte-identical. No change to the existing `rich51` ACTIVE_RUNTIME or the formal RC.

**Status:** SOURCE_WIP until CI confirms the exact head; Studio solo/2client, actual view obstruction, Android 15min FPS, 32 PC/Android comparison photos, kid FUN, human ART, and OWNER acceptance are **NOT_TESTED**. `ART_NO_GO`, `PRODUCT_NO_GO`, `OWNER_ACCEPTED=0`, `FORMAL_RC_INTEGRATED=NO`. A pass in static or build QA cannot lift these gates. Original route behavior and visual compatibility must be checked in Studio before B final adoption.
