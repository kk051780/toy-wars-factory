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
