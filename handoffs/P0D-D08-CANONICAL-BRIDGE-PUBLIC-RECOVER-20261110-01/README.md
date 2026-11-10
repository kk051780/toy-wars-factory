# TRAP RAIDERS — D08 canonical single-event bridge reference

**Packet** `P0D-D08-CANONICAL-EVENT-BRIDGE-20261110-01` · `TRAP_RAIDERS` · `p0d-siege-v19`.

This is a NEW *disabled-by-default, server-only* adapter for the **existing** v40 `ChaosEventCore.luau` from sealed packet `c0b0bf692410cb651893c38f1a453c93d9f8b3b5`. It does **not** introduce another event RNG/chooser, spawn bosses, modify NPC combat, or apply weather. The real PC's `RoundCoordinator` is unobserved from this chat, so the adapter requires explicit, OWNER-reviewed trusted callbacks.

**What it closes:** The real PC v43-A report [#213 #6758415195](https://github.com/kk051780/toy-wars-factory/issues/213#issuecomment-6758415195) found no installed `ChaosEventCore` in the running game, although old v40 reference source exists. D07 `GoroganCombinedRuntime` also expects a canonical v40 `ACTIVATE` and must **not** be given an invented second event picker. This bridge wires the old v40 one-choice decision to controlled WARNING/ACTIVATE/CLEANUP consumers.

**Security:** Only a real server-controlled round snapshot and server RNG may feed it; a callback's self-declared boolean is not proof of authenticity. No RemoteEvent input. One roll, one warning, one activation, one cleanup. Round switch, clock rewind, duplicate/replay and callback failure deny safely; 1024 epoch cap requires an audited production strategy. No DataStore, marketplace, client privileges or player IDs are persisted. Server event recipients must recheck the current round epoch themselves.

**Ambiguous boss naming:** Old v40 chooses `RAIGALD` on S2/S4; more recent D07 refers to `LIGARDO`. No implicit alias: default `RAIGALD_LIGARDO_ALIAS_REVIEW_REQUIRED`. PC must check character canon and source before explicitly setting `approvedRaigaldAsLigardo` true. **Weather** requires an existing OWNER-reviewed weather runtime handler or fails closed *before* warning, rather than pretending a weather mechanic works.

**Timing:** Reference v40 selects after 20 seconds. Normal/Boss/Weather probabilities 65/25/10 via exactly one trusted integer 0–99. Boss warning 2.5 seconds; boss `ACTIVE` 17 seconds; the Gorogan attack module runs only up to 14 seconds independently. Weather warning 2 seconds, active duration 5–8 seconds. Server deadline insufficient => permanent normal round, no RNG reroll.

**Run local tests (does not compile Luau):**

```shell
python -m unittest discover -s tests -q
python tools/verify_packet.py TRAP_RAIDERS_D08_CanonicalEventBridge.zip
```

See `docs/CODEX_HANDOFF.md` for staged integration and strict blockers. **Do not** install both old/new schedulers, or the old `GoroganServerRuntime` and new `GoroganCombinedRuntime` simultaneously. Windows Codex restore, Luau parser, Roblox Studio 2/3-client, physical device, saved Place cold-reopen and real event visuals are **NOT_TESTED**.
