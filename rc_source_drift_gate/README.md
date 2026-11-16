# EGGRUMBLE V3: live 26-source RC admission freshness guard

Dedicated PR #490. Other owners implement: #482 seven jobs / field / combat / castle & eggs / neutral / field items / lobby, #484 quality AI and SOURCE composer, #485 ART, #487 SCORE, #488 independent runtime evidence. This file modifies **no gameplay modules**.

## Active path (V2)

The relevant current composite is **not** the old `.github/workflows/p0d-eggrumble-gq-art-score-composite.yml` 21-script run. The current #484 composer uses:

- `.github/workflows/p0d-eggrumble-gq-current26-private.yml` and its exact three immutable author/ART/SCORE checkouts.
- `quality_repair/EGGRUMBLE_V3_GQ_CURRENT26_20261116/compose.py`: source-selective author 21 + original ART 4 + SCORE 1 = 26 scripts (23 server / 3 client), including 3 quality-owned AI/castle adaptations.
- The latest 26-source **same quality HEAD** GitHub workflow run must be completed/successful. Historical 21-source or stale-HEAD green runs do not count.

The live guard requests current #482/#484/#485/#487 PR heads from read-only GitHub REST, validates all eight-domain source mappings (plus actual blob availability), the live three fixed-source workflow checkouts, composer contract and actual same-HEAD 26-source workflow conclusion. The old manifest 16 scripts **continues to exist as #484's private quality source**, but is not falsely treated as the actual combined 26-source output. The old V1 `evaluate()` is retained only for regression and historical drift comparisons; `live_audit()` now invokes `evaluate_active26()`.

## Execution and status boundary

```sh
python3 -m unittest discover -v -s rc_source_drift_gate/tests
python3 rc_source_drift_gate/check_live_intake.py --out P0D_LIVE_RC_SOURCE_DRIFT.json
python3 rc_source_drift_gate/check_live_intake.py --strict
```

- `SOURCE_REVIEW_READY_ONLY` means **the author 21 and pinned current26 source CI contract** are up-to-date, and this separate live gate sees zero SOURCE-generation blockers. It does not establish game functionality inside Studio, PC/Android screenshots, ART quality, FUN, OWNER acceptance or official RC integration.
- `SOURCE_RECONCILIATION_REQUIRED` means a missing required original, stale three-source pin, invalid composer, or missing/failed **same-head 26-source** build. `--strict` exits 2. It does not overwrite, merge or take locks.
- `AUDIT_UNAVAILABLE_FAIL_CLOSED` indicates an API error, incomplete data or unexpected schema. Never count as success.
- The intentionally nonblocking reporting workflow exits zero to **retain the JSON artifact** even when the above decision is RED; reporting CI SUCCESS is not equivalent to admission GO.

## Actual same-head candidate proven at 2026-11-16 JST

