#!/usr/bin/env python3
"""Cumulative REAL67 -> REAL68 with genuine RC85 TwinBiomes + training/bond.
One new owned environmental Script, patch existing sole neutral Combat writer.
No second Game/Remote/Store and no preexisting script lost. Studio only.
"""
from __future__ import annotations
import argparse, hashlib, json, pathlib, shutil

NEW_ROUTE='ServerScriptService/EGGRUMBLE_LegacyTwinBiomes'
NEW_FILE='sources/ServerScriptService/EGGRUMBLE_LegacyTwinBiomes.server.luau'
COMBAT_ROUTE='ServerScriptService/EGGRUMBLE_SevenRoleCombat'
COMBAT_FILE='sources/ServerScriptService/EGGRUMBLE_SevenRoleCombat.luau'
FLAG='GQ8_RC85_TWIN_BIOMES_TRAINING_BOND_REAL68_20261119'
OLD_DOJO=''' -- GQ8_RC85_DOJO_RECONCILE_20261119
 -- Original RC85 session-only dojo +5% per level (<=20%). Only the
 -- existing Combat neutral Swarm hit consumes this. Player/server attributes
 -- are set by the Studio-only SocialPlaza station; client changes do not
 -- replicate to the authoritative server attribute table.
 if root.Parent==p.Character and p:GetAttribute("EGGRUMBLE_DojoServerGranted")==true then
  local kind=if p:GetAttribute("EGGRUMBLE_Role")=="BEAST" then "Beast"
   elseif stageBasic==true then "Weapon" else ""
  if kind~="" then
   local level=p:GetAttribute("EGGRUMBLE_Dojo"..kind.."Level")
   if typeof(level)=="number" and level==math.floor(level)
    and level>=1 and level<=5 then
    neutralDamage*=1+(level-1)*.05
   end
  end
 end
'''
NEW_DOJO=''' -- GQ8_RC85_DOJO_RECONCILE_20261119 retained unchanged behavior when bond is absent;
 -- GQ8_RC85_TWIN_BIOMES_TRAINING_BOND_REAL68_20261119 original no-stack policy.
 -- We combine at most the larger dojo/twin session-only buff in the EXISTING
 -- neutral Swarm damage variable, not in bots, PvP, guardians or castle hits.
 local sessionDojoBoost=1
 if root.Parent==p.Character and p:GetAttribute("EGGRUMBLE_DojoServerGranted")==true then
  local kind=if p:GetAttribute("EGGRUMBLE_Role")=="BEAST" then "Beast"
   elseif stageBasic==true then "Weapon" else ""
  if kind~="" then
   local level=p:GetAttribute("EGGRUMBLE_Dojo"..kind.."Level")
   if typeof(level)=="number" and level==math.floor(level)
    and level>=1 and level<=5 then
    sessionDojoBoost=1+(level-1)*.05
   end
  end
 end
 local twinBoost=1
 if RunService:IsStudio() and root.Parent==p.Character and p.Character==char
  and session.rules.phase=="ACTIVE" and session.world and session.world.Parent
  and p:GetAttribute("EGGRUMBLE_QueuedMode")==session.mode
  and p:GetAttribute("EGGRUMBLE_Eliminated")~=true
  and p:GetAttribute("EGGRUMBLE_TwinBondServerGranted")==true then
  local twinWorld=session.world:FindFirstChild("EGGRUMBLE_TwinBiomes")
  if twinWorld and twinWorld:IsA("Model")
   and twinWorld:GetAttribute("FeatureId")=="GQ8_RC85_TWIN_BIOMES_TRAINING_BOND_REAL68_20261119"
   and p:GetAttribute("EGGRUMBLE_TwinBondWorldKey")==twinWorld:GetAttribute("WorldKey")
   and p:GetAttribute("EGGRUMBLE_TwinBondMode")==session.mode then
   local endAt=p:GetAttribute("EGGRUMBLE_TwinBondEndsAt")
   local level=p:GetAttribute("EGGRUMBLE_TwinBondLevel")
   if typeof(endAt)=="number" and endAt==endAt and os.clock()<endAt
    and typeof(level)=="number" and level==math.floor(level)
    and level>=2 and level<=3 then
    twinBoost=if level==3 then 1.2 else 1.1
   end
  end
 end
 neutralDamage*=math.max(sessionDojoBoost,twinBoost)
'''

def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def check(v:bool,name:str):
 if not v:raise ValueError('RED_TWIN68_'+name)

