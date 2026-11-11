# Independent QA of the corrected 27-file S1 composite

Game: **TRAP_RAIDERS** | work: `p0d-siege-v19` | release: `P0D-S1-KIDS-RC01`.

This is a separate **read-only independent source audit** for the already-produced, immutable D07/D08 spatial-composite candidate at Git commit `ff291d7a5e6dc53e841552d1abc3cbdf9a805f48`. It is **not** the sole #220 protected RC branch, and it does not merge, enable boss release gates, touch Roblox Studio, use Windows Codex, or publish.

It reuses unchanged Git object blobs of the independent verifier sources from `c65d2d5caecf1052c15951dedbf3959684d3dc59`:
- `vendor/verify_rc_wiring.py` exact blob `824d2693f2371db832203cb13b35f79b3c24e6bc`;
- `vendor/verify_source_snapshot.py` exact blob `a940f0ea896cf8d3f2b6c6700e92ade608fdc52b`.

The Python runner audits the candidate's actual strict `PUBLIC_SOURCE_V1` manifest (27 files, correct Rojo mappings, no false game-ready), runs the **original Chat Python assembler** on the 18 source units from the original `SOURCE_PLAN_CORRECTED.json` using only local files, asserts the exact output `CHAT_RC_RECEIPT.json` bytes match the author's immutable receipt, and independently checks the assembled source bytes, singleton round/event/damage authority, no duplicate mounts, and unchanged Studio NOT_TESTED state.

It also runs **four negative cases** against temporary files: tamper a Game Luau byte; forge a false Studio PASS receipt; inject a second round authority inside an otherwise correctly signed new source plan; and insert an extra fake status key into the source manifest. Every case must reject fail-closed. Only `tempfile.TemporaryDirectory` is written; never modify candidate or Git files. GitHub Actions uses a branch-only trigger and `contents:read` token, no packages or paid APIs.

**Run:**
```sh
PYTHONDONTWRITEBYTECODE=1 python3 handoffs/P0D-S1-INDEPENDENT-CORRECTED-COMPOSITE-QA-20261111-01/tools/run_independent_composite_qa.py
```

**Acceptance truth:** this workflow may establish a PASS for independent actual source/assembly/static Rojo evidence for the *immutable corrected candidate*. It **cannot** establish actual Roblox native Luau syntax success, game balance, boss physical damage, genuine 2-client play, mobile UX, real users, production revenue, final RC acceptance, or OWNER publication authorization. For S1 completion, the sole #220 integrator must create a fresh real RC commit with all selected gameplay and safe UX, then receive final independent QA and OWNER-directed Studio verification. Overall game release score remains `UNKNOWN_PENDING_GATE_AUDIT`.
