# TRAP RAIDERS D14 — CART three-packet integration contract (source-free)

**Game:** `TRAP_RAIDERS` · **Work:** `p0d-siege-v19` · **Contract version:** `P0D_D14_TRIAD_TRACE_V1`

## What this bundle is, and is not

Runnable Python standard-library trace consistency checker, synthetic example, tests, and a mapping contract. It verifies **only a normalized, sanitized event record**. A trace claiming `source: SERVER` can be forged: it is NOT independently attested by this checker, and a clean run **does not** imply that Roblox Studio executed, that vehicles visibly moved, or that any private Luau was integrated. No 3D source, Roblox asset, real player information, password, secret key, or production event code is in this bundle.

| Role | Immutable valid source | Contract ownership |
|---|---|---|
| Seat authority | `0bcf39c22c583604d72ccac47d29fc9d87b7e662` / `P0D-D14-VEHICLE-SEATS-20261110-01` | Sole server two-slot reservation/boarding/expiry authority. Do not duplicate. |
| CART server motion | `2cd3fb9b31bfe7817ca0ceba7456300c3a41bd12` / `P0D-D14-CART-RAIL-MOTION-20261110-02B` | Sole pure rail move/pose authority. **`cae5691b...`/`...02` is superseded** because its 3D rendering collided with another chat; refuse it. |
| CART/RAFT client visuals | `3c78cd0af618f320fe9d0aafe7569e1e9b95b4b0` / `P0D-D14-CART-RAFT-VISUAL-20261110-02` | Decorative noncolliding 3D only; `0/2`–`2/2` badge derives from server seat facts. Renderer must never acquire server authorization. |

