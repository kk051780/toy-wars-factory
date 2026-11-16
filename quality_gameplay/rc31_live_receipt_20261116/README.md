# GQ RC31 live receipt (read-only, independent eight-lane slice)

This scope only audits progress-report provenance, not gameplay implementation.
It is separate from #526 (67-feature design trace), #568 (balance outliers),
#575 (Result), #571 (StoneGiant), and all original gameplay source PRs.
No Game/Host/Combat/Swarm/BotActors/Item/Remote/Store/Place source is modified.

## Problem reproduced 2026-11-16

Canonical RC branch rc/p0d-s1-kids-rc01 was independently fetched at
cd3e95bd7c53e9320d85bf950d12f50bf2df2bcd. Official V3 Actions run
43865970246 was SUCCESS on that exact SHA and ZIP artifact size 173588 bytes,
artifact ID 14226555210. ZIP bytes are not the single .rbxlx Place size.

Both rc_fastlane/EGGRUMBLE_V3_ACTIVE.json.last_verified_rc_run.rc_head_sha and
rc_fastlane/ACTIVE.json.source_profiles.eggrumble_v3_31.last_verified_rc_run.rc_head_sha
still recorded historical 935e50f6e590c3bd783e2dc8aac947627f57fd5f.
Trusting the historical manifest for current capacity/CI is incorrect.
This mismatch does not mean the latest official Actions failed.

## Checks

- Independently supplied official live SHA versus BOTH recorded receipts.
- Eight domain source-author immutable SHA anchors and feature flags, 31 sources.
- Consistent companion profile, unique feature IDs and legal catalogue stages.
- Historical receipt is reported as HISTORICAL_RECEIPT_ONLY; the CLI never
  invents current CI success. Strict mode exits code 2 for stale receipts.
- The default active profile is tracked separately: current rich51; V3 is
  canonical companion but not yet the main playable profile.
- Studio, Android, FUN and owner acceptance are not inferred from CI.
- 13 mutation-oriented standard-library tests and a read-only PR workflow
  produce JSON evidence, not a Studio build.

Run with a 40-character HEAD independently read from the official branch:

python3 -m unittest discover -s quality_gameplay/rc31_live_receipt_20261116 -p 'test_*.py' -v

python3 quality_gameplay/rc31_live_receipt_20261116/receipt_audit.py --repo-root . --official-head OFFICIAL_SHA

## RC integration and rollback

This isolated source candidate does not modify official RC or live game code.
Only #220 may adopt it into the official RC via latest-HEAD expected-SHA
nonforce CAS and same-HEAD CI. Personal author replies are not prerequisites.
Rollback removes only this scoped QA folder and workflow; 31 gameplay source
bytes and the rich51 default profile remain unchanged.

PC Studio TEAM/BR, solo with 15 AI, Android 15 minutes, #420 ART/FUN and
OWNER acceptance remain NOT TESTED / NO GO.
