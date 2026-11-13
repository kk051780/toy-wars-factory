# P0D Egg Relay — isolated S2 pure policy

Original gameplay idea: a stolen egg can be passed to a nearby teammate under strict **server-only** authorization. This branch is an optional S2 product experiment and does NOT change the actual Roblox Game.

- `src/EggRelayPolicy.luau` — original pure eligibility policy, returns allow/deny receipt without mutating Game/Remote/Store/score/XP.
- `tests/reference_policy.py` — independent Python behavior reference (NOT a native Luau interpreter).
- `tests/test_reference_policy.py` — 33 offline happy-path and negative tests, including replay, cross-team, distance, blocked LOS, double-carry, cooldown, death, stun.
- `INTEGRATION_CONTRACT.md` — exact server-state mapping, atomic handoff transaction requirements, genuine Studio 2-client/Android acceptance and rollback.

Local Python 3 test command:

```bash
python -m unittest discover -s tests -p 'test_reference_policy.py' -v
```

At source handoff: local Python reference 33/33 PASS; **native Luau compiler NOT_TESTED, true Roblox Studio NOT_TESTED, source-in-Game NOT_IMPLEMENTED, 2-client/Android/FUN NOT_TESTED, Product #250 selected NO, official #220 RC adopted NO**. The source-only tests cannot demonstrate real game playability.

Every future adoption decision must pass #219 Product DRI, #250 Product Selection and #220 sole official RC writer, followed by OWNER actual private Studio testing. S1 progress remains last official 75/100 / FUN_NO_GO. No main/merge/Roblox publication/payments/PC Codex/automations were touched.
