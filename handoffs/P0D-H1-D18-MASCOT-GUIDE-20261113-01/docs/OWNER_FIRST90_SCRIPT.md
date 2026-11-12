# H1 D18 living mascot, 0–90 seconds, private test

| When | Expected experience | Actual test gate |
|---|---|---|
| 0–15sec after team spawn | Friendly red-hot original D18 dragon bobs beside own spawn, clearly different from ordinary procedural Parts | 2clients see own correct mascot, no second model/server clones |
| COUNTDOWN/ACTIVE tap | "たまごの道をきく" E or mobile tap; 4 golden lights point to the actual enemy EGG Part | check team RED -> BLUE EGG; BLUE -> RED EGG; only source-true targets |
| Carrying an enemy egg | A second tap now points back to own SCORE_PAD; original egg & score authority still S1 | 2clients actual egg steal/drop/capture, inspect pointer updates |
| During results/lobby | Mascot and local hints disappear; new round reconstructs once | no stuck prompt, memory leak, client duplication |
| After owner's play | H0 existing original H1 vs this H1 + one readable guide; unprompted child clarity, visual enjoyment, next-run intent | real human assessment UNKNOWN, not synthetic |

Rollback: original intact full #248 H1 SHA c73f305fb412927aee05b399a4f54a2a16d0579f; no merge. Performance source budget: 17 original geometry Parts + one prompt anchor, at most 4 tiny local wayfinding parts, heartbeat <= ~11Hz. No new authoritative game effect. Child-readable on a real phone and fun: NOT_TESTED.
