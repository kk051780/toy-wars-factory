# EGGRUMBLE — product name canonicalization (OWNER 2026-11-16)

**Official player-facing game name: EGGRUMBLE** (exact uppercase). Do **not** continue displaying "TRAP RAIDERS", "Trap Raiders" or "TRAP_RAIDERS" as a title.

This is a **real source-only branding change candidate**, not a completed official RC integration or a published Roblox Experience metadata rename.

## Source changes in this candidate

1. `releases/P0D_S1_KIDS_RC01/src/client/HUD.client.luau`: changed boot/loading banner, lobby title, round countdown and results line to **EGGRUMBLE**. During ACTIVE gameplay the existing minimalist scoreboard remains untouched.
2. `releases/P0D_S1_KIDS_RC01/default.project.json`: change **Rojo build project name** to `EGGRUMBLE_S1_CHAT_RC01`; keep existing script instances/paths identical.

## Important migration boundaries

- **Do not rename internal identifiers**: `TRAP_RAIDERS` internal game ID, `TrapRaidersS1Remote`, `TrapRaidersS1HUD`, `TrapRaidersShared`, `TrapRaidersS1`, `TrapRaidersCoach`, repo `toy-wars-factory`, existing PR/issue IDs, branch names, existing save keys, or immutable historical artifacts. Internal renaming can break Remote/DataStore/contract/source-lock compatibility.
- Real, active in-Place HUD may be assembled from more recent authors/overlays than the base file. **RC integrator #220 must patch the actually selected, newest source** rather than assuming an old base script is what the latest game runs. Ensure all visible surfaces: lobby, character selection, play hints, scoreboard where name is displayed, results, boot banners, Studio Place project title, Android title.
- No extra persistent text overlay is introduced in ACTIVE; the OWNER previously rejected obstructive always-on HUD.
- **Roblox Experience public/private title, universe/place metadata and thumbnail** are platform-side settings, *not* changed by editing Rojo project name. Only an authenticated owner-authorized platform operation should rename these; do not Publish or change account settings automatically.
- `TRAP RAIDERS` historic mentions in older Github Issues and existing approvals remain readable for traceability; future work should use `EGGRUMBLE (formerly TRAP RAIDERS)` once, then `EGGRUMBLE`.
- Change in-game brand without changing the rules of egg capture/return, 7 classes, role selection, DataStores or PvP contracts.

## Acceptance gates

- Verify current official RC HEAD and rebuild with exact, latest effective HUD/Game, not just the historical base profile. Confirm visible name in opening, lobby, role picker, countdown and results on actual Studio build and Android.
- Verify neither networking nor persistence keys changed and gameplay controls remain intact. Preserve no-duplicate Game/HUD/Remote and existing rollback.
- Source-exact Luau/Rojo check on same RC HEAD, capture before/after screenshots for all brand surfaces, OWNER confirms.
- This candidate's status: `SOURCE_WIP / RC_NOT_INTEGRATED / ENGINE_UNTESTED / ROBLOX_METADATA_NOT_CHANGED`.

Rollback: revert these two files only; no other game script/schema was modified by this branding slice.