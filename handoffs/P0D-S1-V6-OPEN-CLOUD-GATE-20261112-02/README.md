# P0-D S1 V6 — no-Codex read-only Open Cloud engine gate

**Only** the original TRAP_RAIDERS S1 RC at `1263a03701211a652b99b91d2339575dc8104eff` is pinned. The official single-writer branch is not modified. These files are an independent gate candidate for #220 to review, not authority to deploy, publish, or override P0-A/B/C.

- `OpenCloudS1Probe.luau` executes **read-only in a real headless Roblox engine** when an authorized operator explicitly submits it against a confirmed private staging place/version. It checks Game/MapBuilder/Rules/TrapRules/Lobby source placement, exactly one remote, real map-created castles/egg prompts/pads/spawns, two teams, and trap folder. It does not cause a match, attack, or gameplay mutation. A pass is **not** 2-player, phone, human, boss, or monetization evidence.
- `cloud_gate.py` is a fail-closed, standard-library Python launcher. The default `python cloud_gate.py` prints the pinned RC and source digest and **never connects to Roblox**. `python -m unittest test_cloud_gate.py -v` tests the guard offline.
- Before any cloud run, the OWNER must separately approve (outside PUBLIC GitHub) the exact private staging universe/place/version and attest that **this specific uploaded place version corresponds to the approved RC SHA**. Without the verified release/version mapping, no task can honestly test the RC. Record a private receipt with the exact keys below. Do not commit real credentials, private IDs, or receipts to PUBLIC GitHub.
- A future approved operator may execute exactly one task using `RBLX_OC_API_KEY` as a private environment secret and `python cloud_gate.py --execute --owner-approved --receipt <PRIVATE_JSON_PATH>`. This code does **not** upload a Place or call SavePlaceAsync, and **never automatically publishes**. Headless engine tests cannot replace actual 2-client or mobile QA.

Private receipt schema (the numbers shown are **illustrative only**):
```json
{
  "environment": "PRIVATE_STAGING",
  "rc_commit_sha": "1263a03701211a652b99b91d2339575dc8104eff",
  "universe_id": 123,
  "place_id": 456,
  "version_id": 789,
  "probe_sha256": "<64 lower-hex from dry-run>",
  "owner_approved_for_readonly_cloud_qa": true
}
```

A matching source hash and manually attested version alone are **not independent proof** of uploaded Place equivalence. The operator must compare actual version history/upload receipts first. All dynamic Roblox QA results remain `NOT_TESTED` until a real task returns a log with the positive marker. Prior native Luau tests with fake Roblox services count only as **offline tests**.

Official sources: https://create.roblox.com/docs/cloud/reference/features/luau-execution ; https://create.roblox.com/docs/projects/file-based-workflows ; archived reference sample https://github.com/Roblox/place-ci-cd-demo (sample is not a security policy or final guarantee).

**Not changed:** #220 sole RC writer, current source files, main, releases/ root, actual Studio, public Roblox, paid or API expenditures, P0-A/B/C, and the five existing automations. Latest official overall S1 score is **75/100** (#220 audit); this headless gate candidate adds **zero** release-score points before actual execution and sole integrator audit.