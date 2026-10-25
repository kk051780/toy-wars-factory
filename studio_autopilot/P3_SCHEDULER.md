# Studio Autopilot P3 — multi-game scheduler (proposal mode)

This isolated module turns P1 per-game manifests, untrusted state observations and human/manual or scheduled signals into a deterministic, **read-only** priority shortlist. It never calls GitHub, Automations, cloud AI, Roblox, billing or publishing APIs. An apparently eligible or selected project is **not** a permission to execute.

Each registered game has its own repository, coordinator ref, distinct author/reviewer/meta identities, and PR capacity. Duplicate cross-game authority is rejected. A manual GO and scheduled wakeup during one planning cycle resolve to a single project candidate and a shared idempotency key, avoiding duplicate author intents. Rotation favors the game with the oldest last-served cycle instead of starving quieter projects. Main QA failure, stale main checks, existing lease, full PR slots or missing proof block selection.

Run unit tests: `python3 -m unittest discover -s tests -p 'test_multigame_scheduler.py' -v`. No second real game or production scheduler was connected; the second game in the tests is a synthetic example.

## Phase exit criteria

This is an **early P3 staging step**, not a completed P3. Before real task dispatch: P2 trusted live GitHub evidence must be fully approved and demonstrated on protected main; issuer must atomically claim unique per-game CAS lease; manual GO and scheduled run event IDs must use the same durable queue; fault injection should cover crashes, duplicate delivery, epoch changes, starvation and token/budget isolation; review must separately approve per-game exact-head CI and post-merge main QA. Never run both a periodic dispatcher and a manual controller without a common lease. Enabling dispatch/publication or external inference is out of scope.
