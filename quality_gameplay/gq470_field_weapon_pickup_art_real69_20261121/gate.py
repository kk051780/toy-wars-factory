#!/usr/bin/env python3
"""REAL69 exact world-weapon pickup visual overlay, no official RC write."""
from __future__ import annotations
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path

HERE=Path(__file__).resolve().parent
PATCH=HERE/'FIELD_WEAPON_REAL69.patch'
RC='e80973c354f14a0d0088577f3cc1a875454f0f8f'
ROUTE='ServerScriptService/EGGRUMBLE_FieldItemPickups'
REL='sources/ServerScriptService/EGGRUMBLE_FieldItemPickups.luau'
OLD='8fbf9187267df800c5c4a6379b1e2e3db0de4c363854a805c40c378bd0bb9658'
NEW='3db8b5dadb8017f0ae01c53092d3ed53d408076ee2dc3a8bb88a8d9a364824e8'
FEATURE='GQ470_FB015_FIELD_WEAPON_PICKUP_FACETS_REAL69_20261121'
PROJECT='EGGRUMBLE_REAL69.project.json'
RECEIPT='REAL69_LEGACY_INTAKE_RECEIPT.json'

def sha(b):return hashlib.sha256(b).hexdigest()
def need(flag,code):
 if not flag:raise AssertionError('FIELD_WEAPON_ART_RED_'+code)

def selected(root):
 doc=json.loads((root/PROJECT).read_text())['tree'];out={}
 def walk(node,parents):
  for name,child in node.items():
   if name.startswith('$') or not isinstance(child,dict):continue
   route='/'.join(parents+[name]);p=child.get('$path')
   if p is not None:
    target=(root/p).resolve()
    need(target.is_relative_to(root.resolve()) and target.is_file(),'PATH')
    need(route not in out,'DUPLICATE_ROUTE')
    out[route]=target
   else:walk(child,parents+[name])
 walk(doc,[])
 need(len(out)==69 and out.get(ROUTE)==root/REL,'SIXTY_NINE_REAL_SOURCES')
 return out

def validate(original,candidate):
 need(original.startswith('--!strict\n') and candidate.startswith('--!strict\n'),'STRICT_LUAU')
 need(FEATURE not in original and candidate.count(FEATURE)==1,'ONE_REAL_MARKER')
 for token in ('assert(RunService:IsStudio()','function Items.start(session:any,positions:{Vector3})',
     'function Items.weaponDamageMultiplier(', 'function Items.weaponReachBonus(',
     'if isV3Match and not interactionGuard.allow(',
     'local stageSet={', 'local weaponBuffs:', 'session.itemStop=function()'):
  need(token in original and token in candidate,'PRESERVE_ITEM_OWNER_'+token)
 need(original.count('Instance.new("WedgePart")')+1==candidate.count('Instance.new("WedgePart")'),
      'EXACT_ONE_STATIC_WEDGE_CONSTRUCTOR')
 need('facet.CanCollide=false;facet.CanTouch=false;facet.CanQuery=false' in candidate,
      'NO_PHYSICS_RAYCAST')
 need('facet.Material=Enum.Material.SmoothPlastic' in candidate,'MATTE')
 need('facet.Parent=folder' in candidate,'SAME_ITEM_LIFECYCLE')
 need('available=false;prompt.Enabled=false;base.Transparency=1;shaft.Transparency=1;facet.Transparency=1' in candidate,'HIDE_WHEN_TAKEN')
 need('available=true;prompt.Enabled=true;base.Transparency=0;shaft.Transparency=0;facet.Transparency=0' in candidate,'RESTORE_ON_RESPAWN')
 need(candidate.count('local facet=Instance.new("WedgePart")')==1,'ONE_FACET_PER_WEAPON_SITE')
 for denied in ('Instance.new("ScreenGui")','Instance.new("RemoteEvent")',
                'RenderStepped:Connect(', 'MarketplaceService','DataStoreService'):
  need(candidate.count(denied)==original.count(denied),'NO_AUTHORITY_OR_HUD_'+denied)
 for kind in ('SUN_BLADE','WIND_SPEAR','THUNDER_BOW'):
  need('"'+kind+'"' in candidate,'THREE_WEAPON_KINDS_'+kind)
 # Source identity is further enforced by pinned NEW SHA after actual patch application.

