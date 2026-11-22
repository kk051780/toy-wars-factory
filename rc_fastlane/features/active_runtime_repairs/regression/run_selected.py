#!/usr/bin/env python3
"""Run frozen repair contracts against the actual selected ACTIVE66 sources.

Local binary and workflow-controlled source builds are explicit trust profiles.
Fixtures retain their existing mocks and scope; this is not a new independent
approval, a complete Game bootstrap, or a Roblox engine test.
"""
from __future__ import annotations
import argparse
import base64
from contextlib import contextmanager
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys

HERE=Path(__file__).resolve().parent
LOCK_SHA256='9e8cdcd5ac9b956e31ac8e1586dd5a549f646c8f49802b16f46ed27c865ed4ce'
SUITES=('spawn12','equip9','evolution19','recovery14')
MODULES={
    'equip9':['PersistentHatchStore','ProgressionRules','EvolutionRules','SixSkillAtomicProfile',
              'FocusTrainingScheduler','SessionSixSkillXPPreview','RewardEquipRules','PowerFantasyRules','S1Rules'],
    'evolution19':['FocusTrainingScheduler','SessionSixSkillXPPreview','SixSkillAtomicProfile',
                   'ProgressionRules','EvolutionRules','PersistentHatchStore'],
    'recovery14':['FocusTrainingScheduler','SessionSixSkillXPPreview','SixSkillAtomicProfile',
                  'ProgressionRules','EvolutionRules','PersistentHatchStore','RewardEquipRules','S1Rules'],
}
EQUIP_ANCHORS={
    'CAN_WRITE':('local function canWriteProfile(player: Player): boolean\n','-- These replicated attributes are sourced from a successful canonical Store load\n'),
    'RESTORE':('local function restoreSavedProfile(player: Player)\n','-- DataStore UpdateAsync may commit despite a failed caller response.\n'),
    'COMMIT':('local function commitFreeReward(player: Player,receipt: string,item: string)\n','local function loadHatchProfile(player: Player)\n'),
    'REMOVAL':('Players.PlayerRemoving:Connect(function(player)\n','-- V4 six-skill durable ticket: minted by the ORIGINAL Game; no Remote and no\n'),
    'EQUIP':('local function applyEquipScout(player: Player,data:any)\n','local function applyActualScout('),
    'SHUTDOWN':('game:BindToClose(function()\n',None),
}
RECOVERY_ANCHORS={
    'FAILURE':('local persistenceState: {[Player]: string} = {}\n','local persistentProfiles:'),
    'CAN_WRITE':('local function canWriteProfile(player: Player): boolean\n','-- These replicated attributes'),
    'RESTORE':('local function restoreSavedProfile(player: Player)\n','-- DataStore UpdateAsync may commit'),
    'REWARD':('local function commitFreeReward(player: Player,receipt: string,item: string)\n','local function loadHatchProfile('),
    'LOAD':('local function loadHatchProfile(player: Player)\n','local scoutModels:'),
    'EQUIP':('local function applyEquipScout(player: Player,data:any)\n','local function applyActualScout('),
    'EVOLVE':('local function applyEvolveScout(player: Player,data)\n','-- P0D SEVEN JOBS / MVP v1:'),
    'REMOVE':('Players.PlayerRemoving:Connect(function(player)\n','-- V4 six-skill durable ticket:'),
}

def check(ok,reason):
    if not ok:raise ValueError(reason)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def ident(raw):return {'bytes':len(raw),'sha256':sha(raw)}
def encoded(value):return (json.dumps(value,indent=2)+'\n').encode()
def write_json(path,value):path.write_bytes(encoded(value))

def new_observation():
    return {'phase':'ARGUMENTS','owned_output':False,'processes':[],
            'source_inputs_unchanged':None,'suite_predicates':{},'suites':{}}

@contextmanager
def observe_process(observation,argv,timeout,kind,suite=None):
    record={'kind':kind,'suite':suite,'actual_argv':argv,'timeout_seconds':timeout,
            'exit_code':None,'timed_out':False,'phase':'RUNNING','stdout':None,'stderr':None}
    observation['processes'].append(record)
    try:
        yield record
    except subprocess.TimeoutExpired as error:
        record.update(timed_out=True,phase='TIMED_OUT',stdout=error.stdout,stderr=error.stderr)
        raise

