#!/usr/bin/env python3
"""Static RC85 twin source conservation and negative tests. Native/Rojo follows in CI."""
import hashlib, pathlib, tempfile, json, shutil
from compose_real68 import patch_combat, sha, OLD_DOJO
p=pathlib.Path(__file__).parent
lua=(p/'EGGRUMBLE_LegacyTwinBiomes.server.luau').read_text()
composer=(p/'compose_real68.py').read_text()
req={
 'original_biomes': ['CoralGarden_','ThunderLookout_','WestBank','EastBank','AlwaysOpenSafeRoute','GQ8_RC85_WCS_Canyon'],
 'original_species':['AWARIN','SANGORU','RAIKO','KUMONON','BubbleHalo','CoralAntler_','ThunderHorn_','CloudWing_'],
 'real_training':['function Training.advance','MAX_PRACTICE = 7','REPEAT_WAIT_SECONDS = 20','if xp >= 7 then return 3 end','if xp >= 3 then return 2 end'],
 'real_bond':['function Bond.select','MAX_DURATION = 180','SWITCH_WAIT = 20','function Bond.pveMultiplier','if current.level==3 then return 1.2 end','return 1.1'],
 'guards':['if not RunService:IsStudio() then return end','player:GetAttribute("EGGRUMBLE_QueuedMode")~=mode', 'player:GetAttribute("EGGRUMBLE_Eliminated")==true', 'Workspace:Raycast(origin,body.Position-origin,ray)','world.Destroying:Connect(function()', 'WorldKey', 'arena.Parent==lobby'],
 'attack_authority':['EGGRUMBLE_TwinBondServerGranted','EGGRUMBLE_TwinBondEndsAt','EGGRUMBLE_TwinBondWorldKey'],
}
for label,needles in req.items():
 for s in needles:assert s in lua,(label,s)
for b in ['Instance.new("RemoteEvent")','OnServerEvent:Connect(','DataStoreService','MarketplaceService','TakeDamage(']:
 assert b not in lua, b
assert lua.count('local function install(')==1
assert lua.count('makeGuide(info, side)')==2
assert 'neutralDamage*=math.max(sessionDojoBoost,twinBoost)' in composer
assert 'other_existing_source_count_modified' not in composer
# Original exact source fingerprints are pinned and verified against real old Place.
for name,original in [
('TwinBiomes.luau','c54cf6c8284e2f57a5b9fdb440317afcd363f4db83343c9b33e5783c488ef8f4'),
('TwinCreatureTraining.luau','c59c6c3873f42f0c850ffc77beb20479ecb209250d2635294f89b61cfd00ac89'),
('TwinBondPolicy.luau','4c02c1933714ff0af09344b490f35f71db5d41534659e8b11ca4bed1d7235d09')]:
 candidate=p/name
 if candidate.exists():assert hashlib.sha256(candidate.read_bytes()).hexdigest()==original,name
# Dojo repair negative gate: a pre-modified source with no anchor/double-port is rejected
base='pre\n'+OLD_DOJO+'\npost\n'
merged=patch_combat(base)
assert merged.replace(merged[merged.index(' -- GQ8_RC85_DOJO_RECONCILE_20261119 retained'):merged.index('\n -- Both hit APIs') if '\n -- Both hit APIs' in merged else merged.index('\npost')],OLD_DOJO)==base
for invalid in (merged,base.replace('GQ8_RC85_DOJO_RECONCILE_20261119','CORRUPT'),base+OLD_DOJO):
 try:patch_combat(invalid)
 except ValueError: pass
 else:raise AssertionError('MUTANT_PASSED')
print('GQ8_TWIN68_3_ORIGINAL_RC85_FLAGS_PLUS_COMBAT_NO_SECOND_OWNER_NEGATIVE_PASS')