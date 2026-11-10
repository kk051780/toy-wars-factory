# D07 Gorogan Rig / Navigation / Damage — QA

- Scope: original Luau R6-like physical rig and server Pathfinding/MoveTo driver, brief STOMP_RESOLVE receipt, actual server Humanoid damage gate. Requires PC integration; no Roblox Studio access.
- Offline: deterministic Python oracle (rate limits, lifetime, replay, attack dedupe, safe-zone/LOS gates), source-shape assertions. **86/86 PASS** on this isolated ChatGPT runtime with `python -m unittest discover -s tests -q`; includes independent Python policy models, static Luau shape assertions and AES/ZIP negative tests.
- NOT_TESTED: Luau bytecode compile, actual R6 rig movement, server network ownership in Studio, obstruction/LOS in real maps, damage/telegraph coupling, 2/3-client, emulator/real phone, local PC source SHA and Studio exit.
- Mandatory: Real current PC source and canonical event/Stage, older v39 and v43-A scope QA. No public secrets, no main writes/merge/release/paid features.
