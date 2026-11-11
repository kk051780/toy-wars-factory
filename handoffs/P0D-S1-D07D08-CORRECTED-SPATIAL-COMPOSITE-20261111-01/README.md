# P0-D S1 — corrected D07/D08 + actual spatial STOMP source composite

**TRAP_RAIDERS / p0d-siege-v19 / 2026-11-11 JST**  
**STATUS: CHAT_BUILD_READY (source only) · Roblox Studio NOT_TESTED · owner publication NOT_APPROVED.**

## What was actually assembled

This is one standalone `candidate/` Rojo project with **27 manifest-listed source/project/docs/test files** and **18 actual Python-assembled source/project units**. It builds on the prior genuine S1 Game, approved original D07 Gorogan physical code, original v40 + D08 event chooser, exact original policy for client STOMP danger ring, and includes both independent corrective Host/Binding modules.

This is the FIRST composite delivery from this lane with ALL THREE of:
1. The real Game and HUD candidate plus one existing TrapRaidersS1Remote and one match/egg/damage/event owner.
2. True server-sent `START`/`STOMP` positions and a passive local-only eight-segment danger ring at the actual STOMP center, no duplicate giant rig or client damage.
3. Two independent source corrections from the other author: studio test negative UserId canonical roster resolution and authenticated successful D08 NORMAL/BOSS terminal completion (no false D08_FAILED on same epoch). Only the exact two source modules were copied from the original review overlay.

One additional local-client replay bug was fixed: after a correct D07 END or TTL expiry, the same round's `lastEventId` is retained, so a delayed or replayed START cannot resurrect the warning. Only a fresh server serial or non-ACTIVE phase resets this lock. The original `GoroganVisualPolicy.luau` remains byte-for-byte intact.

### Provenance

| Component | Immutable source |
| --- | --- |
| Original initial S1 Game | `35d7d0525388e885aac8281eff2315a59831e0cf` |
| Earlier complete spatial ring candidate | `1d95be29c72067d91db5e4e14f87515fa628e4da` |
| Independent corrective 2-module overlay | `53e4db1972478026a0630f5b901f6869d69df8c6` |
| Rebuilt 27-file GAME source manifest and pinned assembler source | `0771491241c4402881a10deb118ca2146a9b2142` |

The full overlay source packet is replicated at `overlay-source/` by immutable Git blobs, including its **previously not-run 34-case Python test suite**, for independent reproducibility. All other original D07/D08/v40/AI/rig/damage modules are unchanged from the earlier source candidate.

## Actual offline testing (not simulation and not Studio)

[Passing GitHub Actions actual CI run](https://github.com/kk051780/toy-wars-factory/actions/runs/43030100583)

- **80/80** original S1 Python offline gameplay regressions: PASS.
- **46/46** candidate S1 Game single authority, local D07 ring, and exact composition regressions: PASS.
- **34/34** independent overlay author's original previously unexecuted Python cases: PASS.
- Total **160/160** executable Python unit checks PASS, tested on the SAME actual composite game source branch. They are source/logic contracts, NOT native Luau runtime or Roblox physics.
- **27/27** actual game source/project/docs/test hashes passed the original official `P0D_PUBLIC_SOURCE_V1` source verifier; strict manifest SHA256 `ab69ec5a7b21f43a761ee2d371c2e988133bdadbd8548ea2918eb0da7d0d65fc`.
- **6/6** original overlay source/docs/test hashes also passed independent public source verification; strict manifest SHA256 `31d97e8f862a2277bf6bf8dea4866540ed40120ce04b1a6bdcd27530e8960575`.
- The original Python `chat_rc_assemble.py` actually assembled **18/18** real Luau/project files into a temporary source output, verified each byte length+SHA256 and `CHAT_RC_RECEIPT.json` plan hash. The resulting immutable Python receipt is stored at `CHAT_RC_RECEIPT.json`, SHA256 `93e0964d6ff7ffad8ee79c58116574c486435c71652bba38cbe94f8e1e665cf9`. Source pinned in `SOURCE_PLAN_CORRECTED.json` to commit `0771491241c4402881a10deb118ca2146a9b2142`.

Reproduction in a clean clone of this handoff branch:

```sh
python3 handoffs/P0D_PUBLIC_SOURCE_HANDOFF/tools/p0d_public_pack.py verify \
  --root handoffs/P0D-S1-D07D08-CORRECTED-SPATIAL-COMPOSITE-20261111-01/candidate \
  --packet-id P0D-S1-D07D08-CORRECTED-SPATIAL-COMPOSITE-20261111-01
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s handoffs/P0D-S1-D07D08-CORRECTED-SPATIAL-COMPOSITE-20261111-01/candidate/tests -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s handoffs/P0D-S1-D07D08-CORRECTED-SPATIAL-COMPOSITE-20261111-01/tests -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s handoffs/P0D-S1-D07D08-CORRECTED-SPATIAL-COMPOSITE-20261111-01/overlay-source/tests -v
python3 handoffs/P0D_S1_SOURCE_PLAN_SNAPSHOT_20261111_01/tools/chat_rc_assemble.py \
  --plan handoffs/P0D-S1-D07D08-CORRECTED-SPATIAL-COMPOSITE-20261111-01/SOURCE_PLAN_CORRECTED.json \
  --source-root handoffs/P0D-S1-D07D08-CORRECTED-SPATIAL-COMPOSITE-20261111-01/candidate \
  --out /tmp/p0d_d07d08_corrected_spatial
```

Compare resulting receipt bytes with the fixed `CHAT_RC_RECEIPT.json`. Avoid an existing output directory.

## Sole #220 integrator acceptance and limitations

**This is NOT the protected release RC**; owner RC remains an unchanged initial S1 SHA until the exclusive #220 editor adopts sources. Do not merge entire author branch: compare source/game changes against the integrator's actual latest Game and independently selected other lanes.

**Two independent source booleans remain hardcoded OFF** in `candidate/src/server/Game.server.luau`:
`CANONICAL_S1_ENABLED = false`; `D07_D08_RELEASE_REVIEW_APPROVED = false`. Thus, no genuine boss is activated in this source until the owner independently approves native/Studio acceptance. Do NOT treat source CI green as final Roblox gameplay QA.

Critical remaining release work:
- Full native Luau parse, Roblox Studio 2-client and mobile QA with real D07 AI/physics/damage/respawn/LOS/negative UserIds, ring on actual center, visual telegraph latency, real round cleanup and normal exit are **NOT_TESTED**.
- D07 server telegraph is 2s but a late client packet can show fewer than 2s; its local ring does NOT grant immunity or change HP and cannot certify fair reaction time.
- D08 original v40 classifies **10% WEATHER** without an approved S1 weather handler, currently fail closed; no fake weather mechanic promised.
- Original D07 physical 14s vs D08 17s event duration needs real matched cleanup and source-native acceptance.
- S1 recovered epoch rejects serial >=1024; requires an independently reviewed long-running server strategy.
- Separate source lanes' lobby team rebalance, D15 traps, D11 neutral NPC, first minute tutorial/mascot and other gameplay are **not falsely represented as integrated here**. The sole #220 integrator must do the final source selection/composition.

Before owner final Windows Studio QA, #220 should choose source packs, create a NEW fresh complete game SHA and strict manifest plus assembly plan/receipt for that selected final RC, and request independent whole-game static+dynamic QA. PC Codex remains reserved for end-to-end Roblox Studio verification, then separately authorized public game release. No main/RC writes, merges, Roblox publish, paid services, P0ABC CAS modifications or five existing ChatGPT automations were performed.
