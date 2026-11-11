# TRAP RAIDERS — S1 Game.server D07/D08 source integration candidate

**Status: CHAT_BUILD_READY / OPT-IN DISABLED / STUDIO NOT TESTED / NOT RELEASE READY**  
Date: 2026-11-11 JST · game: `TRAP_RAIDERS` · work: `p0d-siege-v19`

This packet is materially more than a design document. The `candidate/` directory
is a self-contained Rojo source project with its **ACTUAL edited**
`src/server/Game.server.luau` and `src/client/HUD.client.luau`, the
eight exact original public D07/D08/v40 modules, the reviewed
`S1CanonicalRoundHost` and `S1GoroganLiveBindings`, unchanged S1
map/config/egg/combat modules, 80-case Python game source test tree and a
strict **25-file `P0D_PUBLIC_SOURCE_V1` source manifest**.

## Original inputs and evidence

- Original **untouched single-authority initial S1** source commit:
  `35d7d0525388e885aac8281eff2315a59831e0cf`.
- Canonical S1 host plus eight immutable original public modules:
  `aeb6aa748c70be2fab8e652ad6623d1b2c3989c6`.
- New concrete server physical callback factory (one reviewed module):
  `32f5bb13aefc979369d35319cecaac9572cf7020`.
- Patched `candidate/` source first frozen at:
  `80a486d8c2d5a9d76a898bd4f557b7fd42659052`.
- Real run:
  https://github.com/kk051780/toy-wars-factory/actions/runs/42992803431
  - 25/25 source manifest verified with the **original official pack tool**.
  - 80/80 actual candidate S1 Python regressions PASSED.
  - 18/18 new entrypoint/source-authority negative contract checks PASSED.
  - 16/16 actual Python Chat source assembly files copied and independently hashed.
  - A REAL Python-generated `CHAT_RC_RECEIPT.json` is pinned at this
    handoff root (receipt SHA256 `e1fcaf82a895083e18188e48316ce01a8e71ce32a2dce9137d169d6249fc645d`).
  - `SOURCE_PLAN_CANDIDATE.json` pins exactly 16 actual runtime/project
    source units to the real historical candidate commit. These are
    *source-only* checks; no Luau parser or Roblox Studio run was performed.

## Actual Game changes

The existing Game **remains the only Script** and still owns match epoch,
victory, egg pickup/drop/delivery, HP, role changes, attack validation,
spawning and one RemoteEvent. The optional host is called from its
existing `tickRound` and only after fresh `resetRound`. On match end or
reset it calls physical-boss cleanup before changing epochs. The old
cosmetic 55/62-second alarm chooser is **removed entirely**.

The real original v40/D08 chooser is invoked only by the existing Game
tick. `BossBinding` supplies original D07 AI, physical rig, damage gate
and receipt window from the authenticated server roster and world raycasts.
The existing `TrapRaidersS1Remote` sends server-to-client
`BOSS_VISUAL` records; the patched HUD can display the short
`STOMP` danger cue, but clients cannot choose a boss, target or damage.
No second event RNG, inbound Remote listener, boss rig implementation,
separate server Script or gameplay loop is introduced.

### Important review gate

Both code constants are intentionally `false`:

```luau
local CANONICAL_S1_ENABLED = false
local D07_D08_RELEASE_REVIEW_APPROVED = false
```

This preview still runs normal egg/castle play and **does NOT actively
spawn D07 or select D08 events** until the sole #220 integrator explicitly
reviews real runtime dependencies, QA and opts in by updating BOTH
server-only constants. Do not treat source package completion as feature
runtime completion. Neither the current RC branch nor main was changed
by this packet.

## Reproduce offline on an isolated checkout

```bash
python3 handoffs/P0D_PUBLIC_SOURCE_HANDOFF/tools/p0d_public_pack.py verify \
  --root handoffs/P0D-S1-GAME-CANONICAL-HOST-PATCH-20261111-01/candidate \
  --packet-id P0D-S1-CANONICAL-GAME-PATCH-20261111-01

python3 -B -m unittest discover -s handoffs/P0D-S1-GAME-CANONICAL-HOST-PATCH-20261111-01/candidate/tests -v
python3 -B -m unittest discover -s handoffs/P0D-S1-GAME-CANONICAL-HOST-PATCH-20261111-01/tools -p test_game_entrypoint.py -v

python3 handoffs/P0D_S1_SOURCE_PLAN_SNAPSHOT_20261111_01/tools/chat_rc_assemble.py \
  --plan handoffs/P0D-S1-GAME-CANONICAL-HOST-PATCH-20261111-01/SOURCE_PLAN_CANDIDATE.json \
  --source-root handoffs/P0D-S1-GAME-CANONICAL-HOST-PATCH-20261111-01/candidate \
  --out /tmp/p0d_s1_chat_integrated_preview
```

Compare that temporary `CHAT_RC_RECEIPT.json` with the pinned handoff
root `CHAT_RC_RECEIPT.json` and all 16 resulting source/project bytes.

## Honest release blockers (still open)

1. **No Roblox native Luau compile or actual Studio run on this new candidate**;
   physical rigs/pathfinding/collision/2-team live HP and full mobile UI
   remain unchecked. Previous separate Windows tests concern a different
   local Place and cannot be called a PASS for this source.
2. D08's authentic v40 selection has **10% WEATHER** and no approved S1
   weather handler here: fail closed, no invented meteor/rain gameplay.
3. Original D07 boss physical lifetime 14s vs D08 v40 event lifetime 17s
   requires actual synchronized cleanup and HUD check.
4. The `STOMP` HUD uses a bounded server timestamp; **network latency
   can shorten a player's visible warning**. Only synchronized real
   two-client capture establishes a safe effective minimum. This
   candidate does not certify either client's reaction window.
5. Original S1 epoch `serial >= 1024` is refused by current recovered
   bridge. A safe long-lived server epoch design is required.
6. Additional selected gameplay/UX (D11 neutral, first-minute guidance,
   mascot collection, market differentiation, balancing) is maintained
   by other Chat lanes. None is falsely described as already integrated.

**Next #220 sole-CHAT-INTEGRATOR action:** inspect newest RC and these
exact code changes; select or skip in your exclusive release branch,
repair the relevant blockers, regenerate a fresh pinned full source
manifest/assembly plan/receipt, run independent static and dynamic QA,
then OWNER-direct the final Windows Codex Studio 2-client/mobile/
normal-exit verification when truly near launch. No main merge,
production Roblox publish, paid operation, PC Codex invocation,
P0-A/B/C CAS or five ChatGPT automations happened here.
