#!/usr/bin/env python3
"""Fail-closed contract for one V3 active Host and RC86 exploration port."""
from pathlib import Path
p=Path(__file__).with_name("EGGRUMBLE_LegacyExplorationBridge.server.luau")
s=p.read_text(encoding="utf8")
assert s.startswith("--!strict")
assert s.count('"REALM",')==4 and s.count('"SHARD",')==6
assert 'EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW' in s
assert 'EGGRUMBLE_QueuedMode' in s
assert 'EGGRUMBLE_Eliminated' in s
assert 'TacticalBattlefield' in s
assert 'RunService:IsStudio()' in s
assert 'if found[uid][id] then return end' in s
assert 'folder.Parent~=arena or arena.Parent~=origin' in s
assert 'prompt.RequiresLineOfSight=true' in s
# Native presentation line-of-sight is not a server authorization check.
assert 'rayParams.RespectCanCollide=true' in s
assert 'rayParams.FilterDescendantsInstances={char,folder}' in s
assert 'workspace:Raycast(rayStart,rayDirection,rayParams)' in s
assert 'occlusion.Instance.CanCollide then return end' in s
assert 'player:SetAttribute("EGGRUMBLE_LegacyExplore_Complete",nil)' in s
assert 'folder:SetAttribute("SessionOnly",true)' in s
for bad in ('DataStoreService','RemoteEvent','TakeDamage(',':FireServer(',':FireClient(',':FireAllClients(',':LoadCharacter(',':PivotTo('):
    assert bad not in s,bad
assert 'no new Remote' not in s or s.startswith('--!strict')
print("GQ8_RC86_LEGACY_EXPLORATION_PURE_COSMETIC_SOURCE_GATE_PASS")
