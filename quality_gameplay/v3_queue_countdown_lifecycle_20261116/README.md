# EGGRUMBLE V3 — abandoned lobby queue countdown (non-overlap)

## Defect and real play impact
In existing original V3 Host PR #484 (`6b52eaf1f2725496277998fe0c5532b7a8fcaab5`, original Host blob `c1ff23cd2883401d44d6fc47311bebcfd53eb1c6`), first entrant A starts a 12-second timer. A may leave at second 2; if B joins at second 5, `#queue==1` creates B's new timer but A's old timer remains valid because `queueEpoch` is unchanged. The old timer can launch B after **7 seconds instead of 12**. In a game where the roster is filled by AI and castle/egg matching begins when countdown expires, this can start an unintended match before B has chosen job or defense.

## Unique change
One existing Host callback only: on `Players.PlayerRemoving`, after removal from a **not-yet-active** queue, increment that queue mode's epoch **only if the queue became empty**. Keep continuous occupied queues' original timer and the other mode independent. Existing `joinQueue` timer captures this epoch, so this uses its existing authority—no new Game, Remote, queue source, session, results, score, or cooldown.

## Full 8-domain source scope
Character/7 roles: unchanged; field and multi-eggs: unchanged; battle/HP: unchanged; personal castles: unchanged; neutral horde/boss/AI: unchanged; field items: unchanged; lobby: **one epoch invalidation**; balance/results: unchanged. Preserve original #482/#484 game, #485 ART, #487 SCORE and other isolated writers. This file is not a duplicate lobby system or #513 private gate or #492 spectate client.

## Evidence and gate
- `compose.py`: exact original Git blob, unique Lua anchor, reversible ON or zero-write byte-exact OFF; reject source drift and in-place modification.
- `tests/test_queue.py`: positive, mutation, rollback and duplicate-anchor tests.
- `native_queue.py`: extract the **real** Host `joinQueue` and `PlayerRemoving` callback for deterministic Luau VM execution; requires orphan timer, occupied queue, independent BR, and late entrant cases.
- Actions on this branch: pinned original Host, same-source native test, entire original 16-source native parsing and private Rojo Source/Class exact; private artifacts only.

No original author files touched. Source-only DRAFT, NOT formal RC. This PR is not merged directly. Target writer #220 must take the exact 1-callback overlay into the latest reconciled Host **only after** fresh source-lock and authorized non-force CAS; same-HEAD official Native/Rojo/Place/ZIP and adoption receipt. No main/Publish/paid/Windows or Studio claim. Real 2client/Android/#420 ART/FUN/OWNER tests remain NOT_RUN. Source drift or failed native validation is RED; revert by selecting original Host bytes (OFF).
