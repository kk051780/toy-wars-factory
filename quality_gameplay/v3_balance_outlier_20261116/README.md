# GQ V3 — maximum-round-duration tail gate (non-overlap candidate)

* Owner scope: **only** this directory and dedicated CI workflow. No source file in original #482/#487 or existing official RC is modified.
* Existing original **BalanceMetrics** blob pinned to `1cb9316faa41f646bf2c18e15c6ddc46fc93bc78` at existing original SCORE owner #487 head `438a406ccfda5563053d783d7561797ccd364361`. No new Game/Remote/Store/HUD, score evaluator or gameplay rule.
* Unique product-quality defect: `evaluate()` bases releaseReady on median duration. A 720s TEAM game and 1500s BR game produce median 1110s and **false PASS** even though a game exceeded the 1200s maximum. This undermines the owner-specified match deadline. #499 fixes in-game deadline; **this work is exclusively the different balance acceptance false-PASS**.
* Fix: source-select *one existing* BalanceMetrics slot; fail closed if the original blob drifts; add `overlongCount` and `longestRoundSeconds`; require `overlongCount==0` for releaseReady. No auto-stop of games, no reward changes.
* Native: original balance spec plus new actual Luau outlier/boundary/mode test. Source regression: anchored 3 replacements + mutation failure + byte-exact OFF rollback.
* Integration gate: #220 sole authenticated writer may select this **existing-slot replacement** into an isolated 31-source companion only after native+Rojo same HEAD, source/class exact 31/31, feature-flag OFF regression, and current official RC CAS. This PR itself does not edit formal RC, main, default rich51, or Roblox publish.
* Safety: `SOURCE_CANDIDATE`, `STUDIO_NOT_TESTED`, `ANDROID_NOT_TESTED`, `ART/FUN_NO_GO`, `OWNER_ACCEPTED=0`. A code test is not a player test. No author acknowledgement wait.
* Rollback: select the untouched original #487 Git blob above. A future 31-source chooser must preserve all other 30 Source/Class bytes, including #541 Swarm, #537/#540/#539 Host and #489 Item.
