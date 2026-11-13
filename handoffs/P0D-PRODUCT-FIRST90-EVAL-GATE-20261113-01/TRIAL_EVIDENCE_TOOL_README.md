# FIRST90 owner trial evidence gate — offline v2

For `P0D-FUN-H1-001`, this is a **report completeness checker** for real human-provided Studio observations, not a Studio player, an engine validation, an adoption decision, or a FUN guarantee.

```bash
python -m unittest discover -s handoffs/P0D-PRODUCT-FIRST90-EVAL-GATE-20261113-01/tests -v
python handoffs/P0D-PRODUCT-FIRST90-EVAL-GATE-20261113-01/tools/assess_trial_result.py \
  handoffs/P0D-PRODUCT-FIRST90-EVAL-GATE-20261113-01/TRIAL_RESULT_TEMPLATE.json \
  handoffs/P0D-PRODUCT-FIRST90-EVAL-GATE-20261113-01/A40_COMPARISON_TRIAL_TEMPLATE.json
```

Exit code 2 is **expected** on the untouched templates: both trials are `NOT_TESTED`. Make separate copies, fill only with actually observed owner results (local private Place SHA256, two-client/real Android verification, Output or capture, human fun score and date). `PRODUCT_DRI_REVIEW_CANDIDATE` means only that the report is filled consistently; the validator does **not** inspect/verify the truth of Studio sessions, the SHA against binary, 2-client device identity, or playable Roblox behavior.

The six hard gates must be reported `PASS`, and human first90/replay scores must average >=4/5 with replay desire >=4/5. This threshold is a *suggested PRODUCT rule* and does not modify #220's official scoring or #250 selection. Any actual failed gate means `REVISE_BLOCKED`; missing evidence means `WAITING_EVIDENCE`; low fun means `REVISE_FUN`. All output explicitly says `official_rc_adopted=false`.

Candidate refs are intentionally locked to B42 First90 (`837853e66278e38bb79f6399c3e8bfc9a2403be6`, private trial selected) and A40 V6 (`4b09de3eb70abb2e79268ce41bdecc4b614d39df`, comparison only). Rich45 B42+V7+Sky+2-dojo source (`646cd9bd18b3428235ada06a763f9c5ac65b6883`) is an optional **unselected** private candidate and deliberately not accepted into this B42/A40 gate unless #250 separately amends selection.

Real gameplay source, official RC, main, Windows Codex/Studio actions, publication, payments and the 5 automations are untouched.

Provenance: #218 all-chat, #219 PRODUCT_DRI, #250 adoption, #220 sole official RC writer. The #220 last published release evaluation was 75/100 / FUN_NO_GO, not changed by this tool.
