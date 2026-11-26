# Current69 Capture lifecycle continuation

This is the original GQ8 Capture source lane from issue #832 and closed,
superseded PR #840. PR #840 remains closed. The source branch is
`feature/gq8-viral-real55-20261119`; the exact eleven-path scope is registered
as `P0D-GQ832-CAPTURE-LIFECYCLE-20261123-7A4B9B0B` in
[grant 7088404028](https://github.com/kk051780/toy-wars-factory/issues/218#issuecomment-7088404028).
The scope does not grant formal RC writes or constitute source approval.

## Behavior changed

The existing client now separates a yielding platform start call from the
current recording attempt and consent period. Turning recording OFF and ON
does not authorize an old clip. An epoch change fences callbacks before a
synchronous stop completion can run. A stale successful start is stopped
before another start is allowed. A terminal callback retires only its own
current UI state; it does not stop or clear a newer recording. If completion
arrives before the pending start returns, that return does not resurrect the
completed recording.

The normal recording stop/save path, the visual function and GUI construction
are unchanged. Recording remains optional, initially OFF, and Studio-only.
The 7/9/15-second durations and existing server notifications are preserved.
No Host, Remote, HP, combat, score, storage or gameplay authority is added.

| Source | Bytes | SHA-256 |
| --- | ---: | --- |
| Selected official original | 6,425 | 51f28c53a5a930225e5eba1668b48f0734b762d50cc74ae8528da3867e75c285 |
| Historical v2 control | 6,980 | 786db18b3be2ad600c1037e99744fd1c4309b9317329390faf1d03c9d70f8e92 |
| Selected v3 lifecycle candidate | 7,414 | 18b8b67741fee206870a7941fdb3b5a39c6bc42925abcd53271137d9fb458215 |

The original-to-v3 delta is +989 bytes. Twelve unique, exact edits are retained
in INPUT_LOCK.json. Their reverse produces the original bytes. Reversing only
the last four edits produces the historical v2 control.

## Current69 input and composition

INPUT_LOCK.json fixes formal input
`dcb501673d7959e4904cf360ef0119917e6aa2e0`, official push run
`45083333379`, artifact `14777998713`, and its complete 110-member ZIP:
5,319,187 bytes,
`58e53ab1bffe5de2fea9be6dc9dcff533da9d643c0569a5570c9227fa450d98d`.
The lock includes all 69 route/path/class/body identities, the raw project,
the original Place, fixed fixture/case identities and ordered contract results.

The current69 entry verifies fresh official-ref/run/artifact values and the
entire archive before extraction. It rejects drift, unsafe paths, duplicate
members and links. Physical bytes are checked before UTF-8/JSON decoding.
Existing output directories are not overwritten. New checks use explicit
exceptions and remain active with Python optimization.

ON replaces one already existing Capture body. The other 68 bodies and the
raw project remain exact. OFF is constructed by reversing the selected ON
body, then building that resulting source tree. It is not a copied Place
or an ON build relabelled as OFF.

The output bundle contains:

- `input_archive.zip`: the exact selected official input ZIP.
- `input/`: the original input, including its original official receipt.
- `input_api/`: the official-ref, run and artifact JSON used for value binding.
- `ON/` and `OFF/`: the two actual source trees and raw project.
- `COMPOSITION_RECEIPT.json`: actual source HEAD/tree and input HEAD separately.
- `QA/`: fixed programs, raw execution/build logs, negative-test records and
  measured results produced by the verification entry.

The candidate is explicitly noncanonical and not adopted into the formal RC.
The original receipt under input/ describes only its original official input.
The offline functions check supplied API values; they do not authenticate a
provider or impersonate a registered reviewer.

## Preserved regression contracts

Five fixture/case files are reused byte-for-byte. The completion suite extracts
the same 869-byte normal-control block from epoch_cases.luau; no copy with
weaker assertions is introduced.

| Native program | Required observed result |
| --- | --- |
| Original client, epoch suite | 20 PASS / 7 RED, 27 observations |
| v3 client, epoch suite | 27 PASS / 0 RED |
| Inverse-derived historical v2, completion suite | 25 PASS / 7 RED, 32 observations |
| v3 client, completion suite | 32 PASS / 0 RED |

The expected RED controls demonstrate detection of the old behavior. They are
not reported as successful old gameplay. Acceptance binds the ordered case,
observation name and outcome, complete FINISH records, raw stdout/stderr,
exit status, fixture skeleton and the one exact full source span in each
program. Both suites share six normal observations; 27+32 does not mean
59 independent features.

The gate also compiles all 69 selected ON sources with Luau
`f46d879e28302a430029304f7f6a162aed66f103`, builds ON and inverse OFF with
Rojo 7.7.1, checks all 69 Source/Class routes and 75 instances, and compares
non-Source XML. OFF must exactly equal the 828,114-byte official parent Place
with SHA-256
`356bcfc9b5602b03a04f77f9638e15175be2deec084ef2a9d95963cadf7586f6`.
Input/source/project/contract/archive drift negatives run normally and with
Python -O. Their expected rejection is separate from Native behavior results.

## Entry points and CI

The original compose_real56.py and test_real56.py prefixes and their original
legacy CLI tails remain exact. The existing workflow preserves the complete
legacy job payload. Its original live-Real55 fence is retained.

- Push/PR events run the explicit `current69` gate.
- Manual dispatch defaults to `current69`.
- `legacy55` dispatch selects the preserved historical gate. Its old formal
  HEAD fence still rejects a moved formal RC.
- An invalid dispatch value fails the current gate rather than skipping both.
- A skipped legacy job is not a new legacy PASS.

The existing workflow downloads the pinned input, builds the pinned tools and
invokes:

```sh
python3 -B quality_gameplay/gq8_viral_real55_20261119/compose_real56.py current69 \
  --archive INPUT.zip --out NEW_OUTPUT \
  --ref-json formal-ref.json --run-json official-run.json \
  --artifact-json official-artifact.json --source-head ACTUAL_COMMIT

python3 -B quality_gameplay/gq8_viral_real55_20261119/test_real56.py current69 \
  --bundle NEW_OUTPUT --luau PATH_TO_LUAU --compile PATH_TO_LUAU_COMPILE \
  --luau-source PINNED_LUAU_CHECKOUT --rojo PATH_TO_ROJO \
  --source-head ACTUAL_COMMIT
```

The source checkout must be the stated immutable commit, contain the formal
and original-source ancestry, and differ from the locked formal tree in only
the eleven registered files. Every selected repository file must equal its
Git blob. Local validation is labelled
`LOCAL_IMMUTABLE_CANDIDATE_NOT_REMOTE`; hosted CI records its actual checked-out
GitHub HEAD. Local and remote commit identities are not interchangeable,
even when their trees match.

The first published source commit preserves the original branch H as its
first parent and the freshly reviewed formal H as its second parent.
Independent actual-HEAD diff/CI/artifact review is required before PREP_READY.
If formal input changes, stop and rebind the actual input and affected checks;
do not relax the live-input fence.

## Ownership and limits

The eleven paths are listed in INPUT_LOCK.json. The author of the lifecycle
source and composition/workflow binding is root; map_review authored the
epoch fixture/contracts and portable verification wrapper; review_intake
authored the completion fixture/contracts. The registered independent
actual-HEAD reviewer is `/root/planning_gap`, which authored none of those
source or tests.

Canonical six-path selection, the shared GQ8 workflow, GUI layout and the
two original #953 visual producer paths remain outside this scope. The #953
visual proposal is preserved with its full-source guards. Reusing it with
v3 requires explicit same-owner composition scope and new complete-source
binding.

These Native programs use a generic API model. They do not exercise real
CaptureService, device/window events, a saved video or gallery integration.
The prompt callback returns false. Character=nil excludes VFX rendering.
Completion-before-start-return is a conditional ordering defense, not a
documented platform-order guarantee. Studio, Android and FUN remain
NOT_TESTED; ART remains NO_GO. Formal runtime selection and actual engine
acceptance are separate subsequent gates.