def patch_combat(s:str)->str:
 check(s.count(OLD_DOJO)==1,'ORIGINAL_COMBAT_DOJO_ANCHOR_MISMATCH')
 check(FLAG not in s,'DUPLICATE_COMBAT_PORT')
 before={k:s.count(k) for k in ('remote.OnServerEvent:Connect(', 'TakeDamage(', 'MarketplaceService','DataStoreService','FireServer(', 'ProximityPrompt')}
 t=s.replace(OLD_DOJO,NEW_DOJO,1)
 check(t.replace(NEW_DOJO,OLD_DOJO,1)==s,'UNRELATED_COMBAT_CHANGES')
 check(all(t.count(k)==v for k,v in before.items()),'COMBAT_NEW_AUTHORITY_OR_WRITER')
 check(t.count('neutralDamage*=math.max(sessionDojoBoost,twinBoost)')==1,'BONUS_EXACT_ONCE')
 return t

def load_sources(base:pathlib.Path,project:dict):
 # traverse actual .project.json, not filenames or a guessed count; fail for duplicate routes
 result={}
 def walk(node,parts):
  if isinstance(node,dict):
   if '$path' in node:
    route='/'.join(parts)
    path=base/node['$path']
    check(route not in result and path.is_file(), 'MISSING_OR_DUPLICATE_'+route)
    result[route]=(node['$path'],path.read_bytes(),node.get('$className'))
   for k,v in node.items():
    if not k.startswith('$') and isinstance(v,dict):walk(v,parts+[k])
 walk(project['tree'],[])
 return result

