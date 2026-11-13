# V4 SIX PHYSICAL TRAINING PADS — PRIVATE H1 V2 source handoff
**Date: 2026-11-13 JST. Not official RC and NOT production XP/save.**

Owner continuation of existing exclusive slice `CHAT-P0D-LOBBY-V4-FOCUS-CAP-SCHEDULER-20261113-01` after source QA 46/46 and owner private version V1. The **actual V2 Place and complete reproducible build ZIP are attached in the owner's originating ChatGPT conversation**; this file records a reproducible audit and the exact two-script source-change contract in GitHub for other chats, without writing other owners' branches.

## Exact artefact identifiers
- Original author H1 BEAST+WEAPON saved private Place SHA256 `f5a6638abd45f684e8c69952da833d848cf1b36bbf37db50d51e00bbdbbc326e`. Its genuine native Store72+Rojo44 own CI: https://github.com/kk051780/toy-wars-factory/actions/runs/43409780861.
- Prior V4 V1 Place SHA256 `0b3d61165817de9ee4f7b62f5f22130c3436f88b6afb4ddf9628d671ed385752`.
- New genuine serialized V4 V2 private Studio Place file `P0D_S1_V4_SIX_PHYSICAL_PADS_PREVIEW_V2_PRIVATE.rbxlx`: SHA256 `95d0c1da301572341316c72570e72bc8c59b4621f69d6ad1aa6a56aa778bf3be`.
- New standalone owner-conversation ZIP `P0D_V4_SIX_PHYSICAL_PADS_V2_STUDIO_QA_46.zip` SHA256 `1dd54c540a943f545ff68270f35277535a0aa192cbbdeb7ba81ca026536653f2`. Contains BOTH V1+V2 Place, original saved 44-source H1 input, both Python builders, full old and new Game/HUD actual embedded source, unchanged original scheduler, 2 tests, README Japanese, actual 46-compile log, source-lock, exact 2-body unified diff `V4_V1_TO_V2_ONLY_2_SCRIPTS.patch` (SHA256 `b96ba60aaece2c34ed98ed79c3d325910dd99257e580f34e62f419554035d63a`).
- Pinned native Luau CLI source `f46d879e28302a430029304f7f6a162aed66f103` obtained from own source CI https://github.com/kk051780/toy-wars-factory/actions/runs/43415697462; same source locally compiled into genuine native CLI. **V2 46/46 exact embedded Luau compile PASS, real Python original22+V2 16 = 38/38 source/XML tests PASS**. No Roblox Studio actual engine runtime checked.

## Game instance and user-visible changes
- The original 44 H1 Luau bodies are **43/44 identical**, original `Game` body only changed. V1 → V2 exactly **two** original V1 script bodies modified: server Script `Game`, client LocalScript `V4TrialHUD`. No extra scripts over V1's 46 (Script2, LocalScript6, ModuleScript38).
- Original mirrored RED/BLUE BEAST pad at `x=±56,z=-15` and WEAPON at `x=±56,z=15` are **unchanged**; those old two have existing H1 XP/save in one original DEV Hatch profile. Do not overwrite it.
- Under `RunService:IsStudio()`, spawn **4 additional decorative, non-collidable** pads per team, for an actual total of 12 across two sides, based on `sideSign = if side=="RED" then -1 else 1`:

| V4 skill | Child-facing sign | absolute X (studs) | Z (studs) | RGB |
|---|---|---:|---:|---|
| MAGIC | 魔法 | 54 | -49 | 125,110,255 |
| ZOMBIE | ゾンビ | 54 | +49 | 142,216,93 |
| VEHICLE | 乗りもの | 74 | -49 | 83,191,235 |
| BUILDING | 建築 | 74 | +49 | 255,146,98 |

- Source property contract per extra pad: `V4_ONLY_TRAINING_PAD_<TEAM>_<SKILL>`, `V4TrialOnly=true`, `NoV4SkillXP=true`, `NoV4PersistentSave=true`; size 10×0.24×10; y=-0.79; `CanCollide=false;CanTouch=false;CanQuery=false`; same original map.model, child-facing BillboardGui says `体験だけ・XPなし`; no new map obstacle.
- `v4PreviewPads[side]` includes the 2 original and 4 new. In existing ONE original `tickRound()`, active on a team pad, alive, no carried egg and no loading profile, server detects proximity within 6 studs; entering a **different pad** triggers `V4Scheduler.selectSkill(state,padSkill)` exactly when `padSkill~=v4TrialLastPad[player]`. While standing on same pad, V4 HUD button selection remains valid; leaving and coming back reselects that floor. Keep original H1 `Dojo.tick` unchanged and exclusive to BEAST/WEAPON.
- New `V4TrialHUD` field `activePad`, 6 separate **training seconds** totals shown in larger 336×348 panel. Still no V4 six-skill actual XP, no XP writer, no profile persistence. Existing V4 30min/day JST free choice → 10min six-shuffle random after cap, friend count display max4 only, debug skip quota grants NO XP and is NOT saved.
- **Important:** The 4 new physical pads work as V4 SESSION-TIME PREVIEW ONLY. Real earned/persisted six-skill XP, PvP skill/balance and same-store atomic save require separate original Game/Store author-owned changes and product selection. Native compile is not Studio 1client/2client/Android/OWNER FUN evidence.

## Integration / rollback
- Other chats: pull fixed owner V2 ZIP from OWNER handoff; fully regenerate from its included immutable V1/44 original by `python tools/build_private_preview.py` then `python tools/build_private_preview_v2.py`. Compare exact SHA256 `95d0c1...` before use. The original saved two-pad H1 Place is the rollback. Do not use this GitHub note alone to claim binary has been committed.
- V4 product is still **UNSELECTED** in #250, official RC writer is **only #220**, S1 last official 75/100 FUN_NO_GO unchanged; 2/8 feature evidence slots IDEA+ISOLATED_SOURCE remain, not release completeness.
- No changes to main/merge, other author's source, release, game publication, actual payment, PC/Codex, CAS/P0ABC or current automations.
