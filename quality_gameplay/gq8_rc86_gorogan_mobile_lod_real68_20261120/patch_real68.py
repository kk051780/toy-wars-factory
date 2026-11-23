#!/usr/bin/env python3
"""Port old RC86 Gorogan mobile tier LOD into existing REAL68 A01 client.
No second script, Remote, game authority or Store. Exact OFF68 retained.
"""
from __future__ import annotations
import argparse, hashlib, json, pathlib, shutil

ROUTE='StarterPlayer/StarterPlayerScripts/EGGRUMBLE_ArtDistanceLOD'
ORIGINAL_SHA='7b2936ef15a025409d54acb498b79254a8bf2957ade2faf96f1bb1985f103889'
FLAG='GQ8_RC86_GOROGAN_MOBILE_LOD_REAL68_20261120'

def sha(raw:bytes)->str: return hashlib.sha256(raw).hexdigest()
def must(ok:bool,why:str)->None:
    if not ok: raise ValueError('RED_GOROGAN_LOD_'+why)
def one(src:str,old:str,new:str,why:str)->str:
    must(src.count(old)==1,'ANCHOR_'+why)
    return src.replace(old,new,1)

def patch(src:str)->str:
    must(sha(src.encode())==ORIGINAL_SHA,'CURRENT_A01_SOURCE_DRIFT')
    must(FLAG not in src,'DUPLICATE_LOD')
    must('EGGRUMBLE_StoneGiantVisual_VisualOnly=190' in src,'ORIGINAL_A01_STONEGIANT')
    must('GQ8_RC86_FB016_FOLIAGE_SIGHTLINE_V3_20261119' in src,'FOLIAGE_PARENT_LOST')
    must('local MAX_TRACKED_PARTS=1800' in src and 'local UPDATE_INTERVAL_SECONDS=1.2' in src,'BUDGET_CHANGED')
    src=one(src,'local hidden:{[BasePart]:boolean}={}',
        '''local hidden:{[BasePart]:boolean}={}
-- '''+FLAG+''': one existing A01 pass, never a second render loop.
-- Old RC86 mobile thresholds: detail 52, silhouette 118 studs.
local goroganCaps:{[BasePart]:number}={}
''','STATE')
    helper='''-- Only ornaments created by the existing V3 StoneGiant art owner.
-- No culling of real boss torso, weakpoint, weapons, HUD or original decorations.
local function goroganCap(part:BasePart):number?
 if part.Name:sub(1,11)~="ART_Gorogan" then return nil end
 local ancestor:Instance?=part.Parent
 local belongs=false
 for _=1,MAX_ANCESTOR_STEPS do
  if not ancestor then break end
  if ancestor.Name=="EGGRUMBLE_StoneGiantVisual_VisualOnly" then
   belongs=true;break
  end
  ancestor=ancestor.Parent
 end
 if not belongs then return nil end
 local silhouette=part.Name:find("CrownHorn",1,true)~=nil
  or part.Name:find("BackSpine",1,true)~=nil
  or part.Name:find("FlankArmor",1,true)~=nil
 if MOBILE then return if silhouette then 118 else 52 end
 return if silhouette then 182 else 82
end

'''
    src=one(src,'local function register(instance:Instance)',helper+'local function register(instance:Instance)','HELPER')
    src=one(src,' records[instance]=maxDist\n trackedCount+=1',
        ' records[instance]=maxDist\n goroganCaps[instance]=goroganCap(instance)\n trackedCount+=1','REGISTER')
    src=one(src,' records[instance]=nil\n hidden[instance]=nil',
        ' records[instance]=nil\n goroganCaps[instance]=nil\n hidden[instance]=nil','REMOVE')
    src=one(src,'local maxDist=distance*limit*margin',
        'local maxDist=math.min(distance*limit,goroganCaps[part] or math.huge)*margin','ONE_PASS')
    src=one(src,' table.clear(hidden)\n table.clear(canopies)',
        ' table.clear(hidden)\n table.clear(goroganCaps)\n table.clear(canopies)','CLEANUP')
    must(src.count('RunService.RenderStepped:Connect')==1,'ORIGINAL_FOLIAGE_LOOP_PRESERVED')
    must(src.count('task.spawn(function()')==1,'SINGLE_EXISTING_DISTANCE_LOOP')
    for token in ('RemoteEvent','DataStoreService','Humanoid:TakeDamage','FireServer('):
        must(token not in src,'NO_AUTHORITY_'+token)
    return src