def decoded_process(process,record):
    # Capture exact bytes first. TextIOWrapper retains the prior text=True
    # default encoding, strict errors and universal-newline behavior on success.
    record.update(exit_code=process.returncode,stdout=process.stdout,stderr=process.stderr,phase='STDOUT_DECODE')
    with io.TextIOWrapper(io.BytesIO(process.stdout)) as stream:stdout=stream.read()
    record['phase']='STDERR_DECODE'
    with io.TextIOWrapper(io.BytesIO(process.stderr)) as stream:stderr=stream.read()
    record['phase']='OUTPUT_CAPTURED'
    return subprocess.CompletedProcess(process.args,process.returncode,stdout,stderr)

def emit_failure(observation,exit_code,error=None):
    """Best-effort evidence only; never changes a gate result or retries work."""
    try:
        processes=[];streams=[]
        for index,record in enumerate(observation['processes']):
            item={key:value for key,value in record.items() if key not in ('stdout','stderr')}
            for channel in ('stdout','stderr'):
                raw=record[channel]
                filename=f'FAILURE_PROCESS_{index:02d}_{channel.upper()}.bin'
                item[channel]={'available':raw is not None,
                               **(ident(raw) if raw is not None else {'bytes':None,'sha256':None}),
                               'file':filename if raw is not None else None}
                if raw is not None:
                    streams.append((filename,raw,{'process_index':index,'kind':record['kind'],
                        'suite':record['suite'],'stream':channel,**ident(raw),
                        'base64':base64.b64encode(raw).decode('ascii'),
                        'utf8_display':raw.decode('utf-8',errors='backslashreplace')}))
            processes.append(item)
        diagnostic={key:value for key,value in observation.items() if key not in ('processes','owned_output')}
        diagnostic.update(schema='ACTIVE66_REPAIR_FAILURE_DIAGNOSTIC_V1',status='FAIL_DIAGNOSTIC_ONLY',
                          runner_exit=exit_code,exception_type=type(error).__name__ if error else None,
                          exception=str(error) if error else None,processes=processes,native_admission=False)
        if observation['owned_output']:
            try:
                output=Path(observation['output'])
                for filename,raw,_ in streams:(output/filename).write_bytes(raw)
                write_json(output/'FAILURE_DIAGNOSTIC.json',diagnostic)
            except Exception as diagnostic_error:
                diagnostic['diagnostic_file_error']={'type':type(diagnostic_error).__name__,'reason':str(diagnostic_error)}
        # Inert JSON lines retain recoverable bytes even if CI skips artifacts.
        print('ACTIVE66_REPAIR_FAILURE '+json.dumps(diagnostic,ensure_ascii=True),flush=True)
        for _,_,stream in streams:
            print('ACTIVE66_REPAIR_FAILURE_STREAM '+json.dumps(stream,ensure_ascii=True),flush=True)
    except Exception as diagnostic_error:
        try:print('ACTIVE66_REPAIR_DIAGNOSTIC_OUTPUT_ERROR '+repr(diagnostic_error),file=sys.stderr,flush=True)
        except Exception:pass

def piece(text,start,end):
    check(text.count(start)==1,'SOURCE_START_NOT_UNIQUE:'+start)
    tail=text.split(start,1)[1]
    if end is None:return start+tail
    check(tail.count(end)==1,'SOURCE_END_NOT_UNIQUE:'+end)
    return start+tail.split(end,1)[0]
def insert(text,marker,value):
    check(text.count(marker)==1,'FIXTURE_MARKER_NOT_UNIQUE:'+marker)
    return text.replace(marker,value,1)

def read_fixtures():
    raw=(HERE/'fixtures.lock.json').read_bytes();check(sha(raw)==LOCK_SHA256,'FIXTURE_LOCK_DRIFT')
    lock=json.loads(raw);fixtures={}
    for name,row in lock['fixtures'].items():
        path=HERE/name;check(not path.is_symlink(),'FIXTURE_SYMLINK_REFUSED')
        raw=path.read_bytes();check(ident(raw)=={k:row[k] for k in ('bytes','sha256')},'FROZEN_FIXTURE_DRIFT:'+name)
        fixtures[name]=raw.decode()
    return lock,fixtures

