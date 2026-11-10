# v43-A independent handoff QA

- **Performed by:** ChatGPT local tool runtime; code not yet integrated with PC original Roblox Place.
- **Implemented:** Pure Luau `NeutralSkirmishCore`, Python reference model, deterministic server-only faction capture and hostility contract.
- **Test command:** `python -m unittest discover -s tests -q`
- **Observed result:** `Ran 56 tests` / `OK` (46 gameplay/reference + 10 transport/security tests). Python tests exercise the reference model and GitHub packaging utilities. Actual Luau execution **NOT_TESTED**.
- **Known invariants:** 3 second uncontested claim, 8 second alliance lease, 4 second cooldown, max one neutral controlled per team, 2 neutral units in MVP, 14-stud eligibility, max 1 second credited per tick, contested resets, egg carrier blocked, duplicate actor fail-closed, stale time fail-closed, match end neutralizes.
- **Security:** AES-256-GCM round trip and wrong key failure tested, zipped path traversal/manifest tamper rejected offline. GitHub upload/readback must be separately confirmed.
- **Unverified:** Real server authority/RemoteEvent validation, NPC pathfinding/combat, Studio Luau compile, actual Play/Stop, 2 or 3-client gameplay, physical/mobile, FPS, persistence, D1/revenue.
- **Prior baseline:** v37 latest saved Place SHA `c56459c29595f5ecde5521565862d0a4ea3c8a426a35cbb1d539ad6e08fd4741` is a provenance target only; **current PC may have a newer baseline**. Do not integrate v43 until v37 and v39 intake gates are resolved.
