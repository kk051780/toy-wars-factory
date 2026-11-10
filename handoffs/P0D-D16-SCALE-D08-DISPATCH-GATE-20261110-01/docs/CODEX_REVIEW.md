# Windows Codex review: cross-pack D08/D16 trusted event gate

**Source-only, disabled reference.** No auto-execution is authorized from this file. Preserve actual newest local Windows Place, saved sources and SHA checkpoints before testing; never reset to the old `v43-A` Place simply because it is named in an issue.

## Expected *trusted* server interfaces

| Source | Proven expected fields / contract | Review requirement |
| --- | --- | --- |
| D08 `CanonicalEventBridge.onWeatherActivate` | envelope `{matchId, stage, epoch, kind="WEATHER", subtype, phase="ACTIVATE", validUntil}` with `validUntil` in **seconds** | Validate actual PC D08 and one-choice v40 `ChaosEventCore`, not a second chooser |
| OWNER `readRound` | `matchId, stage, epoch, startedAt, deadline, now, active` with time **seconds** | Must be server-only and authoritative, current round/monotonic source; never remote-supplied |
| OWNER `readRoster` | server-confirmed array of up to 24 unique numeric user IDs | Revalidate actual membership after callbacks; never trust a client payload |
| OWNER `chooseGiantTarget` | trusted server selection from the roster if and only if explicitly mapped to `GIANT_ONE` | Check in round again after selection and validate exact target |
| D16 `D16ScaleFxCore` | `new`, `begin`, `snapshot`, `close` (now in **milliseconds**) | Gate converts server seconds to milliseconds; no Core internals patched |
| D08 `onCleanup` | `{matchId, stage, epoch, kind, subtype, reason}` **no phase** | Route only to the previously accepted D16 event; idempotent acknowledge of no-active cleanup belongs to the OWNER-reviewed multiplexer |

## Integration blockers: do not auto-map

1. `WX01_METEOR`, `WX02_SMALL`, `WX03_CROWN`, `WX04_GLIDE`, `WX05_CLOCK` are D08-recognized weather names, **not** evidence that any particular one should trigger `GIANT_ONE` or `MINI_ALL`. The *actual PC* gameplay definition must be reviewed before constructing `approvedSubtypeEffects`. The sample Python oracle's WX02 mapping is a synthetic test fixture **only**.
2. The D08 bridge can have **only one** `onWeatherActivate` and `onCleanup` callback. The owner-reviewed server-only router must dispatch *other* weather events to their actual approved handler and delegate to this scale gate **only for a confirmed scale mapping**. Do not replace all D08 weather handlers with the D16 gate: unapproved subtype intentionally returns `false` and would stop the D08 bridge.
3. The reference D16 scale module changes **no avatar or visual**. `visualRendererReady` must remain false until an actual reviewed display-only renderer is bound; it must not touch server hitboxes, character physics or player combat. D16 VISUAL_REPLICA is a separate candidate, and duplicate renderers must not coexist.
4. D08 event lifetime can be shorter than D16's fixed 8-second TTL; call `Gate:snapshot()` or D08 cleanup regularly in the approved server lifecycle, respecting the *earlier* D08 deadline. This file creates **no** timer itself. Check pre- and post-yield round and roster identity, duplicate ACTIVATE, stale CLEANUP, player departure and server stop.
5. If actual PC source has a competing event scheduler, different epoch/clock/roster semantics, D08 source absence, or a different D16 source already installed: **HOLD**; report exact diff and obtain direct OWNER resolution instead of silently guessing.

## Explicit safe construction skeleton (INACTIVE, not runnable gameplay)

```lua
local gate = D16ScaleD08DispatchGate.new(D16ScaleFxCore, {
    enabled = false,           -- remain false until actual OWNER PC approval
    approvedByOwner = false,   -- a local config flag, NOT cryptographic authorization
    visualRendererReady = false,
    approvedSubtypeEffects = {}, -- NO guessed mapping
    readRound = verifiedReadRound,
    readRoster = verifiedReadRoster,
    chooseGiantTarget = verifiedServerTargetChooser,
})
```

`verifiedReadRound`, `verifiedReadRoster`, `verifiedServerTargetChooser` above are **deliberately undefined placeholders**, not working runtime code. Do not connect client `RemoteEvent` directly to `:onWeatherActivate`. Never modify the original D08 or D16 branch to try this candidate.

## Acceptance matrix

- [ ] Exact current Windows source/Place, SHA, CHECKPOINT/RESUME, active Studio ownership and safe backup recorded.
- [ ] D08 canonical chooser and weather event subtype/phase/time semantics verified; no secondary scheduler, duplicate event handler or RNG.
- [ ] OWNER-approved mapping separately justified using real gameplay source. Renderer present and non-collidable; scale policy does not alter physics or hits.
- [ ] Native Luau parser + actual server tests; 2/3 clients over two rounds, duplicate start/replay denial, early round close, disconnect and false client requests.
- [ ] D08 deadline (possibly 5s) takes precedence over D16 8s TTL; cleanup called/observed exactly as desired; no stale visual after expiration.
- [ ] S1 and all intended stages plus landscape mobile emulator performance, normal Studio Stop/Edit/save/close and owned-PID exit captured with real evidence.
- [ ] Output actual source/Place SHA and test results to #213/#218 without secrets or private player data; only then mark PC intake/Studio tested.

The original old D16 SCALE_FX archive remains `HANDOFF_BLOCKED_ORIGINAL_BYTES_UNAVAILABLE`. This **new** gate and the new D16 scale core are possible alternatives, not the old ZIP and not a pair of authenticated legacy conversions.
