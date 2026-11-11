# P0-D two-meter progress visibility guard (source-only)

Owner directive: [#218 all-chat addendum](https://github.com/kk051780/toy-wars-factory/issues/218#issuecomment-6807393284), [#220 sole S1 score owner](https://github.com/kk051780/toy-wars-factory/issues/220), and unchanged [V3](https://github.com/kk051780/toy-wars-factory/blob/0fd269f83c338839e7ce0ef670263f1f9133b00b/handoffs/P0D_PROGRESS_PRODUCT_STUDIO_V3_20261111/OWNER_PROCESS_V3.md).

This **read-only, standard-library** Python CLI validates a manually supplied two-meter report and renders compact Japanese `[P0D_PROGRESS_V3]` text for every chat, preventing accidental per-lane 100% -> game 100% substitution. It does **not** fetch GitHub, independently validate the audit comment, verify SHA bytes, compute an official whole-game score, or make any Roblox/Windows/CI/money/release actions. A syntactically valid URL is **not proof**; each author must actually open #220 and confirm its latest evidence. Only the sole #220 integrator can audit the original 100-point gate and publish the official number. If no audited breakdown has been published, use `UNKNOWN_PENDING_GATE_AUDIT`.

## Usage

```sh
python report_guard.py example_unknown.json
python -m unittest -v test_report_guard.py
```

To report an audited `global.pct`, a human operator must independently confirm #220's latest itemized evidence audit, then set `audit_status=AUDITED`, `audit_points=pct`, `audit_max_points=100`, exact `last_rc_sha` and a specific `#220#issuecomment-N` URL. The checker checks format only; it does not guarantee the audit actually exists. The own-lane percentage is always derived from its fixed `accepted/total` checklist; `null/null` means denominator unknown. No invented delta with no comparable official prior audit.

Always show both values even when unchanged; present source-only test success and full Studio testing separately. S1 first release remains blocked until independent QA, owner-direct final Windows Studio, market/human acceptance and separate OWNER authorization. No main/RC edits, merges, production publish, payments/spending, protected P0-A/B/C CAS, or changes to five existing automations.
