# GQ648 — grounded V3 lobby / safe first spawn (RC31 candidate)

## Distinct product defect

The actual original `EGGRUMBLE_LobbyCastleModesPreview.server.luau` creates seven role stands, five defense stands and TEAM/BR portals, but never creates a supporting lobby floor or a neutral SpawnLocation. The original V3 Studio project also has no Workspace floor or spawn mapped. A newly entered character can fall into the void before selecting a match. This is a source-backed risk, NOT yet a Studio-confirmed reproduction.

Existing #539 improves labels, #611 validates ProximityPrompt reach, #615 improves queue ETA; none supplies the missing physical lobby. No duplicate lobby session manager is introduced.

## Fix / safety boundaries

* Inject exactly one anchored 118×4×144-stud physical lobby floor, relative to the original Host `root`, covering portal, role and defense stands. Add exactly one neutral SpawnLocation at lobby center.
* Bind both existing and future Players on CharacterAdded. Route a living, current Avatar into the lobby floor only when the player has no active TEAM/BR session; never move participants inside a live match.
* Reuse the one existing `EGGRUMBLE_LobbyCastleModesPreview` Script. 31 total scripts, 30 source byte-identical. One Host addition only; no new Game, Remote, Save, Score, inventory, battle authority, publication or payment.
* OFF rollback is exactly the preceding GQ527 selected Host; no change to original 30 other scripts.
* Earlier #527 BotActors, #499 deadline, #615 queue, #582 zombie GUARD, #618 BEAST, #611 prompt and all eight domains retained.
* One test file contains duplicate/missing-anchor/session negative tests and 31-script mapping/source-exact positive checks. Official companion workflow uses Native Luau31/31 and true Rojo Source/Class31/31 after the previous GQ527 selection, with separate GQ648 receipt and final actual Studio Place SHA.

## Status and future acceptance

`SOURCE_PATCHED`, candidate CI required. This PR does not modify `main`, the existing official `rc/p0d-s1-kids-rc01` branch, Roblox Studio or Android. Official SOURCE admission requires #220 sole authenticated, non-force expected-head CAS, then same official HEAD V3 and legacy S1 CI, actual artifact checks, feature flag/evidence accounting, and rollback. The independent #646 late-death Rules and #647 builder Host are concurrently in flight; if adopted first, rebase from newest official HEAD and rerun all 31-source tests instead of blind cherry-picking stale workflow.

Actual Studio startup with no preexisting SpawnLocation, with a disabled/remote SpawnLocation, SOLO/TEAM/BR 2client, respawn, win/replay, Android 15-minute and child FUN remain `NOT_TESTED`; never mark PRODUCT_GO based on source-only CI.
