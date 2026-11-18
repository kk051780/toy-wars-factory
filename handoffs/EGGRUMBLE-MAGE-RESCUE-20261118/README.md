# GQ8 / BATTLE-MAGE-REVIVE — lane8 independent source candidate (2026-11-18)

- FEATURE_ID: BATTLE_MAGE_RESCUE_20261118
- CLAIM: #765 lane8 ONLY. Reuse existing 7-role MAGE id, never add an 8th job.
- Base official RC: `261b75d0a7093db5c13db3b95dad9a2911f78689`
- Target: `rc/p0d-s1-kids-rc01`; authored only on `feature/gq8-mage-rescue-20261118-1218`.
- Source: `EGGRUMBLE_MageRescuePolicy.luau` — one pure decision/state module; no Humanoid write, RemoteEvent, new Game/Combat/Host, arena, money, persistent save or client-controlled authority.
- Original HP regen integration candidate #775 and its author #773 remain byte untouched. Existing mage heal/line-of-sight original #510 remains the sole real gameplay healing owner until B integrates lane8.

## Behavior (requires authentic server facts)
- Server-authorized MAGE may heal living current TEAM allies or BR self for 30% of *target* MaxHP, capped, cooldown 18 seconds. Full-health heals do not consume cooldown.
- TEAM-only MAGE may reserve one **protected-downed** living teammate for a 3-second uninterrupted channel. One reservation per target blocks simultaneous competing mage revives. Finish restores target HP to 35% of target MaxHP, cooldown 40 seconds, token consumed exactly once.
- Reject stale match epoch/avatars, caster not MAGE, eliminated castle, not current caster/target, cross-team targets, BR other-player rescue, dead Humanoid, >22 stud, wall obstruction, 60 second downed deadline, interrupted channel, double ticket.
- Deliberate **no fake resurrection**: existing official 31 may let Humanoid die at zero. Calling this pure module does not convert death into a 1-HP protected downed state. B must integrate a bounded, server-owned downed lifecycle into the existing single Host/Combat source before marking game playable. Do not merely add ModuleScript 32 and claim revive works.
- Channel cancellation must be invoked by the server on move/attack/stun, range or LOS loss, role/round/character change, death, target recovery, or player exit. Periodically rerun live facts at commit.
- Caller must apply the returned numeric HP on the server atomically with the finish token; channel result is a **decision**, not a server-authority substitute.
- Token and cooldown are ephemeral round state; create a new state per match epoch. No extra write to Store.

## Evidence gates
1. This branch includes a source-derived *real* native Luau VM harness, exhaustive happy path and negative tests, intentional zero-second channel mutant expected RED.
2. Candidate native test success is not a 31/32 canonical source compile; current official V3 has exactly 31 selected scripts and gameplay integration is **NOT_YET_DONE**.
3. B #220 only may compose genuine current31 -> existing Combat+Host (single healer and protected-downed owner), attach this policy as one new ModuleScript, native ON/OFF, Rojo Source/Class, rollback byte exact, sameHEAD Actions, and non-force expected-SHA CAS. Re-fetch latest formal SHA first. Do not reuse old original #482 Game as a second authority.
4. No author's personal ACK needed. No main modification, merge, Roblox Publish, paid features, unapproved spending or protected RC direct writes by this lane.
5. YELLOW: high HP regen #775 composition must be reconciled with MAGE 30% active heal; downed interception + true native/Studio trace must verify double-fire, DOT, anti-spam, and resurrection timeout. Flag OFF must be the genuine original31.
6. ART/MOBILE/FUN/OWNER_ACCEPTED = NO_GO until real 2-client Studio, low-end Android 15m, and first 3-minute FUN evidence.

## RC progress rubric for successor
- Pure policy source + native negative tests: preparation.
- Server-owned downed capture + active MAGE inputs wired through one existing Combat/Host: gameplay runtime.
- Same-HEAD native/Rojo + OFF31 rollback + formal CAS/readback: official **private** RC intake.
- Real play/Android/FUN: human acceptance, never inferred from CI alone.
