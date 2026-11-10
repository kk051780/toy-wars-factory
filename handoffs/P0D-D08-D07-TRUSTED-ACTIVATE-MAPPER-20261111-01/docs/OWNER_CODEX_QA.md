# OWNER Codex acceptance sequence — D08/D07 activation shim

## Ownership and dependency

Read Issue #218 TOP and latest comments, then Issue #213 genuine PC evidence and #217 cross-P0 contract. Preserve the real latest Place/source/HEAD/CHECKPOINT SHA before edits. Real PC owner integration is distinct from a GitHub source readback. As of the source review, Windows Codex reported `21/21` original keyless packs with `321` manifest-listed file checks in #218 comment `6770229340`; that receipt is **not** a Studio pass.

Use only original D08 canonical event bridge SHA `70dcc3b50129c288441452776360588184ca6c22` and original D07 combined SHA `80a1f0ce15adfb475df0c95677f9966bb760a8ae` as interface references. D08 emits `phase="ACTIVATE"`, `stage` and `validUntil`. D07 Combined needs `event="ACTIVATE"`, a verified callback `isCanonicalActivation`, and `untilAt`. Do not bypass any genuine RoundCoordinator attestation. The new mapper is **OFF by default** and must never subscribe to a client RemoteEvent.

## Must-pass gates prior to enable

1. Decide whether newer actual PC code already correctly maps D08 to D07; if it does, **NO-OP** on this packet. Never install two boss runtimes, two event choosers, two damage gates or two callback mappers.
2. Source SHA/byte verification using the package `BUILD_MANIFEST.json`; run `python -m unittest discover -s tests -v`, expect 35 tests PASS. This tests a Python model and static Luau text **only**. Perform an actual native Luau parser/require test before claiming syntax acceptance.
3. Give the mapper only genuine server `RoundCoordinator.readTrustedRound()` values. Review full D08 handler setup (`enabled=true` only after approval); ensure D08's `onBossActivate` is the **only** callable connection to mapper `:handle`. Review D07 `isCanonicalActivation` to call `mapper:isCanonicalActivation(activation)` using object identity while callback is in flight.
4. Wire `abortCombined(roundId)` to stop the exact already-running D07 combined boss (rig + damage + receipt + visual cleanup). If abort cannot be guaranteed, KEEP DISABLED. Test callback exception, yield with round epoch change, expiry during yield, clock rollback, stale stage, duplicate event, client-shaped table, missing/invalid server snapshot, simultaneous/duplicate boss activation, and limit 128.
5. Verify D07 `mintServerEventId`, true stage anchor/ground, server NPC Humanoid with server network ownership, and true `STOMP_RESOLVE` receipt validation. No direct client damage.
6. Run S1/S3 Play/Stop 2-client: exactly ONE canonical boss spawn, 2s telegraph, valid 0-8 HP damage only in server-approved hit window, dodge/no-hit proof, no double damage, stage mismatch reject, cleanup on round transition, no unbounded client Visual models, no scheduler conflict. Verify S2/S4 unrelated events unchanged.
7. Review real client visual follows physical boss movement; mapper intentionally does **not** solve the client visual position drift flagged by the previous D07/D08 audit. Test mobile landscape/HUD/FPS (emulator != real phone). Stop->Edit->Save->normal owned Studio process exit/PID disappearance. Report all SHA, real output and PASS/BLOCKED separately.

## Stop conditions

Any callback yield with stale server epoch, unconfirmed abort, duplicate boss listener, boss-movement visual drift, damage receipt not tied to one true `STOMP_RESOLVE`, unowned/unknown Studio instance, or missing checked PC baseline means HOLD and rollback isolated copy. GitHub issue comments are **not executable Windows Codex commands**. OWNER must directly instruct the PC session.
