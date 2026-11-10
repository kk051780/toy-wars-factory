# D07 combined runtime — QA status

- Game-specific synthetic Python oracle and static source contractual regression: **68 PASS** (case-count including source tests).
- ZIP/manifest adversarial transport tests: **15 PASS**.
- Aggregate: **83/83 PASS**, fresh extracted ZIP rerun required before final delivery.
- Real Luau compiler: **NOT_TESTED**; Roblox Studio Play/Stop/R6 pathfinding/Humanoid damage/mobile FPS: **NOT_TESTED**.
- Windows PC original source/Place SHA: **UNVERIFIED_PC_LOCAL**. Historical v43-A PC SHA is a referenced past fact, not current local game.
- Existing 4 reference packets were inspected from actual local ZIPs to derive API signatures, not rebuilt and not changed.
- Security: Module deliberately no direct Roblox client Remote handler, no second RNG/event scheduler, no direct `TakeDamage`; integrates existing privileged damage gate.
- Known risk: actual PC server might not yet have `ChaosEventCore` as canonical event picker; its integration with existing weather is a separate AUTHORITY / DESIGN gate. R6 physical NPC and map nav path must be Studio-tested.
