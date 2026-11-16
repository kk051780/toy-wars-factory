# EGGRUMBLE V3: live source-to-RC freshness gate

**Dedicated non-overlap scope:** no character, field, battle, castle, neutral, item, lobby, ART or SCORE gameplay modules rewritten. Compare their latest PR heads against the candidate that the sole RC integrator (#220) might adopt.

## Existing owners

- #482 owns actual 7 roles, 21 skills, physical eggs, castle, lobby, mobs, giant boss, field pickups.
- #484 owns quality adaptations for AI path/castle access and the private composite build.
- #485 owns visual modules; #487 owns scoreboard scoring.
- #488 owns actual device evidence checks (separate from this source freshness gate).
- #220 alone owns official RC writes and non-force/CAS intake.

## What this code **implements**

1. Read live PR 482/484/485/487 heads through GitHub read-only REST.
2. Parse actual source mappings in their 482/484 Rojo V3 projects; require eight domain coverage with real script identity, class, and location.
3. Compare exact Git tree blob SHAs across all shared modules. #484-owned BotActors, BotPathRouter, LobbyCastleModesPreview differ by design and are flagged for manual diff review; unowned source drift blocks.
4. Parse the real #484 ART+SCORE composite workflow's pinned refs, and flag if either differs from current #485/#487 head. Do not falsely accept historical 21/21 source-exact CI as a current-build certificate.
5. Record the official RC HEAD read-only. Never infer official adoption from module count, clean CI, or private Place construction.

## Run

- Test: python3 -m unittest discover -v -s rc_source_drift_gate/tests
- Report only: python3 rc_source_drift_gate/check_live_intake.py --out P0D_LIVE_RC_SOURCE_DRIFT.json
- Enforcing: python3 rc_source_drift_gate/check_live_intake.py --strict

Reporting mode emits SOURCE_RECONCILIATION_REQUIRED while still returning exit code 0 for logging; **this is not a quality PASS**. Strict mode returns code 2 for blockers. The GitHub workflow runs regression tests, emits current JSON, and stores a five-day artifact. The tool uses GITHUB_TOKEN only for read-only API access, never writes a credential to output.

## Acceptance and rollback

Once the report is reconciled against current four original HEADs, #484 should build an actual single Place from latest source and prove native Luau + source-exact Rojo, with pinned immutable hashes. Only #220 may select source changes into the authenticated official RC with rollback and same-HEAD CI. Studio 1+15AI / 2+14AI, Android 15-min FPS, visual-quality gate #420, children FUN, and OWNER acceptance remain distinct. Nothing in this isolated PR updates main, official RC, Roblox Publish, purchase or payment.
