# EGGRUMBLE V3 / GQ-ZOMBIE-COMMAND — unique SOURCE candidate

**Scope:** `quality_gameplay/v3_zombie_command_20261116/**` and its own native QA workflow. Original #482 HEAD `fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9`. Fixed starting official RC31 HEAD `cd3e95bd7c53e9320d85bf950d12f50bf2df2bcd`. The official RC branch, its 31 selected sources, author branches and main are **not edited** by this PR.

## Why this is separate rather than a duplicate

The #482 SevenRoleCombat ZOMBIE skill C uses three temporary `makeEffect` puppets and three delayed player-centred `blast` callbacks, not autonomous minions with orders. #526's catalog gap identifies missing commandable ZOMBIE AI. Search of current game-quality PR titles found no existing ZOMBIE command implementation. #533/#541 neutral melee and #555/#536 enemy bot AI are **not** rewritten; they remain different actors and owners.

This PR introduces a **server-only opt-in minion squad**, keeping the one existing original damage/score/HP authority:

- `EGGRUMBLE_ZombieOrderPolicy.luau`: FOLLOW/GUARD/FOCUS, three-unit cap, 14-second expiry, 48-stud acquisition, short-range 6-damage *permits*, per-unit and squad cooldowns, epoch/mode/owner-alive filtering, ally and old-match rejection, LOS requirement, cleanup.
- `EGGRUMBLE_ZombieSquadRuntime.luau`: actual Roblox Model/Humanoid minions and `MoveTo`, server network ownership, 0.25-second evaluation, cleanup on avatar replacement / round exit. All strikes go through injected existing-author `opts.hit`, which **must recheck authority** before changing HP/KO/score.
- Native Luau tests and isolated workflow. No new RemoteEvent, round controller, DataStore, damage service, reward service, or alternative score authority.

## Eight-domain effects / what remains owned elsewhere

| Domain | This slice | Existing owners unchanged |
|---|---|---|
| Characters | ZOMBIE summon/command policy, not an eighth class | #482/#530 seven roles |
| Field | Humanoid movement and no teleport; runtime navigation still requires Studio validation | #485 field / #536 navigation |
| Battle | Conditional hit permit only; existing callback validates the actual damage | #529/#530 Combat |
| Castle | ownerAlive guard stops squad after castle elimination | #537/#547 castle |
| Neutral soldiers | Can target a current-mode neutral through authorised callback | #533/#541 Swarm |
| Items | No item claims, consumptions or cooldowns | #489, candidate #517 |
| Lobby | No change to TEAM/BR, class-selection or opt-in | #539 |
| Balance | cap 3, lifespan 14s, 6 damage, 1.5s/unit and 0.4s/squad attack gates | #487/#528 |

## Acceptance status and required real integration

**Implemented source != formal RC integration.** To be playable, the #220 sole authenticated writer must integrate this adapter **into the one existing ZOMBIE skill C** (never a second Combat Script), selecting the new command policy while preserving all other 30/31 RC scripts byte-exact and checking the selected Combat's whole #530+ source. The final official companion should retain 31 scripts, using source-inline/in-existing-Combat adaptation rather than installing extra standalone authorities. Then exact same HEAD native31, Rojo31 Script/Source/Class, real Place/ZIP hashes, strict OFF rollback, latest-HEAD nonforce CAS, and official push workflows must pass.

Current states: **SOURCE_CANDIDATE**; isolated native workflow pending; `FORMAL_RC_ADOPTED=NO`; `STUDIO_2CLIENT=NOT_TESTED`; `ANDROID_15MIN=NOT_TESTED`; `ART/FUN/OWNER=NO_GO`. Main, Roblox Publish, real payment, Windows and default S1 rich51 are not touched. Original author's personal acknowledgement is not a stop condition, but source lock/one-writer RED checks remain mandatory.

## Engine smoke conditions for later #220 intake

Invoke from existing Combat only on ZOMBIE skill-C authorised server cast. In Solo+AI and TEAM+BR, verify three actual models spawn, follow/guard/focus and hit permitted enemies using existing server damage, never allies; wall obstructed damage is rejected; castle elimination/respawn/end/old-round immediately deletes minions; item/egg/KO accounting unchanged. Verify 15-minute low-end Android and ART gate separately.
