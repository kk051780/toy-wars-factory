# BATTLE-ATTR-VFX — eight attribute silhouettes (lane 2 / #765)

**State:** isolated client presentation SOURCE candidate; **NOT canonical RC**, **NOT Studio/Android FUN certified**.
**Feature:** BATTLE_ATTR_VFX_20261118
**Unique claim:** #765 comment 6968039688; #766 owns affinity mathematics, #770 its original31 bridge; #775 owns passive HP; lane8 owns MAGE revive. This lane does not touch those files.

## Actual LuaU
- `ElementVisuals.client.luau` exports `describe(element,kind,outcome,lowEnd)`, `capacity()`, `render(element,kind,outcome,position,lowEnd)`.
- Eight *visually different outlines* beyond hue: FIRE jagged flame, WATER wave, LIGHTNING broken zigzag, WIND curled current, EARTH angular rock, ICE snow-crystal, DIVINE closed halo, CURSE chain-and-hook.
- WEAPON / ATTACK / SHIELD presentation. ADVANTAGE thick/double-pulse metadata, RESIST thin, IMMUNE diagonal slash. Actual HUD text for those outcomes belongs to #765 lane3, not this writer.
- A rendered cue uses exactly one invisible anchor and at most eight short camera-facing Beams (at most four on low-end). Maximum eight active cue anchors, Debris cleanup in 0.42–0.9s. No gameplay collision, bright box/sphere filler, persistent FX, or costly world scan.
- Does not receive client commands or compute damage; caller **must supply an existing server-confirmed attribute, hit, shield outcome, and world position**. Invalid IDs/outcomes fail closed; nil camera/server calls render nothing.

## QA evidence / rollback
- Native source-derived Luau test runs all 8 elements × 3 presentation kinds × 4 outcomes = **96 descriptor combinations**, rejects indistinguishable geometry, tests low-end beam cap and no overlong object lifetimes.
- Deliberate mutant raising 8 active FX to 88 must fail with `RED_BUDGET`, proving the bound is tested.
- Source-only, new isolated paths; canonical existing 31 Luau scripts byte-unchanged. **OFF = omit client module and any later adapter**, preserves old behavior; no combat or serialized state migration.

## Formal RC adoption request to unique #220 integrator
1. Re-fetch latest `rc/p0d-s1-kids-rc01` SHA and this candidate's source SHA. Before adoption, inspect #765 lane2/3 and any newer presentation owner to prevent overlap.
2. Attach as **client-only ModuleScript**, invoke from the **already authoritative** V3 SkillFX/ImpactFeedback/confirmed hit pipeline. Do **not** create a second damage/hit/score/attribute/HP Remote authority; avoid hardcoded attributes where server has no confirmed element.
3. Compose current original31+client module and minimal existing client presentation hook; verify class/source for ON and exact OFF31; compile true Native and Rojo same HEAD. Perform source lock, nonforce expected-SHA CAS and official HEAD readback **only using #220 authorized writer**.
4. Verify in genuine Studio 2-client: 8 outlines, weapon/attack/shield, advantaged/resisted/immune differentiable without color, no phantom HIT, camera/round destruction, children HUD not obscured. Low Android 15-minute FPS/memory and first 3 minutes of FUN remain YELLOW until measured; this preparation does not imply a pass.

## Eight-domain coordination
Character = immutable 7 roles; Field = no world edits; Battle = only visual layer; Castle = no HP writes; Neutral = no hit claim; Items = future confirmed weapon visuals; Lobby = no UI writes; Balance = #766 multiplier source not copied. Sole writer #220 handles formal RC. MAIN, publish, monetization, and spend untouched.
