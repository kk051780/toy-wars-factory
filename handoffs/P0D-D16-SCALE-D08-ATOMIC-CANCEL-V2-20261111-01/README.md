# TRAP RAIDERS — D16/D08 atomic-cancellation gate V2 (keyless)

**Game:** `TRAP_RAIDERS` · **Work:** `p0d-siege-v19`  
**New packet:** `P0D-D16-SCALE-D08-ATOMIC-CANCEL-V2-20261111-01`

This is **new, independent, public-source reference code**, not recovered D16 AES originals. It is an optional, default-disabled **replacement for this author's V1** gate at [`ac50372942712503f836fb84d6331ef3bcc4b8f2`](https://github.com/kk051780/toy-wars-factory/tree/ac50372942712503f836fb84d6331ef3bcc4b8f2/handoffs/P0D-D16-SCALE-D08-DISPATCH-GATE-20261110-01). **Never install V1 and V2 together.**

The original D16 SCALE-FX source archive remains sealed: packet `P0D-D16-SCALE-FX-20261110-01`, recorded ZIP SHA256 `d5df52cd3b2fdf26bca05bc38123ac81d27024c944c4a465d66e3a4e0ad0c7cd`. This V2 is **not byte-identical** and cannot be counted as an old-source migration. The existing keyless pure Scale core is separately pinned at commit `883ca3b790c938587c5d9c305a887a1ffff1249f` and the only proposed D08 event dispatcher at `70dcc3b50129c288441452776360588184ca6c22`.

## Why the V1 should be held for PC integration

The earlier gate invokes approved `readRound`, `readRoster` and `chooseGiantTarget` callbacks which can yield. A D08 CLEANUP while activation is suspended may encounter V1's `self.active == nil` and return `INACTIVE`, allowing the resumed activation to set up an effect after cleanup. Additionally, V1 `stop()` clears the gate's active pointer but does not call the ScaleCore close method. These are **static source review findings**, not observed live exploits.

## V2 behavior

- `cancelGeneration` and a pending event identity make D08 matching `onCleanup`/`stop()` synchronously revoke an in-flight activation, including during server callbacks. Post-callback checks refuse stale work.
- A matching cleanup *before* scale core activation returns `CANCELLED_PENDING`. Stop and active cleanup call `Core.close` using a validated, nonregressing server-time witness. A rollback close is attempted even if a supplied `Core.begin` unexpectedly suspends.
- A snapshot revalidates its cancellation generation after any yielding readRound callback. Round close/deadline/clock reverse suppress the effect and close active Core state.
- The gate never creates a new D08 selector, weather RNG, scheduler, Roblox `Instance`, RemoteEvent, avatar scale, collider, damage, physical glide or purchase mechanism.
- The gate is **OFF unless all three** are explicitly true: `enabled`, `approvedByOwner`, `visualRendererReady`. There are **no predefined weather-subtype-to-scale mappings**: actual D08 weather mapping is a PC review decision. The single canonical weather dispatcher must route all unrelated weather to their own reviewed handlers, not to this scale gate.
- `D16ScaleD08GateV2.luau` is a **ModuleScript reference**, not a ready-to-publish Roblox package. Actual integration requires inspected local live code/API and native Luau/Studio test.

## Offline checks

```shell
python -m unittest discover -s tests -p 'test_*.py' -v
```

The Python model/test harness checks normal and adversarial **synchronous callback-interleaving analogues** plus static assertions on the emitted Luau code. Passing does **not** mean native Luau parsing, scheduler interleaving, Roblox Studio, multiplayer, mobile or proper Studio shutdown has been exercised. See [`docs/CODEX_REVIEW.md`](docs/CODEX_REVIEW.md).

## Scope guard

Do not modify the old D16 source/encrypted ZIP, existing D08/Gorogan/vehicle/glide/clock/visual authors' branches, actual OWNER PC Place/source, `main`, locks/CAS, Roblox production release, paid items or any existing Automations. GitHub Issue comments are documentation, not execution authorization. Owner Windows Codex is the only PC/Studio integrator, after direct instruction.
