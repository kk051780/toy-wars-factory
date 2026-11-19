#!/usr/bin/env python3
"""#470 FB-STAGE-LOOT real RC85: 3 useful ground weapon types + six pickups.
Original Game, Horde and egg authorities remain single and server-owned.
Exact 84 parent/lock; add one ModuleScript and edit only real Game.
No main/official RC writes, publication, marketplace or paid dependencies.
"""
from __future__ import annotations
import argparse,hashlib,json,copy
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from xml.etree import ElementTree as ET
from collections import Counter
PARENT='P0D_RC84_SIEGE_STRIKE_VFX_AI_ARRIVAL_PRIVATE.rbxlx'
PARENT_SHA='0f256dfd46cad4ff1f94d09730eb6bc1d285ed6fc29f4801cae6e59ea8f4e63a'
PARENT_GAME_BLOB='9b7fb4648b9b6c6b5efbc958ecdf275e46f6830d'
MODULE='server/StagePickupLoot.luau'
GAME='server/Game.server.luau'
OUTPUT='P0D_RC85_3_USEABLE_STAGE_WEAPONS_SIEGE_BEAST_TRAPPER_SOLO_PRIVATE.rbxlx'
OFFICIAL='d2f3ed1a47558fdaf07be0181c83c698bdb2ce34'
EXPECTED_SHA='501688966820ae80833a7cae1d5a8b4fc908b9b30062dd1c3f727a356cc15387'
EXPECTED_BYTES=832695
EXPECTED_GAME_BLOB='060633a00a8ae25d3717dc1107548679c9385153'
EXPECTED_MOD_BLOB='3fb954f4bcc9d5728b55cc284e6519c304bd61c2'

def sha(x):return hashlib.sha256(x).hexdigest()
def blob(s):
 b=s.encode('utf-8')
 return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def once(s,a,b,label):
 if s.count(a)!=1 or b in s:raise ValueError('GAMESOURCE_DRIFT_'+label+':'+str(s.count(a)))
 return s.replace(a,b,1)

def collect(place):
 root=ET.fromstring(place);found={}
 for item in root.iter('Item'):
  if item.get('class') not in ('Script','LocalScript','ModuleScript'):continue
  p=item.find('Properties')
  if p is None:continue
  n=p.findtext("string[@name='Name']");t=p.find("string[@name='Source']")
  if not n or t is None or t.text is None or n in found:
   raise ValueError('INVALID_OR_DUPLICATE_SOURCE')
  found[n]=t
 return root,found

