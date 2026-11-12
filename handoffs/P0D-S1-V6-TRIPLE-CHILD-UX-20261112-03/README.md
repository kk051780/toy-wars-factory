# P0-D S1 V6 — Triple child UX integrated preview (NOT official RC)

**Status:** integrated source-only review candidate, **NOT TESTED in Roblox Studio**, **NOT authorized to publish**. Built as a new isolated branch from immutable official RC `1263a03701211a652b99b91d2339575dc8104eff`. Official `rc/p0d-s1-kids-rc01`, `main`, all public Roblox worlds, P0-A/B/C and five existing Automations remain untouched.

## Actual joined code

The complete canonical `releases/P0D_S1_KIDS_RC01/` game tree is inherited from the pinned official RC (not just a package list). Three already separately tested candidate Luau sources have been transplanted **byte-for-byte** in distinct files; the release folder's existing 37-item `BUILD_MANIFEST.json` has been repaired accordingly. No other game source was modified. Not the sole #220 writer; this preview is a proposed input for #220's exclusive official integration after review.

| Actual release file | Source SHA (candidate) | New Git blob | New SHA256 | UTF8 bytes |
| --- | --- | --- | --- | --- |
| `src/server/MapBuilder.luau` | `78f849af28e15d7e990dd2690f2cafff0854d001` | `94655d019fdf9798fa24a350ebf49f8290465ac0` | `e05e0566d9471fa066db4e23f59b1ffd222a426a37bb4386b23ffc9a25cb5171` | 5130 |
| `src/shared/FirstMinuteModel.luau` | `e29d37737890671d458072bebe729127878700f6` | `967ea52df79884e6c73e3e0952d5a97de0d1796e` | `b9a9b74e7ba71fb8f545b7cfe4ad0445a4edfbdd5cf6be9c21f183198971a679` | 5879 |
| `src/client/HUD.client.luau` | `10940c76d708f99be908c587094c00757b22e7f6` | `b3d3996c40c690e19007a36a847d5b10fc6a1522` | `0399f21ea9784f0f964eba4dac91057916242d5066ade59b9c82e2de5320df20` | 9017 |

## Rationale / risk

- Japanese 3D prompts and labels clarify where to steal eggs and return them. Source edits to `MapBuilder` affect displayed strings only; all 27 Part physical geometry, prompts, server authority and objective IDs unchanged from the real V6 map. Prior isolated source/native checks completed (168 source-geometry semantics, 20 text, 8 mutants); new three-way *Studio* check still absent.
- Guardian-only FirstMinuteModel copy mentions visible trap action in first minute, correct 20-second cooldown and own side restriction. Raider score and serial behavior unchanged; prior isolated real model native checks124 and nine mutants completed.
- Mobile GuardianTrap button moves to right edge above attack (6px gap), avoiding known potential left-hand thumbstick overlap. **A physical smartphone test has not yet established the defect or the fix.** Prior isolated original+candidate parser/source checks, 6 geometry cases, and 5 mutation controls were reported successful.

## Review gate before any official adoption

1. Compare the final preview branch with frozen official RC. **Exactly** four files within `releases/P0D_S1_KIDS_RC01/` may differ: the three Luau paths above plus `BUILD_MANIFEST.json`. The only unrelated addition is this dedicated review-only handoff root. Game.server, S1TrapRules, S1Rules, lobby, boss OFF flags, Rojo project, damage/Remote authority, tests and docs are byte-identical.
2. Run `python handoffs/P0D-S1-V6-TRIPLE-CHILD-UX-20261112-03/verify_preview.py` from a clone of **this exact branch and commit**. This verifies the release manifest and all 37 files, source Git blob pinning, source changes and safety constraints. A successful manifest or local test is **not** a native Luau or Studio pass.
3. Compile/execute the **three-way composition** in upstream genuine Luau CLI, re-run native Game+MapBuilder+TrapRules and client HUD/Coach negative tests, then build a review-only real Rojo `.rbxlx` on exact full source. Do not use prior 2-way binary as if it included third mobile HUD patch.
4. Under separately authorized private place, get real 2-player game/egg/trap/score/rematch proof and real mobile thumbstick+trap+attack+ProximityPrompt/fps/human first-minute proof. Current official S1 75/100 last sole #220 audit; all new review work adds **zero** engine/human/OWNER approval points.
5. Sole #220 integrator reviews and **chooses** INCLUDE/REVISE/SKIP. No patch to their official branch without explicit exclusive ownership coordination and full source-test refresh. OWNER independently approves first Roblox public release if all gates pass.

## Source and scope references

- Canonical #218: https://github.com/kk051780/toy-wars-factory/issues/218
- Sole integrator #220: https://github.com/kk051780/toy-wars-factory/issues/220
- Prior joined two-way preview actual Rojo: https://github.com/kk051780/toy-wars-factory/issues/220#issuecomment-6813546843
- Mobile separate original source: https://github.com/kk051780/toy-wars-factory/issues/229#issuecomment-6813743372

**Forbidden:** `main` direct writes, unrelated lanes, official RC overwrite, merge, Roblox publish, extra spend, secret exposure, background claim of Studio pass. Keys not required to review this source. All candidate code is original TRAP_RAIDERS-only PUBLIC_SOURCE_V1.
