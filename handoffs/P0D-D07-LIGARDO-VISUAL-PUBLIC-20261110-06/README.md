# TRAP RAIDERS — D07 ライガルド（S2/S4）ビジュアル参照実装

This is an **independent client-only 3D visual candidate, NOT gameplay AI** and not a tested Studio prefab.

**Game:** TRAP_RAIDERS; **work_id:** p0d-siege-v19; **packet_id:** P0D-D07-LIGARDO-VISUAL-20261110-03.

## What is built

- `src/LigardoVisualPolicy.luau`: pure Lua/Luau one-event-per-round client lifecycle/anti-replay policy.
- `src/LigardoVisualBuilder.luau`: original angular electric-wyrm appearance using anchored non-colliding locally created Roblox Parts. 18 parts high detail / 14 parts low detail, no external assets, no Humanoid, no physics, no hitbox, no damage.
- `src/LigardoClientController.luau`: binds an existing server-authored visual RemoteEvent (assigned by PC integrator) and updates at <=12.5 Hz, cleans after TTL and explicit round-end.
- `reference/ligardo_policy.py`: executable independent oracle, unit tests in `tests/`, manifest and self-contained offline archive verifier.

**Design:** segmented blue/teal wyrm with a bright crown, forked lightning horns, four fins, and non-damaging glowing lightning bars during TELEGRAPH/ACTIVE. Phase warning is VISUAL ONLY: it is NOT the actual server hitbox and not proof of attack timing. No paid asset usage.

## Canonical event integration contract (PC integrator owns)

The first server-owned **single** v40 boss/event chooser must emit stage-specific event; on S2/S4 it may map existing canonical boss identifier (verify the real PC source spelling, do not assume it is `BOSS_LIGARDO`) into local-only public packet:

```lua
{ roundId="round77", boss="LIGARDO", stage=2,
  eventId="event-1", seq=1, phase="TELEGRAPH", remainingMs=9000,
  visualCenter=Vector3.new(0,0,0) }
```

Subsequent `ACTIVE` and `END` must share eventId with increasing seq; expiry and match-stop always remove the visual. No parallel event scheduler. `visualCenter` must be derived and clamped from the genuine server map, never a client-submitted position. The client validates finite/bounded coordinates, but cannot independently authenticate all game state. The PC integrator must check source and normalize the actual existing event name. Per this package there is NO `BOSS_LIGARDO` code written server-side.

Install the 3 `src/` Lua modules **only after** matching to the actual PC source. Put them as sibling ModuleScripts under a PC-owned LocalScript; call `require(script.Parent.LigardoClientController).mount(authenticatedBossVFXRemote, genuineRoundId, workspace, true, true)` (illustrative only; PC must verify RemoteEvent parent, lifecycle, local map and front-end). `.close()` on round end, disconnect, teleport or shutdown. Never use an untrusted arbitrary `remote` from a received payload.

## Security/QA gates

- This reference code is encrypted when delivered to PUBLIC GitHub. Key does not belong on GitHub, issue, Actions, automation or build logs.
- `python -m unittest discover -s tests -q` = offline policy/static/manifest tests; no Luau binary is currently available.
- Windows Codex must restore in private new directory, ZIP/manifest verify, inspect Luau syntax/API, smoke in unpublished Studio, 2/3 clients and mobile FPS, round-end cleanup and close PID, before any `STUDIO_QA_PASS` claim.
- v37 last saved Place QA, v39-H1 one-pack integration and v43-A dependency order have priority. Do NOT modify protected P0-A CAS or main, merge, Roblox publish, paywall, purchases, expenditure.
- Existing Gorogan S1/S3 visual, Gorogan AI S1/S3, D16 weather/scale/glide, other ChatGPT claim scopes remain untouched.