def selected_input(dist):
    path=HERE.parents[2]/'apply_active_runtime_repairs.py'
    spec=importlib.util.spec_from_file_location('active66_selector',path)
    selector=importlib.util.module_from_spec(spec);spec.loader.exec_module(selector)
    manifest,_=selector.read_manifest();snapshot=selector.file_map(dist)
    check(sha(snapshot['default.project.json'])==manifest['base_metadata_sha256']['default.project.json'],
          'SELECTED_PROJECT_DRIFT')
    check(selector.SELECTION_FILE in snapshot,'SELECTED_REPAIR_DIST_REQUIRED')
    selection=json.loads(snapshot[selector.SELECTION_FILE])
    flags={k:selection[k] for k in ('game_fixes','evolution_retry','equip_recovery')}
    check(all(type(x) is bool for x in flags.values()),'BOOLEAN_SELECTION_REQUIRED')
    check(not flags['equip_recovery'] or flags['game_fixes'],'RECOVERY_REQUIRES_GAME_FIXES')
    chosen=[name for name,key in [('game_lifecycle','game_fixes'),('evolution_retry','evolution_retry'),('equip_failure_recovery','equip_recovery')] if flags[key]]
    check(chosen and chosen==selection['selected_repairs'],'REPAIR_SELECTION_MISMATCH')
    check(selection['selection_manifest_sha256']==selector.MANIFEST_SHA256,'WRONG_SELECTION_LINEAGE')
    sources={p.removeprefix('src/'):raw for p,raw in snapshot.items() if p.startswith('src/') and p.endswith('.luau')}
    check(len(sources)==66 and set(sources)==set(manifest['source_gitblobs']),'SELECTED66_INVENTORY_REQUIRED')
    changed={manifest['features'][name]['path']:manifest['features'][name] for name in chosen}
    for path,raw in sources.items():
        if path in changed:
            row=changed[path];check(sha(raw)==row['after_sha256'] and len(raw)==row['after_bytes'],'SELECTED_REPAIR_SOURCE_DRIFT:'+path)
        else:check(selector.blob(raw)==manifest['source_gitblobs'][path],'UNSELECTED_SOURCE_DRIFT:'+path)
    pins={p:selector.blob(raw) for p,raw in sources.items()}
    check(json.loads(snapshot['SOURCE_LOCK.json'])['blobs']==json.loads(snapshot['RC_FEATURE_LOCK.json'])['source_gitblobs']==pins,'SELECTED_LOCK_MISMATCH')
    source_manifest=selector.encoded(selector.projected_source_manifest(dist,sources))
    check(snapshot[selector.SOURCE_MANIFEST]==source_manifest,'SELECTED_SOURCE_MANIFEST_DRIFT')
    return selector,snapshot,sources,flags,sha(source_manifest)

def command(argv,timeout=20):
    run=subprocess.run(argv,capture_output=True,text=True,timeout=timeout)
    check(run.returncode==0,'PROVENANCE_COMMAND_FAILED:'+repr(argv)+':'+run.stderr)
    return {'argv':argv,'exit_code':run.returncode,'stdout':run.stdout,'stderr':run.stderr}

def cache_entries(raw):
    result={}
    for line in raw.decode().splitlines():
        if not line or line.startswith(('#','//')) or '=' not in line or ':' not in line.split('=',1)[0]:continue
        declaration,value=line.split('=',1);key,_=declaration.split(':',1)
        check(key not in result,'DUPLICATE_CMAKE_CACHE_KEY:'+key);result[key]=value
    return result

