# P0D / D07 optional heartbeat fail-closed guard (source only)

- **Game:** TRAP_RAIDERS / `p0d-siege-v19` / `P0D-S1-KIDS-RC01`
- **Immutable parent S1 RC:** `1263a03701211a652b99b91d2339575dc8104eff`
- **Original candidate target:** `releases/P0D_S1_KIDS_RC01/src/server/S1CanonicalRoundHost.luau`, exact Git blob `61501c982619e54db6a09cf11b188ef872c1666e`
- **Actual Combined source checked:** `src/server/GoroganCombinedRuntime.luau` in the same RC, Git blob `f10dedf357476e658857131c0843f237825a1c0f`
- **Delivery:** Complete keyless original-derived `candidate/src/server/S1CanonicalRoundHost.luau` plus source-locked Python `tests/test_source_contract.py`. This new packet changes **only one conditional guard** relative to the verified original Host blob.

## Risk and change

The current Combined heartbeat legitimately returns `nil,nil` for no event and `{kind=...},nil` on a valid command. It returns `nil,"HEARTBEAT_FAIL_CLOSED"` on internal exception, but also `nil,"INACTIVE"` and `nil,"REENTRANT_HEARTBEAT"` for invalid calls. The original Host recognized only the special error string and otherwise silently accepted these unexpected nil+reason results.

This candidate changes its sole reject condition to `not good or reason ~= nil or (cmd ~= nil and type(cmd) ~= "table")`. It preserves success for idle and table commands while aborting on **any** unexpected error reason, thrown call, or invalid non-table command. It still uses existing `self:stop("D07_HEARTBEAT_FAILED")`: no new damage/round/Remote/clock source.

## Offline validation

Run from this packet root:

```sh
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

The tests reconstruct the *exact original* Luau by reversing the one guard and require its original Git blob SHA to match. The tuple truth table is a Python reference **not** native Luau execution. Fixed-source readback and a native Luau/runtime integration test are distinct gates; **native parser, Roblox Studio, 2 clients, phone, physical boss attack timing, D08 runtime, and human QA are NOT TESTED by this packet**.

## Integrator handoff / DO NOT auto-enable

This is an **optional review candidate** for the sole #220 RC writer. Before taking it, re-fetch the current sole RC branch and compare original Host blob. If the current Host has advanced, **NO-OP and re-review**, never blindly overwrite. Check D07 D08 real paired tests and negative cases, including `INACTIVE`, `REENTRANT_HEARTBEAT`, `HEARTBEAT_FAIL_CLOSED`, thrown heartbeat, bad return shape, valid idle, valid MOVE, and END.

Keep `CANONICAL_S1_ENABLED=false` and `D07_D08_RELEASE_REVIEW_APPROVED=false` in official `Game.server.luau` until OWNER explicitly authorizes actual boss integration and full final Studio QA. Do not change `main`, official `rc/`, other chats' branches, protected P0-A/B/C, existing automations, game publishing, or payments.

The already playable S1 egg/fortress core is unchanged; this source-only candidate does not raise the #220 sole-integator 75/100 release audit.
