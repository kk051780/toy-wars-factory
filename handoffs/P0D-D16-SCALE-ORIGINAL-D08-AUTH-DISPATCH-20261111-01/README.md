# TRAP RAIDERS — exact-original D16 ScaleFx ↔ D08 trusted weather dispatch (OPTIONAL)

**Game:** `TRAP_RAIDERS` / `p0d-siege-v19`  
**Packet:** `P0D-D16-SCALE-ORIGINAL-D08-AUTH-DISPATCH-20261111-01`  
**State:** independent keyless source candidate, **disabled by default**, not Windows Codex integrated, not Studio tested.

This package solves a **real API mismatch**. The exact original recovered D16 `ScaleFxCore.luau` (immutable Git commit `584b11ef24cf3d44695d86b505207491bbd3844e`) exposes `Core.new(matchId)` and `Core.begin(state,matchId,eventId,kind,actorId,roster,nowSeconds)`. Earlier **clean-room** D16 scale adapter V1 `ac50372942712503f836fb84d6331ef3bcc4b8f2` / V2 `1877222d4817153435bc5cfacdf1bb4e90d75aff` expect a *different* core API and **must not** be installed against the authentic recovered original. This new optional module calls the **original signatures only**.

## Scope and non-features

`luau/OriginalScaleD08AuthorityGate.luau` is a pure server-side state/callback adapter that can receive a D08 canonical, genuine **WEATHER ACTIVATE** callback and forward to the authentic original D16 effect. It never chooses weather, rolls RNG, creates a scheduler, listens to a RemoteEvent, changes an avatar model, applies gameplay scaling, changes physics/HP/damage, or purchases anything. It exposes `new(originalCore, ownerServerConfig)`, `activate`, `cleanup`, `tick`, `leavePlayer`, `snapshot`, `stop`. It does **not** include original D16 or D08 code; those are separate verified immutable references.

Canonical D08 bridge, not a new chooser: `70dcc3b50129c288441452776360588184ca6c22` `luau/CanonicalEventBridge.luau`. The D08 handler's envelope contains `{matchId, stage, epoch, kind="WEATHER", subtype, phase="ACTIVATE", validUntil}`; the original D16 core requires **an additional genuine server-generated eventId**, server roster, explicitly approved `GIANT_ONE` or `MINI_ALL` effect, trusted actor for GIANT, and seconds-based server clock. This adapter supplies the contract **only via OWNER-reviewed server callbacks**.

The adapter **never assumes** e.g. `WX02_SMALL = MINI_ALL` or any other subtype-to-effect mapping. Owner-reviewed `subtypeToOriginalKind` must be explicitly passed; unspecified subtypes reject. An unassigned weather event must be handled by the existing authentic weather handler, not blindly routed here or made to disable D08. This module requires both `enabled=true` **and** `ownerApproved=true` to operate. No sample code enables it by default.

## Authority and cancellation

- The PC integrator must provide `isCanonicalActivate(envelope)` and `isCanonicalCleanup(envelope)` as strict **server provenance / table-identity** attestation on the actual D08 callback objects, not merely a check that a caller's fields match.
- `readRound()` supplies trusted `{matchId, stage, epoch, startedAt, deadline, now, active}`. `now` is **server seconds** in the same time domain as original D16 `Core.begin/advance`, with no client input. Id/epoch, clock monotonicity, active round and expiry are checked before and after yielding callbacks.
- `getTrustedRoster(matchId)` returns 1–16 unique trusted **string IDs**, not Player objects or client payloads. `chooseTrustedGiantActor(envelope, roster)` picks one of these server-owned IDs for GIANT. `mintServerEventId(envelope)` creates a unique authoritative ID.
- Per-round one-attempt receipt, bounded 128 rounds. Genuine cleanup, owner stop, round replacement, stale epoch, clock rollback, D08 `validUntil` or original 8-second TTL close and revoke. No postponed callback may start a new effect after cleanup.
- `snapshot()` returns an isolated copy of visual-only `scaleMilli` (`1600`/`700`), target string IDs and seconds-based expiry. It cannot make avatars bigger or smaller; real visual synchronization is **separate work**.

## Local offline tests

```bash
python -m unittest discover -s tests -q
```

59 synthetic Python behavioral/static-contract tests pass, including cancellation during yielding trusted callbacks, server expiry, original method signatures, no implicit weather mapping or Remote/physics dependencies. **Python oracle does not execute Luau or Roblox Studio.** Its purpose is to define expected behavior for subsequent native tests, not claim Roblox QA.

## Windows Codex handoff

Read `docs/OWNER_CODEX_ACCEPTANCE.md`. The OWNER's actual Windows Codex session is the *only* game integrator. It must first preserve real current local source, Place and SHA, follow #218 owner rules and currently active D07 Studio QA, receive the 22nd exact original D16 packet with independent SHA verification (22nd intake tool commit `72fa23177c1fdce8433a9ecc565787d1ca5dcd6e`), and compare existing game before deciding if this candidate is necessary. If the true PC already has a passing original-compatible D16 weather handler, use **NO-OP**. Don't install old cleanroom adapter V1/V2 or two scale cores.

**Original-source recovery counter:** 22 byte-authenticated old originals currently public, 21 included in older Windows 21-packet receipt; this new module is **not** another historical source recovery. No main modification, merge, Roblox production publish, or charge permitted by this handoff.