def main(base:pathlib.Path,out:pathlib.Path,src:pathlib.Path,head:str):
 check(base.is_dir() and not out.exists(),'BASE_OR_OUT')
 proj=json.loads((base/'EGGRUMBLE_REAL67.project.json').read_text())
 receipt=json.loads((base/'REAL67_LEGACY_INTAKE_RECEIPT.json').read_text())
 check(receipt['source_count']==67 and receipt['parent_all66_byte_identical']==True,'PARENT_REAL67_RECEIPT')
 check(receipt['new_route']=='ServerScriptService/EGGRUMBLE_LegacyCanyonRoutes' and receipt['ported_policy_flags']==['WCS_F01_C01'],'PARENT_WCS')
 files=load_sources(base,proj)
 check(len(files)==67,'ORIGINAL_67')
 check(COMBAT_ROUTE in files and NEW_ROUTE not in files,'TARGET_ROUTES')
 check('GQ8_RC86_STARRY_PATH_SINGLE_REALM_REAL66_20261119' in files['ServerScriptService/EGGRUMBLE_RealmBattleCore'][1].decode('utf8'),'STAR_PARENT')
 check('GQ8_RC86_TRAPPER_PAIR_PORT_20261119' in files[COMBAT_ROUTE][1].decode('utf8'),'TRAPPER_PARENT')
 check('GQ8_RC86_UNDEAD_SQUAD_COMMAND_RECONCILE_20261119' in files[COMBAT_ROUTE][1].decode('utf8'),'UNDEAD_PARENT')
 raw=src.read_bytes()
 check(20000<len(raw)<45000 and raw.count(FLAG.encode())==1,'REAL_TWIN_SCRIPT')
 for needle in (b'function Training.advance',b'function Bond.select',b'TwinCodex',b'AWARIN',b'SANGORU',b'RAIKO',b'KUMONON',b'ServerGranted',b'CoralGarden',b'ThunderLookout'):
  check(needle in raw,'MISSING_ORIGINAL_TWIN_'+needle.decode())
 for bad in (b'Instance.new("RemoteEvent")', b'OnServerEvent:Connect(',b'DataStoreService',b'MarketplaceService',b'TakeDamage('):
  check(bad not in raw,'NEW_TWIN_AUTHORITY_'+bad.decode())
 originalCombat=files[COMBAT_ROUTE][1]
 patched=patch_combat(originalCombat.decode('utf8')).encode('utf8')
 shutil.copytree(base,out)
 # OFF67 must point to a separate ORIGINAL source tree; the main REAL68 tree
 # intentionally modifies its Combat. Never mistake the patched source for OFF67.
 off=out/'off67'
 off.mkdir(exist_ok=False)
 for route,(rel,oldraw,_) in files.items():
  oldfile=off/rel
  oldfile.parent.mkdir(parents=True,exist_ok=True)
  oldfile.write_bytes(oldraw)
 (off/'EGGRUMBLE_REAL67.project.json').write_bytes((base/'EGGRUMBLE_REAL67.project.json').read_bytes())
 check(len(load_sources(off,proj))==67,'OFF67_ORIGINAL_PROJECT_SOURCE_COUNT')
 for route,(_,oldraw,_) in files.items():
  check(load_sources(off,proj)[route][1]==oldraw,'OFF67_SOURCE_CHANGED_'+route)
 path=out/NEW_FILE
 path.parent.mkdir(parents=True,exist_ok=True)
 path.write_bytes(raw)
 (out/COMBAT_FILE).write_bytes(patched)
 (out/'OFF_COMBAT_REAL67_EXACT.luau').write_bytes(originalCombat)
 # Exact everything else, including newest canyon overlap fixes.
 for route,(relative,source,_) in files.items():
  data=(out/relative).read_bytes()
  if route==COMBAT_ROUTE:check(data==patched,'COMBAT_EDIT')
  else:check(data==source,'MUTATED_EXISTING_'+route)
 server=proj['tree']['ServerScriptService']
 check('EGGRUMBLE_LegacyTwinBiomes' not in server,'SOURCE_DUPLICATE')
 server['EGGRUMBLE_LegacyTwinBiomes']={'$path':NEW_FILE}
 proj['name']='EGGRUMBLE_REAL68_TWIN_BIOMES_ONE_FORMAL_RC_PRIVATE_STUDIO'
 (out/'EGGRUMBLE_REAL68.project.json').write_text(json.dumps(proj,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
 written=load_sources(out,proj)
 check(len(written)==68 and len(set(written))==68,'FINAL_68')
 check(written[NEW_ROUTE][1]==raw and written[COMBAT_ROUTE][1]==patched,'FINAL_SELECTED')
 for route,(_,content,_) in files.items():
  if route!=COMBAT_ROUTE:check(written[route][1]==content,'NONLOSS_'+route)
 r={
  'schema':'GQ8_TWIN68_RC85_REAL67_CUMULATIVE_V1','official_head':head,
  'formal_branch':'rc/p0d-s1-kids-rc01','selected_source_count':68,
  'previous_selected_source_count':67,'existing_source_count_preserved':67,
  'unchanged_existing_source_bodies':66,'one_existing_combat_modified':True,
  'added_game_or_store_or_remote_owners':0,'new_server_script_count':1,
  'new_script_route':NEW_ROUTE,'new_script_sha256':sha(raw),
  'combat_original_sha256':sha(originalCombat),'combat_patched_sha256':sha(patched),
  'source_adopted_flags':['TWIN_BIOMES_4NPC_V1','TWIN_CREATURE_TRAINING_V1','TWIN_BOND_PVE_COMPANION_V1'],
  'old_RC85_script_sha256':'c54cf6c8284e2f57a5b9fdb440317afcd363f4db83343c9b33e5783c488ef8f4',
  'old_RC85_training_sha256':'c59c6c3873f42f0c850ffc77beb20479ecb209250d2635294f89b61cfd00ac89',
  'old_RC85_bond_sha256':'4c02c1933714ff0af09344b490f35f71db5d41534659e8b11ca4bed1d7235d09',
  'rc85_real_source_artifact':14158848286,
  'studio_only':True,'original_training_xp_cap':7,'practice_level_3_at_xp':7,'practice_cooldown_seconds':20,
  'original_species':['AWARIN','SANGORU','RAIKO','KUMONON'],
  'per_arena_species_character_instances':8,'per_arena_biomes':2,
  'original_bond_seconds':180,'switch_wait_seconds':20,'neutral_damage_bonus_level2':1.1,'neutral_damage_bonus_level3':1.2,
  'pve_bonus_nonstack_with_dojo':True,'same_existing_combat_neutral_damage_writer':True,
  'starfall_meteor_canyon_trapper_undead_preserved':True,
  'not_tested':['Studio_1_2_client','Android_15min','child_fun','art','owner_acceptance'],
  'product':'NO_GO','old48_feature_complete':False,'roblox_publish':False,'work_codex_used':False,
  'rollback':'Exact parent REAL67; original one Combat source at OFF_COMBAT_REAL67_EXACT.luau',
  'source_hashes':{route:sha(b) for route,(_,b,_) in sorted(written.items())},
  'source_classes':{route:('Script' if rel.endswith('.server.luau') else 'LocalScript' if rel.endswith('.client.luau') else 'ModuleScript') for route,(rel,_,_) in sorted(written.items())},
 }
 (out/'REAL68_LEGACY_INTAKE_RECEIPT.json').write_text(json.dumps(r,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
 print('GQ8_RC85_TWIN_BIOMES_4_SPECIES_7XP_180S_BOND_SINGLE_NEUTRAL_COMBAT_REAL68_SOURCE_NONLOSS_PASS', len(written),sha(raw))

if __name__=='__main__':
 p=argparse.ArgumentParser()
 p.add_argument('--base',type=pathlib.Path,required=True)
 p.add_argument('--out',type=pathlib.Path,required=True)
 p.add_argument('--source',type=pathlib.Path,required=True)
 p.add_argument('--head',required=True)
 a=p.parse_args();main(a.base,a.out,a.source,a.head)