def runtime_provenance(args,lock):
    runtime=args.luau.absolute()
    check(runtime.is_file() and not runtime.is_symlink(),'RUNTIME_MUST_BE_REAL_FILE')
    raw=runtime.read_bytes();check(len(raw)>=64 and raw.startswith(b'\x7fELF'),'RUNTIME_MUST_BE_REAL_ELF')
    result={'profile':args.runtime_profile,'runtime_path':str(runtime.resolve()),'runtime_sha256':sha(raw)}
    if args.runtime_profile=='local-pinned-binary':
        check(args.luau_source_dir is None and args.luau_build_dir is None,'LOCAL_PROFILE_HAS_NO_SOURCE_BUILD_ARGUMENTS')
        check(sha(raw)==lock['runtime_profiles']['local-pinned-binary']['sha256'],'WRONG_LOCAL_RUNTIME_BINARY')
        result['trust']='Exact frozen local ELF identity; no source build claim.'
        return result
    check(args.luau_source_dir is not None and args.luau_build_dir is not None,'CI_SOURCE_AND_BUILD_DIR_REQUIRED')
    source=args.luau_source_dir.resolve();build=args.luau_build_dir.resolve()
    check(source.is_dir() and build.is_dir(),'CI_SOURCE_OR_BUILD_DIR_MISSING')
    check(runtime.resolve()==build/'luau','RUNTIME_OUTSIDE_BUILD_DIRECTORY')
    cache=build/'CMakeCache.txt';check(cache.is_file() and not cache.is_symlink(),'REAL_CMAKE_CACHE_REQUIRED')
    raw_cache=cache.read_bytes();entries=cache_entries(raw_cache)
    home=entries.get('CMAKE_HOME_DIRECTORY','')
    check(home and Path(home).is_absolute() and Path(home).resolve()==source,'CMAKE_HOME_MISMATCH')
    cache_dir=entries.get('CMAKE_CACHEFILE_DIR','')
    check(cache_dir and Path(cache_dir).is_absolute() and Path(cache_dir).resolve()==build,'CMAKE_BUILD_DIRECTORY_MISMATCH')
    check(entries.get('CMAKE_GENERATOR')=='Ninja' and entries.get('CMAKE_BUILD_TYPE')=='Release'
          and entries.get('LUAU_BUILD_TESTS')=='OFF' and entries.get('LUAU_BUILD_CLI')=='ON','WRONG_EXISTING_CMAKE_BUILD_PROFILE')
    top=command(['git','-C',str(source),'rev-parse','--show-toplevel'])
    check(Path(top['stdout'].strip()).resolve()==source,'SOURCE_MUST_BE_GIT_CHECKOUT_ROOT')
    head=command(['git','-C',str(source),'rev-parse','HEAD'])
    check(head['stdout'].strip()==lock['runtime_profiles']['ci-pinned-source-build']['commit'],'WRONG_RUNTIME_SOURCE_COMMIT')
    status=command(['git','-C',str(source),'status','--porcelain=v1','--untracked-files=all'])
    check(not status['stdout'],'DIRTY_RUNTIME_SOURCE')
    untracked=command(['git','-C',str(source),'ls-files','--others'])
    check(not untracked['stdout'],'UNTRACKED_RUNTIME_SOURCE')
    compiler=entries.get('CMAKE_CXX_COMPILER','')
    check(compiler and Path(compiler).is_absolute() and Path(compiler).is_file(),'REAL_CXX_COMPILER_REQUIRED')
    version=command([compiler,'--version'])
    cmake=shutil.which('cmake');check(cmake is not None,'CMAKE_EXECUTABLE_REQUIRED')
    result.update({'source_dir':str(source),'source_commit':head['stdout'].strip(),'tracked_and_untracked_clean':True,
                   'source_validation_commands':[top,head,status,untracked],
                   'build_dir':str(build),'CMakeCache_sha256':sha(raw_cache),'CMake_home_directory':entries['CMAKE_HOME_DIRECTORY'],
                   'compiler_version':version,'cmake_executable':str(Path(cmake).resolve()),'cmake_sha256':sha(Path(cmake).read_bytes()),
                   'trust':'Existing trusted workflow-controlled pinned source/CMake build; not a cryptographic source-to-binary attestation.'})
    return result

def modules_for(suite,sources):
    return {name:sources['server/'+name+'.luau'] for name in MODULES.get(suite,[])}

