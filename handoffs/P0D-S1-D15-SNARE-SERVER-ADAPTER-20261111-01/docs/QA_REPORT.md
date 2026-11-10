# D15 S1 adapter source-only QA

As of 2026-11-11 JST. Native Luau parse, Roblox Studio, real mobile, public release and monetization remain NOT_TESTED / NOT_AUTHORIZED.

- One opt-in Luau server ModuleScript; exact original Core is referenced by SHA but **not cloned** or modified in this packet.
- No new RemoteEvent, OnServerEvent, heartbeat, RNG, RoundCoordinator, direct Humanoid:TakeDamage or WalkSpeed assignment. Game remains sole authoritative round, combat, data writer.
- Server trusted Players/GetTeam/GetRole/GetPhase/current server clock callbacks; only server-selected nearest actor in 3D with direction and Raycast line-of-sight; rejects unknown requests, dead/untamed/ally/wall/behind/distance/active immunity; teammate-only nearest trapped rescue.
- New bridge requires existing Game's `Rules.validSeq` to have accepted an intent before passing `sequenceAuthorized=true`. Source-only tests check the boundary exists; actual Roblox exploit testing is outstanding.
- Original Core emits tick receipts and handles 12s cooldown /2s root / rescue+escape/ 6s immunity. Bridge invokes only injected canonical damage callback, with match/caster/victim/tick dedupe key and server-side roster check.
- Legitimate Studio negative UserIds mapped by private server-only numeric ids, not sent to clients. Server game time is normalized to elapsed seconds 0..3600 to meet original Core.

Offline test suite: `python -m unittest discover -s tests -v`. These test **20 static Luau integration assertions and 32 independent Python deterministic target/clock/receipt behavior cases**. They are not genuine engine runs. Later use actual Studio 2client/mobile and independent replay QA before acceptance.
