# P0D S1 — D07 spatial STOMP warning, exact source candidate

Game: `TRAP_RAIDERS` / `p0d-siege-v19` / `P0D-S1-KIDS-RC01`.
**STATUS: source-ready, both original D07/D08 activation gates FALSE, NOT
real Studio-tested, not cleared for public release.**

## Fixed actual source defect

The earlier real Game+HUD candidate
`4b66dd8a9b34a45cf12e58684e0e4372df3f8b07` connected the original
GoroganCombinedRuntime `START` and `STOMP` packets to the existing
`TrapRaidersS1Remote`, but **discarded the genuine server-origin
`packet.position`**. The HUD could display a text-only stomp warning;
clients had no actual world attack center for a local ring.

This candidate provides the full 27-source/docs/test-file project under
`candidate/`. The ONLY game source changes from the previous patch are:
- `src/server/Game.server.luau`: forward sanitized trusted original
  `position={x,y,z}` and `stageId="S1"` in existing
  server-to-client `BOSS_VISUAL` packets, requiring a valid point for
  `START` and `STOMP`. Reject NaN and out-of-range points.
- `default.project.json`: explicitly mount two NEW client siblings
  beside unchanged HUD: original `GoroganVisualPolicy` ModuleScript
  and new `S1GoroganStompRing` LocalScript.
- `src/client/GoroganVisualPolicy.luau`: exact original public Luau Git
  object from `e9b0a7496a69bda3e0e6527ff4d112d50cf70e80`,
  no rewrite or second original visual-policy fork.
- `src/client/S1GoroganStompRing.client.luau`: a NEW passive client-only
  visual adapter. Reuses existing S1 Remote and the original policy
  replay/epoch/3-STOMP safety rules; receives the server's actual
  `STOMP` center and renders at most eight local anchored, noncolliding,
  nonquerying, nontouching red ring segments for the time still available
  from the real server timestamp. Periodic 0.1s cleanup, no new
  RemoteEvent/FireServer, no damage, rewards, AI, persistence, or
  second physical boss model. The original D07 physical rig is already
  server-generated, so duplicating the full giant locally is avoided.

The core original S1 map, egg/HP/role/combat, recovered v40/D08 and
D07 AI/rig/damage/receipt, previous original Host+Binding remain EXACTLY
as in the earlier opt-in candidate. All 27 immutable source files are
covered by a strict canonical `P0D_PUBLIC_SOURCE_V1` manifest.

## Genuine offline evidence

Read-only independent GitHub Actions:
https://github.com/kk051780/toy-wars-factory/actions/runs/42995056163

- Actual original/candidate game 80/80 Python tests: **PASS**.
- Previous D07/D08 single-authority Game source checks 18/18: **PASS**.
- New visual exact-source/replay/epoch/ground-ring negative contracts
  18/18: **PASS**. Total 116/116 Python tests.
- Original official `p0d_public_pack.py verify`: PASS for all
  27 source files, original strict 6 manifest root keys;
  checksum `11cf5c33c8f44d3fc4ea8a123a2ad3135039208a2b8ff841167efe9a5bd7cfd4`.
- ACTUAL Python Chat release assembler ran on **18** real source and project
  units (game, HUD, original D07/D08 modules and new ring adapter), all
  output source bytes SHA256 verified. Actual receipt
  `CHAT_RC_RECEIPT.json` SHA256:
  `59a43cc343f29abf3c79fa6285b3ec84cb363e2c72941605be954f2bbd8b5eed`.
- Assembly uses `SOURCE_PLAN_SPATIAL.json` with exact source commit
  `c7d93a955b146698dd7218f261dd3d1eac589a6a`.
  The manifest, plan and receipt were read back from the isolated GitHub
  branch. CI does NOT execute Roblox/Luau native engine, physics or 2 clients.

## Standalone reproduction

```sh
python3 handoffs/P0D_PUBLIC_SOURCE_HANDOFF/tools/p0d_public_pack.py verify \
 --root handoffs/P0D-S1-D07-SPATIAL-STOMP-RING-20261111-01/candidate \
 --packet-id P0D-S1-D07-SPATIAL-STOMP-RING-20261111-01
python3 -B -m unittest discover -s handoffs/P0D-S1-D07-SPATIAL-STOMP-RING-20261111-01/candidate/tests -v
python3 -B -m unittest discover -s handoffs/P0D-S1-D07-SPATIAL-STOMP-RING-20261111-01/tests -v
python3 handoffs/P0D_S1_SOURCE_PLAN_SNAPSHOT_20261111_01/tools/chat_rc_assemble.py \
 --plan handoffs/P0D-S1-D07-SPATIAL-STOMP-RING-20261111-01/SOURCE_PLAN_SPATIAL.json \
 --source-root handoffs/P0D-S1-D07-SPATIAL-STOMP-RING-20261111-01/candidate \
 --out /tmp/p0d_s1_spatial_assemble
```
Compare the resulting `CHAT_RC_RECEIPT.json` with the immutable one in
this packet; the output directory must not already exist.

## Required future #220 sole-integrator review

1. This is a **candidate** based on an earlier Game source, not a patch
   applied to the protected current RC. The sole #220 integrator must
   compare its latest Game/HUD/Project and select or skip these exact
   three source changes. Do not merge the entire handoff branch.
2. The original `CANONICAL_S1_ENABLED` and
   `D07_D08_RELEASE_REVIEW_APPROVED` are still both FALSE. Nothing
   actually spawns a boss in the playable RC from this packet alone.
3. Independent static QA has already found TWO separate pre-existing
   Host/Binding issues, from #220 issuecomments 6791732698 and
   6791758548 (Studio negative test UserIds and terminal D08 cleanup).
   Another source author claimed a correction overlay on #218 comment
   6791952419. Resolve/verify that overlay in the REAL combined RC
   **before** enabling; this spatial-only lane does not overwrite it.
4. The effect cannot guarantee a minimum full 2-second client reaction
   window under network latency: the server-owned D07 attack window
   still controls actual damage. Test measured visible notice and hit
   safety with 2 clients in native Studio. If insufficient, change
   server-owned telegraph safety design with authority review; never
   grant immunity/damage from a client visual.
5. D07 physical TTL 14s vs original D08 event 17s, original 10% WEATHER
   without approved handler, event epoch >=1024 and remaining D11/other
   features still require #220 final game integration decisions.
6. After integrating new changed source, regenerate final full strict
   source manifest, actual pinned assembly plan and Python receipt, run
   independent static+dynamic QA, and only then OWNER-direct the
   Windows Codex final Roblox Studio 2-client/mobile and normal-exit
   gate. Separate OWNER approval is required for live release.

Protection: no writes to `main`, `rc/p0d-s1-kids-rc01`,
other lanes/automations, no merge, publication, paid operation or PC
Codex action.
