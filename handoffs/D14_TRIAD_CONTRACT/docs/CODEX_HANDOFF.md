# OWNER → Windows Codex handoff: D14 CART triad, only after current PC safety gate

**This file does not trigger any PC action.** OWNER directly gives the instruction to existing Windows Codex. This source-free QA bundle is safe to read publicly; all actual D14 Luau ZIPs and keys live in separate private handoffs.

## Priority and gates

0. Get newest #213/#218/#217 and actual Windows `CHECKPOINT`, `QA_REPORT`, manifest, local source/Place/ZIP SHA. The PC report [#213 #6758211567](https://github.com/kk051780/toy-wars-factory/issues/213#issuecomment-6758211567) reports v39 final saved 2client PASS and v43-A candidate two/three-client S1 scoped PASS, but v43-A final save, full 4-map/7-class regression, trace-check and **owned Studio normal exit are not yet confirmed**. Finish that PC stage before D14. Never downgrade a newer Place to historical v39.
1. Check D14 exact source ownership: seats v2 `0bcf39c22c583604d72ccac47d29fc9d87b7e662`, CART server motion 02B `2cd3fb9b31bfe7817ca0ceba7456300c3a41bd12`, CART/RAFT visuals `3c78cd0af618f320fe9d0aafe7569e1e9b95b4b0`. **Never use superseded `cae5691b622045af57674d922a08a96764354412`**. Raft water physics are other-chat scope, not used in this CART pilot.
2. When OWNER explicitly authorizes one isolated D14 pilot, restore each AES256-GCM packet separately into a *new owner-controlled private folder* using exact game/work/packet/ZIP SHA, the generic fixed safe restore utility and separately supplied OWNER keys. Never put keys, plaintext Luau, Place or ZIP into PUBLIC GitHub. Run SHA/manifest/CRC, Python tests and actual Luau parse. Review real method signatures before writing adapters—PUBLIC readmes are not definitive API specifications.
3. Start only S1 CART **one team, one vehicle**, with the original server seat ledger as *sole* authority, `CartServerAdapter` as *sole* rail position authority, and original client CART prefab only as noncolliding renderer. Bind `BOARD` only to authoritative successful server seat grant (not attempted Remote). `ADVANCE` only to previously-authorized driver and server-authored waypoints. Render client-only `0/2`, `1/2`, `2/2` using server facts, never client-generated seat facts. Every invalidation (death/quit/egg/trap/reset) must stop movement at the last server pose.
4. Export a **sanitized** event record using `docs/INTEGRATION_CONTRACT.md` normalized schema to an owner-only folder. Run:

```powershell
python tools/verify_d14_triad_trace.py examples/synthetic_cart_trace.json
python -m unittest discover -s tests -v
python tools/verify_d14_triad_trace.py C:\\private\\p0d-d14-qa\\cart_trace_redacted.json
```

5. A green trace check is only `CONSISTENT_TRACE_REVIEW_ONLY`, never proof of Roblox Studio execution or source authentication. Validate the actual server callbacks separately; record 2-client and 3-client results (including spoof, replay, egg carrier denial, disconnect/death/respawn, round end). Carry out real Play/Stop and mobile FPS/R6/R15 tests. Check regression of v39 rewards, v43-A NPC owner, S1-S4/7 jobs. Record real saved Place and source SHA; normal Quit only the Studio instance created for this test, PID disappearance and `STUDIO_CLOSED_VERIFIED`. Unrelated Studio PIDs must be preserved.
6. Failures or missing evidence → HOLD/NOT_TESTED, not `STUDIO_QA_PASS`. No main write/merge/Roblox production publication, real charge/purchase/added spend, P0-A/B/C/CAS bypass or alteration of existing Automations.

## Evidence entry to #218 after real Windows work

Keep public comments metadata-only: `packet_id`, `source fixed commit`, `ZIP expected/restored SHA`, `test type` (OFFLINE_TRACE_CONSISTENT versus ROBLOX_STUDIO_SCOPED_PASS), actual Place SHA, passed/failed/blocked scenario counts and owned Studio exit. Never post the redacted trace if it still contains sensitive identifiers. Results here are **NOT_YET_RUN_ON_OWNER_PC**.