def render(suite,sources,flags,lock,fixtures):
    game=sources['server/Game.server.luau'].decode();modules=modules_for(suite,sources);excerpts={};observations=[]
    if suite=='spawn12':
        program=fixtures['spawn.template.luau']
        for marker,start,end in [('SPAWN','local function assignSpawn(player: Player, character: Model)\n','-- EGG RAID RUMBLE experiment:'),
                                  ('CHARACTER_ADDED','    player.CharacterAdded:Connect(function(character)\n','    if player.Character then task.spawn(')]:
            code=piece(game,start,end);program=insert(program,'--@@'+marker+'@@--',code);excerpts[marker]=ident(code.encode())
    elif suite=='equip9':
        module_text='local factories,cache={},{}\nlocal function require(name)\n if cache[name]then return cache[name]end\n local v=factories[name]();cache[name]=v;return v\nend\n'
        for name,raw in modules.items():
            module_text+=f'factories[{json.dumps(name)}]=function()\nlocal script={{Parent={{WaitForChild=function(_,name)return name end}}}}\nreturn(function()\n'+raw.decode()+'\nend)()end\n'
        for name,alias in [('PersistentHatchStore','PersistentHatch'),('RewardEquipRules','RewardRules'),('ProgressionRules','Progression'),('PowerFantasyRules','Power'),('S1Rules','Rules')]:
            module_text+=f'local {alias}=require({json.dumps(name)})\n'
        program=insert(fixtures['equip.template.luau'],'--@@MODULES@@--',module_text)
        cases=fixtures['equip.cases.luau']
        if flags['equip_recovery']:
            cases=cases.encode()[:lock['equip_case_prefix_bytes']]
            check(sha(cases)==lock['equip_case_prefix_sha256'] and cases.count(b'case("')==9,'EQUIP_NINE_CASE_PREFIX_DRIFT')
            cases=cases.decode()
            observations=[{'name':r['name'],'status':'SUPERSEDED_BY_SELECTED_RECOVERY14'} for r in lock['vectors']['equip9']['historical_observations']]
        program=insert(program,'--@@CASES@@--',cases)
        for marker,(start,end) in EQUIP_ANCHORS.items():
            code=piece(game,start,end);excerpts[marker]=ident(code.encode())
            if marker=='CAN_WRITE' and flags['equip_recovery']:
                helper=piece(game,'local profileFailure: {[Player]: {equipOnly: boolean}} = {}\n','local persistentProfiles: {[Player]: any} = {}\n')
                excerpts['ACTUAL_RECOVERY_STATE_AND_HELPER']=ident(helper.encode());code=helper+code
            program=insert(program,'--@@'+marker+'@@--',code)
    else:
        name='name' if suite=='evolution19' else 'n'
        program=f'local modules={{}}\nlocal script={{Parent={{WaitForChild=function(_,{name})return {name} end}}}}\nlocal require=function({name})return assert(modules[{name}],"MISSING_MODULE:"..{name})end\n'
        for module,raw in modules.items():program+=f'modules["{module}"]=(function()\n'+raw.decode()+'\nend)()\n'
        if suite=='evolution19':program+=fixtures['evolution.cases.luau']
        else:
            fixture=fixtures['recovery.fixture.luau']
            for marker,(start,end) in RECOVERY_ANCHORS.items():
                code=piece(game,start,end);fixture=insert(fixture,'--@@'+marker+'@@--',code);excerpts[marker]=ident(code.encode())
            program+=fixture+'\n'+fixtures['recovery.cases.luau']
    check('--@@' not in program,'UNFILLED_FIXTURE_MARKER')
    raw=program.encode()
    for name,source in modules.items():check(raw.count(source)==1,'COMPLETE_MODULE_NOT_EMBEDDED_ONCE:'+name)
    return raw,{'complete_modules':{name:{'source_path':'server/'+name+'.luau',**ident(value)} for name,value in modules.items()},
                'literal_Game_excerpts':excerpts,'superseded_observations':observations}

def parse(stdout):
    cases=[];observations=[]
    for line in stdout.splitlines():
        if line.startswith('CASE\t'):
            _,name,status,detail=line.split('\t',3);cases.append({'name':name,'status':status,'detail':detail})
        elif line.startswith(('CASE|','OBSERVATION|')):
            kind,name,status,detail=line.split('|',3)
            (cases if kind=='CASE' else observations).append({'name':name,'status':status,'detail':detail})
        elif line.startswith(('PASS\t','FAIL\t')):
            fields=line.split('\t',2);cases.append({'name':fields[1],'status':fields[0],'detail':fields[2] if len(fields)>2 else ''})
    return cases,observations

