# S1 one-owner D15 integration guide — #220 sole writer only

Source status: OPTIONAL_ADAPTER_READY, NOT_INSTALLED, NOT_ENGINE_TESTED.

## 1. Required immutable input files

Review/read whole original D15 from commit `85967eb6b7ace4d2a749b65041cb4ca975cafdf0`, file `handoffs/P0D-D15-TRAP-RESCUE-LIBRARY-RECOVER-20261110-01/luau/TrapRescueCore.luau`. Verify SHA256 exactly `da7c0b46f39d4e0a64bd397fcc16fcf9e4502c879179371cd221d42ea8db8174` and size 8190. **Never treat this bridge as a copy** of the original Core. Do not use a second D15 cleanroom module simultaneously.

Copy recovered D15 original module to `releases/P0D_S1_KIDS_RC01/src/server/TrapRescueCore.luau` and *new bridge* `src/S1D15TrapBridge.luau` to `releases/P0D_S1_KIDS_RC01/src/server/S1D15TrapBridge.luau` **in the integrator's isolated release branch**, not main and not from this independent Chat lane. Existing project `ServerScriptService/TrapRaidersS1: {"$path":"src/server"}` maps both new modules without any new or duplicate `$path`.

## 2. Necessary Game.server.luau integration points (sole #220 integrator)

Existing Game.server.luau is the only source of phase/team/job/seq and damage:

```luau
local TrapCore = require(script.Parent:WaitForChild("TrapRescueCore"))
local TrapBridge = require(script.Parent:WaitForChild("S1D15TrapBridge"))
local trap = TrapBridge.new(TrapCore, {
    getTeam = getTeamName,
    getRole = function(p) return roles[p] or "RAIDER" end,
    getPhase = function() return match.phase end,
    serverNow = serverNow,
    applyPoisonDamage = function(target, caster, amount, receipt)
        -- Recheck original ROUND/COMBAT authority: ACTIVE, enemy team,
        -- both alive, current round, valid receipt, no spawn invulnerability.
        -- Then and ONLY THEN canonical Game may call Humanoid:TakeDamage(amount).
        -- Do NOT invent a second damage handler in this bridge.
    end,
    onStatus = function(p, status)
        -- Game handles WalkSpeed = rooted ? 0 : RoleWalkSpeed[currentRole],
        -- restoring on release or round end. Add trap flags to existing
        -- SNAPSHOT; client can show a single easy-to-tap ESCAPE action.
    end,
})
```

No code in this *example* is a ready damage implementation; it deliberately keeps the authoritative Game logic and epoch check in the integrator's sole domain. Integrator must supply production callback bodies, avoid redundant speed or HP writers and preserve original S1 egg carry/win semantics.

- **resetRound** after Game assigns fresh `match.serial`, starts ACTIVE and writes canonical `match.startedAt`: `trap:endRound()` (clear stale) then `trap:beginRound(match.serial, match.startedAt)`.
- **tickRound** during existing ACTIVE tick, call `trap:update()` **once** before normal broadcast. Do NOT spawn another heartbeat or create another event chooser.
- **stopRound** and other Results/abort paths: `trap:endRound()` once, then existing result and snapshot handling; root/poison state cannot leak into rematch.
- **Players.PlayerRemoving**: `trap:removePlayer(player)` before or alongside original carrier cleanup. Death/respawn will be reconciled via server-only `getBody` each tick; optional call update after a Humanoid death.
- **existing remote.OnServerEvent** single listener: for `TRAP_CAST`, `TRAP_RESCUE`, `TRAP_ESCAPE`, run `Rules.validSeq(data.seq,lastSeq[player] or 0)` exactly once, consume `lastSeq[player]` and only then call `trap:handleIntent(player,data.action,true)`. Never forward `data.target`, `data.position`, `data.damage`, `data.team`, `data.job` or client clock. Keep current ATTACK/ROLE paths intact and do not create another Remote or OnServerEvent listener.
- **TRAPPER role** is NOT present in current S1. If selected for first release, explicitly add TRAPPER to server `applyRole`, Config RoleHealth/WalkSpeed and castle/combat damage table values (owner balances) and one optional client HUD role/button. Without role selection, cast deliberately returns WRONG_JOB. No hidden instant power activation.
- For `onStatus`, use current Game's `RoleWalkSpeed` baseline and recheck the same Humanoid/character generation; do not restore stale speed into another respawn or override a more authoritative stun. Reset all statuses at match end and make trap status visible to players; no forced repeated tap/paid escape.

## 3. Static/behavior QA before final PC Studio

- Verify initial Game has exactly **one** OnServerEvent:Connect, **one** round tick and one real HP/Combat writer. Original D15 Core and bridge are ModuleScripts only, not independent server scripts.
- Test two clients: TRAPPER vs enemy front/behind/wall/far/dead/immune; early escape, 1.25-s escape, ally rescue after .5-s, enemy can't rescue; 12-s cast cooldown, per-caster 1 trap, 3x3-HP poison cap; force death/quit/team change/reconnect and match end at each tick; no cross-round damage and no double poison receipt.
- Stage a private, isolated Studio source-only RC; verify 2-client actual engine/time with negative test-player UserIds, mobile touch HUD and root/unroot; no release until a separate OWNER approval and full normal Studio exit evidence. Existing egg theft/score/castle victory/rematch must remain unchanged.
- Reviewer must verify when injecting actual original D07 boss and D08 event that no second chooser, second poison damage authority or new unreviewed Remote is added.

## 4. Acceptance / rollback

Define `S1_D15_TRAP_SOURCE_SELECTED` only if the two module hashes, unique Rojo mounts, original Core provenance, canonical game callback diff and independent real-source QA match. Before actual Studio, status remains `S1_D15_SOURCE_ONLY_NOT_ENGINE_TESTED`.

If performance/first-minute simplicity or integration fails, **skip D15 in S1** without blocking existing 2-player egg/castle first release; keep packet available as an S2 feature. No D15 monetization or pay-to-win switches.

## V1.1 poison receipt contract update

Use the new five-component server-only receipt `matchId:casterId:targetId:successfulCastGeneration:poisonTick`. The canonical Game damage callback must preserve and dedupe this *complete* receipt, not truncate it to the old four fields. Each accepted D15 cast increments generation; rejected intents do not. Same-target recast after the original 12-second cooldown must allow three fresh damage ticks, while repeated ticks from the *same cast* remain ignored. Do not accept `castGeneration` or receipt IDs from client packets. Studio two-round/recast regression remains required.
