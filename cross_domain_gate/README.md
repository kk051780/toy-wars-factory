# Cross-domain gameplay evidence gate — P0D GQ (independent)

This lane checks **evidence completeness**, not actual Roblox behavior. Other PRs
own 7-role Luau (#482), game assembly (#484), art (#485), result score (#487),
competitive product QA (#471/#472), and the authenticated RC writer (#220).
DO NOT copy or modify their game source. No merge/main/publish/spend.

## GQ01–GQ06 evidence collection (all 7 domains covered)
- GQ01: Assassin moves through traversable castle; egg pickup is server-approved,
  delivery is server-counted, wall pickup is blocked (character/field/castle/item).
- GQ02: Correct role weapon, real multi-target damage, actual neutral KOs counted
  (character/battle/neutral).
- GQ03: Attack item consumed, real castle HP change, meaningful defense response
  (character/castle/item).
- GQ04: Summoned beast follows on traversable field, then damages real neutral
  NPCs (character/field/battle/neutral).
- GQ05: Seven roles available, server ACK, role-specific weapon, lobby selection
  overlay disappears (character/battle/lobby).
- GQ06: **Android physical device** touch interaction for role selection, fighting,
  egg/castle objective, neutral/item visibility and HUD layout (all seven).

Each PASS requires **same official writer-pinned RC commit SHA and same rebuilt
Place SHA256**, UTC-offset timestamp, Studio/Android device, HTTPS observation
record, plus all behavior assertion flags true. Use an actual video/log record,
not a test fixture. Supply `--expected-rc-sha` from writer #220 to prevent
self-declared or stale RC evidence.

An empty/unrun or contradictory report returns PRODUCT_NO_GO.
A complete report returns EVIDENCE_READY_FOR_HUMAN_REVIEW, **not** game approval.
#420 art/FUN/mobile performance, #470 competitive product quality, final
official RC CAS/CI and OWNER acceptance are separately required.

CI runs only synthetic unit tests of this checker; a green CI **never** means
Studio, Android, or gameplay passed. Do not place synthetic evidence into the
official RC history.

Command: `python cross_domain_gate/check_integration.py path/to/real_observations.json --expected-rc-sha YOUR_OFFICIAL_RC_HEAD`
