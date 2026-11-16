# EGGRUMBLE V3 GQ S12 — elimination spectator (ISOLATED DRAFT)

- OWNER intent: quality gate keeps implementation moving without 14-chat file/feature collisions, and tracks source → officially integrated RC → Studio/Android/human FUN separately.
- Scope/owner: **ONLY** `handoffs/P0D-GQ-SPECTATE-20261116-S12/**` and its own CI workflow.
- Dependency: source-only V3 author [#482](https://github.com/kk051780/toy-wars-factory/pull/482) at fixed `fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9`, [#470](https://github.com/kk051780/toy-wars-factory/issues/470).
- Branch is stacked on #482 for diff visibility; **no edits to #482 owned 7 roles, battle, castle/eggs, field, neutral, item, lobby/round, AI; no edits to #484/#485 ART/#487 SCORE/#220 official RC**.
- Private Rojo manifest maps the *actual* 21 original V3 scripts by relative path, then adds **one** independent spectator LocalScript as the 22nd. Actual changes are **one Luau client file, one isolated manifest, tests and documentation**. No clones of Game/HUD/Store/Remote or paid content.
- Public repo: general spectator control logic only; no secret, experience ID, source IP from a private build, assets, keys, copyrighted media.

## Player-visible behavior

Once this session's **server** sets `EGGRUMBLE_Eliminated=true` after a personal castle falls, a compact 266 × 71 panel appears in the top-right. It watches the **same** TEAM or BATTLE_ROYALE arena already containing the player's original `Castle_<UserId>`. Players can cycle live castles, watch the whole battlefield, or stop watching. No revenge attacks/rewards during elimination. Camera ownership/previous subject is restored on end or manual dismissal. Only client-local camera/UI changes; server castle, score, egg and neutral records untouched.

Session match ends → existing #482 RoundReplay clears `EGGRUMBLE_Eliminated` and `EGGRUMBLE_QueuedMode`; spectator stops and removes GUI. On a second match the camera can start again. The panel does not appear before real elimination and cannot be used as server authority by pretending a client attribute.

## Eight-area coverage without duplicate implementation

| Area | Existing source reused | This unique slice |
|---|---|---|
| CHARACTER | #482 seven real roles & attack | Does not reset role/abilities on elimination |
| FIELD | #482 three-route world | Scene overview targets original `TacticalBattlefield` |
| BATTLE | #482 server combat | Observation only; never fires attacks |
| CASTLE | #482 CastleMatchRules/server castle models | Tracks only live `StandardCore`, excludes fallen |
| NEUTRAL | #482 SwarmCombat/boss | Visible in unchanged world; no new NPC or KO |
| ITEM | #482 field pickups | Visible in unchanged arena; cannot spawn/use items |
| LOBBY | #482 queued mode/round cleanup | Existing queue/round remains authoritative, camera restored |
| BALANCE | #487 SCORE and #482 rules | No reward/score/egg edits; no spectator advantage in active match |

**Important limitation:** The game is the original #482 **Studio preview**, not a production RC. This script assumes #482 currently publishes a dark gray fallen `StandardCore`, `EGGRUMBLE_QueuedMode`, `EGGRUMBLE_Eliminated`, and original arena naming. Any original author rename must be revalidated with explicit source-lock; color-only alive-state rendering is a visual indicator, not a security assertion.

## Build and testing

- Candidate Rojo project: `EGGRUMBLE_SPECTATOR_STUDIO.project.json`. It should compile source-exact to a **private/unpublished** `.rbxlx`. It is NOT a new Game root or official #220 RC.
- `python3 -m unittest discover -v -s handoffs/P0D-GQ-SPECTATE-20261116-S12/tests -p 'test_*.py'`
- Own GitHub Action: native Luau parser pinned to `f46d879e28302a430029304f7f6a162aed66f103`, pinned Rojo v7.7.1 artifact SHA-256, 22-source embedded source-exact verification. Green CI is **SOURCE QA only**.
- Manual test plan: in offline isolated Studio, enter TEAM, defeat all eggs/castle on player, confirm camera appears only after real elimination; cycle surviving castle, overview, dismiss; end/abandon match, assert no leaked camera or GUI; enter BR and repeat. Test lobby without elimination and two simultaneous mode arenas. Android touchscreen, 15-minute FPS and OWNER FUN remain **NOT_TESTED** until real evidence supplied.

## #220 official intake / rollback

1. Unique SOURCE only, no edits to old script bodies; author #482 HEAD **must be re-pinned to current** when intake starts, because new author HEAD may move.
2. Add only `EGGRUMBLE_EliminationSpectator` as an additional `StarterPlayerScripts` LocalScript to current accepted V3 project; leave Game/HUD/Store/Remote, #485 ART and #487 SCORE untouched. Current isolated manifest demonstrates the exact connection without modifying other authors' manifest.
3. #220 solely performs authenticated non-force CAS of its **own** official RC branch after independent QA and same-HEAD source-lock/Place test. Explicitly refuse to merge entire stacked draft PR.
4. Rollback: remove the one spectator LocalScript mapping/entry, leaving all 21 original V3 sources unchanged.
5. Missing Studio/Android/OWNER acceptance keeps `ART_NO_GO / FUN_NO_GO / PRODUCT_NO_GO`; publication and monetization remain disabled.

### Progress (per this independent slice, not total EGGRUMBLE completion)

`Luau=1/1 committed; isolated Rojo project=1/1 committed; tests=CI pending; private place=CI pending; official RC integrated=0/1; Studio=0/1; Android=0/1; OWNER FUN=0/1.` No whole-game percent is inferred from this row. Official RC status must come from #220 fixed SHA and receipt, not a green draft build.
