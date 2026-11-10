# TRAP RAIDERS · S1 independent dynamic trace QA v1

Game: `TRAP_RAIDERS` · work_id `p0d-siege-v19` · feature slice `S1_TRACE_SCENARIO_QA_ONLY`.

This is an **independent, read-only Python 3.10+ QA harness** for release candidate `P0D-S1-KIDS-RC01`. It verifies a serialized 2-client match trace (join, teams, egg, damage/HP, rejected forged action, boss warning, server deadline, victory/reset). It does not create gameplay, modify the RC tree, inspect SHA/project files, or execute Roblox Studio.

## Local test

```sh
python -m unittest discover -s tests -v
python src/trace_qa.py fixtures/s1_positive.synthetic.json
python src/trace_qa.py fixtures/s1_positive.synthetic.json --release
```

Expected: 27 offline unit tests PASS; synthetic fixture passes scenario checks; **release command blocks** with status `BLOCKED_NO_REAL_CAPTURE`, exit 2. This is intentional until actual server/client Studio capture is available.

## Real RC handoff to #220 integrator

1. Do **not** instrument a second authoritative event system. In the only server-owned match/capture/attack/reward logic, emit read-only `QA_S1_TRACE_V1` event observations after genuine committed actions; `WARN_VISIBLE` observations come from both test clients, then join into one monotonic server-time trace for offline checking. Never trust client-supplied hit/HP/reward/score/epoch.
2. Use single `match_id` + epoch and contiguous `seq`. `t`/`deadline` are **seconds** on a **single synchronized server time axis** (e.g. `workspace:GetServerTimeNow() - serverRoundOrigin`). No mixing `os.clock()`, epoch ms, or latency-unadjusted client timestamps. `receipt_id` is globally unique per trace for server accepted damage / rejected fake actions.
3. Export one UTF-8 JSON object matching `fixtures/s1_positive.synthetic.json`; set `capture_mode=STUDIO_CAPTURE`, `studio_session`, `place_id` and immutable 40-hex `source_commit` for a genuine captured run. The independent test harness validates metadata syntax, **cannot authenticate that these strings came from a live Studio**.
4. `python src/trace_qa.py captured.json --release` should finish with status `TRACE_CONSISTENT_STUDIO_METADATA_UNVERIFIED`; that is **not a native Studio PASS**. Attach real PC console logs, Place/Studio identification, 2client and mobile evidence separately under final OWNER-direct Windows QA.
5. Feed any error back to the RC integrator as a specific defect and fix the original module. This lane never changes `rc/p0d-s1-kids-rc01` or another chat's source.

`--partial` permits incomplete feature coverage only for debugging; it must never be used for release signoff.

## Coverage and limitations

Checks: deterministic event order/clock/epoch, distinct red/blue players, HP/castle math, friendly-fire ban, non-replayed receipt, boss warning fixed absolute deadline (~2.0 sec), both red/blue client warning views, client deadline projection tolerance (0.1 sec), user-visible remaining warning >=1.5 sec, authorized egg victory or castle victory/forfeit, round reset, explicit DONE, rejected spoofed request observation.

**Limitations:** Trace observations can be forged; this tool does not prove game implementation, native Luau parsing, physics, UI visibility, mobile usability, persistence or studio provenance. 1.5 sec is a proposed S1 usability acceptance threshold responding to the historical red 0.93 vs blue 1.96 sec warning discrepancy; integrator/OWNER may adjust only with an explicit product decision. The script checks event data structure and plausible game transitions, not whether all real events were captured. Accepting a fake-Remote `REMOTE_REJECT` log does not prove remote denial without independently observed real client inputs.

Protected: **no main write, merge, Roblox public publish, paid spend, owner PC modifications, P0-A/B/C CAS/auth, or Automations modifications**. Original source selection and RC composition remain entirely owned by #220 CHAT-INTEGRATOR. No additional Codex per-packet QA.