def patch_game(s):
 s=once(s,'SevenJobs.TrapperWarp = require(script.Parent:WaitForChild("TrapperWarpService"))',
    'SevenJobs.TrapperWarp = require(script.Parent:WaitForChild("TrapperWarpService"))\n'
    'SevenJobs.StageLoot = require(script.Parent:WaitForChild("StagePickupLoot"))','PRIVATE_MODULE_IMPORT')
 s=once(s,'''local function within(player: Player, world: Vector3, dist: number): boolean
    local ok, root = healthy(player)
    return ok and root ~= nil and (root.Position - world).Magnitude <= dist
end''',
    '''local function within(player: Player, world: Vector3, dist: number): boolean
    local ok, root = healthy(player)
    return ok and root ~= nil and (root.Position - world).Magnitude <= dist
end
-- FB-STAGE-LOOT: no new Game local or Remote and no shadow damage/score authority.
-- Server validation runs again on EVERY pickup and EVERY neutral mob hit.
SevenJobs.StageLoot.start(map.model,function(player)
    local alive,root=healthy(player)
    return alive and root~=nil and match.phase=="ACTIVE"
        and carry[player]==nil and player:GetAttribute("P0D_LateJoinSpectator")~=true
        and (getTeamName(player)=="RED" or getTeamName(player)=="BLUE"),
        match.serial,root
end)''','LIVE_MAP_STAGE_LOOT_START_AFTER_HEALTHY')
 s=once(s,'*twinBondOnlyNeutralMobBonus(player)))',
    '*twinBondOnlyNeutralMobBonus(player)))\n'
    '                *SevenJobs.StageLoot.damageMultiplier(player,now,match.serial)',
    'SERVER_NEUTRAL_HORDE_BONUS')
 s=once(s,'return horde:hit(pos,dir,damage,now,player.Character)',
    'return horde:hit(SevenJobs.StageLoot.hitOrigin(player,pos,dir,now,match.serial),\n'
    '                        dir,damage,now,player.Character)',
    'SERVER_SEVENJOB_M1_REACH')
 s=once(s,'touched,defeated=horde:hit(root.Position,look,\n                originalPveDamage,now,player.Character)',
    'touched,defeated=horde:hit(SevenJobs.StageLoot.hitOrigin(player,root.Position,look,now,match.serial),look,\n'
    '                originalPveDamage,now,player.Character)',
    'SERVER_FALLBACK_M1_REACH')
 s=once(s,'    SoloTeamBots.stop()\n    SevenJobs.TrapperWarp.clearAll()\n    match.phaseUntil',
    '    SoloTeamBots.stop()\n    SevenJobs.TrapperWarp.clearAll()\n'
    '    SevenJobs.StageLoot.endRound() -- no loot buff survives a finished round\n'
    '    match.phaseUntil','STOP_ROUND_CLEANUP')
 s=once(s,'local function resetRound()\n    SoloTeamBots.stop()\n    SevenJobs.TrapperWarp.clearAll()',
    'local function resetRound()\n    SoloTeamBots.stop()\n    SevenJobs.TrapperWarp.clearAll()\n'
    '    SevenJobs.StageLoot.endRound() -- revive pickups, clear old buffs','RESET_ROUND')
 s=once(s,'            SevenJobs.TrapperWarp.clearOwner(player) -- team migration revokes pair',
    '            SevenJobs.TrapperWarp.clearOwner(player) -- team migration revokes pair\n'
    '            SevenJobs.StageLoot.clearPlayer(player) -- same team safety for loot','REBALANCE_REVOKE')
 s=once(s,'    player.CharacterAdded:Connect(function(character)\n        clearEarnedPowerVisual(player)',
    '    player.CharacterAdded:Connect(function(character)\n'
    '        SevenJobs.StageLoot.clearPlayer(player) -- pickups do not survive death\n'
    '        clearEarnedPowerVisual(player)','RESPAWN_REVOKE')
 s=once(s,'    SevenJobs.TrapperWarp.clearOwner(player) -- disconnect cleanup',
    '    SevenJobs.TrapperWarp.clearOwner(player) -- disconnect cleanup\n'
    '    SevenJobs.StageLoot.clearPlayer(player) -- no departed player buff','LEAVE_CLEANUP')
 for p in ('summonSevenBeast','SevenJobs.ArmamentM1.strike','SevenJobs.TrapperWarp.place',
           'SoloTeamBots.tryHumanHit','horde:tick(now,eligibleSoloPlayers(),healthy)',
           'personalEggDeposits[player]=(personalEggDeposits[player] or 0)+1'):
  if p not in s:raise ValueError('EXISTING_REAL_GAME_FEATURE_LOST:'+p)
 for p in ('remote.OnServerEvent:Connect(','local function tickRound()',
           'local function stopRound(','local function resetRound()'):
  if s.count(p)!=1:raise ValueError('SECOND_GAME_OR_ROUND_AUTHORITY:'+p)
 return s

def add_module(root,body):
 shell=None;parent=None
 for p in root.iter():
  for item in p.findall('Item'):
   props=item.find('Properties')
   name=props.findtext("string[@name='Name']") if props is not None else None
   if name=='SevenJobsRules':
    if shell is not None:raise ValueError('DUPLICATE_ROLE_SHELL')
    parent=p;shell=item
   if name=='StagePickupLoot':raise ValueError('STAGE_MODULE_ALREADY_EXISTS')
 if shell is None or shell.get('class')!='ModuleScript':raise ValueError('NO_AUTHOR_SCRIPT_SHELL')
 fresh=copy.deepcopy(shell)
 used=[int(x.get('referent')) for x in root.iter('Item') if (x.get('referent') or '').isdigit()]
 fresh.set('referent',str(max(used)+1))
 p=fresh.find('Properties');p.find("string[@name='Name']").text='StagePickupLoot';p.find("string[@name='Source']").text=body
 parent.append(fresh)

