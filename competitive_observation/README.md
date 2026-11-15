# P0D #470 — Competitive gameplay observation protocol (isolated)
This branch owns **only measurement evidence**. It does not edit map, combat, role scripts, HUD, assets, official RC or existing #470 scoring code. It is intended for the PRODUCT-QUALITY comparison reviewer; the integration team #220 remains the only canonical writer.

## 4 reproducible scenes × 6 games × 3 trials = 72 observations
1. FIELD_ROUTE: actual playable routes and base-to-base traversal (not guessed stud sizes).
2. MOB_CLEAR_30S: 30s real kills, simultaneous hits and input-to-hit response.
3. ONBOARD_180S: first-time role choice, first hit, objective understanding and obstructive HUD.
4. REPLAY_3MATCH: scored eggs, scored neutral kills, tactical variety, voluntary replay.
Each observation requires a dated video URL/timecode, observer, device and game version. P0D observations also require a pinned official RC SHA. Unmeasured data is **null/absent**, never invented. Scenarios are intentionally not assumed equivalent across game genres; note genre mismatches in observations and never infer commercial success from raw counts.

**Start state:** 0/72 observations; NO_GO. `python3 -B -m unittest discover -s competitive_observation -p 'test_*.py' -v`. `python3 -B competitive_observation/validate_observations.py --input competitive_observation/OBSERVATION_TEMPLATE.json --report /tmp/PQ470_OBSERVATIONS.json` intentionally exits 1 until all 72 real observations have valid declarations. A pass certifies only field completeness, **not video authenticity or gameplay quality**.

No unauthorized merge, publish, monetization or Studio actions. Competitor art/assets must not be copied.
