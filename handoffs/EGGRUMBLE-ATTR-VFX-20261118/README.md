# BATTLE-ATTR-VFX — eight attribute silhouettes (lane 2 / #765)

**State:** isolated native client presentation + optional REAL31->ON33 / exact OFF31 candidate; **NOT canonical RC**, **NOT Studio/Android FUN certified**.
**Feature:** BATTLE_ATTR_VFX_20261118
**Unique claim:** #765 comment 6968039688; #766 owns affinity mathematics, #770 its original31 bridge; #775 owns passive HP; lane8 owns MAGE revive. This lane does not touch those files.

## Actual LuaU
- `ElementVisuals.luau` (ReplicatedStorage ModuleScript) exports `describe(element,kind,outcome,lowEnd)`, `capacity()`, `render(element,kind,outcome,position,lowEnd)`.
- Eight *visually different outlines* beyond hue: FIRE jagged flame, WATER wave, LIGHTNING broken zigzag, WIND curled current, EARTH angular rock, ICE snow-crystal, DIVINE closed halo, CURSE chain-and-hook.
- WEAPON / ATTACK / SHIELD presentation. ADVANTAGE thick/double-pulse metadata, RESIST thin, IMMUNE diagonal slash. Actual HUD text for those outcomes belongs to #765 lane3, not this writer.
- A rendered cue uses exactly one invisible anchor and at most eight short camera-facing Beams (at most four on low-end). Maximum eight active cue anchors, Debris cleanup in 0.42–0.9s. No gameplay collision, bright box/sphere filler, persistent FX, or costly world scan.
- New `EGGRUMBLE_AttributeCue.client.luau` (StarterPlayerScripts) subscribes only to existing server-written `EGGRUMBLE_SkillCastSignature`. The server skill IDs from #482 confirm Mage A=ICE, B=FIRE, C=LIGHTNING, Warrior C=DIVINE, Zombie C=CURSE. Unverified role/slot attributes are **not painted**. Existing signal means cast only, so this adapter renders ATTACK/NORMAL, **never claims real HIT, immunity or multiplier**. Other 3 visual contexts are API-ready pending server-confirmed gameplay event.
- No new RemoteEvent or damage owner. Invalid IDs/outcomes fail closed; nil camera/server calls render nothing.

## QA evidence / rollback
- Native source-derived Luau test runs all 8 elements × 3 presentation kinds × 4 outcomes = **96 descriptor combinations**, rejects indistinguishable geometry, tests low-end beam cap and no overlong object lifetimes.
- Deliberate mutant raising 8 active FX to 88 must fail with `RED_BUDGET`, proving the bound is tested.
- Actual candidate composer `quality_gameplay/gq8_attribute_visual_real31_20261118/compose_real33.py` appends just two real scripts to current original31 ON33 / restores exact OFF31; existing 31 original scripts byte unchanged, no combat or serialized state migration. Formal intake is still only by #220 after same-head CI.

## Formal RC adoption request to unique #220 integrator
1. Re-fetch latest `rc/p0d-s1-kids-rc01` SHA and this candidate's source SHA. Before adoption, inspect #765 lane2/3 and any newer presentation owner to prevent overlap.
2. Reuse the existing `ElementVisuals` ModuleScript plus `EGGRUMBLE_AttributeCue.client` LocalScript. Original server `SkillCastSignature` is enough for five **verified cast-only** elemental flourishes, not actual Hit. Any added advantageous/resistant/immune outcome callback must come from an existing verified server hit/shield event, never client arithmetic. Do **not** create a second damage/hit/score/attribute/HP authority.
3. Compose original31+two presentation scripts (ON33), verify class/source and exact OFF31; compile true Native and Rojo same HEAD. Perform source lock, nonforce expected-SHA CAS and official HEAD readback **only using #220 authorized writer**.
4. Verify in genuine Studio 2-client: 8 outlines, weapon/attack/shield, advantaged/resisted/immune differentiable without color, no phantom HIT, camera/round destruction, children HUD not obscured. Low Android 15-minute FPS/memory and first 3 minutes of FUN remain YELLOW until measured; this preparation does not imply a pass.

## Eight-domain coordination
Character = immutable 7 roles; Field = no world edits; Battle = only visual layer; Castle = no HP writes; Neutral = no hit claim; Items = future confirmed weapon visuals; Lobby = no UI writes; Balance = #766 multiplier source not copied. Sole writer #220 handles formal RC. MAIN, publish, monetization, and spend untouched.
