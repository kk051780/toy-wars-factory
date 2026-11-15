# P0D conditional multiwriter scoped-CAS PREP — #218

**NOT LIVE: PREP ONLY / PRODUCT_NO_GO.**

## OWNER's special quality-gate responsibility

The #470 product-quality gate does not stop at reporting errors. For the SAME FB-ID it must drive: reproduce -> establish root cause -> the original author (or uniquely coordinator-granted QA writer) patches real game source -> negative and same-SHA source QA -> official RC admission -> same-head build and Place/ZIP -> real Studio and Android plus competitor retest -> reject/re-fix until OWNER_ACCEPTED. A passing quality-checker alone counts as zero repaired gameplay defects.

## Multiwriter supersedes the old sole-writer policy *when safe*

OWNER #218 comment 6887245930 authorizes migration to 2–3 independently scoped, authenticated RC writers. Writers use distinct feature branches; each may advance ONE official RC branch through non-force atomic CAS, but only after verified grants and protection. Shared Game/HUD/Remote/Store/HP/score authority needs exclusive lock. Other writers' commits must never be lost; a CAS loser must rebase onto the new HEAD and repeat QA. Never auto-merge a stale candidate. Each author has own FB-ID, feature ID, changed paths, lease and reviewer.

The canonical claim authority remains #469 coordinator registry, not a new duplicate system. This PR creates only multiwriter/gate.py (fail-closed read-only preview) and multiwriter/cas.py (non-force atomic-ref primitive, NO public executable CLI), negative tests and a read-only workflow. Neither file grants GitHub credentials, self-certifies a reviewer, changes official Game or RC, or authorizes a merge. Gate verdict EVIDENCE_READY_NOT_AUTHORIZATION is **not permission to write**. CAS primitive only accepts a future independent protected-workflow authorization bound to exact SHA and paths; a forged Python dict is not genuine authorization. Official installation still needs a GitHub-authenticated trusted dispatcher, real actor identity and check verification.

## Verified current GitHub blocks, read-only 2026-11-15

- Official branch rc/p0d-s1-kids-rc01: protected=false, protection.enabled=false, required checks off.
- Coordinator branch coord/p0d-work-claims: protected=false, protection.enabled=false.
- Repository rulesets enumeration shows an active rule named main, **not evidence of protection for RC/coord**.
- Coordinator registry P0D_EXCLUSIVE_CLAIMS_V1 has claims=[] (zero GRANTED writer lease entries).

Therefore **PRODUCTION_MULTIWRITER=HOLD / AUTHORIZED_WRITERS=0**. This is independent of the OWNER's approval to design the new model. Never bypass protection or fabricate grants.

## Activation gates — all mandatory

1. OWNER/admin establishes and verifies **effective** RC+coordinator branch protection or protected rulesets, secure short-lived writer identities, nonforce updates and allowed paths. If protection restricts direct pushes, create an authorized protected dispatcher instead of weakening it.
2. Coordinator publishes protected, CAS-updated claim grants with unique feature/resource/changed paths, GitHub actor IDs and expiry. The trusted actor/token and actual PR diffs must be read from GitHub, never from PR text or local JSON.
3. Existing #469 claim guard PASS; independent reviewer; zero P0/P1 source findings; source CI SUCCESS matching pinned source HEAD; no duplicate Game/Remote/Store/score authority.
4. Trusted protected GitHub workflow issues one-time, short-lived, actor/sourceSHA/RCbaseSHA/paths-bound authorization. A CAS call creates commit with parent exactly RC HEAD, updates ref force=false. If another writer wins, treat 409/422 as conflict; rebuild on new RC HEAD, rerun CI and independent review. No automatic force or full merge.
5. Prove on a **disposable test branch** with two actual authenticated writers: winner is preserved, loser retries safely, independent QA reruns, rollback safe. Do not mark deployed until real evidence.
6. Apply the genuine source improvement and recheck official same-HEAD CI and actual Place/ZIP; real Studio/Android/fun and OWNER still required to close gameplay FB defects.

Offline tests: python3 -B -m unittest discover -s multiwriter -p test_multiwriter.py -v

No main/force/unauthorized merge/Roblox publish/payment/Windows remote control. This PR is only mechanism PREP and cannot repair the RC gameplay until original P0 authors and approved scoped writers submit real source fixes.
