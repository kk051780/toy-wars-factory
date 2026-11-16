# EGGRUMBLE V3 – optional GQ client FX clarity / active source repair

**Dedicated source:** [DRAFT #503](https://github.com/kk051780/toy-wars-factory/pull/503), original #482 author pinned at `fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9`. 21 original Luau paths and bytes unchanged. #498 was withdrawn due to FX overlap; THIS #503 is the sole continuing client FX candidate. The existing #485 `ART_*` decorative geometry distance-LOD and #504 hit-confirmed audio are separate.

## Actual implementation / corrected safety boundary

- **Seven secondary decorations only:** `WarGod_`, `Mage_`, `Assassin_`, `Esper_`, `MadScientist_`, `Beast_`, `CurseMaster_`. No original game/skill changes and **never hide** the core attack `FX_*` FLASH/RING, `ULTIMATE_*`, server-confirmed `EGGRUMBLE_KO_BURST`, existing real-hit Highlights or boss danger signs.
- Scope target exclusively to existing `workspace.EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW.TEAM_Arena` and `BATTLE_ROYALE_Arena`. Unrelated map, inventory, castle, UI, and lobby Parts with lookalike names must not be hidden.
- Pure `EGGRUMBLE_CombatFXBudget.luau` restricts only SECONDARY objects: touch far threshold 85 studs, desktop 130, protected within 40, 9-stud hide/show distance hysteresis, reduced-effects preference, and bounded overload response.
- `EGGRUMBLE_CombatFXClarity.client.luau` watches newly added transient effect Parts (no full scene enumeration), max 128 tracked, update every 0.22 s, only alters `LocalTransparencyModifier`, restores on removal. Original server creates/deletes/replicates FX unchanged. **Not a network/CPU/server-Part count reduction**.
- Studio-gated optional candidate; **non-Studio Android effect is not active** until the original gameplay author and sole RC writer explicitly wire and test real live builds.

## Source exact and regression proof

`EGGRUMBLE_V3_FX_CLARITY.project.json` maps the exact original #482 21 sources plus our two new StarterPlayerScripts (=23), with no duplicate Game/HP/Store/Remote. The **actual native functional** spec `tests/EGGRUMBLE_CombatFXBudget.spec.luau` covers protected core/ultimate/KO, near distance, invalid distances, touch/desktop, user preference, load, and no-flicker hysteresis. Python negative source/ownership tests verify original source preservation, class placement, arena scope and no gameplay modification. CI also runs pinned native Luau compile 23/23 and byte-exact Rojo private Place 23/23. Source QA is **not** Studio Play or Android performance measurement.

## ROLLBACK and official RC contract

Drop **only** `EGGRUMBLE_CombatFXBudget` and `EGGRUMBLE_CombatFXClarity` from the private Rojo project's `StarterPlayerScripts` entries (or omit these optional 2 scripts entirely). No data migration or original script reset.

#220 must first reconcile current #482 author 21 source with #484 actual 26-source game+AI+ART+SCORE composer (plus live #485/#487), then source-selectively overlay these 2 scripts on the **current** composite. Require nonforce authenticated CAS, full same-HEAD Native+Rojo SourceExact, receipt/ZIP+Place byte, and no claim conflict. Actual TEAM/BR 2-client Studio, 15-min low-end Android FPS median/p10, heat, real damage equality, distant telegraph visibility, FUN/ART and OWNER evidence remain separate. **STUDIO_NOT_TESTED / ANDROID_NOT_TESTED / ART_NO_GO / FUN_NO_GO / OFFICIAL_RC_NOT_INTEGRATED**. No main edit, unauthorized merge, Roblox publication, spending or Windows action.
