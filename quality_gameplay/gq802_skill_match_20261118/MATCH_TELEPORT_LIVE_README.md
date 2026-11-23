# GQ802 optional same-lobby teleport bridge

This is the existing source candidate from PR #807 and spec #802. It is not connected to the current official Host or selected gameplay profile. The feature remains disabled by default. No new lobby, global queue, RemoteEvent, team, HP, score, or reward authority is introduced.

## One cohort, one pending owner

`dispatch` accepts a server-verified group of 8 or 16 live Players in one lobby. It reuses the existing SkillMatchPolicy and checks the existing Host epoch callback. The same `byUser` / `byMatch` pending record now reserves the whole local cohort before the yielding MemoryStore claim. While that claim is pending, another dispatch overlapping that cohort returns `ALREADY_DISPATCHING` before generating another GUID or issuing another MemoryStore or teleport request.

The pending record starts in `CLAIMING`. A late teleport-failure notification cannot retry a claim that has not reached teleport. After the claim, dispatch rechecks the active epoch, the 90-second pending lifetime, current ownership, and the exact captured Player instances. Leaving and rejoining with the same UserId does not authorize an old captured roster.

Only after these checks does the record become `TELEPORTING` and call `TeleportService:TeleportAsync`. Claim failure, epoch change, expiry, roster change, or an initial teleport exception releases entries only while that exact pending record still owns them. An old completion must not clear a later owner's reservations. Unused MemoryStore tickets expire under their existing TTL; cleanup does not delete an unverified remote record.

Existing contracts remain: ticket TTL 180 seconds, local pending expiry 90 seconds, retry limit two, reuse of the same reserved destination, and no in-game TEAM assignment for BR. The opt-in, Studio, reserved-server, destination, roster, and server-owned arrival guards remain enabled.

## Roblox service boundary

The adapter uses server-generated GUIDs with `TeleportOptions.ReservedServerId`, `MemoryStoreHashMap:UpdateAsync`, and `TeleportService:TeleportAsync`. Arrival validation reads the server-owned MemoryStore ticket; client-visible TeleportData remains an untrusted transport hint. Cross-lobby global matching still requires a separately reviewed shared queue and coordination, and is not implemented here.

Current official references:

- [MemoryStoreHashMap UpdateAsync](https://create.roblox.com/docs/reference/engine/classes/MemoryStoreHashMap): the service call yields and applies updates atomically to a single key. Different generated match keys do not reserve the same local cohort against each other.
- [Reserved server routing](https://create.roblox.com/docs/projects/teleport-private-servers): generate a GUID for `ReservedServerId` and reuse it for retries.
- [Testing teleports](https://create.roblox.com/docs/projects/teleport#test-teleports-in-studio): current Studio Test and Team Test support `TeleportAsync` without publishing. Test-mode IDs and Team Test reserved-server IDs have documented differences from production.

The previous statement that Studio cannot test `TeleportAsync` is outdated. This correction does not remove this adapter's intentional Studio OFF guard, relax production arrival validation, or claim that an engine test was performed. Any enabled Studio or destination integration needs its own scoped setup and evidence.

## Evidence and integration limits

The retained original Native tests cover policy, synchronous duplicate rejection, destination checks, arrival tampering, expiry, same-ID retry, BR behavior, feature OFF, and network errors. The bounded continuation models yielding service entry to check concurrent cohort reservation and ownership-preserving cleanup. These are source-derived Native tests with controlled services, not actual Roblox MemoryStore or teleport sessions.

Canonical source selection, Host call sites, destination `verifyArrival` wiring, same-HEAD integrated Native/Rojo and inverse rollback, and real engine/client acceptance are still required. Source-candidate CI success alone does not mean the official game uses this adapter. OFF remains omission of this optional adapter; no public release, main promotion, or paid functionality is authorized by this package.
