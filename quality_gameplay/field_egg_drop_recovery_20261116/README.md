# EGGRUMBLE GQ — Fallen egg carrier field-recovery candidate (2026-11-16)
Status: SOURCE_WIP / SOFT_CLAIM_NOT_GRANTED / OFFICIAL_RC_NOT_CHANGED / STUDIO_NOT_RUN / ANDROID_NOT_RUN / OWNER_NOT_ACCEPTED.

## Distinct cross-domain defect and bounded fix
Original #482 LobbyCastleModesPreview uses a dead carrier's unbounded world X/Z to create physical drop eggs. If the player dies beyond the TacticalBattlefield (falls through the floor, crosses an edge), tokens remain conserved yet a physical egg may become unreachable. This is a source-derived risk, not observed device proof.
Exactly one new pure server-side FieldEggDropBounds policy keeps TEAM X=-620 and BR X=620 arenas separate and clamps egg centers inside existing 890x1050-stud battlefield with 40-stud padding. It does not change Y, egg quantity, tokens, actor/owner, item effects, boss, AI, combat, roles, score or settlement. Nonfinite impact uses server castle coordinates; otherwise arena center. Valid in-arena deaths are unchanged.

## Original author reuse / ownership
- #482 is original owner of 7 jobs, 21-source Game, castle, eggs and lobby; no author branch edits.
- #484 AI and 26-source composer, #485 ART, #487 SCORE, #489 ITEM, #494 neutral, #500 castle defense, #506 respawn protection and #508 KO attribution are not replaced.
- #218 SOFT claim comment 6907114391, no authenticated grant yet.
- Only our independent path and dedicated CI are committed. Composer copies 20 original sources byte-exact, overlays one require plus one drop-site calculation into a private generated lobby, and appends only one new policy ModuleScript. 21 original plus 1 new = 22-source private candidate.
- Fixed original author HEAD fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9. Re-check current author HEAD before RC selection.

## CI / native / device
Workflow executes Python positive/negative source checks, the exact native Luau module with 18 assertions, Luau syntax for all 22 bodies, genuine private Rojo Place and a 22-source exact embedded class/text verifier. CI success remains source-only, not production RC or Studio behavior.

## #220 authenticated writer intake
1. Acquire #218 CLAIM GRANT plus #482 author acknowledgment (or original author directly adopts same fix). Do NOT merge this stacked PR wholesale.
2. On latest #484 26-source composer, keep #485 ART/#487 SCORE and the latest accepted original source, add this one policy and the one host hook. Never duplicate ITEM/neutral/AI/role/score systems.
3. #220 sole authenticated writer must pin current official RC head, pass source-lock and same-HEAD native/Rojo/Place/ZIP, perform non-force CAS; no main merge, Publish, or charge.
4. Studio TEAM/BR 2+clients: carry 1-3 eggs, die beyond the arena, verify released eggs land on the correct mode floor, are physically pickable, and conserve server token counts; verify normal deaths, reconnect, root destroyed, and later rounds.
5. #420 Android low-spec 15min FPS/touch/thermal, PC art, kid FUN and OWNER acceptance remain mandatory. Nonfatal YELLOW with owner/repro/flag-OFF/rollback; RED native/source/CAS blocks.

Rollback: omit module and restore the exact unmodified #482 lobby require + death-drop landing line. No persistent data change.
