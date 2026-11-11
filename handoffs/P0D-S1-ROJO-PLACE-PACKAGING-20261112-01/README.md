# Real Rojo Place build gate (independent, keyless S1 packaging)

`packet_id=P0D-S1-REAL-ROJO-RBXLX-SOURCE-PACKAGING-20261112-01`

This is an independent read-only *real build* check against the actual 33-file TRAP RAIDERS composite at immutable commit `0ca2b7ea9f29aa79727b2e7e53a01af093df5b90`. It neither creates a release nor writes the sole official RC branch.

- Real Rojo CLI pinned to **7.7.1**, official Linux x86_64 release ZIP SHA256 `00feb4fa0829a1dd72b49df2639da519a352bfe13cadcd83969e2ba2bb5693c4` ([official Rojo releases](https://github.com/rojo-rbx/rojo/releases/tag/v7.7.1)).
- GitHub Actions checks binary checksum, then runs **real** `rojo build default.project.json -o TRAP_RAIDERS_S1.rbxlx`.
- No local PC or Roblox credentials needed. It verifies the file as Roblox XML Place and all **20 exact embedded Luau Source bytes**, exact class/name/service hierarchy, single Game.server script, HUD and FTUE. The existing 32-file strict source manifest SHA256 is verified.
- Tests run deliberately mutated copies of the actual exported XML and require fail-closed on missing/moved HUD, changed Source, duplicate Game script, script-class spoofing, invalid XML. The test code is genuine, no pre-recorded Rojo PASS.
- Successful Actions run uploads `TRAP_RAIDERS_S1.rbxlx` and source-bound `VERIFIED_BUILD_RECEIPT.json` as a **private CI artifact**. Download from that run's Artifacts panel; no Roblox experience is published.
- The standalone S1 is from public game source built by Chat, not proven byte-identical to the latest OWNER Windows Roblox Place.

**LIMITS:** Successfully generating an actual Place file is stronger than static inspection, but NOT Studio 2-client networking, actual Roblox API execution, physical combat, touch/mobile FPS, Godot/Unity compatibility, child testing or OWNER publication approval. Authentic D07/D08 behavior remains gated OFF by deliberate source flags. Integrator #220 must choose whether to ingest any candidate; it retains exclusive RC write authority and owns the global 100-point score.

Safety: PUBLIC_SOURCE_V1, no encryption or private access key, no main/official RC edits, merge, publish, paid features, additional expenses, Windows Codex run, protected P0-A/B/C CAS or existing automations.
