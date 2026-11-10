# D15 Trap & Rescue integration boundary (reference only)

**Game:** TRAP_RAIDERS, **work_id:** p0d-siege-v19, **packet_id:** P0D-D15-TRAP-RESCUE-20261110-01, feature ID **D15**.

This pack adds *one isolated slice* of the v41 trapper concept: chain root, mild poison DOT, teammate rescue, and self-escape. It **does not** implement 7-job ultimate skills, warp traps, 3D traps/VFX, client button, inventory/cosmetics, game integration, or persistence. It is not a cumulative replacement for v37/v39/v40-42/v43-A/B.

## Server authority (mandatory, not supplied by this packet)

1. Only the genuine, existing **server** round manager instantiates `Core.new(realRoundId)`, and the server's player roster supplies `syncPlayer` (userId, BLUE/RED, job, alive, X/Z from RootPart). No direct client-supplied team, job, position, alive, clock or target status may be used. The real match identity is verified before any action.
2. In *each server Heartbeat*: first reconcile player removal, team, role, alive, authoritative position; then call `Core.advance(state, roundElapsedSeconds)`. Apply every `POISON_DAMAGE` event **once** via server-owned combat/humanoid damage logic only after independently checking matchId, source, target and any actual armor/reflect/death rules. This reference does not mutate real humanoid health, WalkSpeed or `eggHolder`.
3. For a `trap` request, the server must identify the invoking Player **from OnServerEvent's first parameter** and select the target only if currently a valid opposing `Player` in the same match. Resolve UserId and position on server and call `tryCast(state, invokingUserId, validatedTargetUserId)`; any unknown field ignored. For self-escape use `tryEscape(state, invokingPlayer.UserId)` only; do not accept a targetId sent by client.
4. Teammate rescue similarly authenticates the invoking Player and validates the target from server; game also checks line-of-sight/obstacles and physical proximity in XYZ (this pure X/Z sample cannot do it). Apply status effects only in the server controller, not via client-sent `isRooted` values.
5. `Core.status` gives `{trapped, rooted, poison, immunityRemaining}` for a filtered UI view. Root duration 2.0 s; available voluntary escape at 1.25 s; teammate rescue after 0.5 s if within 10 studs; immunity 6 s after release; poison three 3-HP ticks (9 max) and none after successful rescue/escape. A trapped egg carrier **never auto-drops** their egg; existing egg ownership and victory remain completely unchanged.
6. If caster/target dies, disconnects, changes teams or round ends, clear effects. RoundEnd calls `Core.endMatch`, drops outstanding DOT events, and stops prompts. Do not let the reference change death/revival or scoring.
7. No gameplay stats, XP, stamps, DataStore, boss/weather events or P0-A shared writers are touched. Do not copy over v37 source. Check existing slowing/poison/CC logic to prevent double application and unintended immunity bypass.

## Minimal staged QA acceptance

- Offline: Python model tests, source contract inspections, ZIP SHA/manifest verification (not Luau compile).
- Isolated Studio ModuleScript + `TrapRescueSmoke.server.luau` should print `P0D_D15_SMOKE_PASS` **only if actually run in Studio**. It is **not** a multiplayer proof.
- 2-client / 3-client: BLUE TRAPPER versus RED victim and RED rescuer; attempt allied trapping, out-of-range cast, 12 repeats, forged `userId`, outsider rescue, early escape, late escape, death/reconnect and simultaneous trap application; verify exactly one active trap per victim, immunity, 9-HP DOT cap and no phantom damage after removal.
- Run actual movement/root UX on PC and iPhone landscape emulator. Use reduced-motion prompts and an explicit tappable `脱出` action, not forced repeated tapping, and allow ally rescue in easy-to-understand UI. Measure FPS and count unintended deaths. Real phone and VFX are separate acceptance gates.
- Most importantly: run final saved Place SHA's v37 egg capture→drop→recapture→win→rematch baseline. Owner's Studio only Play/Stop→Edit→save→normal quit→PID disappearance. Do not mark **STUDIO_QA_PASS** without engine evidence.

## Precedence and dependency

#218 is coordination source, #213 is actual game QA, #217 is cross-P0 auth/transport. D15 depends on D01 and D03. Another chat owns D13 defender response; do not combine or overwrite. PC integrator first v37 final SHA QA, then v39-H1 real integration, then v43-A; this D15 remains **READY_PACKET_DEPENDENCY_HOLD** until owner approves next isolated acceptance. If an existing D15 trap engine already exists in the PC build, compare contracts and treat this as a reference only.