- [#484 26-source private build #43798960450](https://github.com/kk051780/toy-wars-factory/actions/runs/43798960450) on author-specific quality SHA `bbdb1906a0d0750bbb0e0c7b31a955b98d72c65a`: completed SUCCESS; private ZIP artifact 65,603 bytes, *not official RC ZIP*. Detailed Place payload/source checks are owned by #484 workflow.
- [#490 V2 source admission gate #43799312815](https://github.com/kk051780/toy-wars-factory/actions/runs/43799312815) on `5f1449f1d0c840a9c791baf5f8f3173c01a6071d`: 14/14 offline regression PASS plus actual live audit `SOURCE_REVIEW_READY_ONLY` with zero reported SOURCE-generation blockers at observation time.
- All author/quality ART/SCORE heads are **not assumed immutable across later runs**. Re-query live heads immediately before the real #220 CAS admission.

## Required #220 intake and non-duplication

#220 alone is the authenticated official RC writer. It must verify latest sources and branch provenance, sole authoritative Game/Remote/HP/score/save state, full source-lock, pinned native Luau+Rojo actual Place, rollback and non-force CAS; reply with official SHA and **official** ZIP bytes / KiB and Place bytes when measured. Other authors own gameplay repair on their own scope. Studio 1+15 AI, 2+14 AI, Android 15m, ART #420, FUN and OWNER stay NO_GO until actually observed. Never merge the stacked #484 PR wholesale or treat the artifact as an authorized production build.

No main writes, protected RC branch writes, PR merge, Roblox publish or payments from #490.


## V3 optional runtime activation evidence — actual source, not an engine test

This same PR additionally implements `runtime_activation.py` and seven new tests.
After checking all current26 original author/compiler/head conditions, the live
gate reads five **original** #482 files from the exact pinned author SHA via
read-only GitHub API, recording sha256 and line-specific executable guards:

1. `EGGRUMBLE_LobbyCastleModesPreview.server.luau` early-returns when
   `not RunService:IsStudio()` (before any V3 lobby/session initialization).
2. `EGGRUMBLE_BotActors.luau` requires Studio in `start`.
3. `EGGRUMBLE_SevenRoleCombat.luau` requires Studio in `equip`.
4. `EGGRUMBLE_RoundReplay.luau` asserts Studio during match cleanup.
5. `EGGRUMBLE_MatchResultService.luau` asserts Studio before results.

The top-level lobby guard blocks **all eight gameplay domains** in the V3
preview when launched as an unmodified normal Roblox server: character, field,
battle, castle/egg, neutral, item, lobby, balance. This does **not** imply the
legacy official RC branch itself cannot run; it proves that copying the V3
Studio-only host wholesale is not a production-equivalent runtime solution.

The output field `runtime_activation.production_runtime` is
`BLOCKED_STUDIO_ONLY_GAME_HOST` when executable guards appear. The distinct
`decision=SOURCE_REVIEW_READY_ONLY` may remain true for private SOURCE
review under OWNER's V6 YELLOW nonfatal flow, but `product_go=false` remains
mandatory. Removing those guards without a single authoritative host adapter
can create duplicate Game/Remote/HP/egg/score/Store, so #490 **never edits
them**. The original #482 author and authenticated sole #220 RC writer must
selectively reconcile production host, with negative tests and rollback.

For a strict *absence-of-known-guard* preflight use:

    python3 rc_source_drift_gate/check_live_intake.py --require-no-studio-only-guards

It exits 3 while Studio-only or missing mandatory authority sources remain.
Even a zero result would mean only *known static guards absent*, never Studio
2-client, Android, FUN, ART or OWNER acceptance.

**Source test run**: #490 Actions 43800168895 / head
`52c0bf835d13eb76f74f476d42fdaf6b8923274e`: 21/21 regression
cases completed SUCCESS, actual author code guard inspection confirmed
`BLOCKED_STUDIO_ONLY_GAME_HOST` and all eight-domain impact. Not an
engine execution or official RC adoption.


## V4: all 26 effective source runtime guard inspection, without competing for author code

The earlier V3 five-file guard scan revealed an actual normal-server blocker, but it read some raw #482 files that are replaced by the #484 and #487 original owners during composition. V4 makes this scope precise and complete:

- Walk #482's 21 author Rojo modules.
- Use #484's actual quality-selected `BotActors` and `BotPathRouter`, not old original bots.
- Use #487's original result adapter and `ScoreBalance`, not original #482 result text.
- Use all four real #485 ART Luau source files, including client LOD. No new art or composer is authored here.
- Inspect the original host's preserved **pre-castle-ramp** guard. The generated host's full bytes are not claimed by this gate (actual source lineage/byte verification belongs to #491).
- The live `full26_runtime_activation` summary reports all executable `RunService:IsStudio()`-based restrictions per gameplay domain, tagged `game_guard_count` versus `art_guard_count`, with immutable author commit and original source hash; no Studio/Android run is claimed. Missing or unknown source selection causes fail-closed.

New test file `test_effective_runtime_selection.py` validates 7 overlay/guard-negative cases. New `test_full26_runtime.py` validates 8 more selection and art-vs-game guard scenarios. All tests run with no network; the live CI read-only job then checks immutable GitHub heads and all 26 actual owner source files.

**Important:** a newer #484 current26 Native/Rojo SUCCESS and a successful source scan are *private development source readiness*, not product GO. The true canonical #220 writer must select actual production Game/Remote/Store authority before nonStudio mobile play can be accepted. Never remove guards as a blanket replacement or duplicate the already live Game. No main/official RC writer change, PR merge, Roblox publishing or payment from this quality tool.


## Latest quality-owner repin checkpoint (2026-11-16 13:xx JST)

After the prior read-only audit, #484 quality author advanced from
`2aeb4fd856657c9298a2763d9204d0c9d9b031cb` to
`6b52eaf1f2725496277998fe0c5532b7a8fcaab5`.
Actual GitHub compare shows four changed files: current26 CI workflow,
quality BotActors, spatial-quality test, native neutral fault test.
Therefore the earlier #490 selected BotActors source byte hash cannot be
reused as evidence for this newer quality HEAD; re-run the live audit.

#484 itself built a new truly source-exact private 26-script Place on that
HEAD: [same-head GitHub Actions 43802122900](https://github.com/kk051780/toy-wars-factory/actions/runs/43802122900)
SUCCESS, real Place **218,949 bytes** SHA256
`7afbc4db3035c4f8985927f89128fcbc0cd09c2857b58305099a751560bd7115`,
private artifact **66,359 bytes** ID `14196449069`. Not canonical RC
Place or ZIP. New runtime-guard and original-byte source selection MUST be
recomputed at the new head; Studio/Android/OWNER still NO_GO.
