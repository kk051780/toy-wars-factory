# P0-D v43-A integration acceptance gate (public-safe)

**What this is:** An actual Python checker, one synthetic sanitized test trace, a deterministic negative-test suite and a Codex QA contract for TRAP RAIDERS v43-A S1 neutral-capture integration. It is *not* a game module. No Roblox source, binary Place, secret key or real user logs are included.

The acceptance guard models a single neutral NPC contested by BLUE and RED: minimum 3s uninterrupted capture, 8s temporary lease, 4s cooldown. It detects stale/replayed events, early/invalid state changes, double ownership with the existing v37 neutral-control system, missing cleanup, and accepted claims from egg carriers/dead/out-of-range actors. All actor identifiers must be synthetic pseudonyms.

Run:

```shell
python tools/verify_v43a_trace.py fixtures/valid_s1_contest_capture.json
python -m unittest discover -s tests -q
```

The checker exits **0** only for a structurally valid sanitized trace; exits **2** for a rejected trace. JSON reports always say `NOT_VERIFIED_BY_THIS_TOOL` for Studio QA. A caller can manipulate log fields. True verification requires OWNER-approved Windows Codex to inspect real server source, capture trusted evidence, run Roblox Studio client tests and confirm safe exit.

Read [`docs/INTEGRATION_CONTRACT.md`](docs/INTEGRATION_CONTRACT.md) before trying to fit the v43-A module to v37's existing NPC ownership. The schema is a proposed acceptance format; if the PC source uses another authority representation, adapt it explicitly rather than fabricating matching test logs.

Source statuses: Windows original v39 was reported scoped Studio PASS in Issue #213; v43-A has **not** been reported restored/integrated to PC. This public-safe tool is supplemental and does not change that status.

Reference: [P0-D coordinating Issue #218](https://github.com/kk051780/toy-wars-factory/issues/218) · [v39 PC evidence](https://github.com/kk051780/toy-wars-factory/issues/213#issuecomment-6753848890) · [safe restore](https://github.com/kk051780/toy-wars-factory/blob/d37eec1b653d060ae27568ddcd5f501da9662081/tools/restore_handoff_safe.py).

**No main change, merge, Roblox publication, payment, extra spend, private commercial source, P0-A/B/C controller change or Studio operation.**
