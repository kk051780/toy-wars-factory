# P0-D D14 outbound visual publisher — PC owner integration contract

**GAME** `TRAP_RAIDERS` / work `p0d-siege-v19`. Unique feature slice: **server-owned outbound visual frame relay**, not a seat authority, motor or model. The module is **disabled by default** until the Windows Codex OWNER has verified the actual PC API. Never wire this directly to `OnServerEvent` or trust client supplied seat facts/position/round/time.

Existing immutable references (all separately AES encrypted): **SeatCore v2** `0bcf39c22c583604d72ccac47d29fc9d87b7e662`; **CART pure rail** `2cd3fb9b31bfe7817ca0ceba7456300c3a41bd12`; **RAFT water** `027fd926a9d315a84f701086448fa5c1febc6697`; **client visuals** `3c78cd0af618f320fe9d0aafe7569e1e9b95b4b0`; optional **Rider safety** `0af53f121b35f2e822c63514112360d220c92227`. Their APIs are encrypted; the actual types must be reviewed by OWNER PC after restore. **Do not assume this `TR_D14_VISUAL_V1` DTO is already the client visual schema:** implement `authority.encodeVisual(frame)` only after reviewing the real ClientVisualPolicy. If mismatch, STOP until a reviewed mapping exists.

## Trusted PC adapter obligations (fail closed)

- `authority.isTrustedRound(roundId)` validates server's actual round coordinator S1/S2, not the caller's assertion.
- `authority.getSnapshot(vehicleId)` fetches current canonical seat epoch, round/team, active driver/passenger booleans, selected model type, monotonic server tick, existing movement core pose and source sequence. Never pass client Remote values directly.
- `authority.getRecipients(frame)` returns only genuine current `Player` instances (max 4), server roster authorized; no user IDs or player names in visual DTO. Validate recipients before sending.
- `authority.encodeVisual(frame)` explicitly maps fields into the prior client-only visuals' real accepted snapshot schema, preserving round/time/sequence and maximum TTL. No new scheduler, second seat ledger or client authority.
- Call `Adapter.new({enabled=true, remote=<server-owned RemoteEvent>, authority=<canonical adapter>})` only in a backed-up **unpublished** Place after script inspection. `beginRound()` then `publishFromServer(vehicleId)` on the server's existing tick path; `stop()` on match end. No separate loop or new Remote inbound consumer.

## Safety/edge contract

2–4 vehicles max 4. Output at most 10Hz per vehicle (except immediate seat-presence transitions); TTL 1.5s. Authoritative prior `sourceSeq`, seat epoch, per-round server clock are required. Reject stale/negative/NaN/Infinity time and positions, stale round, duplicate seq, reused vehicle IDs, >16stud/s CART or >8stud/s RAFT displacement, client seat teleport and movement after driver disappears, passenger without driver, movement without driver. Output DTO allowlists keys: schema, roundId, teamId, vehicleId, stage, kind, seq, serverTime, expiresAt, position, direction, moving, driverPresent, passengerPresent.

Caveat: the trust booleans must derive **solely from real server authority**. The policy cannot prove they are truthful. No physical seat, server model PivotTo, world collision, or actual player movement in this package. Visual-only `RemoteEvent:FireClient` does not authorize game controls.

## OWNER Windows Codex next-gates

1. Read latest #213/#218/#217 and local checkpoint. PC latest confirmed v43-A scoped QA; OWNER's priority is saved Place **cold-restart QA then D07 Gorogan**, not automatic D14 installation. Preserve latest saved Place/source SHA and all earlier results. No new work if protected gate disallows.
2. In later D14 intake, safely restore this package and each applicable existing D14 reference with separately delivered OWNER private keys; validate ZIP+manifest SHA. Never use the superseded D14 old CART 3D package `cae5691b...` or old seat v1 `250658...`.
3. Run actual Luau parser, inspect authority `getSnapshot` and encoded visual API, validate match epochs, no inbound Remote, spoofed client, seat death/disconnect, rate limit, stage/match reset and camera/mobile. Use prior `D14_TRIAD_CONTRACT` source-free trace validator for sanitized actual server trace.
4. S1 small unpublished Studio: 2/3 clients, 0/2 → 1/2 → 2/2, cart and raft snapshots, stop on driver quit, spoofed Remote, delayed/replayed snapshots, 4-map 7-job regression, genuine physical mobile later. Save/Stop/normal exit ONLY Codex-owned Studio PID. Capture actual QA and SHA; do not mark PASS on this offline model alone.

**Local offline Python tests are a reference oracle, not actual Luau compile or Studio play.** PUBLIC GitHub ciphertext only; key + plain source ZIP must stay private. No main/merge/publish/paid action/P0-A/B/C CAS changes.
