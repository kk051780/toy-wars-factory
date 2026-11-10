# TRAP RAIDERS P0-D | D15 trap / poison / rescue | independent ChatGPT reference packet

This is a new, standalone **non-integrated** reference. `Core` is a pure Luau state machine; tests are Python model regressions and static interface checks. Nothing in this packet runs Roblox Studio or can certify existing game's source SHA.

Capabilities: TRAPPER to enemy chain (≤16 studs), 2-s root, bounded poison 3×3 HP, 12-s cast cooldown, teammate rescue at ≥0.5-s within 10 studs, solo escape at ≥1.25-s, 6-s post-release immunity. No enemy team rescue or friendly-fire, repeat damage, extra egg drops or win changes.

See `docs/CODEX_INTEGRATION.md` before using this code. Caller must supply the **authentic server clock, real roster, world position and validated invoking Player**. Pure reference cannot itself authenticate remote events and its Python tests do not establish real Luau behavior.

Offline checks:

```sh
python -m unittest discover -s tests -q
python tools/verify_packet.py TRAP_RAIDERS_D15_ChatLead.zip
```

Roblox Studio / 2client / mobile / DataStore / real combat integration: **NOT_TESTED**.

Public repo policy: source inside this ZIP must never be committed in plaintext to public `toy-wars-factory`; use OWNER-approved private repo or AES-256-GCM encrypted JSON on unique handoff branch with fixed commit and remote readback. The key is for the OWNER's private chat only. No `main`, merges, publication or cost.
