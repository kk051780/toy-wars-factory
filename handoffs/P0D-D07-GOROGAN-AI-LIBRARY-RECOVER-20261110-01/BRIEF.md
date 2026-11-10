# TRAP RAIDERS D07 Gorogan server AI – reference packet

- 1 neutral boss per round, only canonical `BOSS/GOROGAN` for S1/S3.
- Bounded 14s active segment inside the existing v40 17s event window; 2s visible attack telegraph; max 3 attacks, 8 server damage per target each at true impact, 7-stud radius, after a genuine server LOS/ground/safe-zone check. No permanent levels or paid combat buffs.
- Deterministic closest player arbitration with tie ID (BLUE/RED symmetric); bounded chase intentions and 42-stud leash; no teleport or NPC spawning from pure core.
- Full isolation from D13 guard AI, D15 traps, D16 weather, v39 stamps and v42 XP. Public GitHub stores only AES-GCM ciphertext and generic documentation.
