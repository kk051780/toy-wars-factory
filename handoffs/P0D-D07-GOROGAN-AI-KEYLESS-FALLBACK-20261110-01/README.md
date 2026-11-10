# D07 S1 Gorogan AI: keyless clean-room fallback

Status: PUBLIC_SOURCE_V1 reference candidate, NOT Studio accepted.
Game: TRAP_RAIDERS; work: p0d-siege-v19.
Packet: P0D-D07-GOROGAN-AI-KEYLESS-FALLBACK-20261110-01.

This is a NEW independent alternative, not a decryption and not byte-identical to
legacy sealed Gorogan Server AI commit 80483ad6543fd73dfaf8a21ecf7b58dc2eca75e1.

The Luau module is inactive by default, has no Roblox service calls and does not
apply damage. Only a genuine server controller should beginRound and pass trusted
snapshots. The module emits TELEGRAPH then at least 2s later STOMP_INTENT with
max_damage 8, requiring a real one-time server AttackReceiptWindow/HP authority.
It never treats the intent alone as an attack receipt or damage success.

Integration rules:
1. Compare with the latest PC CHECKPOINT, v43-A, real S1 RoundCoordinator and
   existing D07 RigDriver, DamageBoundary and AttackReceiptWindow interfaces.
2. The PC adapter must own server-only target selection, clocks, stages and
   receipt idempotency. Never trust a client Remote for target, timestamp or HP.
3. Do not add a second event lottery, HP writer, boss AI, or scheduler.
4. Keep adapter DISABLED until owner-controlled isolated Studio tests verify
   a real S1 STOMP_RESOLVE receipt, 2 clients, warning, dodge, hit, rematch,
   landscape mobile HUD and Studio normal exit.
5. If the original author later republishes the exact legacy source as public,
   compare both branches separately; do not overwrite either source silently.

Offline tests are Python text-contract checks only; they do not execute Luau.
Existing v43-A and PC boss-rig passes are preserved and not claimed here.
No main modification, merge, Roblox publish, automation, or spend is authorized.
