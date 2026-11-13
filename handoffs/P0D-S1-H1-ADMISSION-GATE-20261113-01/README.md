# P0D-S1 H1 admission QA V2 — 2026-11-13 JST

Independent read-only fail-closed review, NOT the official RC writer. No merge, main, original authors' source, or Roblox Place is modified.

## Exact evidence
- New optional PRIVATE H1-V5 candidate: 646cd9bd18b3428235ada06a763f9c5ac65b6883. https://github.com/kk051780/toy-wars-factory/tree/646cd9bd18b3428235ada06a763f9c5ac65b6883/handoffs/P0D-RC-H1-DOJO-SKYV5-STRICT-20261113-01
- Successful original author CI: https://github.com/kk051780/toy-wars-factory/actions/runs/43415851018 (native Luau 45/45, Rojo 45/45, Python 53, Solo40, Dojo47, strict sky792). Private Place sha256=96dada63baa2b99e321b5f9eb35a0f335aa22925212e66a8a9b32c48cf5ffd2d, artifact 14030858994. This QA branch has NOT independently downloaded the binary.
- Previous H1 45 candidate rollback: 79804116b0a144a33c6466340cfb476eefa3ca4d. V5 changes precisely two of 45 original source bodies (physical sky ground docks and strict same-egg diagnostic), as source author reported.
- Last official S1: 1263a03701211a652b99b91d2339575dc8104eff / 75 of 100 / FUN_NO_GO, unchanged.
- Actual H1 optional source includes B42 egg modes, V7 horde, physical sky, studio solo, 2 BEAST/WEAPON auto-dojo SESSION ONLY. Full six-skill V4 XP/save and payments are NOT INCLUDED.
- Product #250 has selected original B42 First90 for PRIVATE TEST BASELINE ONLY, not official RC. V5 remains unselected and is not official RC.

## Run
python3 -m unittest discover -v -p 'test_*.py'
python3 admission_gate.py CURRENT_H1_ADMISSION.json
python3 admission_gate.py CURRENT_H1_ADMISSION.json --place /path/to/original/nonpublished.rbxlx

Current receipt intentionally exits 2 / BLOCKED for no official selection, actual RC independent QA, real Studio two-client, Android, OWNER FUN, source lock or authority review. If actual original binary supplied later, static scan can validate SHA256, Script/LocalScript/ModuleScript counts, exactly one named server Game, DTD rejection and size bound. It does not test Roblox runtime.

Positive acceptance flags require attributable GitHub evidence links; links must be independently verified, not trusted at face value. Even all positive gates yield only ELIGIBLE_FOR_SOLE_INTEGRATOR_REVIEW, NEVER RC_INTEGRATED.

## Next actions
1. OWNER privately tests selected B42 baseline vs optional V5 in actual Roblox Studio. Test two teams, castle/egg carrying over newly grounded sky routes, negative dropped/swapped egg and wrong-score 4/4, Android UX and FUN.
2. Product DRI #219/#250 formally selects or rejects V5. Private baseline selection does not imply adoption.
3. Sole #220 integrator alone checks current official RC source-lock and singleton Game/Remote/round/HP/score/XP/store authority, narrow diffs/rollback, and independent real RC QA prior to any source adoption.
4. OWNER separately authorizes actual publish or paid features. Both remain OFF.

Read-only CI workflow p0d-s1-h1-admission-gate-20261113.yml runs 11 unit tests and confirms current optional candidate remains BLOCKED, without changing existing five automation schedules, main or Windows Codex.
