# GQ822 — Real44 direct-damage coverage, not invulnerability implementation

Feature: GQ822_ACTUAL44_DIRECT_DAMAGE_ROUTE_COVERAGE_20261119
Original owner directive: #822. Separate source-only policy implementation: #823.
Current live gameplay source authority: existing #815, original weather42 #796.

This isolated **read-only quality gate** identifies all direct Humanoid:TakeDamage
call sites from the actual original-source private 44-script Studio Place
of #815 (run 44376856212). It checks 44 source files, the real Place
SHA, every known damage call exactly once, and four malicious mutants:
duplicate call, replaced direct HP write, hidden extra TakeDamage,
and removed Combat source. Produces a JSON receipt with victim category and
original source SHA256. Missing or new damage routes RED before anyone claims
coverage. Run with --require-wired intentionally REDs: invulnerability
is **not connected** to real game sources.

Important: direct TakeDamage coverage is NOT a proof of all damage,
status, environmental elimination or knockback handling. The new #823
InvulnerabilityPolicy is pure source and cannot make human damage zero until
the same authenticated original damage/CC owners consult it before harm.
Do not use ForceField alone to certify direct Health assignments, DoT,
storm, Boss, all PvP or status. The report does not grant gameplay completion.

Eight-domain coexistence:
- CHARACTERS: original seven roles retained, no new role/HP authority
- FIELD: weather42 land/sea/air source unchanged
- BATTLE: list direct server damage sites, no duplicated hit loops
- CASTLE: existing siege+guard routes accounted for
- NEUTRAL: current #815 singleton Swarm and original NeutralFinisher/Curse kept
- ITEM: original #796 3D HEAL/DASH/SHIELD kept, no second Item
- LOBBY: existing two modes untouched; no commerce source
- BALANCE: current cooldowns preserved; new invul budget needs true engine wiring

The CI source artifact and report are PRIVATE, not the official RC or a
Studio 2-client, Android FPS, ART or child-FUN acceptance. Certified #220 B
must later make the actual single-source invulnerability bridge and verify
all 7 roles × 3 activation routes × TEAM/BR × DoT/boss/weather/PvP/status,
source-lock and rollback with non-force expected SHA CAS and official same-HEAD
readback. No previous original author ACK needed. No main, Publish, Robux or expenses.
