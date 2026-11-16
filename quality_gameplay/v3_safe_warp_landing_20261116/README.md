# EGGRUMBLE V3 — wind dash / psychic warp body-clearance gate (PRIVATE SOURCE)

Status: isolated DRAFT only. This does **not** modify the original Game/Combat branch, official RC, main, Roblox Studio, publication or paid products.

## What was observed in ACTUAL original source

- #482 author HEAD: fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9.
- Original one Combat Git blob: 66e666418b7c23d41f87faa5d61eb6e2770a463e.
- safeMove() was called for NINJA/WIND (25 studs) and TRAPPER/SAFE_WARP (20 studs) and checked only **one forward Raycast from root+2 studs** plus a ground ray at destination, then character PivotTo. It did not check a player-sized landing volume or that the intended point was inside the original match's TacticalBattlefield.
- This is a SOURCE-DERIVED collision/teleport bypass risk, **not a confirmed Roblox Studio reproduction**.

## Narrow original-author patch

The fail-closed patch_safe_warp.py applies **only** to original EGGRUMBLE_SevenRoleCombat.luau in a newly generated *private* copy and requires exact Git blob + three unique anchors.

- It samples 9 forward traces at foot/body/head and left/center/right, conservatively using first hit instead of old center ray.
- It verifies destination is inside same active session's original TacticalBattlefield with a 4.5-stud edge margin.
- It uses existing ground/sloped-height limits, plus GetPartBoundsInBox for a 3.2 × 4.5 × 3.2 stud avatar clearance.
- Existing **egg-carry restriction**, all seven classes, distance, cooldowns, server-only Tool activation, damage authority, status, neutral AI, Item and castle logic remain original.
- Two call sites pass original session to same helper. No duplicate Game, input Remote, Store, KO/Score, hitbox, VFX, item or boss source.

compose_private21.py builds one original-author-preserving 21-script Rojo package: **20 originals byte-identical**, only generated Combat selected. It verifies actual rbxlx script class + source SHA256 when built; author source is never modified.

## Proof gates and required OWNER follow-through

1. New 16 Python positive/negative source-lock and package tests.
2. All original #482 source contracts and pinned native Luau **21/21 syntax compilation**, actual Rojo **21/21 Source/Class exact** in GitHub Actions when run and verified.
3. **NOT TESTED** until real Studio engine trial: close wall, shoulder-width arch, roof landing, TEAM/BR field edge, origin inside castle, normal unobstructed terrain, carrying 1–3 eggs, Assassin WIND and Esper WARP, TEAM human+15 AI, BR human+15 AI. Reject regressions or blocked legitimate mobility.
4. #482 author approval, #218 CLAIM_GRANTED, #220 sole authenticated non-force CAS, current blockers to formal RC adoption; updated official HEAD same-HEAD CI/real Place & ZIP bytes and rollback; #420 Android 15m ART/FUN/OWNER acceptance remain NO_GO.

OFF/rollback: never select generated Combat overlay; use original 21-project. **No official RC integration as of this patch.**

Non-overlap: #489 item fairness, #502 AI egg targeting, #503 FX, #506 respawn protection, #510 MAGE heal LOS, #516 DOT lifecycle, #518/#519 boss stomp LOS and #520 ridge+shield remain separately owned. This lane only touches movement clearance in original-author-review-generated Combat copy.
