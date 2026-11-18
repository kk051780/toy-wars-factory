# GQ8 Core36 historical post-CAS source-adoption receipt

## Nonoverlapping defect and safe repair

The sole authenticated #220 writer accepted original Realm #764 + Regen #775
as private V3 Core36 via nonforce expectedSHA CAS to
`f77b4d4393d9e9b19b65566413432a7a9f13962b`.
The matching official postpush [Core36 #44232589275](https://github.com/kk051780/toy-wars-factory/actions/runs/44232589275)
passed Native36, Rojo Source/Class36, and OFF31, producing
GitHub Actions ZIP artifact ID 14396515259 of 366128 bytes.

The original Core36 selector JSONs still contain their pre-adoption
`PENDING_CANDIDATE` and `official_nonforce_expected_sha_cas=false`
fields, which are truthful as **creation-time selection metadata**, but
**not** truthful if misread as the postpush historical acceptance state.

**First attempt was rejected correctly by the existing Core36 adoption-only
workflow** (`RED_RC_MOVED_BEFORE_ADOPTION` on PR #793 commit
`0c4d9445313d04accfb21e34ee68610d3a215c56`): that workflow
accepts only the original exact 3-path Core36 adoption transaction from
its immutable 31-source base. Do not disable or weaken its guard.

Instead this corrected PR adds an **append-only** source receipt at
`rc_fastlane/EGGRUMBLE_V3_CORE36_POSTCAS_RECEIPT_20261118.json`
and a self-contained negative QA, preserving BOTH original selection JSONs
byte-for-byte. This also does not re-author #780/#787 source composers or
#790 first-play proof. The new receipt is historical, pinned to exactly
one observed official SHA and one completed official Actions run; later
CURRENT HEAD must be fetched anew. No adopted source count increase.

## Source / scope

- No existing game, art, AI, client, Script, Remote, Store, Host, Combat,
  Swarm, Castle, Item, HUD, player movement or original selector modified.
- The only new source is JSON historical evidence, Python tests, a read-only
  Actions check and README.
- Fixed baseline: original 31 + Realm3 + Regen2 = **36 private sources**;
  primary S1 `rich51` remains the default.
- The receipt's ZIP byte value is **not** standalone .rbxlx byte size.
- Studio 2client, Android15m, art and human FUN remain
  NOT_TESTED/NO_GO; no Roblox Publish/paid/spending.

## Integration and rollback

Candidate branch is independent and cannot write to the formal RC.
Only authenticated B #220 may accept this **metadata-only new file**
after current-source/source-lock and same-head checks under nonforce
expectedSHA CAS. No original author acknowledgement is needed.
Rollback = omit/delete the new receipt/QA; original game/selector unchanged.
The first attempt failed; do not mislabel it successful. This corrected
head's own workflow must complete SUCCESS before marking PREP_READY.
