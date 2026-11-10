# Offline QA report: D11 v43-A acceptance gate

- Scope: public-safe trace contract checker + synthetic fixtures + negative tests only.
- Python tests: **57 / 57 PASS**, executed locally with `python -m unittest discover -s tests -q`.
- Synthetic valid trace: `ok=true`, one capture, one denial, 3 ownership snapshots, `studio_qa=NOT_VERIFIED_BY_THIS_TOOL`.
- Negative cases: double v37/v43 ownership, missing snapshots, too-fast/too-stale capture, contested capture without reset, egg carrier/dead/out-of-range acceptance, lease/cooldown early, bad/stale sequence, unknown sensitive keys, malformed or excessive input, symlinks and duplicated JSON fields, CLI rejection.
- Python model / schema does not imply a real v43-A gameplay integration.
- Windows restored v43-A: **NOT_TESTED**. Luau compile/parse: **NOT_TESTED**. PC source adapter: **NOT_TESTED**. Studio 2/3client: **NOT_TESTED**. Physical smartphone: **NOT_TESTED**. Independent genuine server log provenance: **NOT_VERIFIED**.
- No production source or player/identity data present.
