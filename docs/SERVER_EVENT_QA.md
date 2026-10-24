# Server event regression — native Lua 5.4 fixtures only

The complete canonical server script is loaded with deterministic service,
Instance, event and coroutine-scheduler substitutes. Callback code is not
extracted or reimplemented. The actual balance module is used. No provider,
network, Roblox Studio, physics, replication, rendering or client execution is
part of this harness. It cannot certify multiplayer, mobile or exploit behavior.

## Reproduced defect and fix

The PR #29 server at `2bf5e40fbca7e5420edcb324319e95c8c4f038a3`
(Git blob `5d3d85d28025f83414ea812297bb93a58ea36699`) passes 25 fixtures
but fails two: a NaN distance permits toy selection and a paid factory upgrade.
In IEEE comparisons, `NaN > 13` is false, so rejecting only distances above 13
admits the synthetic invalid value. Requiring `distance <= 13` to be true rejects
it. Missing roots still short-circuit, and ordinary distances through 13 remain
accepted. Both selector-pad and upgrade-station checks use this condition.

The fixed script passes all 27 fixtures. This demonstrates the callback's numeric
logic under the fixtures; it does not demonstrate that a client can inject such
a position into a Roblox server or that engine replication accepts it.

## Covered behavior

- Existing players, duplicate join, four-plot capacity, waiting-player backfill,
  disconnected waiters, multiple departures and a stale join event.
- Selector distance boundaries, identity, missing root, infinity and NaN.
- Upgrade boundary, infinity, NaN and no charge on rejected activation.
- Remote unit allowlist and rate limiting; actors without sessions are ignored.
- Normal deferred teleport, exit/character replacement during the wait, detached
  membership, missing-root timeout and a root arriving after departure.

PlayerRemoving is modeled before removing the player from the service. Spawned
callbacks resume immediately until yielding; waits resume at explicit fixture
times. These controlled schedules are not Roblox timing or physics emulation.
The fixture list order is deterministic; no FIFO guarantee for the real
Players:GetPlayers result is claimed.

Primary API references used to scope these substitutes:
- https://create.roblox.com/docs/reference/engine/classes/Players
- https://create.roblox.com/docs/reference/engine/libraries/task
- https://create.roblox.com/docs/reference/engine/datatypes/Vector3

## Reproduce and inspect evidence

Run `lua5.4 tests/server_event_spec.lua` from the repository root. CI additionally
checks out the immutable pre-fix server, verifies its Git blob and requires that
it fail exactly the two NaN cases. Every other old-server fixture must pass.
The canonical fixed-server run must succeed. Both logs are archived as
`twf-server-event-fixtures-not-engine`; existing QA gates remain required.

The owner-approved [PR #30](https://github.com/kk051780/toy-wars-factory/pull/30)
merged at `1e29505f62192597de6019f97a8b87447b1998e8`. It includes the separately
proposed selector/backfill and lifecycle fixes from #28/#29; those source
proposals remain open and their gameplay changes must not be applied again.
The numeric fix changes two lines and adds 14 UTF-8 bytes relative to #29.
The full integration changes only the server among the four game Lua files:
25,726 bytes / 663 lines before, 26,559 bytes / 676 lines after (+833 / +13).
Character definitions, stats, prices and roles are unchanged.

[Post-merge main QA](https://github.com/kk051780/toy-wars-factory/actions/runs/40102033728)
and [handoff verification](https://github.com/kk051780/toy-wars-factory/actions/runs/40102033772)
both passed on the merge commit. QA includes the exact pre-fix negative control,
all 27 fixed-server event fixtures, 53 Python tests, 37 balance assertions plus
4,000 stress cases, 21 policy checks, exact official compiler regeneration,
installer hashes and deterministic handoff. C00014 records the completed merge
and supersedes the historical draft state in C00011-C00013. Gemini remains held;
Roblox release remains on HOLD pending actual engine and player evidence.
