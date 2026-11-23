#!/usr/bin/env python3
"""PR943 exact one-client PREP, Native/Rojo checks and reversible composition.

SOURCE_QA does not grant formal RC, Studio, ART, Android or FUN acceptance.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, shutil, subprocess, sys, tempfile
from pathlib import Path
from xml.etree import ElementTree as ET

DIR=Path(__file__).resolve().parent
REPO=DIR.parents[1]
PATCH=DIR/'ROLE_MOTION_REAL69.patch'
LOCK=json.loads((DIR/'source_lock.json').read_text())
ROUTE='StarterPlayer/StarterPlayerScripts/EGGRUMBLE_ProceduralSkills'
REL='sources/'+ROUTE+'.client.luau'
PROJECT='EGGRUMBLE_REAL69.project.json'
BASE=LOCK['runtime_source']['base']['sha256']
ORIGINAL=LOCK['runtime_source']['original943']['sha256']
NEW=LOCK['candidate_source']['sha256']
RC=LOCK['official_parent']['head_sha']
FEATURE='GQ470_FB015_ROLE_MOTION_READABLE_REAL69_20261121'

def sha(data): return hashlib.sha256(data).hexdigest()
def identity(data): return {'bytes':len(data),'sha256':sha(data)}
def check(test,name):
    if not test: raise AssertionError('ROLE_MOTION_RED_'+name)
def integer(value,wanted): return type(value) is int and value==wanted
def write_json(path,data): path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')

def selected(root):
    tree=json.loads((root/PROJECT).read_text())['tree'];found={}
    def walk(node,parents):
        for name,item in node.items():
            if name.startswith('$') or not isinstance(item,dict): continue
            route='/'.join(parents+[name])
            if '$path' in item: found[route]=root/item['$path']
            else: walk(item,parents+[name])
    walk(tree,[])
    check(len(found)==69 and found.get(ROUTE)==root/REL,'SELECTED_69_ROUTE')
    check(all(p.is_file() and not p.is_symlink() and p.resolve().is_relative_to(root.resolve())
              for p in found.values()),'ALL69_REGULAR_IN_ROOT')
    return found

def validate(source):
    check(source.startswith('--!strict\n'),'LUAU_STRICT')
    check('if not RunService:IsStudio() then return end' in source,'STUDIO_ONLY')
    check('EGGRUMBLE_SkillCastSignature' in source,'SERVER_CAST')
    check('local MAX_ANIMATED_AVATARS=16' in source and 'local MAX_VIEW_DISTANCE=130' in source,'MOBILE_BOUNDS')
    check('local DURATION={A=.26,B=.48,C=.82}' in source,'SERVER_PACING')
    check(source.count('RunService.PreSimulation:Connect(')==1 and 'RenderStepped:Connect(' not in source,'ONE_LOOP')
    check('local pulse,snap=motionProfile(t,slot)' in source and 'local function smoothstep(t:number)' in source,'TIMING')
    check('local strikeEnd=(slot=="A") and .36 or .42' in source,'A_STRIKE_PHASE')
    check('local holdEnd=(slot=="A") and .62 or .54' in source,'A_25FPS_HOLD')
    check('characterListener:Disconnect()' in source,'LISTENER_CLEANUP')
    check('resetPose(record)\n   active[uid]=nil\n  end' in source,'OFFSCREEN_UNPOSE')
    check('EGGRUMBLE_BasicCastSerial' in source and 'binding.token~=token' in source,'BASIC_SERVER_OBSERVER')
    for job in ('WARRIOR','MAGE','NINJA','TRAPPER','BUILDER','BEAST','ZOMBIE'):
        check('role=="'+job+'"' in source,'JOB_'+job)
    for denied in ('Instance.new(',':FireServer(',':TakeDamage(','DataStoreService','task.spawn(','task.wait('):
        check(denied not in source,'NO_AUTHORITY_'+denied)

def test_mutations(source):
    # Original four negative controls remain in force.
    for token in ('characterListener:Disconnect()','local pulse,snap=motionProfile(t,slot)',
                  'if not RunService:IsStudio() then return end','RunService.PreSimulation:Connect('):
        check(token in source,'NEGATIVE_PRECONDITION')
        try: validate(source.replace(token,'',1))
        except AssertionError: continue
        raise AssertionError('ROLE_MOTION_MUTANT_NOT_REJECTED_'+token)

def validate_parent_api(run,artifacts,jobs,ref):
    parent=LOCK['official_parent'];wanted=parent['artifact']
    check(ref.get('object',{}).get('sha')==RC,'FRESH_FORMAL_REF')
    check(integer(run.get('id'),parent['run_id']) and integer(run.get('run_attempt'),1),'PARENT_RUN_ATTEMPT')
    check(run.get('head_sha')==RC and run.get('head_branch')==parent['branch'],'PARENT_HEAD_BRANCH')
    check(run.get('event')=='push' and run.get('path')==parent['workflow'],'PARENT_PUSH_WORKFLOW')
    check(run.get('repository',{}).get('full_name')==parent['repository'],'PARENT_REPOSITORY')
    check(run.get('status')=='completed' and run.get('conclusion')=='success','PARENT_RUN_GREEN')
    matched=[a for a in artifacts.get('artifacts',[]) if a.get('name')==wanted['name']]
    check(len(matched)==1,'UNIQUE_ARTIFACT_NAME');artifact=matched[0]
    check(integer(artifact.get('id'),wanted['id']) and artifact.get('expired') is False,'ARTIFACT_ID_LIVE')
    check(integer(artifact.get('size_in_bytes'),wanted['zip']['bytes']),'ARTIFACT_SIZE')
    check(artifact.get('digest')=='sha256:'+wanted['zip']['sha256'],'ARTIFACT_DIGEST')
    wr=artifact.get('workflow_run',{})
    check(integer(wr.get('id'),parent['run_id']) and wr.get('head_sha')==RC
          and wr.get('head_branch')==parent['branch'],'ARTIFACT_RUN_HEAD')
    matched=[j for j in jobs.get('jobs',[]) if integer(j.get('id'),parent['job_id'])]
    check(len(matched)==1,'PINNED_JOB');job=matched[0]
    check(integer(job.get('run_id'),parent['run_id']) and job.get('name')=='compose-one-v3'
          and job.get('status')=='completed' and job.get('conclusion')=='success','PARENT_JOB_GREEN')

def parent_api_self_test():
    p=LOCK['official_parent'];a=p['artifact']
    valid=[{'id':p['run_id'],'run_attempt':1,'head_sha':RC,'head_branch':p['branch'],
            'event':'push','path':p['workflow'],'repository':{'full_name':p['repository']},
            'status':'completed','conclusion':'success'},
           {'artifacts':[{'id':a['id'],'name':a['name'],'expired':False,'size_in_bytes':a['zip']['bytes'],
                         'digest':'sha256:'+a['zip']['sha256'],'workflow_run':{'id':p['run_id'],'head_sha':RC,'head_branch':p['branch']}}]},
           {'jobs':[{'id':p['job_id'],'run_id':p['run_id'],'name':'compose-one-v3','status':'completed','conclusion':'success'}]},
           {'object':{'sha':RC}}]
    validate_parent_api(*valid)
    changes=[(0,('run_attempt',),True),(0,('head_sha',),'0'*40),(0,('event',),'pull_request'),
             (0,('conclusion',),'failure'),(1,('artifacts',0,'expired'),True),
             (1,('artifacts',0,'id'),0),(1,('artifacts',0,'digest'),'sha256:'+'0'*64),
             (2,('jobs',0,'id'),0),(3,('object','sha'),'0'*40)]
    for index,path,value in changes:
        mutant=copy.deepcopy(valid);item=mutant[index]
        for key in path[:-1]: item=item[key]
        item[path[-1]]=value
        try: validate_parent_api(*mutant)
        except AssertionError: continue
        raise AssertionError('PARENT_METADATA_MUTATION_ACCEPTED')
    return len(changes)

def patched(source,patch,reverse=False):
    with tempfile.TemporaryDirectory(prefix='gq943-exact-') as td:
        root=Path(td);target=root/REL;target.parent.mkdir(parents=True);target.write_bytes(source)
        patchfile=root/'change.patch';patchfile.write_bytes(patch)
        args=['patch','-p1','--batch','--fuzz=0','--reject-file=-','-i',str(patchfile)]
        if reverse: args.append('--reverse')
        result=subprocess.run(args,cwd=root,capture_output=True)
        check(result.returncode==0,'PATCH_EXACT_PREIMAGE_'+result.stdout.decode(errors='replace')[:120])
        return target.read_bytes()

def compose(base,out,archive=None,api_dir=None):
    check(not out.exists(),'NO_OVERWRITE')
    for name,pin in LOCK['official_parent']['files'].items():
        check(identity((base/name).read_bytes())==pin,'PARENT_FILE_'+name)
    if archive is not None:
        check(identity(archive.read_bytes())==LOCK['official_parent']['artifact']['zip'],'PARENT_ZIP')
    if api_dir is not None:
        check(archive is not None,'API_CONTEXT_REQUIRES_ZIP')
        validate_parent_api(*(json.loads((api_dir/name).read_text()) for name in ('run.json','artifacts.json','jobs.json','ref.json')))
    old=selected(base)
    check({k:sha(p.read_bytes()) for k,p in old.items()}==LOCK['parent_source_hashes'],'PARENT_ALL69_HASHES')
    receipt=json.loads((base/'REAL69_LEGACY_INTAKE_RECEIPT.json').read_text())
    check(receipt['source_hashes']==LOCK['parent_source_hashes'],'ORIGINAL_RECEIPT_HASHES')
    combined=PATCH.read_bytes();n=LOCK['original_patch']['bytes'];original,basic=combined[:n],combined[n:]
    check(identity(original)==LOCK['original_patch'],'ORIGINAL943_PATCH_PREFIX')
    check(identity(basic)==LOCK['basic_fragment'],'BASIC_FRAGMENT')
    check(identity((DIR/'test_native_motion.py').read_bytes())==LOCK['original_native21_file'],'ORIGINAL_NATIVE21_UNMODIFIED')
    source=old[ROUTE].read_bytes();stage943=patched(source,original);check(sha(stage943)==ORIGINAL,'ORIGINAL943_SOURCE')
    candidate=patched(stage943,basic);check(identity(candidate)==LOCK['candidate_source'],'NEW_SOURCE_SHA')
    basic_only=patched(source,basic)
    check(patched(basic_only,original)==candidate,'R_B_COMMUTE')
    check(patched(candidate,basic,True)==stage943,'B_INVERSE_TO_943')
    check(patched(basic_only,basic,True)==source,'B_INVERSE_TO_FORMAL')
    check(patched(candidate,original,True)==basic_only,'R_INVERSE_TO_BASIC_ONLY')
    def motions(raw): return raw[raw.index(b'local function smoothstep('):raw.index(b'local function nearby(')]
    check(motions(candidate)==motions(stage943),'ORIGINAL_MOTION_FUNCTIONS_EXACT')
    validate(candidate.decode());test_mutations(candidate.decode())
    out.mkdir(parents=True)
    # Historical formal receipts/Place remain under an explicit baseline boundary.
    shutil.copytree(base,out/'BASELINE_EVIDENCE')
    shutil.copytree(base/'sources',out/'sources');shutil.copy2(base/PROJECT,out/PROJECT)
    (out/REL).write_bytes(candidate)
    off=out/'OFF69_SOURCE_EXACT';shutil.copytree(base/'sources',off/'sources');shutil.copy2(base/PROJECT,off/PROJECT)
    shutil.copy2(base/'REAL69_LEGACY_INTAKE_RECEIPT.json',off/'REAL69_LEGACY_INTAKE_RECEIPT.json')
    lineage=out/'lineage';lineage.mkdir()
    (lineage/'ORIGINAL943_ProceduralSkills.client.luau').write_bytes(stage943)
    (lineage/'BASIC_ONLY_ALGEBRA_NOT_ADMITTED.client.luau').write_bytes(basic_only)
    (lineage/'ORIGINAL943.patch').write_bytes(original);(lineage/'BASIC_ONLY.patch').write_bytes(basic)
    on=selected(out);rolled=selected(off)
    check({k for k in old if on[k].read_bytes()!=rolled[k].read_bytes()}=={ROUTE},'ONLY_ONE_SELECTED')
    check(all(old[k].read_bytes()==rolled[k].read_bytes() for k in old),'OFF69_EXACT')
    check((out/PROJECT).read_bytes()==(off/PROJECT).read_bytes(),'PROJECT_EXACT')
    hashes={k:sha(v.read_bytes()) for k,v in on.items()}
    write_json(out/'REAL69_LEGACY_INTAKE_RECEIPT.json',{'schema':FEATURE+'_CANDIDATE_ONLY_V2',
        'source_profile':'REAL69','selected_source_count':69,'source_hashes':hashes,
        'source_classes':receipt['source_classes'],'legacy_48_all_ported':False,
        'official_branch':LOCK['official_parent']['branch'],'build_head':None,
        'parent_receipt_sha256':LOCK['official_parent']['files']['REAL69_LEGACY_INTAKE_RECEIPT.json']['sha256'],
        'official_base_head':RC,'formal_rc_adopted':False,'source_status':'SOURCE_ONLY_NOT_FORMAL'})
    report={'schema':FEATURE+'_BASIC_V2','execution_context':'SOURCE_ONLY_NOT_FORMAL',
        'official_head':RC,'official_source_artifact_id':LOCK['official_parent']['artifact']['id'],
        'official_parent':LOCK['official_parent'],'original_source_route':ROUTE,'class':'LocalScript',
        'base_sha256':BASE,'original943_sha256':ORIGINAL,'candidate_sha256':NEW,
        'candidate_source_bytes':len(candidate),'on_sources':69,'off_sources':69,'unchanged':68,
        'changed_routes':[ROUTE],'negative_tests':4,'parent_metadata_negative_tests':parent_api_self_test(),
        'R_B_commutation_and_inverse':'PASS','basic_only_scope':'ALGEBRA_AND_ROLLBACK_ONLY_NOT_ALL20_OR_ART_ACCEPTANCE',
        'added_parts':0,'added_remotes':0,'added_render_loops':0,'native_luau':'PENDING',
        'rojo_on_off':'PENDING','studio':'NOT_TESTED','android15':'NOT_TESTED',
        'human_before_after_screenshots':'0/32','art_gate':'NO_GO','fun_gate':'NO_GO',
        'owner_accepted':False,'formal_rc_adopted':False}
    write_json(out/'ART_CHECK_REPORT_ROLE_MOTION.json',report)
    shutil.copy2(DIR/'source_lock.json',out/'ROLE_MOTION_SOURCE_LOCK.json')
    handoff=out/'B220_ONE_SOURCE_NOT_FORMAL';(handoff/'selected_sources').mkdir(parents=True)
    shutil.copy2(on[ROUTE],handoff/'selected_sources/EGGRUMBLE_ProceduralSkills.client.luau')
    write_json(handoff/'SOURCE_SELECT_MANIFEST.json',report)
    print('GQ470_ROLE_MOTION_REAL69_ONE_SOURCE_68_UNCHANGED_OFF69_NEG4_PASS_NOT_STUDIO')
    return report

def verify(root,luau,compiler,luau_source,rojo):
    report=json.loads((root/'ART_CHECK_REPORT_ROLE_MOTION.json').read_text())
    check(report['candidate_sha256']==NEW and sha((root/REL).read_bytes())==NEW,'VERIFY_SELECTED_SOURCE')
    expected=dict(LOCK['parent_source_hashes']);expected[ROUTE]=NEW
    check({k:sha(p.read_bytes()) for k,p in selected(root).items()}==expected,'VERIFY_ALL69_PINNED')
    check({k:sha(p.read_bytes()) for k,p in selected(root/'OFF69_SOURCE_EXACT').items()}==LOCK['parent_source_hashes'],'VERIFY_OFF69_PINNED')
    for profile in (root,root/'OFF69_SOURCE_EXACT'):
        check(identity((profile/PROJECT).read_bytes())==LOCK['official_parent']['files'][PROJECT],'VERIFY_PROJECT_PINNED')
    check(identity((DIR/'test_native_cast_wiring.py').read_bytes())==LOCK['native20_runner_file'],'VERIFY_NATIVE20_RUNNER')
    evidence=root/'candidate_evidence';evidence.mkdir(exist_ok=False)
    commands=[]
    def run(argv,name):
        result=subprocess.run([str(x) for x in argv],capture_output=True,timeout=120)
        (evidence/(name+'.stdout.log')).write_bytes(result.stdout)
        (evidence/(name+'.stderr.log')).write_bytes(result.stderr)
        commands.append({'name':name,'argv':[str(x) for x in argv],'exit_code':result.returncode,
                         'stdout':identity(result.stdout),'stderr':identity(result.stderr)})
        check(result.returncode==0,'COMMAND_'+name)
        return result
    for label,profile in (('on',root),('off',root/'OFF69_SOURCE_EXACT')):
        for index,path in enumerate(selected(profile).values()): run([compiler,'--text',path],f'compile_{label}_{index:02}')
    generated=evidence/'original21.luau'
    run([sys.executable,'-B',DIR/'test_native_motion.py','--root',root,'--out',generated],'original21_generator')
    run([luau,generated],'original21_native')
    native=evidence/'full_client20'
    run([sys.executable,'-B',DIR/'test_native_cast_wiring.py','--source-root',root/'sources',
         '--reference',root/'lineage/ORIGINAL943_ProceduralSkills.client.luau','--luau',luau,
         '--compiler',compiler,'--luau-source',luau_source,'--out',native,'--expect','green','--label','PR943_BASIC_CANDIDATE'],
        'full_client20')
    baseline=evidence/'unmodified_baseline_red'
    run([sys.executable,'-B',DIR/'test_native_cast_wiring.py','--source-root',root/'OFF69_SOURCE_EXACT/sources',
         '--reference',root/'OFF69_SOURCE_EXACT'/REL,'--luau',luau,'--compiler',compiler,
         '--luau-source',luau_source,'--out',baseline,'--expect','red','--label','FORMAL_BASELINE_EXPECTED_RED'],
        'baseline_red')
    on_place=root/'GQ470_ROLE_MOTION_ON69_PRIVATE.rbxlx';off_place=root/'GQ470_ROLE_MOTION_OFF69_PRIVATE.rbxlx'
    run([rojo,'build',root/PROJECT,'-o',on_place],'rojo_on')
    run([rojo,'build',root/'OFF69_SOURCE_EXACT'/PROJECT,'-o',off_place],'rojo_off')
    check(off_place.read_bytes()==(root/'BASELINE_EVIDENCE/EGGRUMBLE_REAL69_PRIVATE.rbxlx').read_bytes(),'OFF_PLACE_BYTE_EXACT')
    check(identity(off_place.read_bytes())==LOCK['official_parent']['files']['EGGRUMBLE_REAL69_PRIVATE.rbxlx'],'OFF_PLACE_ORIGINAL_PIN')
    def stripped(path):
        doc=ET.parse(path).getroot();check(len(list(doc.iter('Item')))==75,'PLACE_75_INSTANCES')
        sources=[p for p in doc.iter() if p.get('name')=='Source'];check(len(sources)==69,'PLACE_69_SOURCES')
        for p in sources: p.text=''
        return ET.tostring(doc)
    check(stripped(on_place)==stripped(off_place),'NON_SOURCE_PLACE_PROPERTIES_EXACT')
    verifier=REPO/'quality_gameplay/gq8_lss_real31_20261117/rehydrate_real31.py'
    for label,profile,place in (('on',root,on_place),('off',root/'OFF69_SOURCE_EXACT',off_place)):
        run([sys.executable,'-B',verifier,'verify','--project',profile/PROJECT,'--place',place,'--count','69'],'source_class_'+label)
    audit=REPO/'quality_gameplay/gq8_rc85_rc86_real69_feature_truth_20261120/audit_legacy48.py'
    run([sys.executable,'-B',audit,'--self-test'],'legacy48_negative')
    run([sys.executable,'-B',audit,'--base',root,'--report',root/'LEGACY48_FEATURE_AUDIT.json'],'legacy48_actual')
    result=json.loads((native/'REPORT.json').read_text())
    check(result['expectation_observed'] is True and integer(result['summary']['passed'],20)
          and integer(result['summary']['failed'],0) and integer(result['native']['exit_code'],0)
          and result['source']['sha256']==NEW and result['all_inputs_unchanged'] is True,'ACTUAL_NATIVE20_RECEIPT')
    check(result['reference']['sha256']==ORIGINAL,'NATIVE20_ORIGINAL943_REFERENCE')
    for key,lock_key in (('fixture','native20_fixture'),('cases','native20_cases')):
        check({k:result[key][k] for k in ('bytes','sha256')}==LOCK[lock_key],'NATIVE20_'+key.upper()+'_PIN')
    report.update(native_luau='SOURCE_PASS_69_ON_OFF_AND_ORIGINAL21_PLUS_FULLCLIENT20',
        rojo_on_off='SOURCE_PASS',candidate_private_place_bytes=on_place.stat().st_size,
        candidate_private_place_sha256=sha(on_place.read_bytes()),off_place=identity(off_place.read_bytes()),
        unchanged_non_source_place_properties=True,source_gate='SOURCE_QA_PASS_NOT_ENGINE',
        compile_count=138,native_contract_count=20,original_motion_contract_count=21,
        formal_rc_adopted=False,owner_accepted=False,art_gate='NO_GO',fun_gate='NO_GO',
        studio='NOT_TESTED',android15='NOT_TESTED')
    write_json(evidence/'commands.json',commands)
    write_json(root/'ART_CHECK_REPORT_ROLE_MOTION.json',report)
    write_json(root/'B220_ONE_SOURCE_NOT_FORMAL/SOURCE_SELECT_MANIFEST.json',report)
    print('GQ470_ROLE_MOTION_BASIC_SOURCE_QA_PASS_ORIGINAL21_FULLCLIENT20_ROJO69_OFF69_NOT_STUDIO')
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base',type=Path);p.add_argument('--out',type=Path)
    p.add_argument('--archive',type=Path);p.add_argument('--api-dir',type=Path)
    p.add_argument('--self-test',action='store_true');p.add_argument('--verify',type=Path)
    for name in ('luau','compiler','luau-source','rojo'): p.add_argument('--'+name,type=Path)
    a=p.parse_args()
    if a.self_test: print('PARENT_METADATA_NEGATIVE_PASS',parent_api_self_test());return
    if a.verify:
        check(all((a.luau,a.compiler,a.luau_source,a.rojo)),'VERIFY_TOOL_PATHS_REQUIRED')
        verify(*(x.resolve() for x in (a.verify,a.luau,a.compiler,a.luau_source,a.rojo)));return
    check(a.base is not None and a.out is not None,'BASE_AND_OUT_REQUIRED')
    compose(a.base.resolve(),a.out.resolve(),a.archive.resolve() if a.archive else None,
            a.api_dir.resolve() if a.api_dir else None)
if __name__=='__main__': main()
