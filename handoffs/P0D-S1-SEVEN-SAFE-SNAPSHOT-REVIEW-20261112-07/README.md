# P0D TRAP RAIDERS S1 — Seven-feature complete game review (NOT official release)

Date JST: 2026-11-12. Game `TRAP_RAIDERS`; work ID `p0d-siege-v19`; review-only release `P0D-S1-KIDS-RC01`.

## Frozen inputs / limits
- Official original protected RC: `1263a03701211a652b99b91d2339575dc8104eff`, `rc/p0d-s1-kids-rc01`. Only #220 sole `P0D-CHAT-INTEGRATOR-S1-RC01-B` can select and write this branch.
- Full six-feature original source review and genuine native/Rojo build GREEN: `65785c2e3b9bc37a6962f9ace128fbfcbb670901`. Genuine prior GitHub Actions run `43213277718` completed SUCCESS, 21/21 native compile, 37-file manifest, 21 Rojo XML scripts, 9 mutations; this history does not certify THIS new seven-feature code without its own CI.
- New original source feature #237 pinned delivery `6ed1e7e3585e26aff153c7c0c2be2fe68b459ff3`, candidate full `Game.server.luau` Git blob `36d1f90005fef0315011b600b07a6d13b89d2a72` derived from original RC Game, candidate full `FirstMinuteModel.luau` Git blob `d8dda6b1781375612c123f8c83b6f23fe45d09f1` derived from six baseline coach. Verified upstream native test157/157 positive +6/6 adversarial, upstream CI `43212920276`.
- Current entire actual 37-file complete game lives at `releases/P0D_S1_KIDS_RC01` on OWN `review/p0d-s1-v6-seven-safe-snapshot-20261112-07`. **Not** official game RC, not a published Roblox game, not proof of physical Roblox Studio/mobile/multiclient.
- New `Game.server` Git blob `e684ca79b8f5ed279bcdf033f4118bf77d552abb`, SHA256 `ce151d2b41026c454af4b7ac0954e67a0458d401498fbe487a4c9874f6346515`, UTF-8 30201 bytes; new `FirstMinuteModel` blob `d8dda6b1781375612c123f8c83b6f23fe45d09f1`, SHA256 `7ab192f4b1dc7a6ce6750d72ed57d4ed15a41cb85729025a043dd4b411b31d03`, 6331 bytes.
- Existing 37-file `BUILD_MANIFEST.json` updated for exactly those 2 Luau changes.

## Seven distinct safe improvements

1. Japanese child-readable castle / egg / delivery map labels.
2. Guardian first-minute beginner coaching.
3. Guardian trap touch button right stack, away from left native thumbstick.
4. Physical X/Z arena escape safe server-only egg drop + respawn + immunity.
5. D07 Host unexpected heartbeat status fail-closed, D07/D08 **still OFF**.
6. `PlayerRemoving` survivor count safe under both possible GetPlayers snapshot orders.
7. **New** server-only `snapshotUpdateId` advances at each original `snapshotFor` call; existing `SNAPSHOT` now carries `updateId`. Client-only Guardian `FirstMinuteModel` remembers `lastUpdateId`, rejects duplicate/stale same-serial or malformed/legacy packets after a versioned one; accepts legacy until first versioned snapshot. Existing Game/Coach original other bytes frozen. Does not control scoring or combat.

## Review commands

On a clean checkout of this immutable review commit:

```sh
python3 -B handoffs/P0D-S1-SEVEN-SAFE-SNAPSHOT-REVIEW-20261112-07/verify_seven_review.py
python3 -B -m unittest discover -s releases/P0D_S1_KIDS_RC01/tests -p 'test_*.py' -v
```

Automated own-branch review CI: `.github/workflows/p0d-s1-seven-safe-snapshot-review-native-rojo-20261112.yml`. Includes pinned real Rojo 7.7.1 unpublished `.rbxlx`, exact 21/21 source XML QA, **11** malicious XML mutation negative tests, pinned real Luau 21 source compiler, source/37-manifest tests, 14-day unpublished review artifact. **Do not claim CI pass until run job and logs establish success on exact commit**.

## Sole integrator intake and remaining blockers
Only #220 may INCLUDE_OR_SKIP after newest official RC CAS, complete seven-source Python/native/Rojo CI success, review of concurrent candidates, and final OWNER-directed genuine Roblox Studio 2 clients and mobile checks; game physics, egg return, quitting, Guardian HUD, packet delay, boss OFF all need honest receipts. Never treat staging approval as publication approval. Official S1 release score last sole audit **75/100** without increment from this preview. No main/RC/merge, live Roblox publication, paid features/spend, PC Codex, protected P0A/B/C/CAS or five existing automations touched.