def routes(project:dict,root:pathlib.Path)->dict:
    found={}
    def walk(node:dict,parts:list[str]):
        if '$path' in node:
            key='/'.join(parts)
            must(key not in found,'DUPLICATE_ROUTE_'+key)
            f=root/node['$path']
            must(f.is_file(),'MISSING_SOURCE_'+key)
            found[key]=(f, f.read_bytes(), node.get('$className'))
        else:
            for k,v in node.items():
                if not k.startswith('$') and isinstance(v,dict): walk(v,parts+[k])
    walk(project['tree'],[])
    return found

def run(root:pathlib.Path,head:str):
    project_path=root/'EGGRUMBLE_REAL68.project.json'
    receipt_path=root/'REAL68_LEGACY_INTAKE_RECEIPT.json'
    project=json.loads(project_path.read_text())
    receipt=json.loads(receipt_path.read_text())
    old=routes(project,root)
    must(len(old)==68 and ROUTE in old,'REAL68_SOURCE_COUNT')
    must(receipt['selected_source_count']==68 and len(receipt['source_hashes'])==68,'ORIGINAL_RECEIPT_COUNT')
    must(receipt['official_head']==head and receipt['candidate_head']==head,'CURRENT_HEAD_RECEIPT')
    must(receipt['source_adopted_flags']==['TWIN_BIOMES_4NPC_V1','TWIN_CREATURE_TRAINING_V1','TWIN_BOND_PVE_COMPANION_V1'],'TWIN_INHERITANCE')
    must(receipt['source_classes'][ROUTE]=='LocalScript','EXISTING_CLIENT_OWNER')
    for k,(f,b,cls) in old.items():
        must(sha(b)==receipt['source_hashes'][k],'PARENT_HASH_'+k)
    src=old[ROUTE][1].decode('utf8')
    result=patch(src).encode('utf8')
    must(result!=old[ROUTE][1],'REAL_SOURCE_CHANGE')
    must(not (root/'off68').exists(),'NO_DOUBLE_OFF68')
    rollback=root/'off68'
    rollback.mkdir()
    for k,(f,body,cls) in old.items():
        rel=f.relative_to(root)
        out=rollback/rel
        out.parent.mkdir(parents=True,exist_ok=True)
        out.write_bytes(body)
    (rollback/'EGGRUMBLE_REAL68.project.json').write_bytes(project_path.read_bytes())
    must(len(routes(project,rollback))==68,'OFF68_EXACT_68')
    for k,(f,b,cls) in old.items():
        must(routes(project,rollback)[k][1]==b,'OFF68_NONLOSS_'+k)
    shutil.copyfile(root/'EGGRUMBLE_REAL68_PRIVATE.rbxlx',root/'OFF68_EXACT_PRE_LOD.rbxlx')
    old[ROUTE][0].write_bytes(result)
    new=routes(project,root)
    must(len(new)==68,'POST_SOURCE_COUNT')
    for k,(f,b,cls) in old.items():
        must(new[k][1]==(result if k==ROUTE else b),'MUTATION_ONLY_TARGET_'+k)
    receipt['source_hashes'][ROUTE]=sha(result)
    receipt['rc86_gorogan_mobile_lod']={
       'flag':FLAG,'original_rc86_artifact':14161823401,
       'original_legacy_policy':'FB015_GOROGAN_MOBILE_LOD_V1',
       'single_existing_owner':ROUTE,'all68_routes_preserved':True,
       'other67_selected_source_bodies_byte_identical':True,
       'old_client_sha256':sha(old[ROUTE][1]),'new_client_sha256':sha(result),
       'thresholds_mobile_studs':[52,118], 'thresholds_desktop_studs':[82,182],
       'no_new_scripts_or_remotes':True,'hysteresis_and_single_pass_retained':True,
       'rollback':'off68/ original complete 68 source tree and OFF68_EXACT_PRE_LOD.rbxlx',
       'native_rojo':'PENDING_POST_PATCH','studio':'NOT_TESTED','android':'NOT_TESTED',
       'art':'NOT_TESTED','owner_acceptance':False,'publish':False
    }
    receipt_path.write_text(json.dumps(receipt,sort_keys=True,ensure_ascii=False,indent=2)+'\n')
    print('REAL68_GOROGAN_RC86_DETAIL_LOD_SELECTED_ONE_A01_67_UNCHANGED_OFF68_READY')

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--base',required=True,type=pathlib.Path)
    p.add_argument('--head',required=True)
    a=p.parse_args()
    run(a.base,a.head)
