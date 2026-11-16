# GQ-V3-STATUS-TICK-FENCE-20261116-01

## Non-overlapping, verified game defect

Original V3 #482 `EGGRUMBLE_SevenRoleCombat.luau` schedules three `BURN_3S`/`PREDATOR` server-side damage callbacks. Each delayed tick checks only `Humanoid` existence/HP and `session.rules.phase=="ACTIVE"`. The target's castle can be eliminated while the opposing TEAM/BR arena remains active, leaving a former combatant susceptible to a later tick. The callback also lacks explicit original Humanoid identity and round-reference validation. This lane is only the **delayed status-damage safety** repair; it does not duplicate existing 7 jobs, geometry, instant damage, score, defense, AI, item, field, lobby, visuals, sound or other QUALITY PRs.

## Implementation / rollback

- `EGGRUMBLE_StatusTickFence.luau`: pure Luau fail-closed policy requiring same round reference, active/winner-free phase, original target castle alive and identical registered target, same original bot or player Humanoid identity, live Humanoid.
- `EGGRUMBLE_SevenRoleCombat.patched.luau`: one existing server combat source copied into a **generated-only overlay**, with six unique-anchor modifications. Original author source remains unchanged.
- `tools/compose_private22.py`: original 21-source project (fixed #482 SHA) + 20 byte-identical author scripts + one combat overlay + policy = 22 mapped scripts. Emits `project.json` and SHA256 receipt; does **not** write original project/branch or official RC.
- Native VM policy tests and Python source-contract/composition tests; PRIVATE Rojo source-exact artifact CI. CI is source verification, NOT gameplay Studio/Android verification.

**Scope exclusions**: #505 server SkillFX quota, #503 client VFX, #499 end-of-match timeout, #508 neutral death credit, #489 item fairness, #500 castle defense, #506 respawn shield, #487 score, #484 compositor, #482 original author. These files and mechanics are not changed.

**Adoption**: #482 original game author reviews exact source delta, #484 latest 26/27-source composition performs source-selective repair, then only authenticated #220 can non-force-CAS select into current formal RC, same-HEAD native/Rojo/ZIP/Place SHA and SourceLock receipt. After that Studio TEAM/BR, Android15min #420 ART/FUN, and OWNER acceptance. No duplicate engine, no main/merge/Roblox Publish/paid switch/PC execution.

**Rollback**: omit this lane's one combat overlay and helper source mapping; the original #482 combat source remains unchanged. `CLAIMED_SOFT / SOURCE_QA_PENDING / OFFICIAL_RC_ADOPTED=NO / STUDIO_NOT_TESTED / ANDROID_NOT_TESTED / OWNER_ACCEPTED=0`.
