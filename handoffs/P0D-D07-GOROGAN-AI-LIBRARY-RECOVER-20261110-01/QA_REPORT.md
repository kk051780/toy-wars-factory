# QA REPORT — P0D-D07-GOROGAN-SERVER-AI-20261110-02

- `PYTHON_MODEL_AND_STATIC_TESTS`: **87/87 PASS**, 2026-11-10 JST, Linux Python 3.13. Includes 3000-step seeded state property checks, 2-team symmetric targeting, invalid/stale match handling, attack TTL, 2-second windup, movement leash and cooldown, 14 extra archive/AES adversarial tests.
- `ZIP_MANIFEST_BYTES_SHA`: verified locally upon packing; final SHA reported in GitHub README and immutable #218 comment.
- `AES_GCM_LOCAL_ROUNDTRIP`: verified after packaging; wrong-key and tampered ciphertext rejected in tests.
- `LUAU_PARSE`: NOT_TESTED. Static source string checks are not a Luau compiler or Studio simulation.
- `SERVER_DAMAGE`: NOT_TESTED. Real authoritative roster, LOS, live humanoid damage and navigation are callback interfaces, not integrated.
- `STUDIO_2CLIENT`, `STUDIO_MOBILE`, `NPC_PATHFINDING`, `PHYSICAL_PHONE`, `PLAYER_RETENTION`: NOT_TESTED.
- `PC_BASE_SHA`: UNVERIFIED_PC_LOCAL. Existing v37 PARTIAL_NOT_READY, v39 pending.
- `P0A_LOCKS_MAIN_RELEASE_CHARGES`: not modified.

The normalized server callback example is disabled unless explicitly integrated by OWNER Windows Codex. No new scheduler, no additional NPC spawn or real combat mutations are installed by this reference ZIP.
