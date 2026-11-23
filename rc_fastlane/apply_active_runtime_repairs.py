#!/usr/bin/env python3
"""Select reviewed ACTIVE66 repairs for the existing primary Place producer.

The original 66-source distribution remains immutable for its existing strict
PRIVATE70+ consumers. This adapter creates no Game, Remote, Store writer, or
new build pipeline. Independent switches select Game lifecycle or Store retry
repairs. Equipment recovery additionally requires Game lifecycle repairs.
Disabling all performs no filesystem writes, including lock writes.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET

FEATURE_ROOT=Path(__file__).resolve().parent/'features/active_runtime_repairs'
MANIFEST_SHA256='9584b9fddf3a0ec13f918f356d0380eeed61084ab90ad811f77c19a21b787e9f'
CONTINUATION_MANIFEST_SHA256='badf8c3fe09fe23eec65f1549db9c52318c34a423ce5d36259cb84aff9b87e76'
CONTINUATION_FLAG='persistence_continuation_v1'
CONTINUATION_ID='ACTIVE66_PERSISTENCE_REVISION_UI_V1'
REPAIR_FLAGS=(('game_lifecycle','game_fixes'),('evolution_retry','evolution_retry'),
              ('equip_failure_recovery','equip_recovery'))
SELECTION_FILE='ACTIVE_RUNTIME_SELECTION.json'
SOURCE_MANIFEST='ACTIVE_RUNTIME_SOURCE_MANIFEST.json'

def check(ok,reason):
    if not ok: raise ValueError(reason)

def sha(raw): return hashlib.sha256(raw).hexdigest()
def blob(raw): return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
def encoded(value): return (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()

def read_manifest():
    raw=(FEATURE_ROOT/'MANIFEST.json').read_bytes()
    check(sha(raw)==MANIFEST_SHA256,'REPAIR_MANIFEST_DRIFT')
    manifest=json.loads(raw)
    patches={}
    for feature,spec in manifest['features'].items():
        raw=(FEATURE_ROOT/spec['patch']).read_bytes()
        check(sha(raw)==spec['patch_sha256'],'REPAIR_PATCH_DRIFT:'+feature)
        check(raw.startswith(('--- a/'+spec['path']+'\n+++ b/'+spec['path']+'\n').encode()),'REPAIR_PATCH_TARGET_DRIFT')
        patches[feature]=raw
    return manifest,patches

def read_continuation():
    root=FEATURE_ROOT/'continuation_v1'
    path=root/'MANIFEST.json'
    check(not root.is_symlink() and path.is_file() and not path.is_symlink(),'CONTINUATION_RECIPE_REQUIRED')
    raw=path.read_bytes()
    check(sha(raw)==CONTINUATION_MANIFEST_SHA256,'CONTINUATION_RECIPE_DRIFT')
    recipe=json.loads(raw)
    check(recipe['schema']=='ACTIVE66_CONTINUATION_RECIPE_V1' and recipe['id']==CONTINUATION_ID
          and recipe['parent_manifest_sha256']==MANIFEST_SHA256,'CONTINUATION_RECIPE_LINEAGE_MISMATCH')
    patches={}
    for name,spec in recipe['features'].items():
        path=root/spec['patch']
        check(path.is_file() and not path.is_symlink(),'CONTINUATION_PATCH_REQUIRED:'+name)
        raw=path.read_bytes()
        check(sha(raw)==spec['patch_sha256'],'CONTINUATION_PATCH_DRIFT:'+name)
        check(raw.startswith(('--- a/'+spec['path']+'\n+++ b/'+spec['path']+'\n').encode()),
              'CONTINUATION_PATCH_TARGET_DRIFT:'+name)
        patches[name]=raw
    return recipe,patches

def resolve_repairs(flags):
    """One exact recipe plan shared by selection, Native input and artifact binding."""
    check(all(type(flags[key]) is bool for _,key in REPAIR_FLAGS),'BOOLEAN_SELECTION_REQUIRED')
    continuation=flags.get(CONTINUATION_FLAG,False)
    check(type(continuation) is bool,'BOOLEAN_CONTINUATION_REQUIRED')
    check(not flags['equip_recovery'] or flags['game_fixes'],'RECOVERY_REQUIRES_GAME_FIXES')
    check(not continuation or all(flags[key] for _,key in REPAIR_FLAGS),'CONTINUATION_REQUIRES_ALL_THREE_REPAIRS')
    manifest,patches=read_manifest()
    chosen=[name for name,key in REPAIR_FLAGS if flags[key]]
    specs={name:manifest['features'][name] for name in chosen}
    recipe=None
    if continuation:
        recipe,extra=read_continuation()
        chosen+=list(recipe['features'])
        specs.update(recipe['features']);patches.update(extra)
    return manifest,patches,chosen,specs,recipe

def continuation_identity(recipe):
    return {'id':CONTINUATION_ID,'manifest_sha256':CONTINUATION_MANIFEST_SHA256,
            'parent_selected_source_manifest_sha256':recipe['parent_selected_source_manifest_sha256'],
            'contract_lock_sha256':recipe['contract']['sha256']}

def resolve_selection(selection):
    flags={key:selection[key] for _,key in REPAIR_FLAGS}
    if selection.get('schema')=='ACTIVE_RUNTIME_SELECTION_V2':
        check(selection.get(CONTINUATION_FLAG) is True,'V2_CONTINUATION_MUST_BE_SELECTED')
        flags[CONTINUATION_FLAG]=True
    else:
        check(selection.get('schema')=='ACTIVE_RUNTIME_SELECTION_V1'
              and CONTINUATION_FLAG not in selection and 'continuation' not in selection,'WRONG_SELECTION_SCHEMA')
    manifest,patches,chosen,specs,recipe=resolve_repairs(flags)
    check(chosen and chosen==selection['selected_repairs'],'REPAIR_SELECTION_MISMATCH')
    check(selection['selection_manifest_sha256']==MANIFEST_SHA256,'WRONG_SELECTION_LINEAGE')
    if recipe is not None:
        check(selection.get('profile')=='rich51' and selection.get('source_count')==66
              and selection.get('continuation')==continuation_identity(recipe),'CONTINUATION_SELECTION_IDENTITY_MISMATCH')
        check(selection.get('selected_source_manifest_sha256')==recipe['selected_source_manifest_sha256'],
              'CONTINUATION_SELECTED_PROFILE_MISMATCH')
    return flags,manifest,chosen,specs,recipe

def validate_selected_sources(sources,manifest,specs):
    check(len(sources)==66 and set(sources)==set(manifest['source_gitblobs']),'SELECTED66_INVENTORY_REQUIRED')
    changed={spec['path']:spec for spec in specs.values()}
    for path,raw in sources.items():
        if path in changed:
            spec=changed[path]
            check(sha(raw)==spec['after_sha256'] and len(raw)==spec['after_bytes'],'SELECTED_REPAIR_SOURCE_DRIFT:'+path)
        else:
            check(blob(raw)==manifest['source_gitblobs'][path],'UNSELECTED_SOURCE_DRIFT:'+path)

def file_map(root):
    check(root.is_dir() and not root.is_symlink(),'INVALID_OR_LINKED_DIST')
    files={}
    for path in sorted(root.rglob('*')):
        check(not path.is_symlink(),'SOURCE_SYMLINK_REFUSED')
        if path.is_file(): files[path.relative_to(root).as_posix()]=path.read_bytes()
    return files

def source_map(root):
    return {p.removeprefix('src/'):raw for p,raw in file_map(root).items()
            if p.startswith('src/') and p.endswith('.luau')}

def validate_base(base,manifest):
    files=file_map(base)
    sources={p.removeprefix('src/'):raw for p,raw in files.items()
             if p.startswith('src/') and p.endswith('.luau')}
    check(len(sources)==66,'ACTIVE_SOURCE_COUNT_DRIFT')
    pins={p:blob(raw) for p,raw in sorted(sources.items())}
    check(pins==manifest['source_gitblobs'],'WRONG_66_SOURCE_DISTRIBUTION')
    digest=sha(json.dumps(pins,sort_keys=True,separators=(',',':')).encode())
    check(digest==manifest['base_source_gitblobs_sha256'],'WRONG_66_SOURCE_DIGEST')
    for path,digest in manifest['base_metadata_sha256'].items():
        check(path in files and sha(files[path])==digest,'ORIGINAL_METADATA_DRIFT:'+path)
    check(SELECTION_FILE not in files and SOURCE_MANIFEST not in files,'ALREADY_SELECTED_DIST')
    lock=json.loads(files['SOURCE_LOCK.json'])
    features=json.loads(files['RC_FEATURE_LOCK.json'])
    check(lock['blobs']==features['source_gitblobs']==pins,'BASE_LOCK_MAP_DRIFT')
    check(lock['total_scripts']==features['total_sources']==66,'BASE_LOCK_COUNT_DRIFT')
    return files,sources,lock,features

def projected_source_manifest(stage,sources):
    project=json.loads((stage/'default.project.json').read_bytes())
    client_map={node['$path'].removeprefix('src/'):name
                for name,node in project['tree']['StarterPlayer']['StarterPlayerScripts'].items()
                if isinstance(node,dict) and '$path' in node}
    rows={}
    for path,raw in sorted(sources.items()):
        kind,filename=path.split('/',1)
        cls='Script' if filename.endswith('.server.luau') else 'LocalScript' if filename.endswith('.client.luau') else 'ModuleScript'
        suffix='.server.luau' if cls=='Script' else '.client.luau' if cls=='LocalScript' else '.luau'
        name=filename.removesuffix(suffix)
        prefix={'server':'ServerScriptService/TrapRaidersS1','client':'StarterPlayer/StarterPlayerScripts','shared':'ReplicatedStorage/TrapRaidersShared'}[kind]
        if kind=='client': name=client_map[path]
        rows[path]={'instance_path':prefix+'/'+name,'class':cls,'bytes':len(raw),
                    'sha256':sha(raw),'git_blob':blob(raw)}
    return {'schema':'ACTIVE_RUNTIME_SELECTED_SOURCES_V1','profile':'rich51',
            'source_count':len(rows),'sources':rows}

def apply(base:Path,out:Path,profile:str,game_fixes:bool,evolution_retry:bool,equip_recovery:bool=False,
          *,persistence_continuation_v1:bool=False):
    check(all(type(flag) is bool for flag in (game_fixes,evolution_retry,equip_recovery,persistence_continuation_v1)),
          'BOOLEAN_SWITCH_REQUIRED')
    check(profile in ('rich51','rich47','legacy21'),'UNKNOWN_PROFILE')
    check(profile!='rich51' or not equip_recovery or game_fixes,'EQUIP_RECOVERY_REQUIRES_GAME_FIXES')
    check(not persistence_continuation_v1 or (profile=='rich51' and game_fixes and evolution_retry and equip_recovery),
          'CONTINUATION_REQUIRES_RICH51_ALL_THREE_REPAIRS')
    if profile!='rich51' or not (game_fixes or evolution_retry):
        return {'applied':False,'selected_dist':str(base),'profile':profile,
                'game_fixes':False,'evolution_retry':False,'equip_recovery':False,'filesystem_writes':0}
    base=base.absolute();out=out.absolute()
    check(not out.exists() and not out.is_symlink(),'OUTPUT_ALREADY_EXISTS')
    check(out.resolve()!=base.resolve() and not out.resolve().is_relative_to(base.resolve()),'OUTPUT_INSIDE_INPUT')
    flags={'game_fixes':game_fixes,'evolution_retry':evolution_retry,'equip_recovery':equip_recovery}
    if persistence_continuation_v1:flags[CONTINUATION_FLAG]=True
    manifest,patches,chosen,specs,recipe=resolve_repairs(flags)
    before,original,lock,feature_lock=validate_base(base,manifest)
    expected_changed={specs[name]['path'] for name in chosen}
    out.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='active66-selection-',dir=out.parent) as temporary:
        stage=Path(temporary)/'dist'
        shutil.copytree(base,stage,symlinks=False)
        patch_commands=[]
        for name in chosen:
            if recipe is not None and name==next(iter(recipe['features'])):
                parent=projected_source_manifest(stage,source_map(stage))
                check(sha(encoded(parent))==recipe['parent_selected_source_manifest_sha256'],'CONTINUATION_PARENT_PROFILE_DRIFT')
            spec=specs[name]
            check(sha((stage/'src'/spec['path']).read_bytes())==spec['before_sha256'],'FEATURE_BASE_DRIFT:'+name)
            argv=['patch','-p1','--fuzz=0','--batch','--forward','--reject-file=-']
            for command in [argv+['--dry-run'],argv]:
                result=subprocess.run(command,cwd=stage/'src',input=patches[name],capture_output=True,timeout=15)
                check(result.returncode==0,'REVIEWED_PATCH_REJECTED:'+name)
            patch_commands.append({'feature':name,'argv':argv,'patch_sha256':spec['patch_sha256']})
            data=(stage/'src'/spec['path']).read_bytes()
            check(len(data)==spec['after_bytes'] and sha(data)==spec['after_sha256'],'PATCH_RESULT_DRIFT:'+name)
        selected=source_map(stage)
        changed={p for p in original if original[p]!=selected.get(p)}
        check(set(selected)==set(original) and changed==expected_changed,'UNAUTHORIZED_SOURCE_CHANGE')
        check((stage/'default.project.json').read_bytes()==before['default.project.json'],'PROJECT_CHANGED')
        pins={p:blob(raw) for p,raw in sorted(selected.items())}
        source_manifest=projected_source_manifest(stage,selected)
        if recipe is not None:
            check(sha(encoded(source_manifest))==recipe['selected_source_manifest_sha256'],'CONTINUATION_RESULT_PROFILE_DRIFT')
        selection={
            'schema':'ACTIVE_RUNTIME_SELECTION_V1','profile':'rich51','runtime_lane':'ACTIVE_RUNTIME',
            'source_count':66,'original_author_base_count':51,
            'game_fixes':game_fixes,'evolution_retry':evolution_retry,'equip_recovery':equip_recovery,'selected_repairs':chosen,
            'original_source_commit':manifest['source_commit'],
            'original_66_source_gitblobs_sha256':manifest['base_source_gitblobs_sha256'],
            'original_metadata_sha256':manifest['base_metadata_sha256'],
            'selection_manifest_sha256':MANIFEST_SHA256,
            'selected_source_manifest_sha256':sha(encoded(source_manifest)),
            'changed_sources':{p:{'before_bytes':len(original[p]),'before_sha256':sha(original[p]),
                                  'after_bytes':len(selected[p]),'after_sha256':sha(selected[p])} for p in sorted(changed)},
            'source_delta_bytes':sum(len(selected[p])-len(original[p]) for p in changed),
            'patch_commands':patch_commands,
            'original_distribution_modified':False,'original_overlays_preserved':True,
            'private70_and_successor_input_unchanged':True,'PRIVATE_COMPANION_modified':False,
            'rollback':'Rebuild from original66 with selected switches false. Equipment recovery requires Game fixes; all false restores original66 byte-for-byte.',
            'source_review_only':True,'formal_RC_adopted':False,'Studio':'NOT_TESTED',
            'live_DataStore_calls':0,
        }
        if recipe is not None:
            selection.update(schema='ACTIVE_RUNTIME_SELECTION_V2',persistence_continuation_v1=True,
                             continuation=continuation_identity(recipe),
                             rollback='Disable persistence_continuation_v1 to restore exact V3 selected66; disable all four switches to restore original66. Rebuild through this same producer.')
        lock['blobs']=pins;lock['rc_active_runtime_repairs']=selection
        feature_lock['source_gitblobs']=pins;feature_lock['active_runtime_repairs']=selection
        (stage/'SOURCE_LOCK.json').write_bytes(encoded(lock))
        (stage/'RC_FEATURE_LOCK.json').write_bytes(encoded(feature_lock))
        (stage/SELECTION_FILE).write_bytes(encoded(selection))
        (stage/SOURCE_MANIFEST).write_bytes(encoded(source_manifest))
        after=file_map(stage)
        allowed={'src/'+p for p in changed}|{'SOURCE_LOCK.json','RC_FEATURE_LOCK.json',SELECTION_FILE,SOURCE_MANIFEST}
        check({p for p in set(before)|set(after) if before.get(p)!=after.get(p)}==allowed,'UNAUTHORIZED_DIST_CHANGE')
        check(file_map(base)==before,'ORIGINAL_DIST_MODIFIED')
        stage.rename(out)
    return {'applied':True,'selected_dist':str(out),'profile':'rich51','selection':selection}

def verify_non_source_place(raw:bytes,manifest):
    """Preserve the official Place structure/properties for source-only repairs.

    Use the parent's independently fixed official66 algorithm exactly: only
    Source .text is replaced. All other parsed XML data and ordering remain.
    Existing selected-Source verification remains separately mandatory.
    """
    anchor=manifest['place_non_source_anchor']
    check(anchor['algorithm_id']=='ELEMENTTREE_SOURCE_TEXT_SENTINEL_V1'
          and anchor['source_text_marker']=='__ACTIVE_RUNTIME_SOURCE__','NON_SOURCE_ANCHOR_ALGORITHM_DRIFT')
    root=ET.fromstring(raw)
    properties=[node for node in root.iter() if node.get('name')=='Source']
    check(len(properties)==anchor['source_properties']==66,'NON_SOURCE_ANCHOR_SOURCE_COUNT_MISMATCH')
    check(all(node.tag=='string' for node in properties),'NON_SOURCE_ANCHOR_SOURCE_TAG_MISMATCH')
    for node in properties:node.text='__ACTIVE_RUNTIME_SOURCE__'
    canonical=ET.tostring(root,encoding='utf-8')
    check(len(canonical)==anchor['canonical_bytes'] and sha(canonical)==anchor['canonical_sha256'],
          'ARTIFACT_NON_SOURCE_XML_DRIFT')
    instances=sum(1 for node in root.iter('Item'))
    check(instances==anchor['instances'],'NON_SOURCE_ANCHOR_INSTANCE_COUNT_MISMATCH')
    return {'status':'PASS','algorithm_id':anchor['algorithm_id'],
            'canonical_bytes':len(canonical),'canonical_sha256':sha(canonical),
            'source_properties':len(properties),'instances':instances,
            'official_reference':anchor['official_reference'],
            'official_place':anchor['official_place'],
            'selection_manifest_sha256':MANIFEST_SHA256}

def emit_artifact_metadata(base:Path,place:Path,selector_path:Path,active_path:Path):
    """Bind existing primary producer's artifact metadata to its actual Place.

    Called only after the existing producer's checks. The original base and
    PRIVATE consumers remain read-only. This does not build or publish a Place.
    """
    selector=json.loads(selector_path.read_bytes())
    check(Path(selector['selected_dist']).resolve()==base.resolve(),'PRODUCER_SELECTED_DIST_MISMATCH')
    manifest,_=read_manifest()
    check(sha((base/'default.project.json').read_bytes())==manifest['base_metadata_sha256']['default.project.json'],
          'ARTIFACT_PROJECT_DRIFT')
    place_raw=place.read_bytes()
    non_source_identity=verify_non_source_place(place_raw,manifest)
    source_manifest=projected_source_manifest(base,source_map(base))
    xml_rows={}
    def visit(item,parent=''):
        node=item.find("./Properties/string[@name='Name']")
        name=node.text if node is not None else ''
        path=parent+'/'+name if parent else name
        source=item.find("./Properties/string[@name='Source']")
        if source is not None and item.get('class') in ('Script','LocalScript','ModuleScript'):
            check(path not in xml_rows,'DUPLICATE_PLACE_SOURCE_PATH')
            raw=(source.text or '').encode()
            xml_rows[path]={'class':item.get('class'),'bytes':len(raw),'sha256':sha(raw),'git_blob':blob(raw)}
        for child in item.findall('Item'): visit(child,path)
    for item in ET.fromstring(place_raw).findall('Item'): visit(item)
    expected={row['instance_path']:{k:v for k,v in row.items() if k!='instance_path'}
              for row in source_manifest['sources'].values()}
    check(xml_rows==expected,'SELECTED_PLACE_PATH_CLASS_SOURCE_MISMATCH')
    selection_path=base/SELECTION_FILE
    check(selection_path.exists()==selector['applied'],'PRODUCER_SELECTION_RECEIPT_MISMATCH')
    if selector['applied']:
        selection_raw=selection_path.read_bytes()
        selection=json.loads(selection_raw)
        check(selection==selector['selection'],'PRODUCER_SELECTION_LINEAGE_MISMATCH')
        check((base/SOURCE_MANIFEST).read_bytes()==encoded(source_manifest),'PRODUCER_SOURCE_MANIFEST_DRIFT')
        flags,selected_manifest,chosen,specs,recipe=resolve_selection(selection)
        validate_selected_sources(source_map(base),selected_manifest,specs)
    else:
        selection={'schema':'ACTIVE_RUNTIME_SELECTION_V1','profile':'rich51',
                   'runtime_lane':'ACTIVE_RUNTIME','game_fixes':False,'evolution_retry':False,'equip_recovery':False,
                   'selected_repairs':[],'source_delta_bytes':0,'original_distribution_modified':False,
                   'source_count':len(source_manifest['sources']),
                   'rollback':'All repair switches are OFF; existing original producer output is selected.'}
        selection_raw=encoded(selection)
    pins={p:row['git_blob'] for p,row in source_manifest['sources'].items()}
    source_lock=(base/'SOURCE_LOCK.json').read_bytes()
    feature_lock=(base/'RC_FEATURE_LOCK.json').read_bytes()
    check(json.loads(source_lock)['blobs']==json.loads(feature_lock)['source_gitblobs']==pins,'ARTIFACT_SELECTED_LOCK_MISMATCH')
    regression_dir=place.parent/'ACTIVE_RUNTIME_REPAIR_REGRESSIONS'
    if selector['applied']:
        from rc_fastlane.features.active_runtime_repairs.regression.run_selected import artifact_binding
        regression=artifact_binding(base,regression_dir)
    else:
        check(not regression_dir.exists(),'OFF_ARTIFACT_HAS_UNSELECTED_REPAIR_REGRESSION')
        regression={'status':'NOT_SELECTED','required_suites':[],'passed':0,'failed':0}
    active=json.loads(active_path.read_bytes())
    metadata={
        'schema':'ACTIVE_RUNTIME_ARTIFACT_IDENTITY_V1','runtime_lane':'ACTIVE_RUNTIME',
        'active_profile':'rich51','effective_source_count':len(pins),
        'original_author_source_commit':active['source_profiles']['rich51']['source_commit'],
        'original_author_source_count':active['source_profiles']['rich51']['source_count'],
        'selected_repairs':selection['selected_repairs'],
        'selected_flags':{flag:selection[flag] for flag in ('game_fixes','evolution_retry','equip_recovery')},
        'selected_source_gitblobs_sha256':sha(json.dumps(pins,sort_keys=True,separators=(',',':')).encode()),
        'source_manifest_file':SOURCE_MANIFEST,'source_manifest_sha256':sha(encoded(source_manifest)),
        'selection_file':SELECTION_FILE,'selection_sha256':sha(selection_raw),
        'source_lock_file':'SOURCE_LOCK.json','source_lock_sha256':sha(source_lock),
        'feature_lock_file':'RC_FEATURE_LOCK.json','feature_lock_sha256':sha(feature_lock),
        'place_file':place.name,'place_bytes':len(place_raw),'place_sha256':sha(place_raw),
        'official_non_source_identity':non_source_identity,
        'original_distribution_used_by_private70_and_successors':True,
        'PRIVATE_COMPANION_modified':False,
        'repair_regressions':regression,
        'rollback':{'config':'rc_fastlane/ACTIVE_RUNTIME_REPAIRS.json',
                    'game_fixes':False,'evolution_retry':False,'equip_recovery':False,
                    'effect':'Rebuild with all false to restore the existing original primary source and Place bytes.'},
        'adoption_and_engine_status':'Read RC_BUILD_RECEIPT.json; source selection alone does not establish formal adoption or Studio testing.',
    }
    if selection.get(CONTINUATION_FLAG) is True:
        metadata.update(schema='ACTIVE_RUNTIME_ARTIFACT_IDENTITY_V2',continuation=selection['continuation'])
        metadata['selected_flags'][CONTINUATION_FLAG]=True
        metadata['rollback'].update(persistence_continuation_v1=False,
                                    continuation_only='Disable only persistence_continuation_v1 to restore V3 selected66 through the same producer.')
    check(place.read_bytes()==place_raw,'PLACE_CHANGED_DURING_METADATA_VALIDATION')
    for name,raw in [(SOURCE_MANIFEST,encoded(source_manifest)),(SELECTION_FILE,selection_raw),
                     ('SOURCE_LOCK.json',source_lock),('RC_FEATURE_LOCK.json',feature_lock),
                     ('ACTIVE_RUNTIME_ACTIVE.json',encoded(metadata))]:
        (place.parent/name).write_bytes(raw)
    return metadata

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--dist',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--profile',choices=('rich51','rich47','legacy21'),required=True)
    parser.add_argument('--game-fixes',choices=('true','false'),required=True)
    parser.add_argument('--evolution-retry',choices=('true','false'),required=True)
    parser.add_argument('--equip-recovery',choices=('true','false'),default='false')
    parser.add_argument('--persistence-continuation-v1',choices=('true','false'),default='false')
    args=parser.parse_args()
    result=apply(args.dist,args.out,args.profile,args.game_fixes=='true',args.evolution_retry=='true',args.equip_recovery=='true',
                 persistence_continuation_v1=args.persistence_continuation_v1=='true')
    print(json.dumps(result,indent=2))

if __name__=='__main__': main()
