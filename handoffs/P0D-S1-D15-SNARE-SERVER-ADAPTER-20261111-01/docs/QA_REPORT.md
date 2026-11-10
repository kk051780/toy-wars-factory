# D15 S1 adapter source-only QA

As of 2026-11-11 JST. Native Luau parse, Roblox Studio, real mobile, public release and monetization remain NOT_TESTED / NOT_AUTHORIZED.

- One opt-in Luau server ModuleScript; exact original Core is referenced by SHA but **not cloned** or modified in this packet.
- No new RemoteEvent, OnServerEvent, heartbeat, RNG, RoundCoordinator, direct Humanoid:TakeDamage or WalkSpeed assignment. Game remains sole authoritative round, combat, data writer.
- Server trusted Players/GetTeam/GetRole/GetPhase/current server clock callbacks; only server-selected nearest actor in 3D with direction and Raycast line-of-sight; rejects unknown requests, dead/untamed/ally/wall/behind/distance/active immunity; teammate-only nearest trapped rescue.
- New bridge requires existing Game's `Rules.validSeq` to have accepted an intent before passing `sequenceAuthorized=true`. Source-only tests check the boundary exists; actual Roblox exploit testing is outstanding.
- Original Core emits tick receipts and handles 12s cooldown /2s root / rescue+escape/ 6s immunity. Bridge invokes only injected canonical damage callback, with match/caster/victim/tick dedupe key and server-side roster check.
- Legitimate Studio negative UserIds mapped by private server-only numeric ids, not sent to clients. Server game time is normalized to elapsed seconds 0..3600 to meet original Core.

Offline test suite: `python -m unittest discover -s tests -v`. These test **20 static Luau integration assertions and 32 independent Python deterministic target/clock/receipt behavior cases**. They are not genuine engine runs. Later use actual Studio 2client/mobile and independent replay QA before acceptance.

## V1.1 acceptance delta

Previously 52/52 offline PASS could not detect a second successful trap by the same caster on the same victim in a single match. Source was found to use only `matchId:casterId:targetId:tick` as receipt, which incorrectly reused the same keys after original Core allows recast at 12 seconds. The server-only cast-generation fix is accompanied by 10 new negative/positive tests (62/62 total), including recast uniqueness, stale-tick dedupe, round reset and missing-generation fail-closed. Genuine Luau, native original D15 match integration and Roblox Studio are still NOT_TESTED.

## V1.2 epoch / intent anti-flood change

13 additional executable Python boundary assertions/oracle checks added,
result **75/75 PASS**. New callbacks require `getRoundSerial` equality at
round init and before roster/poison processing. Server-owned minimum 0.15s
intent interval rejects repeat actions before any `self:update()` scan;
invalid clocks, stale rounds, and caller-supplied client time fail closed.
No extra network / HP / match writer. Rate state clears on player departure
and new round. All results are source/behavior-model **NOT native Luau tests**.
