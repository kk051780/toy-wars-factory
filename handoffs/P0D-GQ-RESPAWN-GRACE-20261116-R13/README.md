# EGGRUMBLE R13 — castle-respawn anti-camp grace

**Deliverable:** one optional server-owned **real Script** in isolated `handoffs/P0D-GQ-RESPAWN-GRACE-20261116-R13/**`. Original author [DRAFT #482](https://github.com/kk051780/toy-wars-factory/pull/482) has a robust "return after death to home castle" function but no post-return spawn protection. This makes players vulnerable to immediate bot/human spawn camping; this slice does not duplicate any skill, NPC, castle, item, HUD, score or lobby code.

**Non-overlap agreement:** [#218 SOFT CLAIM 6906764068](https://github.com/kk051780/toy-wars-factory/issues/218#issuecomment-6906764068). This remains an **ungranted soft claim**, not permission to write to #220 official RC.

## What a player sees

In the **Studio-only V3** preview, immediately after the original server returns a surviving hero to their personal castle upon `CharacterAdded`, the server supplies a short, invisible Roblox `ForceField`. It prevents the direct `Humanoid:TakeDamage` used by the original player-vs-player skill path and enemy hero-bot path. Protection expires after **2.25 seconds maximum**, or on skill-tool equip, any `ProximityPrompt` activation (egg, field item, gate and so on), death, elimination, leaving/round cleanup or moving out of the near-home region.

The field is server-created, **never client-granted** and never extends an existing forcefield from a SpawnLocation or another feature. If an external shield exists, this source deliberately leaves it unchanged and does not cap its lifetime; existing platform shields need separate measured inspection.

The script does NOT change HP, create/summon NPCs, modify egg ownership, let a carrier teleport while invulnerable, or stop enemy attacks against the player's castle. It does not change art/camera/HUD or paid items.

## Real author contracts reused

- Existing `EGGRUMBLE_QueuedMode` and `EGGRUMBLE_Eliminated` are **server-set Player attributes** in original #482; no Remote request grants grace.
- The original TEAM/BATTLE_ROYALE arena and the user's actual `Castle_<UserId>/StandardCore` are required. A fallen dark-gray core cannot receive new protection.
- A live humanoid + current avatar + near-home distance (≤85 studs) are required. No distant/lobby/old-avatar protection.
- No production-server script installs: the original #482 V3 preview is `RunService:IsStudio()` gated and so is this one.
- In the original source, combat uses `Humanoid:TakeDamage` for PvP and bot-vs-human. The neutral crowd currently does **not** attack players, so this change protects against hero combat but does **not** claim to make neutral fights more dangerous or entertaining.
- Include only the ONE new server script in the existing `ServerScriptService` as an optional session complement. Author's original 21 source files stay byte-exact. Existing game mode, original 7 skills, 3 paths, castle eggs, 110-cap neutral, item/score/lobby are reused.

## Exact candidate

`EGGRUMBLE_V3_RESPAWN_GRACE.project.json` maps the fixed #482 source SHA `fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9` as 21 **unchanged** original Luau files plus this ONE server Script for an isolated 22-source private Place. PR is stacked on #482 for compatibility; **do not merge into #482 or official #220 from this PR as-is**.

The dedicated GitHub Action `p0d-gq-respawn-grace-r13.yml` runs 12 source/security contracts, pinned native Luau compiler against 22 mapped scripts, Rojo v7.7.1 SHA verification and 22-of-22 XML embedded source equality, and publishes a short-lived unpublished private `.rbxlx` + SHA receipt. A green CI validates source/build integrity **only**, not actual Studio protection or device quality.

## Eight categories and original ownership

| Game category | Preserved implementation | This change |
|---|---|---|
| Characters | #482 seven careers and respawn | One safe return after KO, max 2.25s |
| Field | #482 TEAM/BR route geometry | Exact current castle + 85 studs, no teleport |
| Battle | #482 original attack damage and visuals | Roblox built-in ForceField stops immediate burst; first tool equipped ends immunity |
| Castle | #482 core status and HP | Fallen personal castles cannot activate protection; enemy can still raid |
| Neutrals | #482 actual 110 cap and boss | Original AI and neutral logic untouched |
| Items | #482 original FieldItemPickups / #489 fairness | Any world prompt cancels the shield before travel |
| Lobby | #482 queued mode and return/cleanup | Never grant in lobby, other mode, departed/retired arena |
| Balance | #487 original score and #482 server rules | No reward, damage, egg, or siege scoring changes |

## Mandatory private Studio acceptance

1. Select TEAM, kill a human after starting and verify official original `RoundReplay.returnToActiveCastle` respawns near own living castle. For ≤2.25 seconds a nearby enemy hero/bot `TakeDamage` should not reduce HP. After expiry, direct attacks must damage. Verify same for BR.
2. Equip one of the 7 role tools *during* grace; confirm protection ends before the next meaningful attack. Trigger enemy egg theft or item/gate `ProximityPrompt` during grace; verify it ends immediately. Test on Android touch with same action sequence.
3. Ensure old avatar/other mode/abandoned arena/defeated castle/standing far away gets no grace. Stop/switch mode and confirm no leftover ForceField nor old timer affecting the new character. Two players respawning simultaneously must not cancel each other's shield.
4. Inspect whether Roblox auto-generates any native SpawnLocation ForceField. This script does not remove or shorten external shields; if default 10-second invulnerability exists, balance is **NO_GO** until server spawn duration is calibrated by original author/owner.
5. Confirm all #420 screenshots/art, low-end Android 15-min FPS, first 3-min child FUN, and OWNER satisfaction separately.

## RC intake / rollback

Only authenticated official writer [#220](https://github.com/kk051780/toy-wars-factory/issues/220) can take exactly this source into accepted current V3 when original and #484 quality ART/SCORE composer heads are repinned, no conflicting claim exists, full same-HEAD native/source-exact/Studio/client QA succeeds, and non-force CAS is authorized. Rollback: remove only this single Script from `ServerScriptService`; all original paths stay unchanged.

**Progress (R13 feature-only, not product completion):** isolated Luau source 1/1, Rojo manifest 1/1, source-test code 1/1, pinned CI pipeline 1/1, GitHub CI status pending, official RC integrated **0/1**, Studio 0/1, Android 0/1, OWNER accepted 0/1. Product ART/FUN remains **NO_GO**.

No main change, PR merge, production publish, paid usage or Windows/Studio remote operation.
