# Owner-origin idea vault × Web research (manual integration candidate)

2026-10-29 — Issue #109. **Candidate only: not integrated into main; not live market evidence.**

## Source of truth and provenance
The owner's exact Japanese idea is archived as an **OWNER_ORIGINAL_IDEA** in [Issue #109](https://github.com/kk051780/toy-wars-factory/issues/109). Preserve that original text: source URL is unavailable and must not be invented. AI proposals and research-derived improvements use separate IDs and source observations. The prototype's hashes detect ordinary accidental edits and inconsistent transitions; they **do not authenticate a self-rehashed untrusted file**. Durable source trust requires the actual GitHub immutable blob/commit, independently observed and correctly scoped.

Web data require source URL, checked-at timestamp, observed fact, and explicit limitations. No web page, its prose, or its claimed popularity has write/merge authority. Use primary evidence and real player reactions with provenance; check research again when stale. Do not copy competitors' assets, protected trade dress, names or code.

## Read-only implementation and acceptance
- `tools/system_idea_pipeline.py`: validate owner vs Web vs derived provenance; preserve raw text, reject missing parent/cross-game references; allow only planning lifecycle stages and closed deferred/rejected states; compare at least two alternative proposals with unchanged NO_CHANGE baseline and explicit falsification criteria. All candidate scores are **unmeasured hypotheses**, not user impact.
- `tests/test_system_idea_pipeline.py`: 19 tests covering source, tampering, temporal events, cross-project references, invalid scores, baseline and refusal of unauthenticated execution/merge/adoption.
- The Python source has **NO GitHub write, no scheduled dispatch, no network or external inference**, and does not auto-run other code. `dispatch/write/merge/publish/spend` all remain false.
- New owner ideas arriving in chat must be explicitly captured in a permanent repo issue/registry with original words, then proposals connect to them; the current prototype has no automatic conversation ingestion endpoint. The existing registered META prompt has been updated, but its most recent service status was `no_update`.

## Gates after draft code
1. Manual CONTROLLER candidate has a genuine epoch/owner claim; this is **not** a registered META author run and must not be mislabeled as such.
2. Exact-head `offline` + `compile_hold` CI and all accepted regressions must pass. Independent **protected/manual maintenance audit** must verify provenance, policy, changed paths, tests and base before any adoption. Ordinary registered REVIEWER cannot merge this manual `feature/` PR under the current automated lane.
3. The next registered META implementation should bridge this module to a **trusted** GitHub Issue/commit reader and existing `ops/GAME_IMPROVEMENT_BACKLOG.json` without weakening the recorded provenance or granting automatic execution from untrusted Web/JSON.
4. Only later can a scoped, separately reviewed worker implement the selected new toy (CUREBO remains unmerged in PR #98, KURURIN is a candidate in Issue #102), followed by engine/device/player evidence. Do not claim success or guaranteed popularity from ranking scores.
5. Keep all standing Gemini spending and Roblox publication HOLD constraints. No new recurring tasks, credentials, or scope changes.