def negatives(original,src):
 mutants=(src.replace('facet.CanCollide=false','facet.CanCollide=true',1),
          src.replace('facet.CanQuery=false','facet.CanQuery=true',1),
          src.replace('facet.Transparency=1','facet.Transparency=0',1),
          src.replace('facet.Transparency=0','facet.Transparency=1',1),
          src.replace(FEATURE,FEATURE+FEATURE,1),
          src.replace('facet.Parent=folder','facet.Parent=workspace',1),
          src.replace('facet.Material=Enum.Material.SmoothPlastic','facet.Material=Enum.Material.Neon',1),
          src.replace('Instance.new("WedgePart")','Instance.new("RemoteEvent")',1))
 for n,bad in enumerate(mutants):
  try:validate(original,bad)
  except AssertionError:continue
  raise AssertionError('MUTANT_MISSED_'+str(n))
 return len(mutants)

def compose(base,out):
 need(not out.exists(),'NO_OVERWRITE')
 old=selected(base);receipt=json.loads((base/RECEIPT).read_text())
 need(receipt.get('build_head')==RC and receipt.get('selected_source_count')==69
      and len(receipt.get('source_hashes',{}))==69,'PINNED_FORMAL')
 for route,p in old.items():
  need(sha(p.read_bytes())==receipt['source_hashes'][route],'ORIGINAL_SHA_'+route)
 need(receipt['source_hashes'][ROUTE]==OLD,'TARGET_BASE_PIN')
 shutil.copytree(base,out)
 off=out/'OFF69_SOURCE_EXACT';off.mkdir()
 shutil.copytree(base/'sources',off/'sources')
 for name in (PROJECT,RECEIPT):shutil.copy2(base/name,off/name)
 subprocess.run(['patch','-p1','--fuzz=0','--batch','-i',str(PATCH)],cwd=out,check=True,
                stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 on=selected(out);back=selected(off)
 need({r for r in old if on[r].read_bytes()!=back[r].read_bytes()}=={ROUTE},'ONE_CHANGED_ROUTE')
 for route in old:
  need(old[route].read_bytes()==back[route].read_bytes(),'OFF_NOT_EXACT_'+route)
  if route!=ROUTE: need(old[route].read_bytes()==on[route].read_bytes(),'OTHER68_LOST_'+route)
 source0=old[ROUTE].read_text();source1=on[ROUTE].read_text()
 need(sha(source1.encode())==NEW,'NEW_SOURCE_HASH')
 validate(source0,source1)
 mutation_count=negatives(source0,source1)
 report={'feature_id':FEATURE,'canonical_rc_head_before_admission':RC,
   'original_official_run':44695199140,'official_artifact_id':14610422120,
   'profile':'REAL69_PRIVATE_COMPANION','selected_sources':69,
   'only_changed_route':ROUTE,'module_class':'ModuleScript',
   'other_sources_exact':68,'old_sha256':OLD,'new_sha256':NEW,
   'source_bytes_before_after':[len(source0.encode()),len(source1.encode())],
   'pickup_sites':6,'extra_decorative_parts_max':6,'world_collision_change':False,
   'render_connection_delta':0,'new_HUD_or_Remotes':0,'authoritative_item_logic_changed':False,
   'pickup_and_respawn_facet_visibility':'MATCHES_EXISTING_SHAFT',
   'negative_tests_rejected':mutation_count,
   'native_luau':'PENDING_CI','rojo_on_off':'PENDING_CI',
   'studio_solo':'NOT_TESTED','studio_2client':'NOT_TESTED','android15':'NOT_TESTED',
   'screenshots_old_new':'0/32','art_gate':'NO_GO','fun_gate':'NO_GO',
   'formal_rc_adopted':False,'owner_accepted':False}
 receipt['source_hashes'][ROUTE]=NEW
 receipt['gq470_field_weapon_art_candidate']=report
 (out/RECEIPT).write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
 handoff=out/'B220_ONE_SOURCE_NOT_FORMAL';(handoff/'selected_sources').mkdir(parents=True)
 shutil.copy2(on[ROUTE],handoff/'selected_sources/EGGRUMBLE_FieldItemPickups.luau')
 for p in (handoff/'SOURCE_SELECT_MANIFEST.json',out/'ART_CHECK_REPORT_FIELD_WEAPON.json'):
  p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print('GQ470_FIELD_WEAPON_FACET_REAL69_ONE_SOURCE_OFF69_NEG8_LOCAL_PASS')
 return report

def main():
 p=argparse.ArgumentParser();p.add_argument('--base',required=True,type=Path);p.add_argument('--out',required=True,type=Path)
 a=p.parse_args();compose(a.base.resolve(),a.out.resolve())
if __name__=='__main__':main()
