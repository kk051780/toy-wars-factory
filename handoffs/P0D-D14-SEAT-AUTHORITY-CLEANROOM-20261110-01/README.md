# TRAP RAIDERS D14 two-seat authority — CLEAN-ROOM keyless fallback

- `game_id`: `TRAP_RAIDERS`
- `work_id`: `p0d-siege-v19`
- `packet_id`: `P0D-D14-SEAT-AUTHORITY-CLEANROOM-20261110-01`
- `delivery_mode`: `PUBLIC_SOURCE_V1`
- **Type:** NEW alternate implementation; **NOT** restored/decrypted old
  `P0D-D14-VEHICLE-SEATS-20261110-01` / original SeatReference_v2 ZIP.
- **Acceptance:** `REFERENCE_ONLY / NOT_STUDIO / DISABLED_BY_DEFAULT`.

## What is included

`luau/SeatAuthorityPolicy.luau` is a standalone *pure server-side policy*
that proposes two seats (`DRIVER`, `PASSENGER`) after a trusted server has
verified a real occupant and actor generation. It is deliberately NOT wired
into a Roblox Script, RemoteEvent, VehicleSeat, cart path, raft movement, or
WeldConstraint. It does **not** mount a player or mutate an actual Roblox
vehicle; it only emits a `MOUNT_INTENT` requiring separate actual authority
receipt. It cannot be used as proof that a real occupant is seated.

Replays (event time and monotonic sequence), duplicate seats, duplicate
player across roles, stale rounds, a changed vehicle, dead/unauthorized
occupants and mismatched character generations are rejected. An occupying
lease expires after 1.5 seconds unless reverified. No permanent history of
player identifiers, real player records, gems or purchase state is stored.

`tests/seat_reference.py` is a Python oracle for the subset of behaviors
covered by `tests/test_seat_policy.py`, which includes Luau structural safety
assertions. Those tests do not execute Luau or prove actual Studio behavior.

## Collision and intake rules

1. Prefer exact original SeatReference source if the historical author can
   publish it under the OWNER-approved `PUBLIC_SOURCE_V1` contract. Do NOT
   install both original SeatCore and this candidate.
2. Review latest true owner-PC CHECKPOINT, `src`, Place, existing D14 authentic
   seat runtime and five other D14 separate sources (CART_RAIL, RAFT_WATER,
   RIDER_ATTACH, CART_RAFT visual, OUTBOUND). No competing seat writer.
3. Choose a SINGLE server authority and construct an adapter only after
   reviewing real PC APIs. No client-provided `server_authorized` or
   `server_seat_occupant_verified`; both must be derived from actual server
   checks. Do not rely on the intent alone to Weld/Seat a character.
4. Stage to new isolated, unpublished PC clone/Place; run Luau parse, real
   2-player boarding/disconnect/respawn/round reset, fake Remote rejection,
   Android/iPhone controls, saved Place repeat and normal Studio exit/PID
   before calling gameplay PASS.
5. This package does not change other chat branches, protected coordinator,
   main, GitHub PRs, game publication, paid services or automations.

**No keys or AES ciphertext are needed to retrieve this independent candidate.**
It does not represent byte-for-byte recovery of the historical encrypted
package and must not increase the count of migrated original asset packets.
