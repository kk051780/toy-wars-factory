# BATTLE-HP-REGEN / #765 lane 7 / Source PREP, NOT active RC
Base observed official RC: `261b75d0a7093db5c13db3b95dad9a2911f78689` (2026-11-18 08:10 JST).
Exclusive file scope: this directory and `.github/workflows/p0d-gq8-hp-regen.yml`.
Feature ID `BATTLE-HP-REGEN` (not #766 element policy, #764 RealmCore, #770 bridge, #768 balance QA, or mage-revive).

## What the actual Luau policy does
- Known stable seven role IDs only: WARRIOR 250, MAGE 195, NINJA 185, TRAPPER 205, BUILDER 225, BEAST 220, ZOMBIE 230 MaxHP.
- Observe actual **server Humanoid HealthChanged loss** rather than an untrusted client attack request. Existing healing, blocked hits, shields or missed damage cannot fake the last-damage clock.
- Regenerate no sooner than 7 seconds after the last actual health loss (including burn/DOT ticks), at 0.7% of current authoritative MaxHP per second; clamp to MaxHP and each server step to 0.25 seconds (no AFK lag burst).
- Hard refuse inactive/stale character or match, DOT, downed/dead, NaN/infinite numbers, nonpositive step. Returns a numeric *suggestion*, never changes Humanoid or Store and never creates secondary HP/Remote authority.
- Does **not** modify mage special heal, mage revive or any Game/Combat/Host source. Those belong to lanes 8 and 10.

## Required actual integration by sole #220 RC writer
1. Fetch latest 40-char official RC HEAD; keep existing 31 game scripts byte-exact on flag-OFF, no new Combat writer. Source from this feature must be revalidated at fixed SHA.
2. Within existing **server** HP owner, assign initial MaxHP only on validated current avatar spawn and current stable role; ensure new character/session creates fresh `lastDamageAt`. Observe **all** HealthChanged HP reductions from PvP, AI, boss and environment; do not accept a Remote-provided timestamp.
3. The existing HP owner calls `regenDelta(current Humanoid.Health, Humanoid.MaxHealth, os.clock(), lastDamageAt, delta, rules.phase=="ACTIVE", current-session+same-avatar, current DOT flag, downed)` on a bounded server tick and applies only positive delta if identity/session is unchanged; per-tick recheck to avoid delayed resurrect or postmatch heals. Initial `lastDamageAt` is the spawn time (no immediate regen). Unknown role => no stats overwrite.
4. Preserve MAGE active heal and downed/respawn lifecycle; no NPC/neutral/castle healing. Add real native callsite tests, same HEAD full 31+native and Rojo Source/Class, ON/OFF invariant/rollback and official artifact receipts. Cross-check 7-role TTK in studio, including DOT, late-join, respawn, TEAM/BR, disconnect, and stale avatar.
5. Only #220 sole writer may do non-force expected-SHA CAS update to formal `rc/p0d-s1-kids-rc01`. Do not self-merge a candidate PR or touch main/publish/paid systems.

## Reproducible source test
`python3 -B handoffs/EGGRUMBLE-BATTLE-HP-REGEN-20261118/make_native_tests.py --out /tmp/gq8-hp-regen` builds good + intentional delay-removal mutation from **the real Luau**. The dedicated workflow pins Luau `f46d879...`, compiles actual ModuleScript and executes live Luau across seven roles, 7s threshold, DOT, phase/current avatar, downed, over-heal, clock/NaN, health-loss-only timestamps and bounded server frame. Mutant MUST fail.

**No studio, Android, mobile FPS, art, FUN, official RC integration or OWNER ACCEPTED claim at PREP stage.**
