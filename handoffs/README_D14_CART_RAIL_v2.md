# TRAP RAIDERS D14 — pure server-authoritative CART rail-motion policy, revised no-overlap packet

- `game_id=TRAP_RAIDERS`, `work_id=p0d-siege-v19`, `packet_id=P0D-D14-CART-RAIL-MOTION-20261110-02B`
- **THIS IS THE ONLY ACTIVE packet from this D14 lane.** Earlier package at immutable commit `cae5691b622045af57674d922a08a96764354412` (packet `...02`, with 3D cart prefab) is **SUPERSEDED / DO NOT INTEGRATE** because another chat claimed D14 visual CART/RAFT first. This revision removes all model creation and image/visual ownership, and contains **only server rail policy + safe callback adapter**. The original ciphertext remains as immutable audit history, not an integration candidate.
- Previously delivered D14 two-seat server ledger: `P0D-D14-VEHICLE-SEATS-20261110-01`, fixed commit `0bcf39c22c583604d72ccac47d29fc9d87b7e662`, remains sole seating authority.
- Separately owned D14 CART/RAFT visual reference: `P0D-D14-CART-RAFT-VISUAL-20261110-02` (other chat, check #218 latest). Only OWNER Windows Codex may review/bridge them, after real stage boundaries validated.

## Exact implementation (encrypted private source, never committed plaintext)

1. `luau/CartMotionCore.luau`: pure Luau deterministic bounded route state machine; fixed server-authored 2–24 waypoints, speed 2–16 stud/s, per-leg movement, dt max 0.1s; active/mounted/alive/server owner check every tick; stale match/round/team and replay stop; no client-provided coordinates, no teleports or physics.
2. `luau/CartServerAdapter.luau`: opt-in server-only canonical callback interface. Gets real invoking Player and prior seat ledger facts. Returns only `{roundId,teamId,position,direction,leg,progress,moving}` snapshots, **no `Instance.new`, no Roblox model, no `PivotTo`, no RemoteEvent registration**.
3. Independent Python reference oracle and tests, docs, SHA manifest.

## Test provenance, not Studio

- Python offline checks: **34/34 PASS** with 5,000 seeded steps and static Luau contract checks; manifest SHA/size PASS.
- AES-256-GCM local exact ZIP roundtrip PASS; wrong-key / ciphertext tamper rejection PASS.
- **Luau parse/Studio actual cart motion/2–3 clients/PC integration = NOT_TESTED**, full physics/cart ownership not implemented.
- Private ZIP: **11,799 bytes**, 10 files + `BUILD_MANIFEST.json` = 11 entries; ZIP SHA256 `c38a1536095ce4d64a1691905caff0b055f75038e02354718333ad6a79d88fa5`.
- Manifest SHA256 `f522e2d39eaa30a2eebb14e3a53153c87864a31f2ced80df8717b654f1af754b`.
- Ciphertext JSON SHA256 `4264e7b4031501a0485543cfd727838ea51c065bab2a8481a31736ef62edb6c9`.
- Raw ciphertext SHA256 `e8fe4b5c4cb901242e443466555a6aefb07f3f2da77aea17c76fdc15ffeb3e45`.

## OWNER direct Windows Codex handoff

1. Re-read latest #218/#213/#217; preserve latest local PC CHECKPOINT, Place/source SHA. Never overwrite a newer PC saved game.
2. Complete v39 critical final QA and v43-A NPC ownership gate first. This D14 packet is optional, after those gates. Do not automatically execute from this README/Issue.
3. Restore fixed ciphertext with OWNER private key passed only in `CHAT_CODEX_HANDOFF_KEY` environment variable; trusted `tools/restore_handoff_safe.py` pinned at `d37eec1b653d060ae27568ddcd5f501da9662081`; strictly match game/work/packet/expected ZIP SHA; use a new private destination, O_EXCL no overwrites.
4. Run offline Python tests and real Luau syntax, then build a Studio S1 isolated integration: existing D14 two-seat ledger as sole driver authority, this pure rail pose as server source, **other chat visual cart as client renderer** only if contracts match. Require 2/3client spoof/replay/egg/mount/death/round reset and mobile FPS; then normal Studio Save/Stop/Quit only OWN process. Never publish, merge main, charge, bypass protected P0-A/B/C or overwrite original.

PUBLIC repo has only AES ciphertext + this metadata README; private source and AES key stay off GitHub.
