# QA — D07 Ligardo AI

- `game_id=TRAP_RAIDERS`, `work_id=p0d-siege-v19`, `packet_id=P0D-D07-LIGARDO-SERVER-AI-20261110-04`.
- **Local Python unittest:** `90/90 PASS`. Includes pure-logic invariants, 9 seeded randomized scenarios with 1,071 sequential ticks total, server-authorized replay/damage cap, external team revalidation, cooldown, event mismatch, time regression, duplicate player IDs, archive integrity and unsafe ZIP path negatives, static Luau review checks.
- **Local Luau compilation:** `NOT_TESTED` (no Roblox/Luau executable available in this ChatGPT runtime).
- **Actual Windows PC restore/real PC source SHA:** `NOT_TESTED`.
- **Roblox Studio integration/2client/mobile QA:** `NOT_TESTED`.
- **Studio normal exit:** `NOT_TESTED`.
- **Real physical boss AI/hitbox/damage:** `NOT_IMPLEMENTED`.
- **Known risk:** AI `s.pos` tracks proposed moves rather than Roblox Model's actual position; damage adapter refuses if live boss is >2 studs away. Adapter's one-use ledger must be kept live across the round and existing damage pipeline must independently guarantee exactly-once application, even after engine restarts. Real team/event strings and interaction with Gorogan must be checked in PC source. Python static shape tests are not a Luau parser.
- **Security:** no client Remote authority. P0-D originally public repository; ZIP/Luau are PRIVATE, GitHub receives ciphertext JSON and a public-safe README only. 
