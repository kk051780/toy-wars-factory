# GQ8 ITEM cargo/SLOW expiry recheck (2026-11-18)

Source-only, isolated current 31-script EGGRUMBLE companion fix. The existing original #489 ITEM author cancels DASH when an egg is picked up, but its 0.25s watcher exits even if a combat SLOW currently masks the DASH speed. A subsequent SLOW expiry can restore the DASH speed while carrying eggs. Keep watching for the bounded 5 seconds and retry the idempotent undo; retain the old match/character fences, cooldown, HEAL guard and shield cleanup.

**Scope:** existing `EGGRUMBLE_FieldItemPickups` only; other 30 byte-exact, reversible OFF; no extra Game/Remote/Store/Swarm/AI/score, no new HUD, no new paid mechanics. Affected domains: ITEM fairness, egg/castle escape, character speed, combat slow, TEAM/BR balance; field/neutral/lobby are unchanged.

**Native regression:** source-derived real helper run with carrier + deferred SLOW release, no-carrier, and retired match. The previous one-shot helper is an expected RED mutant. All31 Native compile and exact Rojo Source/Class evidence must be green on PR HEAD. Only #220 authenticated writer may move canonical RC using nonforce expectedSHA CAS. No Roblox Studio/Android/FUN pass is implied, and main/publish/charges are forbidden.
