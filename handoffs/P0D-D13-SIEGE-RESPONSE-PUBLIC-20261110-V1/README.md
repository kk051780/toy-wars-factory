# D13 reference handoff
This is a pure decision core and Python oracle. It is NOT a complete AI or game. Source code is confined to the encrypted ZIP; PUBLIC GitHub receives only a sealed AES-256-GCM JSON and sanitized README. This packet has *not* been run through Luau tooling, Roblox Studio, 2client, hardware mobile, or a Windows Codex.

Tests: `cd tests && python -m unittest -v test_siege_oracle.py`.

The server adapter and NPC movement executor must be written by Codex after verifying the real local source. No Boolean `isAuthorized` sent by a client can prove trusted origin. Intents have no movement execution, player position or world target. The Python tests validate a separate logical reference, not parity with actual Luau VM.
