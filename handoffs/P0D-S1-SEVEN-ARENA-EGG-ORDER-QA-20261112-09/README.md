# P0D S1 7-safe full original Game / arena / snapshot integration regression

Independent read-only QA only. The S1 official RC branch remains solely writable by P0D-CHAT-INTEGRATOR-S1-RC01-B. No official RC, main, Studio, launch, payment, or Windows Codex mutation is permitted.

## Exact source under test

- Seven safe source review: `6cc131d3de06fe8799d00f475fc446a526e4b2c4` with 37-file source manifest, Game Git blob `e684ca79b8f5ed279bcdf033f4118bf77d552abb` and source SHA256 `ce151d2b41026c454af4b7ac0954e67a0458d401498fbe487a4c9874f6346515`.
- Six safe direct parent original Game `65785c2e3b9bc37a6962f9ace128fbfcbb670901`, Git blob `a575ef5175ace5aab59f1dbe3ad8dc74d3d1860d`.
- Game must equal exact six Game **plus two ordinal source hunks only**; inverse-byte check enforces ancestry.
- Actual Japanese MapBuilder blob `94655d019fdf9798fa24a350ebf49f8290465ac0` and actual Guardian coach `d8dda6b1781375612c123f8c83b6f23fe45d09f1` are independently pinned.
- Frozen native six-source test harness comes from immutable #234 original + previous successful 6-safe QA `172393f37481cc078bca90ac61a316eeba54357f` (156 assertions and 6 mutants). It is reproduced on the real seven-safe Game source.

## Expected genuine Luau checks

The existing two-team game start, joins/exits, countdown, scoring, attack/seq, egg pickup, recovery at x>130 / |z|>76 / y<-30, egg visibility and prompt restoration, zeroed linear/angular velocities, and spawn destination must all continue to pass. New checks confirm the server-authoritative snapshot `updateId` is present and grows monotonically, without affecting round or egg mechanics. Unsafe source mutations to arena bounds, egg drop, velocity reset, snapshot ordering and PlayerRemoving identity must be independently caught.

Only Roblox services/network/physics are faked; **this is not Roblox Studio real 2-client or mobile QA**. Gameplay source is not edited. The selected seven full review project remains a candidate. The sole #220 integrator can decide whether and when to adopt it after independent acceptance and owner direct final Studio testing.

See `run_seven_arena_native.py` and isolated Actions workflow for exact fixed SHA, native Luau and defect assertions.
