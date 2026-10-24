# Request-specific bound result — input proof remains blocked

Status: **OUTPUT_BOUND_TIGHTENED; NO_VERIFIED_SMALL_INPUT_BOUND; NO_LIVE_CALL**.

The native GenerateContent thinking guide explicitly includes thinking tokens
in the output cutoff. The offline adapter now reserves the actual positive
`generationConfig.maxOutputTokens` for one candidate rather than the entire
model output window. The request body is snapshotted before counting and
forwarding, and the returned candidate-plus-thinking usage must fit that limit.
Continuation, tools, multiple candidates, cached-content references and media
remain unsupported. No automatic continuation or extra SDK calls are added.

Source: https://ai.google.dev/gemini-api/docs/generate-content/thinking

## The unresolved input side

The exact official Python SDK source inspected is commit
`c0e9c54915970948258226e565bde6ef6d5c0b94`, version **2.33.0** (2026-10-23).
Its local tokenizer lookup does not support `gemini-3.8-flash`. The lookup does
recognize the positive controls `gemini-2.5-flash` and `gemini-3.5-flash`.
These are compatibility controls, not proposed model changes or proof that
either provides complete provider framing/billing bounds.

`tools/verify_gemini_input_bound.py` verifies the two original Git blob hashes,
parses their ASTs and runs only the original pure name lookup. It never imports
the SDK or its network dependencies, downloads vocabularies, reads a key or
calls Google. An inspection PASS means the blocker was reproduced; it does
**not** mean an input bound was certified.

Primary sources:
- https://github.com/googleapis/python-genai/blob/c0e9c54915970948258226e565bde6ef6d5c0b94/google/genai/_local_tokenizer_loader.py
- https://github.com/googleapis/python-genai/blob/c0e9c54915970948258226e565bde6ef6d5c0b94/google/genai/version.py
- https://ai.google.dev/api/tokens

CountTokens, an alias to another tokenizer, character/byte ratios and arbitrary
overhead margins are not accepted as certified input bounds. Public material
inspected here did not establish a narrower complete bound for this target.
This is a result for the checked sources and current implementation, not a
claim that every possible future provider mechanism is impossible.

## Exact requirements under the unchanged 10-AIC cap

Using the dated Standard text-rate snapshot and no prior spend/reservations:

| Output cap, including thinking | Input ceiling that would need independent proof | Reservation with the currently proved model input ceiling |
| --- | --- | --- |
| 1 | 133,328 tokens | 78.643575 modeled AIC |
| 512 | 130,773 tokens | 78.8352 modeled AIC |
| 2,048 | 123,093 tokens | 79.4112 modeled AIC |

For the 2,048-token output case, 123,093 input tokens fit the arithmetic and
123,094 exceed it. The threshold is a **requirement for a missing proof**, not
an observed token count or an admission certificate. The diagnostic cannot
reserve a lease or authorize a call. Prior spend reduces the available threshold.

The adapter still uses the documented model input ceiling, 1,048,576 tokens.
Thus even a one-token output is rejected before transport. These conservative
reservations are not expected costs, bills or minimum Gemini request prices.

## Operational result

The existing 10-AIC cap, consumed one-shot marker, request-count guard, shared
persistent accounting and independent-review requirement remain intact. No
new inference, model substitution, recurring execution, automatic merge or
Roblox publication is authorized or triggered. The gateway remains offline
and the real CLI/reviewer clients remain disabled.

The remaining input proof is a **blocker**, not another routine step already
known to be solvable. A future continuation must supply attributable provider
bounds or a separately validated exact model/framing path; it must not turn an
estimate or passing mock test into permission to execute. Live inference still
requires fresh owner authorization after the enforcement prerequisites hold.