def required_suites(flags):
    return [suite for suite in SUITES
            if (flags['game_fixes'] and suite in ('spawn12','equip9'))
            or (flags['evolution_retry'] and suite=='evolution19')
            or (flags['equip_recovery'] and suite=='recovery14')]

def artifact_binding(dist,folder):
    """Validate the just-run workflow evidence before labeling its artifact.

    Evidence files are workflow-controlled, not independently attested execution.
    Exact source/fixture rendering and stdout vectors prevent a stale or partial
    receipt from being presented as this selected artifact's repair regression.
    """
    lock,fixtures=read_fixtures()
    _,_,sources,flags,manifest_sha=selected_input(dist)
    path=folder/'receipt.json'
    check(path.is_file() and not path.is_symlink(),'REPAIR_REGRESSION_RECEIPT_REQUIRED')
    raw=path.read_bytes();receipt=json.loads(raw);required=required_suites(flags)
    check(receipt['schema']=='ACTIVE66_SELECTED_REPAIR_REGRESSION_V1'
          and receipt['status']=='PASS','REPAIR_REGRESSION_MUST_PASS')
    check(receipt['selected_flags']==flags and receipt['source_count']==66
          and receipt['selected_source_manifest_sha256']==manifest_sha
          and receipt['game_sha256']==sha(sources['server/Game.server.luau'])
          and receipt['store_sha256']==sha(sources['server/PersistentHatchStore.luau']),
          'REPAIR_REGRESSION_SELECTED_SOURCE_MISMATCH')
    check(receipt['fixture_lock_sha256']==LOCK_SHA256,'REPAIR_REGRESSION_FIXTURE_LOCK_MISMATCH')
    check(receipt['required_suites']==required and list(receipt['suites'])==required
          and receipt['not_selected']==[s for s in SUITES if s not in required],
          'REPAIR_REGRESSION_SUITE_SELECTION_MISMATCH')
    runtime=receipt['runtime']
    check(runtime['profile']=='ci-pinned-source-build','ARTIFACT_REQUIRES_WORKFLOW_SOURCE_BUILD_PROFILE')
    args=argparse.Namespace(luau=Path(runtime['runtime_path']),runtime_profile=runtime['profile'],
                           luau_source_dir=Path(runtime['source_dir']),luau_build_dir=Path(runtime['build_dir']))
    actual=runtime_provenance(args,lock)
    check(all(runtime[key]==actual[key] for key in ('runtime_path','runtime_sha256','source_dir',
          'source_commit','tracked_and_untracked_clean','build_dir','CMakeCache_sha256',
          'CMake_home_directory','compiler_version','cmake_executable','cmake_sha256')),
          'REPAIR_REGRESSION_RUNTIME_IDENTITY_CHANGED')
    build=runtime['actual_build']
    check(build['argv']==['cmake','--build',runtime['build_dir'],'--target','Luau.Repl.CLI','--parallel','4']
          and build['exit_code']==0 and Path(build['binary_argument']).resolve()==args.luau.resolve(),
          'REPAIR_REGRESSION_BUILD_COMMAND_MISMATCH')
    programs={};passed=0
    for suite in required:
        row=receipt['suites'][suite];scope=folder/suite
        program,binding=render(suite,sources,flags,lock,fixtures)
        check((scope/'generated.luau').read_bytes()==program
              and row['program_sha256']==sha(program),'REPAIR_REGRESSION_PROGRAM_MISMATCH:'+suite)
        cases,observations=parse((scope/'stdout.txt').read_text())
        vector=[{key:r[key] for key in ('name','status')} for r in cases]
        check(row['status']=='PASS' and row['native_exit']==0 and row['expected_vector_exact'] is True
              and cases==row['cases'] and vector==lock['vectors'][suite]['candidate']
              and len(cases)==len({r['name'] for r in cases})
              and row['passed']==len(cases) and row['failed']==0,
              'REPAIR_REGRESSION_CASE_VECTOR_MISMATCH:'+suite)
        check(row['observations']==observations,'REPAIR_REGRESSION_OBSERVATIONS_MISMATCH:'+suite)
        if suite=='equip9' and not flags['equip_recovery']:
            check([{k:r[k] for k in ('name','status')} for r in observations]
                  ==lock['vectors']['equip9']['historical_observations'],
                  'REPAIR_REGRESSION_HISTORICAL_OBSERVATIONS_MISMATCH')
        else:check(not observations,'REPAIR_REGRESSION_UNEXPECTED_OBSERVATIONS')
        check(all(row[k]==v for k,v in binding.items()),'REPAIR_REGRESSION_SOURCE_BINDING_MISMATCH:'+suite)
        check(row['actual_argv']==[runtime['runtime_path'],str((scope/'generated.luau').resolve())],
              'REPAIR_REGRESSION_NATIVE_ARGV_MISMATCH:'+suite)
        programs[suite]=sha(program);passed+=len(cases)
    check(receipt['passed']==passed and receipt['failed']==0
          and receipt['selected_distribution_bytes_unchanged'] is True,
          'REPAIR_REGRESSION_TOTAL_OR_IMMUTABILITY_MISMATCH')
    return {'status':'PASS','receipt_file':folder.name+'/receipt.json','receipt_sha256':sha(raw),
            'selected_source_manifest_sha256':manifest_sha,'fixture_lock_sha256':LOCK_SHA256,
            'required_suites':required,'passed':passed,'failed':0,'program_sha256':programs,
            'runtime_profile':runtime['profile'],'runtime_source_commit':runtime['source_commit'],
            'runtime_sha256':runtime['runtime_sha256'],'CMakeCache_sha256':runtime['CMakeCache_sha256'],
            'fixture_reuse_not_new_independent_approval':True,
            'runtime_trust':'Workflow-controlled build; not cryptographic source-to-binary attestation.'}

