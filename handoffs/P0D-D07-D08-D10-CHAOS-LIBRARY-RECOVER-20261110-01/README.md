# TRAP RAIDERS: v40–42 CHAT-LEAD fallback / reference code

**STATUS: independent reference implementation, not a cumulative v43 release and not Roblox Studio-verified.**

The historical v42.2 archive (`8b9fe213...`) is unavailable in this runtime. This packet uses a **new ID/hash** and never claims to be the historical original. Existing v42.3 remains a separate additive RoundEvidenceGate package, not bundled here.

Content:

- `ChaosEventCore.luau` (v40 boss/v41 weather scheduling): deterministic NORMAL 65 / BOSS 25 / WEATHER 10, 4 stages, no overlapping world events, 20-second minimum, telegraph and cleanup. No automatic effects or game decisions.
- `NeutralBossControlCore.luau` (v40/41): one neutral boss, 7 seconds of a safe **directional only** command from a server-validated relic/free tamer ability. No egg ownership, boss attack/stat manipulation or permanent combat advantage.
- `TimeSafetyCore.luau` (v41): safe 2-second **position only** rewind for a player not carrying the egg, requires real server position validator. Never rewinds HP, score, match clock, inventory, revives or persistence.
- `FairProgressionFallback.luau` (v42): separate **session-only** XP/7-job mastery fallback reference. XP max104/round; mastery max57/round. Level1–25, mastery0–5 cosmetics only. AFK, unauthorized and replay guard. **No DataStore and no v42.2 data migration.**
- `Smoke.server.luau` for isolated Studio manual smoke testing (NOT EXECUTED here).
- Python reference/test suite and verified manifest, plus public-safe shared seal/restore tooling.

The only permitted production integration is after the real Windows Codex has performed v37 final-SHA QA, verified the v39 packet and separately made an OWNER-reviewed decision about v43-A. Integrate v40 and v41 in small slices. Reconcile v42 against any recovered historical v42.2 file before choosing a canonical implementation; **never sum rewards from two ledgers**.

No public plaintext commercial code, main changes, Roblox publishing, payment, upgrades or unauthorized spending.
