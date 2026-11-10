# TRAP RAIDERS v42.3 — Match-result XP evidence boundary

**Add-on to v42.2, NOT a v42.2 replacement.** Prepared in `CHAT_LEAD_QUOTA` because the OWNER reports Codex quota is not yet restored (20:50 JST is the stated reset time, not verification).

| Content | Role |
|---|---|
| `luau/RoundEvidenceGate.luau` | Pure server-validated round snapshot to sanitized result evidence reference |
| `tests/round_evidence_reference.py` | Python oracle; not a Luau runtime |
| `tests/test_round_evidence.py` | Golden, malformed/AFK/action spoof, randomized offline regressions |
| `fixtures/golden_rounds.json` | S1–S4/7-job-compatible server-owned round fixture baseline and cases |
| `docs/INTEGRATION_GATE.md` | Minimal bounded Codex integration contract and acceptance plan |

No asset, script, file or template for current v36 exists in this packet. Integrate only after OWNER verifies local source and v42.2 ZIP. **Never equate Python test PASS with Studio PASS.**

To test locally from this directory:

`python -m unittest discover -s tests -v`

Manifest SHA and ZIP SHA are stamped in `PACKET_MANIFEST.json` and the final chat response. `PACKET_MANIFEST.json` is a ChatGPT handoff manifest, not the authenticated v36 `BUILD_MANIFEST.json`.
