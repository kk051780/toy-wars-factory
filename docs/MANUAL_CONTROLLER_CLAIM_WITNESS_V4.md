# TOY WARS — Controller claim witness v4: final mutable-ref recheck (89 tests)

**Status: independent unmerged source candidate; read-only; no reviewer authority.** This is v2 + a new bound that authenticates *which Git paths changed* in the shared coordinator claim commit. It does NOT prove that GitHub accepted the claim ref before a source branch push for any historical PR. The workflow cannot be dispatched until independently reviewed and installed on accepted main. There is no real provider workflow run or Roblox operation in this package.

## New v4 fix: recheck mutable GitHub refs immediately before branch absence

After v3 has verified the immutable claim commit, parent, both Git trees and JSON
content, it previously checked the main ref once and then immediately checked
absence of the proposed source branch. A *different* CONTROLLER may release
or replace the coordinator claim during those 9 GitHub GETs, or main may advance.
Without a final comparison of the **mutable** coordinator and main refs, a local
return could describe a claim which was no longer the active holder by the time
the branch-absence evidence was collected.

The v4 witness now re-GETs coordinator ref, rejects changed ref/SHA, re-GETs
main ref, rejects changed ref/SHA, then — still **last** — looks for source
branch absence. Thus the successful provider GET sequence contains **11 GETs**
(maximum 12 permitted), including each mutable ref **twice** and both complete
Git trees. For the real Actions host (no injected test timestamp), the original
lease is also checked against the clock immediately before the last request.
The code remains read-only and **does NOT give atomic cross-ref guarantees**:
there remains a race after the last read, branch deletion/reuse cannot be
ruled out by one 404, and original provider run/job identity and independent
review still need separate verification. All authority flags remain false.

Nine new unit tests cover foreign coordinator/identity, holder replacement,
main changes, missing refs, final ordering, and unchanged two-ref baseline.
The original 80 v3 tests are preserved. 

## v3 protection retained: whole-commit provenance scope

The previous v2 validated only the content of `ops/REPAIR_COORDINATOR.json` at the claim commit and its parent. It did not rule out the very same claim commit also changing a hidden permission file or other unrelated source. This is an important gap for future independent review.

`verify_single_coordinator_change` now GETs immutable parent and claim **Git commit tree SHAs**, then performs TWO additional read-only GitHub REST GETs:

- `GET /repos/kk051780/toy-wars-factory/git/trees/{parent_tree_sha}?recursive=1`
- `GET /repos/kk051780/toy-wars-factory/git/trees/{claim_tree_sha}?recursive=1`

It checks each tree `sha`, explicit `truncated:false`, a bounded and duplicate-free path listing, exact modes/type, equality of every unrelated path, exactly one changed `ops/REPAIR_COORDINATOR.json` **blob** SHA matching both separately content-verified file JSON envelopes, and the expected changed `ops` ancestor TREE SHA. Additions/deletions of unrelated files, executable-bit changes, symlink swaps, mismatched/unavailable/truncated tree responses, and spoofed blob-tree mapping are denied. The last provider GET must still be branch absence (true 404 only).

**Original real-GitHub API corroboration:** observed 2026-10-31 on private repo, coordinator epoch327 legal claim commit `f38865e71415ebb0951219580ee4de2530d48916`, sole parent `aa86f25cda228efd2488e13f5081692f6c4cbac3`, original trees `a475194d972f1bcb803b4544113f060c48d36716` and `3299dada55960bbc16e8ec43f92c694a492d2f3d`. Both GitHub GET `?recursive=1` responses had 220 entries and `truncated:false`. The ONLY differing recursive paths were `ops` (tree) and `ops/REPAIR_COORDINATOR.json` (blob). This is an authenticated *original source shape observation* only, **not a replayed provider witness or current authorization**.

Official GitHub REST Git Trees docs confirm the response's `tree`, `sha`, `truncated` schema and `recursive` query behavior: https://docs.github.com/en/rest/git/trees. `workflow_dispatch` requires the workflow file already installed on the default branch: https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow.

## Other v2 protections retained

- Strict repository numeric ID 1431683395, repository name, `GITHUB_WORKFLOW_REF`, event/ref/main SHA and attempt1 host context check before network access.
- GitHub-only token-scoped GET with redirect refusal; no POST, PUT, checkout token persistence, Roblox/AI/inference/billing.
- Claim parent's holder=null, exactly epoch-1, claim only epoch/holder JSON fields changed, owner UUID, main source SHA, 30-minute expiry and current coordinator ref exact match.
- Future source ref must not exist at the read moment (GitHub 404), 403/429/redirect and malformed responses refuse. This is not a never-used-branch proof, nor an atomic future source-creation guarantee.
- All positive return flags remain `provider_authenticated:false`, `independent_review_authorized:false`, `merge_authorized:false`, `roblox_post_authorized:false`.

## Verification

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -q
python3 -m compileall -q tools tests
```

Original v3 **80** Python tests remain, plus **9** new `test_witness_final_ref_recheck.py` cases = **89 / 89 PASS** on local Python 2026-10-31. Tests use synthetic provider fixtures; no GitHub secrets. ZIP includes complete original workflow candidate + source + tests and `SHA256_MANIFEST.json`. Source hashes and clean extraction regression are verified separately.

## Adoption path and hard holds

The original attempt to claim a fresh CONTROLLER lock for v2 found a foreign epoch328. v3 then encountered foreign epoch329 on `controller/manual-go-priority-reader-a581f8a9`. At the start of v4, epoch329 was still held and a separate PR #165 for its owner was already open. **No source branch/PR/main or shared coordinator ref is written by this local candidate.** A legitimate author under a future new lease can create a narrowly scoped **PROTECTED DRAFT** PR with native RED→GREEN tests. Independently review provenance and permissions before accepted-main install. Only then can a trusted host actually dispatch a witness for a future *never-before-used* source branch and a separate trusted reviewer independently inspect original provider run/job/commit evidence.

**Do not relax** PR60's protected reviewer gate, or retroactively approve PR143/144/158 based on this witness design. No source merge, real Rojo `.rbxl` build, Roblox Studio/Open Cloud runtime, publishing, Gemini inference or spending occurred.