Other chat independently owns **RAFT water motion** (claimed issue #218). This contract is CART-only; do not fold RAFT physics into this package. D11 neutral-capture QA and D07 boss work are separate.

## Safe mapping from actual PC Luau (OWNER Codex only)

1. Preserve **latest** original PC `CHECKPOINT`, `RESUME`, saved Place, source SHA256 and manifest. Take a versioned backup of the current unpublished Place. Do not downgrade to older v39 SHA if a newer v43-A save exists.
2. Inspect each actual *decrypted* D14 source. On Windows, restore one fixed-commit sealed handoff at a time with the separate OWNER key, the reviewed non-overwriting restore tool, exact packet ID and expected ZIP SHA; do not extract over main game sources. The actual `VehicleSeatCore` callbacks are **not known from GitHub public README**, so do not guess function signatures or require this normalized schema to equal an actual game Remote API.
3. The PC server owns round ID, roster, vehicle/team/seat state, driver eligibility, and route nodes. Map **successful authoritative seat changes only** to `BOARD`, `UNBOARD`, `DISABLE`. Do not infer success from a client button press. Populate `alive=true`, `mounted=true`, `carrier=false`, `snared=false` for a confirmed `BOARD`; blocked attempts should be recorded in private QA logs and should **not** emit a successful `BOARD` event.
4. The one canonical server motion reference (`CartServerAdapter:advance` / `:heartbeat` once inspected) consumes driver facts from the authoritative seat ledger. `ADVANCE` represents a successful, already server-validated per-leg request; reject client-selected waypoint, distance, orientation, team, seat, player, or speed values. `POSE` represents server `CartServerAdapter` values after movement processing, not client-proposed CFrame. If a player disconnects/dies/carries egg/is snared, emit `DISABLE` after actual seat removal and stop motion immediately before a new moving pose.
5. Client-only model sees an existing server-dispatched visual snapshot, never a client-created source of truth. `VISUAL` is an observed renderer update with a matching `POSE seq`, matching CART/team and current server-derived number of seats. The visual renderer's actual message contract is **unverified** until Codex reviews its private Luau; adapt at the PC boundary, not by changing owner modules.
6. Trace route definitions are server-authored (`2–24` nodes, edges `6–80` studs, speed `2–16` studs/s; one CART per team); trace times `ms` and `seq` are locally monotonic/anonymous per round. Use anonymous `p_*` tokens, not real Roblox IDs or usernames. Never upload raw PC log, username, user ID, IP, Place, decrypted ZIP, private Luau, or key to PUBLIC GitHub.
7. `ROUND_END` is terminal; the checker prevents later events in that record. It cannot prove actual NPC/Seat/Model cleanup occurred. Codex must separately check seats removed, model destroyed, event listeners released, and owned Studio process exited, and attach local log hashes to the PC-only QA record.

## Trace event contract

Top-level `schema`, `game_id`, `work_id`, `round_id`, `provenance`, immutable `reference_commits`, server-authored `routes`, and chronological `events`. Valid source provenance is either `SYNTHETIC` or `PC_SANITIZED_UNVERIFIED` (the latter is a label, not attestation).

- `ROUND_START` and terminal `ROUND_END`: `type, seq, ms, round_id, source=SERVER`.
- `BOARD`: common server fields, `cart_id, team, player, seat=DRIVER|PASSENGER, alive=true, mounted=true, carrier=false, snared=false`.
- `UNBOARD`: common server fields, `cart_id, team, player, seat` matching current occupant.
- `DISABLE`: common server fields, `cart_id, team, player, reason=DIED|DISCONNECT|EGG|SNARED|ROUND_RESET` matching occupant; represents actual authoritative removal, not a failed client request.
- `ADVANCE`: common server fields, `cart_id, team, player, command_seq, leg` validated against current driver/previous stationary pose, per-leg advancement and strictly increasing command sequence.
- `POSE`: common server fields, `cart_id, team, position=[x,y,z], leg` (1-based), `progress` (0..1), `moving`. On reaching the end of a leg, the *old Luau server core increments `leg`, sets `progress=0`, and stops*, so the trace represents the **new leg index** and the exact arrival node. Position must follow the server-authored rail and speed/time bound; initial pose must be stationary at the first node.
- `VISUAL`: `source=CLIENT_VIEW` plus `cart_id, team, pose_seq, seat_count, visual_kind=CART`. It is an observed client render **only**; no player IDs, driver authority, world position, source Remote, or speed fields are accepted.

The validator checks schema, exact packet pins and supersession, source/field allowlists, monotonic sequence/time, 2-seat exclusivity, no double/cart-cross passenger, egg/trap exclusions at boarding, server-only advance, no client-selected coordinates, no replay, rail position, bounded speed, one segment per advance, stale visual IDs, correct seat badge, and terminal round. It is not a full real-time solver and has not been matched to private PC gameplay callbacks. It intentionally rejects traces with gaps over 2,000ms between server pose samples because consistency across a larger gap cannot be assessed.

## Suggested OWNER-only Studio sequence (after v39/v43-A gates)

- Start with ONE BLUE CART on S1, not RAFT, with actual 2/3 client servers. Initial stationary route pose, zero occupants, authorized driver board, second teammate passenger, blocked rival+egg carrier; duplicate boarding and double-advance denied.
- Server-only advance one rail segment, client cart follows 3D pose and `1/2` then `2/2` seat badges, no client-created server motion. Hit endpoint and require a NEW authorized command for next leg; reject spoofed position, mismatched round, replay/extra command.
- Remove/kill/disconnect driver and assert **server motion stop immediately** plus renderer clean state (not only badge change); spectator/late join visual TTL and round reset.
- Confirm 4 maps/7 jobs and previous egg result/rematch/v43-A neutral ownership not broken. Check FPS and physical devices separately. Check visual collision disabled, R6/R15 and mobile layout. Stop→Edit→Save→**normal Quit owned Studio**, verify only owned PID exit and record final SHA.
- Treat test `PASS` output of this Python tool only as `TRACE_CONSISTENT_OFFLINE`, **never** `LUAU_PARSE_PASS`, `STUDIO_QA_PASS`, `PLAYER_ACCEPTANCE`, `PUBLISH_READY` or consent to merge.

## How to run

```powershell
python tools/verify_d14_triad_trace.py examples/synthetic_cart_trace.json
python -m unittest discover -s tests -v
python tools/verify_d14_triad_trace.py C:\\private\\d14\\sanitized_trace.json
```

No network is needed by the validation script. If any input check fails it returns status code `2` and `D14_TRIAD_BLOCKED:<reason>`. A consistent synthetic/PC-supplied trace exits `0` but cannot independently establish PC authenticity.
