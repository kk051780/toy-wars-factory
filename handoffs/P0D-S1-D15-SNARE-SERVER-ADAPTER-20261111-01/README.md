# P0-D / TRAP RAIDERS — S1 original-D15 snare integration adapter

**Status: SOURCE_CANDIDATE / NOT_INTEGRATED / NATIVE_LUAU_NOT_TESTED / STUDIO_NOT_TESTED**

Game `TRAP_RAIDERS`, work `p0d-siege-v19`, packet `P0D-S1-D15-SNARE-SERVER-ADAPTER-20261111-01`.

This package provides an **actual optional server ModuleScript** `src/S1D15TrapBridge.luau` to connect existing, byte-identical recovered original D15 `TrapRescueCore` to the initial S1 **one** server Game controller. It does **not** ship a new copy of the original Core or duplicate a remote, round scheduler, event selector, damage authority, HP, egg, or persistent writer. The integrated S1 owner alone decides whether to add it to the game; no direct source modifications or automatic merging.

## Fixed original sources, not substitutions

- Initial independent Chat S1 source (RC sole writer #220): `35d7d0525388e885aac8281eff2315a59831e0cf`, `releases/P0D_S1_KIDS_RC01/`.
- **Exact recovered original D15**: `85967eb6b7ace4d2a749b65041cb4ca975cafdf0`, `handoffs/P0D-D15-TRAP-RESCUE-LIBRARY-RECOVER-20261110-01/luau/TrapRescueCore.luau`, **8190 bytes**, SHA256 `da7c0b46f39d4e0a64bd397fcc16fcf9e4502c879179371cd221d42ea8db8174`, Git blob `4ca74873b38e305361691d78fa060ac01700a7ec`.
- No assumption that the owner Windows v43-A game or a later S1 RC is byte-equivalent. Do not combine incompatible original/cleanroom D15 implementations.

## Gameplay it allows after integration

A player explicitly choosing **TRAPPER** may cast a short snare on the nearest visible enemy ahead, max 16 studs. Affected player is rooted for 2 seconds by the **existing Game movement owner**, and is eligible to escape after 1.25 seconds or receive teammate rescue after 0.5 seconds within 10 studs. Original D15 enforces 12-second cast cooldown, 6-second post-release immunity, one active victim per caster, and up to three bounded 3-HP poison ticks; **all actual HP damage goes through the original Game controller's callback**. Not a permanent progression reward or paid ability.

## Explicit safety boundaries

- No client-chosen target or position: selecting candidates is server-only, with actual Character HumanoidRootPart, alive, opposing team, XYZ range, facing and raycast LOS.
- No new remote handlers: `Game.server.luau` consumes the existing monotonic `Rules.validSeq` before forwarding a trusted `sequenceAuthorized=true` flag to `Bridge:handleIntent`.
- No event/round timers or own heartbeat: Game's canonical `resetRound` / `tickRound` / `stopRound` own the lifecycle and call `beginRound`, `update`, `endRound`; source original Core time is **elapsed from round start**, not epoch absolute time.
- No second HP writer: the injected `applyPoisonDamage` callback must validate team/phase/epoch/target again before it alone updates humanoid HP. Cross-round poison receipts include match/caster/victim/tick and are deduped before callback.
- No movement ownership: injected `onStatus` callback lets existing Game calculate role baseline speed and restore on unroot/rescue/death/end. This bridge never changes `WalkSpeed`/`Health` directly.
- Original D15 expects positive numeric UserIds; local Studio test negative/0 UserIds are mapped by server to private positive keys within the original valid ID ceiling.
- No auto-fork of TRAPPER: current initial S1 knows only RAIDER/GUARDIAN. Until the **sole #220 integrator** adds TRAPPER to its role/config/HUD, `TRAP_CAST` is correctly rejected as WRONG_JOB.

Read [integration details](docs/INTEGRATION.md) for exact change locations and rollback. Source-only Python test suite:

```bash
python -m unittest discover -s tests -v
```

Python tests model integration invariants and inspect original Luau interface statically; **they do not run Luau** or prove Roblox Studio 2-client/mobile. Final engine tests, 2-client trap rescue + escape, original egg/castle regression and Studio normal exit are required before any release claim.

## Handoff restriction

This Chat owns only the new unique `handoffs/P0D-S1-D15-SNARE-SERVER-ADAPTER-20261111-01` branch root; original D15 author, `rc/p0d-s1-kids-rc01`, public game, P0-A/B/C protected coordination, main, merges, paid content and five automations untouched. No OWNER/Windows Codex action is implied by this README.
