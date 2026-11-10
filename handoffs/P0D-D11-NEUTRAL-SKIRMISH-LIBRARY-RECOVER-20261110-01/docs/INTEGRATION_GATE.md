# v43-A integration contract — NOT YET INTEGRATED

**Dependency gates**: Verify the latest authenticated PC-local `p0d-siege-v19` CHECKPOINT/RESUME/manifest/Place SHA. Finish v37 final saved-Place multiplayer QA and decide v39-H1 integration before testing v43-A. Do not silently overwrite newer game code. No public/game release.

**Server-only adapter**:

1. Create one `NeutralSkirmishCore.new(matchId, {{id="z1",kind="ZOMBIE"},{id="b1",kind="BEAST"}}, serverNow)` per active S1 match from actually spawned existing neutral units. Map unit IDs only from server registry, never client-chosen.
2. On a bounded server heartbeat (at most 1-second steps), build `observations` from **server authoritative** roster, team, alive state, character position, egg possession and intentionally requested capture action (remote input request may only signal intent; validate proximity and cooldown on server). Do not copy a remote-provided `distance`, `team`, `unitId` ownership, `alive`, or `matchId` as proof.
3. Call `step(state, serverNow, observations)`. Apply `CAPTURED`/`EXPIRED` events to existing NPC faction/target selection, without spawning more NPCs or buffing ATK/HP/DEF. Roster ownership, egg ownership, victory rule and round clock are **outside** this module and must be protected.
4. `hostile` is a pure faction/species helper only. Integrate it with the existing attack target filters, server-side. The neutral-versus-neutral default should be zombie-versus-beast, not random same-species friendly fire.
5. `endRound` on match finalization. Reject stale events/closed sessions and ensure no persistent allegiance between matches. No DataStore writes.
6. UI shows contested 3s progress + short 8s temporary allegiance + expiration. Mobile buttons must not overlap existing egg/skill controls. Avoid more than one visible indicator per neutral unit.

**QA gates**:

- Blue uncontested 3s capture; red contested capture resets progress; one-controlled-per-team cap; cooldown after expiry; no action from dead or egg carrier; no client-spoofed team/distance; simultaneous capture deterministic; reconnect/disconnect resets stale visual states.
- Neutral zombie fights neutral beast; BLUE-controlled zombie will not attack BLUE; RED remains enemy; no permanent stats or new spawns.
- S1 2-client and 3-client with no forced teleport; S2–S4 remain unaffected; seven jobs and egg victory regressions; mobile touch UI and FPS; real player test if available.
- `STATE=REFERENCE_ONLY` until Luau compiles and Roblox Studio Play/Stop runs on the integrated Place. Physical mobile, real player retention, D1 and revenue remain NOT_TESTED.

**NO** P0-A/B/C lock bypass, unreviewed main changes, GitHub plaintext of private source, merge, production publish, spending, Robux transactions.
