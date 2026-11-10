# P0-D CHAT-FIRST full-release factory — V2

Owner policy for `TRAP_RAIDERS` only. GitHub PUBLIC source is permitted by OWNER; Roblox production publish and billing are not.

This package defines a new cross-chat source-first/whole-game release pipeline: parallel CHAT-FEATURE production, exactly one CHAT-INTEGRATOR for the complete release candidate and independent CHAT-QA, with **Windows Codex reserved for the near-final/finished game**. The old per-packet Codex QA loop is superseded. No main write, game code edit, new Automation, or production release occurs from these files.

Read `docs/OWNER_POLICY_V2.md` and `docs/RC_PLAN_SCHEMA.md` first. `tools/chat_rc_assemble.py` is a safe, deterministic **offline staging** and manifest/authority/path gate. To run its tests:

```sh
python -m unittest discover -s tests -v
```

**Do not conflate outcomes:** `22/22 offline unit tests PASS` = this process tool passed, not that TRAP RAIDERS is finished, that real Luau compiled or that Studio accepted a final build. There is no assembled candidate in this packet. After chat integration finishes, `docs/CODEX_FINAL_HANDOFF.md` defines the OWNER-directed one-RC-at-a-time PC role.
