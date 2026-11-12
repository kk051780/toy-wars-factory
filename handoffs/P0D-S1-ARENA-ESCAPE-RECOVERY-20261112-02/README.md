# P0D S1 original-source arena-edge recovery candidate

**Status: KEYLESS SOURCE-ONLY, NOT OFFICIAL RC, NOT ROBLOX STUDIO TESTED.**

Game: `TRAP_RAIDERS` / `p0d-siege-v19` / `P0D-S1-KIDS-RC01`.

- Exact **official original RC commit** pinned at source selection: `1263a03701211a652b99b91d2339575dc8104eff`.
- Original real `Game.server.luau` Git blob SHA1 `7c5229f600f17537bc1bbbb0b96b6a2435875374`.
- Original real `MapBuilder.luau` Git blob SHA1 `d2127b8c20c8abd880a21f84aeeb706feeb14ce8` (GrassArena **250 × 142 studs**).
- Complete actual original-derived Luau replacement is `candidate/src/server/Game.server.luau`; only the existing end-of-`tickRound()` rescue loop is replaced.

## Player-facing change

Current S1 resets a player only after falling below Y=-30. A child can leave the 250×142 arena near the X or Z edge without crossing that Y threshold. This candidate also recovers a live RED or BLUE player when X is beyond ±130 or Z beyond ±76 (five studs beyond floor edge), using the existing authoritative server heartbeat and its own map/team spawn. This is **not** a new teleport button, quest, item, reward or map.

For any actual recovery, the existing server **first returns a stolen egg**, restores Guardian slow state, clears linear+angular velocity, sends the character to its team's spawn +4 studs and resets existing respawn protection using the same server clock and `Config.RespawnInvulnerability`. A player cannot use an enemy egg to score by exiting the map. No second remote, second event owner, new tick scheduler, client-position trust or healing is introduced.

S1 map center, boundaries, existing Y<-30 fall behavior, attack, HP, egg score, roles, trap lifecycle and boss OFF controls remain otherwise byte-identical to the official original Game.

## Source integrity and QA

```sh
cd handoffs/P0D-S1-ARENA-ESCAPE-RECOVERY-20261112-02
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

The committed Python test checks exact full original Git blob reconstruction after reversing only this recovery block and checks the pure boundary and safety contracts. On creation, separate source-aware JS contract checks **22/22 PASS** against the actual GitHub candidate+original, plus **12/12** local Python geometry-only assertions PASS. The complete committed source-aware Python unittest is **not yet executed**: do not equate either with a real Luau interpreter or physical Roblox engine.

## Sole integrator / safety gates

Only #220's sole RC integrator may `INCLUDE_OR_SKIP` after re-reading the current RC. If the original Game or MapBuilder blobs differ, **do not overwrite**; rebase manually and rerun security QA. Native Luau parser, 2 real clients, real boundary traversal, egg resetting, touch-screen running/jumping, potential repeated-rescue exploitation and real Studio close verification remain **NOT TESTED**. Do not mark S1 release-ready from this packet.

No changes to official RC, main, merge, Roblox publication, charging, Windows Codex, P0-A/B/C security, or five existing automations.
