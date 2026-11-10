# TRAP RAIDERS D16 ⇐ D08: keyless trusted-event dispatch reference

`packet_id=P0D-D16-SCALE-D08-DISPATCH-GATE-20261110-01` · game `TRAP_RAIDERS` · work `p0d-siege-v19`.

**NEW independently written plaintext reference, not a recovery of the historical encrypted D16 ZIP.** The legacy D16 `P0D-D16-SCALE-FX-20261110-01` original source is **NOT RECOVERED** because the historical ZIP's raw bytes are not accessible here. This package must **not** increment the 21 exact-original source migrations.

## What this actually does

- Provides a **pure server-side** `D16ScaleD08DispatchGate.luau` with `Gate.new`, `:onWeatherActivate`, `:snapshot`, `:onCleanup` and `:stop`.
- Takes only already-generated `WEATHER / ACTIVATE` envelopes from the **one** D08 `CanonicalEventBridge` and feeds a separate D16 `D16ScaleFxCore.begin()` state machine after double readback of the trusted round and server roster. It **does not choose a weather event** or generate random values.
- `enabled=true`, `approvedByOwner=true` **and** `visualRendererReady=true` must all be set in a trusted PC server-only configuration. Defaults are OFF; the booleans alone do **not** establish real authority, and this reference should not be installed live without OWNER Codex review.
- `approvedSubtypeEffects` has **no default mapping**. In particular, the meaning of legacy `WX02_SMALL` / `WX03_CROWN` as `GIANT_ONE` / `MINI_ALL` has **NOT** been confirmed against the real saved PC Place. All test mappings are synthetic.
- Enforces matching server `matchId`/`stage`/`epoch`, unchanged `startedAt`/`deadline` during yielded callbacks, valid non-replayed roster, time monotonicity, expiry at the earlier D08 weather deadline or D16's 8s TTL, and D08 cleanup identity.
- No Roblox instances, hitbox edits, physics, real appearance, Remote listeners, DataStore, payments, gameplay results or production schedule changes. **A working visual requires a separately approved client-only renderer and genuine Studio QA.**

## Immutable dependency facts — never bulk merge branches

- Canonical D08 event bridge (exact original repack): `70dcc3b50129c288441452776360588184ca6c22`, `handoffs/P0D-D08-CANONICAL-BRIDGE-PUBLIC-RECOVER-20261110-01/luau/CanonicalEventBridge.luau`.
- D16 scale pure reference (new, not original): `883ca3b790c938587c5d9c305a887a1ffff1249f`, `handoffs/P0D-D16-SCALE-FX-CLEANROOM-20261110-02/luau/D16ScaleFxCore.luau`.
- D16 visual-replica separate lane: `356dcd0d26aecf7bb5ab3e7d7a697e78a59db74e`. The 3D feature is not automatically wired by this package.
- Shared publication/receipt standard: `b519a17a3152613666822b7d9660742f93a739b7` (`PUBLIC_SOURCE_V1`).

Read `docs/CODEX_REVIEW.md` before any PC intake. The existing owner's Windows Codex is the **only** actual Studio integrator and must receive a direct OWNER instruction; a GitHub comment is not one.

## Tests & status

Run from this packet root: `python -m unittest discover -s tests -q`.

**54 offline stdlib tests pass** (Python behavior oracle and static Luau source contract checks). Native Luau parser, real D08/v40 runtime interface, PC game baseline comparison, two-client and mobile Studio tests, gameplay visuals, Studio normal exit are **NOT_TESTED**. This is not a production-complete feature.

No `main` write, merge, Roblox public launch, payment, spend, P0-A/B/C CAS/auth, shared locks or changes to the five existing Automations.
