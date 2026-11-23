#!/usr/bin/env python3
"""Build a locked one-source GQ805 proposal and its exact inverse. No network/writes to RC."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import types

HERE=Path(__file__).resolve().parent
SOURCE='StarterPlayer/StarterPlayerScripts/GQ805_ShopKioskClient.client.luau'
PROJECT='EGGRUMBLE_REAL69.project.json'
PLACE='EGGRUMBLE_REAL69_PRIVATE.rbxlx'
HELPER='quality_gameplay/gq470_union22_real69_20261122/compose_union22.py'

def need(ok, reason):
    if not ok: raise ValueError('RED_GQ805_'+reason)

def identity(raw):
    return {'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}

def strict_json(raw):
    def pairs(items):
        result={}
        for key,value in items:
            need(key not in result,'DUPLICATE_JSON_KEY')
            result[key]=value
        return result
    def constant(value):
        raise ValueError('RED_GQ805_NONFINITE_JSON:'+value)
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=constant)

def matches(raw, record):
    return (type(record) is dict and type(record.get('bytes')) is int
            and type(record.get('sha256')) is str and identity(raw)==record)

def load_contract(directory=HERE):
    lock=strict_json((directory/'source_lock.json').read_bytes())
    patch=strict_json((directory/'shop_lifecycle_patch.json').read_bytes())
    need(lock.get('schema')=='GQ805_SHOP_LIFECYCLE_LOCK_V1','LOCK_SCHEMA')
    need(patch.get('schema')=='GQ805_SINGLE_EXISTING_SOURCE_REPLACEMENT_V1','PATCH_SCHEMA')
    need(patch.get('source')==SOURCE and lock.get('changed_source')==SOURCE,'SCOPE')
    need(len(lock.get('sources',{}))==69,'SOURCE_COUNT')
    need(type(patch.get('before_body')) is str and type(patch.get('after_body')) is str,'PATCH_BODY')
    before,after=patch['before_body'].encode(),patch['after_body'].encode()
    need(matches(before,patch.get('before')) and matches(after,patch.get('after')),'PATCH_IDENTITIES')
    need(patch['before']==lock['sources'][SOURCE]['identity'],'PATCH_BASE_LOCK')
    need(patch['after']==lock.get('candidate_source'),'PATCH_AFTER_LOCK')
    need(before!=after and len(after)>0,'EMPTY_CHANGE')
    return lock,patch

def transform(raw, patch, reverse=False):
    old='after' if reverse else 'before'
    new='before' if reverse else 'after'
    need(matches(raw,patch[old]) and raw==patch[old+'_body'].encode(),'TRANSFORM_INPUT')
    result=patch[new+'_body'].encode()
    need(matches(result,patch[new]),'TRANSFORM_OUTPUT')
    return result

def load_helper(repo, lock):
    path=repo/HELPER
    need(path.is_file() and not path.is_symlink(),'HELPER_FILE')
    raw=path.read_bytes()
    need(matches(raw,lock['inventory_helper']),'HELPER_DRIFT')
    module=types.ModuleType('gq805_locked_inventory')
    module.__file__=str(path.resolve())
    exec(compile(raw,str(path),'exec'),module.__dict__)
    return module

def inspect_base(base,lock,helper):
    project=helper.read_file(helper.safe(base,PROJECT))
    place=helper.read_file(helper.safe(base,PLACE))
    need(matches(project,lock['project']) and matches(place,lock['place']),'PARENT_PROJECT_PLACE')
    inventory=helper.project_inventory(project)
    need(set(inventory)==set(lock['sources']),'PROJECT_SOURCE_SET')
    found=set()
    for path in (base/'sources').rglob('*'):
        need(not path.is_symlink(),'SOURCE_SYMLINK')
        if path.is_file(): found.add(path.relative_to(base/'sources').as_posix())
    need(found==set(inventory),'EXTRA_OR_MISSING_SOURCE')
    raws={}
    for name,meta in inventory.items():
        raw=helper.read_file(helper.safe(base,'sources/'+name))
        expected=lock['sources'][name]
        need(matches(raw,expected['identity']) and meta==expected['project'],'SOURCE_DRIFT:'+name)
        raws[name]=raw
    place_sources,structure=helper.place_inventory(place)
    for name,meta in inventory.items():
        need(place_sources[meta['route']]=={'class':meta['class'],'raw':raws[name]},'PARENT_PLACE_SOURCE:'+name)
    need(matches(structure,lock['non_source_structure']),'PARENT_NON_SOURCE_STRUCTURE')
    return project,place,raws,structure

def run(command):
    result=subprocess.run([str(x) for x in command],capture_output=True,timeout=120)
    need(type(result.returncode) is int and result.returncode==0,'PROCESS_FAILURE:'+result.stderr.decode(errors='replace')[:1000])
    return {'command':[str(x) for x in command],'exit_code':result.returncode,
            'stdout':identity(result.stdout),'stderr':identity(result.stderr)}

def build(base,out,repo,compiler,rojo,archive,source_head=None,contract=HERE):
    lock,patch=load_contract(contract)
    if source_head is not None: need(re.fullmatch('[0-9a-f]{40}',source_head) is not None,'SOURCE_HEAD')
    helper=load_helper(repo,lock)
    project,parent_place,before,parent_structure=inspect_base(base,lock,helper)
    need(matches(helper.read_file(archive),lock['official_artifact']['archive']),'PARENT_ARCHIVE')
    need(matches(helper.read_file(rojo),lock['toolchain']['rojo_binary']),'ROJO_BINARY')
    need(not out.exists(),'OUTPUT_ALREADY_EXISTS')
    need(not out.resolve().is_relative_to(base.resolve()) and not base.resolve().is_relative_to(out.resolve()),'OUTPUT_OVERLAPS_INPUT')
    after=dict(before);after[SOURCE]=transform(before[SOURCE],patch)
    restored=dict(after);restored[SOURCE]=transform(after[SOURCE],patch,reverse=True)
    need(restored==before,'INVERSE_SOURCE_MISMATCH')
    need([n for n in before if before[n]!=after[n]]==[SOURCE],'CHANGED_SOURCE_SCOPE')
    out.mkdir(parents=True)
    process=[]
    profiles={}
    for label,raws in [('ON69',after),('OFF69',restored)]:
        root=out/label;root.mkdir()
        (root/PROJECT).write_bytes(project)
        for name,raw in sorted(raws.items()):
            path=root/'sources'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
            process.append(run([compiler,'--text',path]))
        process.append(run([rojo,'build',root/PROJECT,'-o',root/PLACE]))
        built=(root/PLACE).read_bytes()
        actual,structure=helper.place_inventory(built)
        need(structure==parent_structure,'NON_SOURCE_STRUCTURE_CHANGED:'+label)
        for name,meta in helper.project_inventory(project).items():
            need(actual[meta['route']]=={'class':meta['class'],'raw':raws[name]},'BUILT_SOURCE_OR_CLASS:'+label+':'+name)
        if label=='OFF69': need(built==parent_place,'OFF_PLACE_BYTES')
        profiles[label]={'source_count':len(raws),'place':identity(built),'project':identity(project),
                         'sources':{n:identity(v) for n,v in sorted(raws.items())}}
    shutil.copyfile(archive,out/'OFF_ORIGINAL_PARENT_ARTIFACT.zip')
    receipt={'schema':'GQ805_LOCAL_SOURCE_BUILD_V1','created_at':datetime.now(timezone.utc).isoformat(),
        'status':'ISOLATED_SOURCE_BUILD_NOT_OFFICIAL_ADOPTION','source_head':source_head,
        'base_rc':lock['base_rc'],'changed_source':SOURCE,'source_bytes_delta':len(after[SOURCE])-len(before[SOURCE]),
        'other68_exact':True,'all69_routes_classes_exact':True,'off_source_project_place_exact':True,
        'profiles':profiles,'process':process,'compiler':identity(helper.read_file(compiler)),
        'rojo':identity(helper.read_file(rojo)),'official_parent_archive':lock['official_artifact']['archive'],
        'studio':'NOT_TESTED','android':'NOT_TESTED','fun':'NOT_TESTED','RC_adopted':False}
    (out/'BUILD_RECEIPT.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    return receipt

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for flag in ('base','out','repo-root','luau-compile','rojo','parent-archive'):
        p.add_argument('--'+flag,type=Path,required=True)
    p.add_argument('--source-head')
    p.add_argument('--contract-dir',type=Path,default=HERE)
    a=p.parse_args()
    r=build(a.base,a.out,a.repo_root,a.luau_compile,a.rojo,a.parent_archive,a.source_head,a.contract_dir)
    print(json.dumps({'result':r['status'],'delta':r['source_bytes_delta'],
        'on_place':r['profiles']['ON69']['place'],'off_place':r['profiles']['OFF69']['place']},ensure_ascii=False))

if __name__=='__main__': main()