def build(parent,out,mod=None,extract=None):
 if mod is None:mod=Path(__file__).with_name('StagePickupLoot.luau')
 with ZipFile(parent) as z:
  names=z.namelist()
  if len(set(names))!=len(names) or any(n.startswith('/') or '..' in Path(n).parts for n in names):
   raise ValueError('UNSAFE_PARENT_ARCHIVE')
  raw=z.read(PARENT)
  lock=json.loads(z.read('SOURCE_LOCK.json'))
  feature=json.loads(z.read('RC_FEATURE_LOCK.json'))
  receipt=json.loads(z.read('RECEIPT.json'))
 if sha(raw)!=PARENT_SHA or receipt.get('official_rc_head')!=OFFICIAL or receipt.get('official_rc_write') is not False:
  raise ValueError('UNVERIFIED_PARENT84')
 root,nodes=collect(raw)
 original={n:t.text for n,t in nodes.items()}
 if len(original)!=84 or lock.get('total_scripts')!=84 or feature.get('total_sources')!=84 or lock['blobs']!=feature['source_gitblobs']:
  raise ValueError('PARENT84_LOCK_COUNT_CHANGED')
 if Counter(blob(s) for s in original.values())!=Counter(lock['blobs'].values()):
  raise ValueError('PARENT84_GITBLOB_DRIFT')
 if lock['blobs'].get(GAME)!=PARENT_GAME_BLOB:raise ValueError('WRONG_AUTHOR_GAME')
 module=Path(mod).read_text(encoding='utf-8')
 game=patch_game(original['Game'])
 nodes['Game'].text=game
 add_module(root,module)
 final=ET.tostring(root,encoding='utf-8')
 _,after=collect(final)
 if len(after)!=85 or set(after)-set(original)!={'StagePickupLoot'}:raise ValueError('REAL85_COUNT_OR_MODULE_DRIFT')
 if any(after[n].text!=original[n] for n in original if n!='Game'):
  raise ValueError('OTHER_83_SCRIPT_SOURCE_CHANGED')
 if after['StagePickupLoot'].text!=module:raise ValueError('NEW_MODULE_CHANGED')
 if sha(final)!=EXPECTED_SHA or len(final)!=EXPECTED_BYTES or blob(game)!=EXPECTED_GAME_BLOB or blob(module)!=EXPECTED_MOD_BLOB:
  raise ValueError('FINAL_PRIVATE_85_HASH_LOCK_DRIFT')
 lock['blobs'][GAME]=feature['source_gitblobs'][GAME]=blob(game)
 lock['blobs'][MODULE]=feature['source_gitblobs'][MODULE]=blob(module)
 lock['total_scripts']=feature['total_sources']=85
 if Counter(blob(t.text) for t in after.values())!=Counter(lock['blobs'].values()):
  raise ValueError('85_SOURCE_DIGEST_MISMATCH')
 report={'schema':'P0D_REAL_USABLE_STAGE_WEAPONS_PRIVATE_RC85_V1',
  'official_rc_head':OFFICIAL,'official_rc_write':False,
  'parent_place_sha256':PARENT_SHA,'place_sha256':sha(final),'place_bytes':len(final),
  'game_gitblob':blob(game),'stage_loot_gitblob':blob(module),
  'script_count':85,'existing_83_script_bodies_exact':True,
  'original_game_neutral_horde_authority_preserved':True,
  'seven_job_special_weapons_preserved':True,
  'stage_world_weapon_count':6,'stage_unique_weapon_types':3,
  'pickup_active_round_only':True,'stage_loot_cannot_buff_egg_carrier':True,
  'physical_held_weapon_aura':True,'shared_game_m1_buff_and_reach':True,
  'server_validated_no_remote_and_no_store':True,'private_off_unless_studio':True,
  'native':'NOT_RUN','rojo':'NOT_RUN','studio':'NOT_RUN',
  'android':'NOT_RUN','owner':False,'product':'NO_GO'}
 with ZipFile(out,'w',ZIP_DEFLATED) as z:
  z.writestr(OUTPUT,final)
  z.writestr('SOURCE_LOCK.json',json.dumps(lock,indent=2,ensure_ascii=False)+'\n')
  z.writestr('RC_FEATURE_LOCK.json',json.dumps(feature,indent=2,ensure_ascii=False)+'\n')
  z.writestr('RECEIPT.json',json.dumps(report,indent=2,ensure_ascii=False)+'\n')
  z.writestr('source/StagePickupLoot.luau',module)
 if extract:
  extract.mkdir(parents=True,exist_ok=True)
  for n,t in after.items():(extract/(n+'.luau')).write_text(t.text,encoding='utf-8')
 return report

if __name__=='__main__':
 p=argparse.ArgumentParser()
 p.add_argument('--parent',type=Path,required=True)
 p.add_argument('--out',type=Path,required=True)
 p.add_argument('--module',type=Path)
 p.add_argument('--extract',type=Path)
 a=p.parse_args()
 print(json.dumps(build(a.parent,a.out,a.module,a.extract),ensure_ascii=False,indent=2))
