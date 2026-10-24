# Complete input-bound review — 2026-10-24

Result: **NO_VERIFIED_SMALL_INPUT_BOUND; NO_PROVIDER_CALL**.

The narrow remaining question was whether a different official SDK supplies the
missing local-tokenizer path for `gemini-3.8-flash`. The inspected source snapshots
all reject names absent from their explicit lookup maps; none maps this target.
No SDK was imported, vocabulary downloaded or provider key read for this review.

| Official repository | Inspected commit | Lookup file | Target in lookup |
| --- | --- | --- | --- |
| googleapis/python-genai | c0e9c549 | google/genai/_local_tokenizer_loader.py | No |
| googleapis/java-genai | de413718 | src/main/java/com/google/genai/LocalTokenizerLoader.java | No |
| googleapis/go-genai | 9ba857f3 | tokenizer/tokenizer.go | No |
| googleapis/js-genai | 0dd787c2 | src/cross/tokenizer/_loader.ts | No |

Full commit and Git blob hashes are recorded in C00009 for reproducibility.
These findings apply to these snapshots. They do not prove that all future SDKs,
provider contracts or separately validated mechanisms are impossible. Merely
changing language or substituting another model's tokenizer is not a current fix.

## API evidence and its limits

Native CountTokens can accept `generateContentRequest`, including steering
information. Its reference also illustrates a contents-only count of 10 followed
by generated prompt usage of 11. That example prevents treating a contents-only
count as a complete bound; it does not prove that every full-request count fails.
The inspected native reference provides no numeric worst-case framing/billing
error bound that this candidate can currently enforce.

The separate Cloud documentation's mismatch warning concerns multimodal input.
It is not proof of inaccuracy for this text-only native request path. The reviewed
native GenerationConfig has output limits; no per-request `maxInputTokens` input
ceiling was found. No undocumented field or arbitrary margin is used as a guard.

Primary references:
- https://ai.google.dev/api/tokens
- https://ai.google.dev/api/generate-content
- https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/capabilities/get-token-count
- https://github.com/googleapis/python-genai/blob/c0e9c54915970948258226e565bde6ef6d5c0b94/google/genai/_local_tokenizer_loader.py
- https://github.com/googleapis/java-genai/blob/de413718286f307f48e3bdd7bff187a9e6dd1629/src/main/java/com/google/genai/LocalTokenizerLoader.java
- https://github.com/googleapis/go-genai/blob/9ba857f3a8f976f9d1fe7a7a82b0cceee840dcb7/tokenizer/tokenizer.go
- https://github.com/googleapis/js-genai/blob/0dd787c23d76139982d7acb01e3c99978f563007/src/cross/tokenizer/_loader.ts

## Engineering consequence

Keep model and cap unchanged and do not call CountTokens with private source as
an unapproved live diagnostic. A future bound needs attributable provider
guarantees or an independently validated exact model/framing path. Do not repeat
these same SDK snapshot inspections as supposed new progress; revisit them only
with changed sources or new evidence. Prepare the independently testable
operational stop for review while inference remains blocked.
