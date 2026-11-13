# P0D-S1 H1 admission safety preflight — 2026-11-13 JST

This is an **independent, read-only preflight** for #250 / #220. It **does not merge or modify RC**, Studio, or any other author's source.

## Fixed evidence
- Official S1 last known RC: `1263a03701211a652b99b91d2339575dc8104eff` (last 75/100; FUN_NO_GO).
- Original integrated candidate: `79804116b0a144a33c6466340cfb476eefa3ca4d`, 45 script source, B42+V7+sky+solo+BEAST/WEAPON Dojo, original native+Rojo Actions 43413293004 SUCCESS.
- Original candidate private .rbxlx SHA256: `1382bf8b3068c60cccfab1160a2e00baf0e4811c0f81b06008c5eaa4779fdd0e`, artifact 14030766490. This branch contains NO binary copy; source project and private user asset remain under original owner's review.
- Rollback comparison: `2afffa49d4173b32c1d8772b5b52c988adfbebc4`.
- The 45-source candidate is a **private optional H1**, not product official selected. Training is only BEAST+WEAPON, session only; NOT six-skill V4 persisted. Last #250 selection is B42 First90 for private H1; no product official RC selection.
- Latest V4 six-skill pure scheduler `77bb734e562245fb9ff9798a95412b9c563c87a2` and visual demo are **not** bundled into this candidate.

## Run
`python -m unittest discover -v` (8 local tests PASS at authoring).
`python admission_gate.py CURRENT_H1_ADMISSION.json` returns exit 2 and explicit blockers, as expected.
With a legitimate downloaded original .rbxlx, pass `--place /path/to/nonpublished.rbxlx` to verify raw SHA256, Script/LocalScript/ModuleScript counts and one named server Game. This is **static XML inspection only**; it cannot validate running Remote/HP/XP/Store authority or real human FUN.

## Next true integration chain
1. #250 PRODUCT_DRI obtains owner **real private Studio** feedback for the currently selected B42 baseline and H1 variants, compares H0/H1, then formally selects/rejects a candidate.
2. #220 sole integrator validates exact source lock, narrow source changes to Game/HUD/DojoRules, independent current RC source QA, single Remote/round/score/HP/XP/store authority, physical world collisions and rollback. **Do not copy wholesale Game twice**.
3. #220 alone writes official isolated RC branch after formal adoption decision and runs full build/offline QA; OWNER privately performs actual 2-client, Android and FUN checks. Original gate currently **BLOCKED**.
4. OWNER separately approves any eventual Roblox publication; paid products and additional spend remain OFF.

Source QA and optional binary existence **do not** satisfy Studio/Android/FUN. No main write/merge, no published live place, no payments, no Windows Codex execution, no P0-A/B/C CAS/automation changes.