def main(observation=None):
    if observation is None:observation=new_observation()
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dist',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--luau',type=Path,required=True)
    parser.add_argument('--runtime-profile',choices=('local-pinned-binary','ci-pinned-source-build'),required=True)
    parser.add_argument('--luau-source-dir',type=Path);parser.add_argument('--luau-build-dir',type=Path)
    args=parser.parse_args();dist=args.dist.resolve();out=args.out.resolve()
    observation.update(phase='INPUT_VALIDATION',output=str(out),dist=str(dist))
    check(not out.exists() and not out.is_symlink() and not out.is_relative_to(dist),'FRESH_OUTPUT_OUTSIDE_DIST_REQUIRED')
    lock,fixtures=read_fixtures();selector,snapshot,sources,flags,manifest_sha=selected_input(dist)
    observation.update(phase='INITIAL_RUNTIME_PROVENANCE',selected_flags=flags,selected_source_manifest_sha256=manifest_sha)
    before_runtime=runtime_provenance(args,lock)
    out.mkdir(parents=True)
    observation['owned_output']=True
    runtime=before_runtime
    if args.runtime_profile=='ci-pinned-source-build':
        argv=['cmake','--build',before_runtime['build_dir'],'--target','Luau.Repl.CLI','--parallel','4']
        observation['phase']='RUNTIME_BUILD'
        with observe_process(observation,argv,180,'RUNTIME_BUILD') as process_record:
            built=subprocess.run(argv,capture_output=True,timeout=180)
            built=decoded_process(built,process_record)
        (out/'runtime_build.stdout.txt').write_text(built.stdout);(out/'runtime_build.stderr.txt').write_text(built.stderr)
        check(built.returncode==0,'EXISTING_RUNTIME_BUILD_FAILED')
        runtime=runtime_provenance(args,lock)
        runtime['actual_build']={'argv':argv,'exit_code':built.returncode,'binary_argument':str(args.luau),
                                 'before_runtime_sha256':before_runtime['runtime_sha256'],'before_CMakeCache_sha256':before_runtime['CMakeCache_sha256']}
    required=required_suites(flags)
    results={}
    observation.update(required_suites=required,suites=results)
    for suite in required:
        observation.update(phase='SUITE_RENDER',suite=suite)
        program,binding=render(suite,sources,flags,lock,fixtures)
        folder=out/suite;folder.mkdir();file=folder/'generated.luau';file.write_bytes(program)
        argv=[str(args.luau.resolve()),str(file)]
        observation['phase']='NATIVE_PROCESS'
        with observe_process(observation,argv,40,'NATIVE',suite) as process_record:
            process=subprocess.run(argv,capture_output=True,timeout=40)
            process=decoded_process(process,process_record)
        (folder/'stdout.txt').write_text(process.stdout);(folder/'stderr.txt').write_text(process.stderr)
        observation['phase']='SUITE_PARSE'
        cases,observations=parse(process.stdout);vector=[{k:r[k] for k in ('name','status')} for r in cases]
        expected=lock['vectors'][suite]['candidate']
        valid=process.returncode==0 and vector==expected and len(cases)==len({r['name'] for r in cases})
        if suite=='equip9' and not flags['equip_recovery']:
            valid=valid and [{k:r[k] for k in ('name','status')} for r in observations]==lock['vectors']['equip9']['historical_observations']
        else:valid=valid and not observations
        observation['suite_predicates'][suite]={'native_exit_zero':process.returncode==0,
            'expected_vector_exact':vector==expected,'case_names_unique':len(cases)==len({r['name'] for r in cases}),
            'observations_valid':([{k:r[k] for k in ('name','status')} for r in observations]==lock['vectors']['equip9']['historical_observations']
                                  if suite=='equip9' and not flags['equip_recovery'] else not observations)}
        result={'status':'PASS' if valid else 'FAIL','actual_argv':argv,'native_exit':process.returncode,
                'passed':sum(r['status']=='PASS' for r in cases),'failed':sum(r['status']!='PASS' for r in cases),
                'expected_vector_exact':vector==expected,'cases':cases,'observations':observations,
                'program_sha256':sha(program),**binding}
        write_json(folder/'receipt.json',result);results[suite]=result
    observation.update(phase='SOURCE_IMMUTABILITY',suite=None)
    unchanged=selector.file_map(dist)==snapshot
    observation.update(source_inputs_unchanged=unchanged,phase='FINAL_RUNTIME_PROVENANCE')
    after_runtime=runtime_provenance(args,lock)
    check(after_runtime['runtime_sha256']==runtime['runtime_sha256'],'RUNTIME_CHANGED_DURING_TESTS')
    if args.runtime_profile=='ci-pinned-source-build':check(after_runtime['CMakeCache_sha256']==runtime['CMakeCache_sha256'],'CMAKE_CACHE_CHANGED_DURING_TESTS')
    valid=unchanged and all(row['status']=='PASS' for row in results.values()) and len(results)==len(required)
    receipt={'schema':'ACTIVE66_SELECTED_REPAIR_REGRESSION_V1','status':'PASS' if valid else 'FAIL',
             'selected_flags':flags,'selected_source_manifest_sha256':manifest_sha,'source_count':66,
             'game_sha256':sha(sources['server/Game.server.luau']),'store_sha256':sha(sources['server/PersistentHatchStore.luau']),
             'fixture_lock_sha256':LOCK_SHA256,'runtime':runtime,'suites':results,
             'required_suites':required,'not_selected':[name for name in SUITES if name not in required],
             'passed':sum(r['passed'] for r in results.values()),'failed':sum(r['failed'] for r in results.values()),
             'selected_distribution_bytes_unchanged':unchanged,'new_independent_approval':False,
             'scope':'Frozen independent fixtures reused on selected full modules and exact Game excerpts; explicit service mocks/deferred queues/cleanup spies retained.',
             'conditional_Parent_retained_order':'Fixture condition only; no Roblox engine event-order claim.',
             'full_Game_bootstrap_executed':False,'live_DataStore_calls':0,'Studio':'NOT_TESTED','formal_RC_adopted':False}
    write_json(out/'receipt.json',receipt)
    observation['phase']='AGGREGATE_COMPLETE'
    if not valid:emit_failure(observation,1)
    print(json.dumps({'status':receipt['status'],'passed':receipt['passed'],'failed':receipt['failed'],'suites':{k:r['passed'] for k,r in results.items()},'runtime_profile':args.runtime_profile},indent=2))
    return 0 if valid else 1

def cli():
    observation=new_observation()
    try:return main(observation)
    except (ValueError,OSError,subprocess.SubprocessError) as error:
        emit_failure(observation,2,error)
        print(json.dumps({'status':'ERROR','reason':str(error)}));return 2

if __name__=='__main__':raise SystemExit(cli())
