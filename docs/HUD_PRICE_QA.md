# HUD price regression — native Lua fixtures only

Main `b4e6901f5880102eb55bd20490eab8c049f2cbc6` displays the current
10 / 28 / 48 toy prices correctly. Those prices are duplicated as HUD literals,
so a later balance edit leaves the labels stale. The existing PR #13 proposes
reading `ToyWarsBalance.UNITS[id].cost`; this main-based candidate preserves
that exact HUD blob, `0dcd1f1f16991b3f02b970361eea9f026d1e8688`.
No balance values, purchase rules, character definitions or models change.

`tests/hud_price_spec.lua` executes the complete HUD file, including button
creation, refresh initialization and activation callbacks. Small substitutes
provide services, UI objects, values and signals. A fresh real balance module
is loaded for each fixture; only its in-memory costs vary. No source snippets
are extracted and no purchase function is reimplemented.

For every displayed price, the real `B.buy` must accept exactly that amount and
leave zero coins. One coin less must be rejected when the price is positive.
All three button identities and one-argument unit-selection payloads must be
preserved. Fixtures cover current prices, separate changes to PON/GUARDON/
TANKURU, all-zero costs and costs at the current maximum wallet value.
The price variations are test inputs, not economy changes in game source.

The immutable original HUD at `2bf5e40fbca7e5420edcb324319e95c8c4f038a3`
has blob `506b2eced0cf74f15341091976090632abbe021a`, identical to current main.
It passes the current-price case and fails exactly the five varied-price cases.
The fixed HUD passes all six. CI verifies the old blob and exact failure list,
then requires the canonical fixed HUD to succeed. Before/after logs are archived
as `twf-hud-price-fixtures-not-ui`.

Run `lua5.4 tests/hud_price_spec.lua` from the repository root. To run the
negative control, set `TWF_HUD_FILE` to a checkout of the pinned original HUD.
Existing server-event, balance/stress, Python, compiler, installer/hash and
handoff checks remain required. Original baseline byte counts are preserved;
the history chain now verifies each of the four Lua files individually.

Game-source delta from current main: four Lua files, 676 -> 678 lines,
26,559 -> 26,753 bytes (+2 lines / +194 bytes), all in the HUD. Server and
balance blobs remain unchanged. The original PR #13 remains open and unmodified;
C00015 records this separate candidate and its newer QA.

These fixtures validate produced text and callback data in native Lua, not
Roblox rendering, touch behavior, module replication, Studio, actual multiplayer
or mobile layout. They read prices at HUD initialization; runtime hot-reloading
of balance prices is not implemented or claimed. Public release stays on HOLD.
PR #30/#31 integration is already complete. This HUD candidate needs its own
explicit integration approval; Gemini operational stops remain in force.
