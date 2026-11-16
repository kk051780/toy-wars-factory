# GQ HUMAN STEALTH PvP — isolated exact-source candidate (2026-11-16)

**State:** SOFT_CLAIM_REQUEST_NOT_GRANTED / PRIVATE SOURCE ONLY / NOT official RC / NOT OWNER accepted.

Original author: #482, fixed HEAD `fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9`, exact `EGGRUMBLE_SevenRoleCombat.luau` Git blob `66e666418b7c23d41f87faa5d61eb6e2770a463e`. Source lock aborts on original drift.

## Independent defect and minimum actual code repair

The existing V3 bot targeting already respects `EGGRUMBLE_StealthUntil`; #502 separately fixes bot attacks on egg carriers. The **two human-target loops** in the original SevenRoleCombat do **not** consult that attribute:

1. `hitHumanHeroes`: opposing humans can inflict direct PvP damage through an active three-second Assassin stealth.
2. `secondaryEffect`: opposing humans can apply stun/slow/mark/burn through the same active stealth.

This candidate adds one reused pure server condition, `humanCombatTargetable`, to these **two existing** loops only: hidden empty-handed targets evade both attacks and debuffs until stealth expires; `session.rules.castles[UserId].heldEggs > 0` (authoritative source) makes the carrier targetable immediately. Normal opponent detection, walls, mode separation, team filtering, damage, cooldown, role identity and player elimination remain unchanged. This mirrors #502 intent **without editing BotActors or creating competing combat/egg ownership**.

## Reproduction, tests, rollback

```sh
python3 -m unittest discover -s quality_gameplay/v3_human_stealth_pvp_20261116 -p test_source_contract.py -v
python3 quality_gameplay/v3_human_stealth_pvp_20261116/build_candidate.py --patched /tmp/Combat.luau --fixed-harness /tmp/fixed.luau --original-harness /tmp/original.luau
```

CI compiles **all 21** original V3 Luau source mappings including this one candidate overlay, executes actual source-extracted human damage+status functions against the original negative repro and 12 corrected native cases, builds an unpublished `.rbxlx` and checks all 21 embedded script sources/class kinds byte-exact. All 20 other author scripts remain identical; no new Game, Remote, score, ART, field, castle, neutral, item or lobby source.

**Before author acceptance:** source-native and private Rojo tests are *necessary, not sufficient*. This isolated branch never touches main, official RC, Studio, Android, Robux purchase or Roblox Publish. Manual two-client TEAM+BR tests, #420 art/mobile/FUN and OWNER acceptance remain open.

**Source-selective integration:** #482 original gameplay owner evaluates overlay; #484 composition consumes one **combined Combat**, not competing whole PRs. #510 MAGE, #516 DOT, #524 warp and this candidate all edit one original Combat source; combine and re-run real same-HEAD Native/Rojo/Studio tests **before** #220 sole authenticated official RC CAS. If no consensus/approval: **rollback** by selecting original author Combat and omitting this overlay; never merge the full stacked PR.
