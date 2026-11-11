# TRAP RAIDERS S1 · Context-aware objective prompts (client-only)

**Status:** `PUBLIC_SOURCE_READY_OPTIONAL__NOT_IN_RC__NOT_STUDIO_TESTED`.

Prevents confusing original native proximity UI actions from being shown to players who cannot perform them. It uses ONLY local `ProximityPrompt.Style`, preserving the existing server `.Enabled` and server `Rules.canSteal/canScore` checks.

| Match state | Own egg UI | Enemy egg UI | Own score-pad UI | Enemy score-pad UI |
| --- | --- | --- | --- | --- |
| LOBBY / COUNTDOWN / RESULTS / invalid | hidden | hidden | hidden | hidden |
| ACTIVE, not carrying | hidden | visible iff server enables it | hidden | hidden |
| ACTIVE, carrying enemy egg, own egg home | hidden | hidden | visible iff server enables it | hidden |
| ACTIVE, carrying, own egg stolen or unknown | hidden | hidden | hidden | hidden |
| Dead / respawning | hidden on fresh snapshot | hidden | hidden | hidden |

This is a narrow **presentation fix**, not a new FTUE tutorial overlay, world-space navigation marker, server-side interaction permission or training dummy. Original S1 map uses `RED_CASTLE/BLUE_CASTLE` with `RED_EGG/BLUE_EGG` and `RED_SCORE_PAD/BLUE_SCORE_PAD`. Only those FOUR prompts are locally managed.

**Safety:** no `RemoteEvent` creation, `FireServer`, `Prompt.Triggered`, or modifications to `Prompt.Enabled`, player position, damage, egg, score, XP, datastore, purchasing or match timing. If an existing prompt Style is Custom before this script sees it, leave it alone. A current malformed snapshot fails closed; stale serials are ignored.

**Validation:** `python -m unittest discover -s tests -v` and SHA manifest. Python is a scenario oracle/static interface check; it does **not** execute Luau or Roblox rendering. `docs/INTEGRATION.md` documents sole-owner #220 integration and rollback. No changes to protected `main`, official `rc/` or Roblox public experience.
