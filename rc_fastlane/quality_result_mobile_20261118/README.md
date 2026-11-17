# GQ8 mobile match results — independent current31 ResultService lane

Feature: GQ8_RESULT_MOBILE_READABILITY_20261118. No original author ACK wait.

Problem: The verified rank/score/KO/egg/castle/Boss result is longer than the minimum 245px result width. The existing one-line TextScaled rendering may shrink feedback excessively on small Android screens.

One existing module: EGGRUMBLE_MatchResultService, VerifiedPersonalStats only. Switch to a fixed 15px GothamBold and two lines within the existing 94px result frame. The server-truth fields are unchanged; gsub only breaks before deposited eggs. Same UI instance, role/winner/scoring, lifetime of eight seconds and frame.

Safety: Original 31 runtime scripts (one ResultService changed, other 30 byte exact), no new Game, Combat, Store, Remote, GUI instance, payment, or live HUD mutation. select() and off() are byte-perfect inverses. Drift and duplicate markers are rejected. Verification rejects altered script counts, class/source mismatches and non-ResultService changes.

Regression: Original pinned #487 score-result source ON and OFF; native Luau compile; malformed negative cases. Formal Rojo31 prepare/verify is supplied for authenticated #220 writer adoption.

Formal build integration: select after GQ8_BOSS_RESULT_SELECTED31.project.json; compile actual new31 Native, Rojo31 true Source/Class; point final Place to selected output. Add manifest flag only upon confirmed official integration, preserving all prior flags. On head drift recalculate from the latest official RC before non-force CAS.

Remaining: Studio TEAM/BR, Android15 and owner FUN acceptance NOT_TESTED. No main, publish or payment mutations.
