# Independent QA for the existing G4 Bot return fix — test-only

This is a **non-overlapping test**, not a second Bot/Router implementation or
second RC. The original author has already requested a narrow source assignment
in [#218 comment 7115147198](https://github.com/kk051780/toy-wars-factory/issues/218#issuecomment-7115147198)
for the bug actually observed in [#364 comment 7114956174](https://github.com/kk051780/toy-wars-factory/issues/364#issuecomment-7114956174).

The only formal RC is `rc/p0d-s1-kids-rc01` at
`72d620d86761f2aa5da80263a251cc5fa63fecbb`. Its original Actions
[run 45132949073](https://github.com/kk051780/toy-wars-factory/actions/runs/45132949073)
provides 69 actual sources / 75 Roblox Instances. The tests download that
unchanged artifact, pin the Place/Actor/Router SHA256, compare the 69 embedded
Source bytes against their source files, reject ambiguous / non-reversible
source replacement and demonstrate an analytically blocked straight return
at the current 2-stud castle sidewall. The analytic example **is not** engine
PathfindingService simulation or a proven root cause.

The optional `GQ470_G4_V21_ACTORS` environment variable enables exact
author-body comparison only if G4's 21,604-byte V2.1 Actor is actually supplied
and SHA256 matches `44a9d578d4225d56152be1139f3925b65376d5c4e33ba3d3505a2e4db1cf94fd`.
No candidate source means **SKIP/NOT_TESTED**, never V2.1 PASS.

No protected game source, production release, Roblox publish, claim, nonce,
lease, review approval or #220 writer action is performed. This draft remains
SOURCE-only. Native TEAM/BR and real V2.1 Studio, same-new-HEAD CI, Android,
3-minute FUN and OWNER acceptance must be demonstrated separately.
