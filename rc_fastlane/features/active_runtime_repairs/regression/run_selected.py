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
CONTINUATION_FLAG='persistence_continuation_v1'
CONTINUATION_SUITES=('revision_v1_spawn12','revision_v1_equip9','revision_v1_evolution19','revision_v1_recovery14',
                     'revision19','ui10','lifetime18','revision_ack11')
COMPATIBILITY_SUITES=('original_spawn12','original_equip9','original_evolution19','original_recovery14','original_ack11')
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
    flags,manifest,chosen,specs,recipe=selector.resolve_selection(selection)
    sources={p.removeprefix('src/'):raw for p,raw in snapshot.items() if p.startswith('src/') and p.endswith('.luau')}
    selector.validate_selected_sources(sources,manifest,specs)
    pins={p:selector.blob(raw) for p,raw in sources.items()}
    check(json.loads(snapshot['SOURCE_LOCK.json'])['blobs']==json.loads(snapshot['RC_FEATURE_LOCK.json'])['source_gitblobs']==pins,'SELECTED_LOCK_MISMATCH')
    source_manifest=selector.encoded(selector.projected_source_manifest(dist,sources))
    check(snapshot[selector.SOURCE_MANIFEST]==source_manifest,'SELECTED_SOURCE_MANIFEST_DRIFT')
    if recipe is not None:
        check(sha(source_manifest)==recipe['selected_source_manifest_sha256'],'CONTINUATION_ACTUAL_SOURCE_MANIFEST_DRIFT')
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

def read_continuation_fixtures(selector):
    recipe,_=selector.read_continuation()
    root=selector.FEATURE_ROOT/'continuation_v1'
    path=root/recipe['contract']['path']
    check(path.is_file() and not path.is_symlink(),'CONTINUATION_CONTRACT_REQUIRED')
    raw=path.read_bytes();check(ident(raw)=={key:recipe['contract'][key] for key in ('bytes','sha256')},
                               'CONTINUATION_CONTRACT_DRIFT')
    contract=json.loads(raw)
    check(contract['schema']=='ACTIVE66_SELECTED_REPAIR_CONTRACT_V2'
          and contract['id']==selector.CONTINUATION_ID
          and contract['original_fixture_lock_sha256']==LOCK_SHA256
          and contract['selected_source_manifest_sha256']==recipe['selected_source_manifest_sha256'],
          'CONTINUATION_CONTRACT_LINEAGE_MISMATCH')
    check(list(contract['positive'])==list(CONTINUATION_SUITES)
          and list(contract['compatibility'])==list(COMPATIBILITY_SUITES),'CONTINUATION_CONTRACT_SUITE_SET_DRIFT')
    fixtures={}
    for name,expected in contract['fixtures'].items():
        path=root/'regression'/name
        check(path.is_file() and not path.is_symlink(),'CONTINUATION_FIXTURE_REQUIRED:'+name)
        raw=path.read_bytes();check(ident(raw)=={key:expected[key] for key in ('bytes','sha256')},
                                   'CONTINUATION_FIXTURE_DRIFT:'+name)
        fixtures[name]=raw.decode()
    return recipe,contract,fixtures

def render_migrated54(suite,sources,flags,lock,original,variants):
    """Explicit seven-case migration; the immutable V1 reader remains unchanged."""
    fixtures=dict(original);extra={};game=sources['server/Game.server.luau'].decode()
    if suite in ('equip9','recovery14'):
        publish=piece(game,'local function publishV4Canonical(player: Player)\n',
                      'local function savedEvolutionForm(player: Player): any?\n')
        extra['literal_Game_publishV4Canonical']=ident(publish.encode())
        if suite=='equip9':
            template=insert(fixtures['equip.template.luau'],'--@@MODULES@@--',
                            '--@@MODULES@@--\nlocal V4XP=require("SessionSixSkillXPPreview")\nlocal V4Scheduler=require("FocusTrainingScheduler")')
            template=insert(template,'--@@RESTORE@@--',publish+'\n--@@RESTORE@@--')
            fixtures['equip.template.luau']=template
        else:
            template=insert(fixtures['recovery.fixture.luau'],' local function publishV4Canonical()end',publish)
            alias=' local Rules=modules.S1Rules\n'
            template=insert(template,alias,alias+' local V4XP=modules.SessionSixSkillXPPreview\n local V4Scheduler=modules.FocusTrainingScheduler\n')
            fixtures['recovery.fixture.luau']=template
        extra['fixture_variant']=ident(template.encode())
        extra['metadata_not_modelled_in_this_legacy_fixture_variant']=True
    if suite in ('evolution19','recovery14'):
        name='evolution.cases.luau' if suite=='evolution19' else 'recovery.cases.luau'
        fixtures[name]=variants[name]
    program,binding=render(suite,sources,flags,lock,fixtures)
    if suite=='equip9':
        old=original['equip.cases.luau'].encode()[:lock['equip_case_prefix_bytes']]
        new=variants['equip.cases.luau'].split('observation(',1)[0].encode()
        check(program.count(old)==1 and new.count(b'case("')==9,'MIGRATED_EQUIP_CASE_PREFIX_DRIFT')
        program=program.replace(old,new,1);extra['case_prefix_variant']=ident(new)
    return program,{'original_binding':binding,'explicit_variant_binding':extra}

def factory_module_text(modules,ui=False):
    text='local factories,cache={},{}\nlocal function require(name)\n if cache[name]then return cache[name]end\n local v=factories[name]();cache[name]=v;return v\nend\n'
    for name,raw in modules.items():
        text+=f'factories[{json.dumps(name)}]=function()\nlocal script={{Parent={{WaitForChild=function(_,name)return name end}}}}\nreturn(function()\n'+raw.decode()+'\nend)()end\n'
    aliases=[('PersistentHatchStore','PersistentHatch'),('RewardEquipRules','RewardRules'),('ProgressionRules','Progression'),
             ('PowerFantasyRules','Power'),('S1Rules','Rules'),('SessionSixSkillXPPreview','V4XP'),('FocusTrainingScheduler','V4Scheduler')]
    if ui:aliases.append(('ModeVoteRules','ModeVote'))
    for name,alias in aliases:text+=f'local {alias}=require({json.dumps(name)})\n'
    return text

def render_equipment_contract(suite,sources,fixtures):
    ui=suite=='ui10';stem='ui' if ui else 'revision'
    game=sources['server/Game.server.luau'].decode();modules=modules_for('equip9',sources)
    if ui:modules['ModeVoteRules']=sources['server/ModeVoteRules.luau']
    fixture=fixtures[stem+'.fixture.luau'];cases=fixtures[stem+'.cases.luau']
    program=insert(fixture,'--@@MODULES@@--',factory_module_text(modules,ui))
    program=insert(program,'--@@CASES@@--',cases);excerpts={}
    for marker,(start,end) in EQUIP_ANCHORS.items():
        code=piece(game,start,end);excerpts[marker]=ident(code.encode())
        if marker=='CAN_WRITE':
            helper=piece(game,'local profileFailure: {[Player]: {equipOnly: boolean}} = {}\n',
                         'local persistentProfiles: {[Player]: any} = {}\n')
            excerpts['ACTUAL_RECOVERY_STATE_AND_HELPER']=ident(helper.encode());code=helper+code
        program=insert(program,'--@@'+marker+'@@--',code)
    extra={'PUBLISH':('local function publishV4Canonical(player: Player)\n','local function savedEvolutionForm(player: Player): any?\n')}
    if ui:
        extra.update({'LOAD':('local function loadHatchProfile(player: Player)\n','local scoutModels:'),
                      'MODE_VOTE':('local function applyModeVote(player: Player,data)\n','-- S2 classic-egg-only DEV feature.')})
    for marker,(start,end) in extra.items():
        code=piece(game,start,end);excerpts[marker]=ident(code.encode());program=insert(program,'--@@'+marker+'@@--',code)
    fragments={}
    if ui:
        hud=sources['client/HUD.client.luau'].decode()
        snapshot=piece(game,'snapshotFor = function(player: Player)\n','broadcast = function()\n')
        fields={
            'ORDINAL_DECLARATION':piece(game,'local snapshotUpdateId = 0\n','snapshotFor = function(player: Player)\n'),
            'ORDINAL_INCREMENT':piece(snapshot,'    snapshotUpdateId += 1\n','    local now = serverNow()\n'),
            'CANONICAL_HATCH_SELECTION':piece(snapshot,'    local uid=h2Ids[player]\n','    local stats=if uid then'),
            'HATCH_PACKET_FIELDS':piece(snapshot,'        -- View-only bounded collection summary.','        -- All progression is server authored.'),
        }
        snapshot_function=fields['ORDINAL_DECLARATION']+'snapshotFor = function(player: Player)\n'
        snapshot_function+=fields['ORDINAL_INCREMENT']+fields['CANONICAL_HATCH_SELECTION']
        snapshot_function+=' return {kind="SNAPSHOT",serial=1,phase=match.phase,updateId=snapshotUpdateId,scores={},hp={},\n'
        snapshot_function+=fields['HATCH_PACKET_FIELDS']+' }\nend\n'
        program=insert(program,'--@@UI_SNAPSHOT@@--',snapshot_function)
        hud_fields={
            'BUTTON_ITEM_BINDING':piece(hud,'local equipButtons={\n','local seq = 0\n'),
            'SNAPSHOT_ORDER':piece(hud,'    if s.kind ~= "SNAPSHOT" then return end\n','    top.Text = string.format('),
            'SAVE_LABEL_AND_PANEL':piece(hud,'    local hatchAvailable=s.hatchEnabled==true\n','    if evolutionPanel.Visible then\n'),
            'CHECKMARK_AND_ENABLED_STATE':piece(hud,'    for _,entry in ipairs(equipButtons) do\n','    instructions.Visible='),
        }
        hud_function='''local function makeHud()
 local Color3={fromRGB=function(r,g,b)return tostring(r)..","..tostring(g)..","..tostring(b)end}
 local saveLabel,equipPanel={},{}
 local starterEquip,forestEquip,starEquip={},{},{}
 local evolutionOpen=false
 local lastSerial,lastUpdateId=-1,-1
 local relayLatest,bossVisual=nil,nil
'''
        hud_function+=hud_fields['BUTTON_ITEM_BINDING']+' local function accept(s)\n'
        hud_function+=hud_fields['SNAPSHOT_ORDER']+hud_fields['SAVE_LABEL_AND_PANEL']+hud_fields['CHECKMARK_AND_ENABLED_STATE']
        hud_function+='''  return true
 end
 return {accept=accept,label=saveLabel,panel=equipPanel,buttons=equipButtons,
  evolution=function(value)evolutionOpen=value end,latest=function()return relayLatest end}
end
'''
        program=insert(program,'--@@HUD_HELPER@@--',hud_function)
        fragments={'literal_Game_snapshot_fragments':{name:ident(raw.encode()) for name,raw in fields.items()},
                   'literal_HUD_fragments':{name:ident(raw.encode()) for name,raw in hud_fields.items()}}
    check('--@@' not in program,'UNFILLED_CONTINUATION_MARKER:'+suite)
    raw=program.encode()
    for name,body in modules.items():check(raw.count(body)==1,'COMPLETE_CONTINUATION_MODULE_NOT_ONCE:'+name)
    return raw,{'complete_modules':{name:ident(body) for name,body in modules.items()},
                'literal_Game_excerpts':excerpts,'fixture':ident(fixture.encode()),'cases_input':ident(cases.encode()),**fragments}

def render_lifetime18(sources,original,fixtures):
    game=sources['server/Game.server.luau'].decode()
    names=MODULES['recovery14']+['PowerFantasyRules','First90GuideRules']
    modules={name:sources['server/'+name+'.luau'] for name in names}
    program='local modules={}\nlocal script={Parent={WaitForChild=function(_,n)return n end}}\nlocal require=function(n)return assert(modules[n],"MISSING_MODULE:"..n)end\n'
    for name,raw in modules.items():program+=f'modules["{name}"]=(function()\n'+raw.decode()+'\nend)()\n'
    fixture=insert(original['recovery.fixture.luau'],' local PersistentHatch=modules.PersistentHatchStore\n',
        ' local PersistentHatch=modules.PersistentHatchStore\n'
        ' local V4XP=modules.SessionSixSkillXPPreview\n local V4Scheduler=modules.FocusTrainingScheduler\n'
        ' local First90Guide=modules.First90GuideRules\n local now=0\n local function serverNow()return now end\n'
        ' local utc=1800000060\n local os={time=function()return utc end}\n'
        ' local hatchSessionGUID="completion_lifetime_20261123"\n local v4ReceiptSerial,progressionEventSerial=0,0\n local carry={}\n')
    fixture=insert(fixture,' local Power={endRound=function()error("unexpected earnedPower fixture path")end}\n',' local Power=modules.PowerFantasyRules\n')
    fixture=insert(fixture,' local function publishV4Canonical()end\n',' --@@PUBLISH_V4@@--\n --@@PROGRESS_UID@@--\n --@@HEALTHY@@--\n')
    fixture=insert(fixture,' --@@REMOVE@@--\n',' --@@REMOVE@@--\n --@@PROGRESS_FUNCTIONS@@--\n --@@V4_FUNCTIONS@@--\n')
    old=' local E={jobs=jobs,timers=timers,records=records,profiles=persistentProfiles,status=persistenceState,\n'
    fixture=insert(fixture,old,old+'  progressStatus=progressionStatus,progressProfile=progressionProfile,trainingPending=v4SavePending,\n')
    fixture=insert(fixture,'  function p:SetAttribute(k,v)self.attrs[k]=v end\n',
        '  p.attributeWrites={}\n'
        '  function p:SetAttribute(k,v)self.attrs[k]=v;table.insert(self.attributeWrites,{key=k,value=v})end\n'
        '  local root={Position={X=-56,Y=1,Z=-15},IsA=function(_,c)return c=="BasePart"end}\n'
        '  local hum={Health=100}\n'
        '  p.Character={FindFirstChild=function(_,n)if n=="HumanoidRootPart"then return root end end,\n'
        '   FindFirstChildOfClass=function(_,c)if c=="Humanoid"then return hum end end}\n')
    fixture=insert(fixture,' return E\nend\n',fixtures['lifecycle.helpers.luau']+'\n return E\nend\n')
    anchors=dict(RECOVERY_ANCHORS)
    anchors.update({
        'PUBLISH_V4':('local function publishV4Canonical(player: Player)\n','local function savedEvolutionForm('),
        'PROGRESS_UID':('local function progressUid(player: Player): number?\n','local delayedRestore:'),
        'HEALTHY':('local function healthy(player: Player): (boolean, BasePart?, Humanoid?)\n','local function within('),
        'PROGRESS_FUNCTIONS':('local function recordServerProgress(player: Player,kind: string)\n','local function removeCarrierVisual('),
        'V4_FUNCTIONS':('local v4Locations={\n','local function v4TickCanonical()\n'),
    })
    excerpts={}
    for name,(start,end) in anchors.items():
        code=piece(game,start,end);fixture=insert(fixture,'--@@'+name+'@@--',code);excerpts[name]=ident(code.encode())
    program+=fixture+'\n'+fixtures['lifecycle.cases.luau']
    check('--@@' not in program,'UNFILLED_LIFETIME_MARKER')
    raw=program.encode()
    for name,body in modules.items():check(raw.count(body)==1,'COMPLETE_LIFETIME_MODULE_NOT_ONCE:'+name)
    return raw,{'complete_modules':{name:ident(body) for name,body in modules.items()},'literal_Game_excerpts':excerpts,
                'cases_input':ident(fixtures['lifecycle.cases.luau'].encode()),'helpers':ident(fixtures['lifecycle.helpers.luau'].encode())}

def render_selected_contract(suite,sources,flags,lock,fixtures,continuation=None):
    if continuation is None:return render(suite,sources,flags,lock,fixtures)
    _,_,variants=continuation
    if suite.startswith('revision_v1_') and suite.removeprefix('revision_v1_') in SUITES:
        return render_migrated54(suite.removeprefix('revision_v1_'),sources,flags,lock,fixtures,variants)
    if suite in ('revision19','ui10'):return render_equipment_contract(suite,sources,variants)
    if suite=='lifetime18':return render_lifetime18(sources,fixtures,variants)
    if suite=='revision_ack11':
        cases=dict(variants);cases['recovery.cases.luau']=variants['ack_episode.cases.luau']
        return render_migrated54('recovery14',sources,flags,lock,fixtures,cases)
    if suite.startswith('original_') and suite.removeprefix('original_') in SUITES:
        legacy=suite.removeprefix('original_')
        if legacy=='equip9':
            # This old fixture predates the real publisher call. Bind that
            # dependency without changing any of its nine case inputs.
            original_cases=dict(fixtures)
            original_cases['equip.cases.luau']=fixtures['equip.cases.luau'].encode()[:lock['equip_case_prefix_bytes']].decode()
            program,binding=render_migrated54(legacy,sources,flags,lock,fixtures,original_cases)
            binding['original_cases_unchanged_dependency_binding_only']=True
            return program,binding
        return render(legacy,sources,flags,lock,fixtures)
    check(suite=='original_ack11','UNKNOWN_CONTINUATION_SUITE:'+suite)
    original=dict(fixtures);original['recovery.cases.luau']=variants['ack_episode.original11.luau']
    return render('recovery14',sources,flags,lock,original)

def parse_contract(stdout,continuation=None):
    cases,observations=parse(stdout)
    if continuation is not None:
        observations += [line for line in stdout.splitlines() if line.startswith('OBSERVATION\t')]
    return cases,observations

def contract_expectation(suite,lock,continuation=None,compatibility=False):
    if continuation is None:return lock['vectors'][suite]['candidate'],0,None
    row=continuation[1]['compatibility' if compatibility else 'positive'][suite]
    return row['vector'],row['native_exit'],row['observations']

def verify_contract_program(suite,program,continuation,compatibility=False):
    if continuation is not None:
        expected=continuation[1]['compatibility' if compatibility else 'positive'][suite]['program']
        check(ident(program)==expected,'CONTINUATION_FROZEN_PROGRAM_DRIFT:'+suite)

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
    if flags.get(CONTINUATION_FLAG) is True:return list(CONTINUATION_SUITES)
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
    selector,_,sources,flags,manifest_sha=selected_input(dist)
    continuation=read_continuation_fixtures(selector) if flags.get(CONTINUATION_FLAG) is True else None
    path=folder/'receipt.json'
    check(path.is_file() and not path.is_symlink(),'REPAIR_REGRESSION_RECEIPT_REQUIRED')
    raw=path.read_bytes();receipt=json.loads(raw);required=required_suites(flags)
    schema='ACTIVE66_SELECTED_REPAIR_REGRESSION_V2' if continuation else 'ACTIVE66_SELECTED_REPAIR_REGRESSION_V1'
    check(receipt['schema']==schema
          and receipt['status']=='PASS','REPAIR_REGRESSION_MUST_PASS')
    check(receipt['selected_flags']==flags and receipt['source_count']==66
          and receipt['selected_source_manifest_sha256']==manifest_sha
          and receipt['game_sha256']==sha(sources['server/Game.server.luau'])
          and receipt['store_sha256']==sha(sources['server/PersistentHatchStore.luau']),
          'REPAIR_REGRESSION_SELECTED_SOURCE_MISMATCH')
    check(receipt['fixture_lock_sha256']==LOCK_SHA256,'REPAIR_REGRESSION_FIXTURE_LOCK_MISMATCH')
    if continuation:
        check(receipt.get('continuation')==selector.continuation_identity(continuation[0])
              and receipt.get('hud_sha256')==sha(sources['client/HUD.client.luau'])
              and receipt.get('contract_lock_sha256')==continuation[0]['contract']['sha256'],
              'CONTINUATION_REGRESSION_IDENTITY_MISMATCH')
    not_selected=[] if continuation else [s for s in SUITES if s not in required]
    check(receipt['required_suites']==required and list(receipt['suites'])==required
          and receipt['not_selected']==not_selected,
          'REPAIR_REGRESSION_SUITE_SELECTION_MISMATCH')
    compatibility=receipt.get('compatibility_observations') if continuation else None
    if continuation:
        check(isinstance(compatibility,dict) and compatibility.get('positive_admission') is False
              and compatibility.get('required_suites')==list(COMPATIBILITY_SUITES)
              and list(compatibility.get('suites',{}))==list(COMPATIBILITY_SUITES),
              'CONTINUATION_COMPATIBILITY_EVIDENCE_REQUIRED')
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
          and type(build['exit_code']) is int and build['exit_code']==0
          and Path(build['binary_argument']).resolve()==args.luau.resolve(),
          'REPAIR_REGRESSION_BUILD_COMMAND_MISMATCH')
    programs={};passed=0;compatibility_programs={};observed_passed=0;observed_failed=0
    plan=[(suite,False) for suite in required]+([(suite,True) for suite in COMPATIBILITY_SUITES] if continuation else [])
    for suite,is_compatibility in plan:
        row=(compatibility['suites'] if is_compatibility else receipt['suites'])[suite]
        scope=folder/'compatibility'/suite if is_compatibility else folder/suite
        program,binding=render_selected_contract(suite,sources,flags,lock,fixtures,continuation)
        verify_contract_program(suite,program,continuation,is_compatibility)
        check((scope/'generated.luau').read_bytes()==program
              and row['program_sha256']==sha(program),'REPAIR_REGRESSION_PROGRAM_MISMATCH:'+suite)
        cases,observations=parse_contract((scope/'stdout.txt').read_text(),continuation)
        vector=[{key:r[key] for key in ('name','status')} for r in cases]
        expected,expected_exit,expected_observations=contract_expectation(suite,lock,continuation,is_compatibility)
        expected_status='EXACT_COMPATIBILITY_OBSERVATION' if is_compatibility else 'PASS'
        pass_count=sum(r['status']=='PASS' for r in expected);fail_count=len(expected)-pass_count
        check(row['status']==expected_status and type(row['native_exit']) is int
              and row['native_exit']==expected_exit and row['expected_vector_exact'] is True
              and cases==row['cases'] and vector==expected
              and len(cases)==len({r['name'] for r in cases})
              and row['passed']==pass_count and row['failed']==fail_count,
              'REPAIR_REGRESSION_CASE_VECTOR_MISMATCH:'+suite)
        check(row['observations']==observations,'REPAIR_REGRESSION_OBSERVATIONS_MISMATCH:'+suite)
        if continuation:
            check(json.loads((scope/'receipt.json').read_bytes())==row,'CONTINUATION_SUITE_RECEIPT_MISMATCH:'+suite)
            check(observations==expected_observations and type(row.get('expected_native_exit')) is int
                  and row.get('expected_native_exit')==expected_exit
                  and row.get('positive_admission') is (not is_compatibility),'CONTINUATION_RESULT_KIND_MISMATCH:'+suite)
            streams={name:ident((scope/(name+'.txt')).read_bytes()) for name in ('stdout','stderr')}
            check(row.get('streams')==streams,'CONTINUATION_RAW_STREAM_MISMATCH:'+suite)
            check((streams['stderr']['bytes']==0) if expected_exit==0 else (streams['stderr']['bytes']>0),
                  'CONTINUATION_STDERR_CONTRACT_MISMATCH:'+suite)
        elif suite=='equip9' and not flags['equip_recovery']:
            check([{k:r[k] for k in ('name','status')} for r in observations]
                  ==lock['vectors']['equip9']['historical_observations'],
                  'REPAIR_REGRESSION_HISTORICAL_OBSERVATIONS_MISMATCH')
        else:check(not observations,'REPAIR_REGRESSION_UNEXPECTED_OBSERVATIONS')
        check(all(row[k]==v for k,v in binding.items()),'REPAIR_REGRESSION_SOURCE_BINDING_MISMATCH:'+suite)
        check(row['actual_argv']==[runtime['runtime_path'],str((scope/'generated.luau').resolve())],
              'REPAIR_REGRESSION_NATIVE_ARGV_MISMATCH:'+suite)
        if is_compatibility:
            compatibility_programs[suite]=sha(program);observed_passed+=pass_count;observed_failed+=fail_count
        else:
            programs[suite]=sha(program);passed+=len(cases)
    check(receipt['passed']==passed and receipt['failed']==0
          and receipt['selected_distribution_bytes_unchanged'] is True,
          'REPAIR_REGRESSION_TOTAL_OR_IMMUTABILITY_MISMATCH')
    result={'status':'PASS','receipt_file':folder.name+'/receipt.json','receipt_sha256':sha(raw),
            'selected_source_manifest_sha256':manifest_sha,'fixture_lock_sha256':LOCK_SHA256,
            'required_suites':required,'passed':passed,'failed':0,'program_sha256':programs,
            'runtime_profile':runtime['profile'],'runtime_source_commit':runtime['source_commit'],
            'runtime_sha256':runtime['runtime_sha256'],'CMakeCache_sha256':runtime['CMakeCache_sha256'],
            'fixture_reuse_not_new_independent_approval':True,
            'runtime_trust':'Workflow-controlled build; not cryptographic source-to-binary attestation.'}
    if continuation:
        check(compatibility.get('observed_passed')==observed_passed
              and compatibility.get('observed_failed')==observed_failed,'CONTINUATION_COMPATIBILITY_TOTAL_MISMATCH')
        result.update(continuation=selector.continuation_identity(continuation[0]),
                      contract_lock_sha256=continuation[0]['contract']['sha256'],
                      hud_sha256=sha(sources['client/HUD.client.luau']),
                      compatibility_observations={'positive_admission':False,'observed_passed':observed_passed,
                          'observed_failed':observed_failed,'program_sha256':compatibility_programs})
    return result

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
    continuation=read_continuation_fixtures(selector) if flags.get(CONTINUATION_FLAG) is True else None
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
    results={};compatibility_results={}
    observation.update(required_suites=required,suites=results)
    plan=[(suite,False) for suite in required]+([(suite,True) for suite in COMPATIBILITY_SUITES] if continuation else [])
    if continuation:observation['compatibility_observations']=compatibility_results
    for suite,is_compatibility in plan:
        observation.update(phase='SUITE_RENDER',suite=suite)
        program,binding=render_selected_contract(suite,sources,flags,lock,fixtures,continuation)
        verify_contract_program(suite,program,continuation,is_compatibility)
        folder=out/'compatibility'/suite if is_compatibility else out/suite
        folder.mkdir(parents=True);file=folder/'generated.luau';file.write_bytes(program)
        argv=[str(args.luau.resolve()),str(file)]
        observation['phase']='NATIVE_PROCESS'
        with observe_process(observation,argv,40,'NATIVE',suite) as process_record:
            process=subprocess.run(argv,capture_output=True,timeout=40)
            process=decoded_process(process,process_record)
        if continuation:
            (folder/'stdout.txt').write_bytes(process_record['stdout']);(folder/'stderr.txt').write_bytes(process_record['stderr'])
        else:
            (folder/'stdout.txt').write_text(process.stdout);(folder/'stderr.txt').write_text(process.stderr)
        observation['phase']='SUITE_PARSE'
        cases,observations=parse_contract(process.stdout,continuation);vector=[{k:r[k] for k in ('name','status')} for r in cases]
        expected,expected_exit,expected_observations=contract_expectation(suite,lock,continuation,is_compatibility)
        valid=process.returncode==expected_exit and vector==expected and len(cases)==len({r['name'] for r in cases})
        if continuation:
            observations_valid=observations==expected_observations
            stderr_valid=not process.stderr if expected_exit==0 else bool(process.stderr)
            valid=valid and observations_valid and stderr_valid
        elif suite=='equip9' and not flags['equip_recovery']:
            valid=valid and [{k:r[k] for k in ('name','status')} for r in observations]==lock['vectors']['equip9']['historical_observations']
        else:valid=valid and not observations
        observation['suite_predicates'][suite]={'native_exit_zero':process.returncode==0,
            'expected_vector_exact':vector==expected,'case_names_unique':len(cases)==len({r['name'] for r in cases}),
            'observations_valid':([{k:r[k] for k in ('name','status')} for r in observations]==lock['vectors']['equip9']['historical_observations']
                                  if suite=='equip9' and not flags['equip_recovery'] else not observations)}
        if continuation:
            observation['suite_predicates'][suite]={'expected_native_exit':process.returncode==expected_exit,
                'expected_vector_exact':vector==expected,'case_names_unique':len(cases)==len({r['name'] for r in cases}),
                'observations_valid':observations_valid,'stderr_valid':stderr_valid}
        result={'status':('EXACT_COMPATIBILITY_OBSERVATION' if is_compatibility else 'PASS') if valid else 'FAIL',
                'actual_argv':argv,'native_exit':process.returncode,
                'passed':sum(r['status']=='PASS' for r in cases),'failed':sum(r['status']!='PASS' for r in cases),
                'expected_vector_exact':vector==expected,'cases':cases,'observations':observations,
                'program_sha256':sha(program),**binding}
        if continuation:
            result.update(expected_native_exit=expected_exit,positive_admission=not is_compatibility,
                          streams={name:ident(process_record[name]) for name in ('stdout','stderr')})
        write_json(folder/'receipt.json',result)
        (compatibility_results if is_compatibility else results)[suite]=result
    observation.update(phase='SOURCE_IMMUTABILITY',suite=None)
    unchanged=selector.file_map(dist)==snapshot
    observation.update(source_inputs_unchanged=unchanged,phase='FINAL_RUNTIME_PROVENANCE')
    after_runtime=runtime_provenance(args,lock)
    check(after_runtime['runtime_sha256']==runtime['runtime_sha256'],'RUNTIME_CHANGED_DURING_TESTS')
    if args.runtime_profile=='ci-pinned-source-build':check(after_runtime['CMakeCache_sha256']==runtime['CMakeCache_sha256'],'CMAKE_CACHE_CHANGED_DURING_TESTS')
    valid=unchanged and all(row['status']=='PASS' for row in results.values()) and len(results)==len(required)
    if continuation:
        check(read_continuation_fixtures(selector)==continuation,'CONTINUATION_INPUT_CHANGED_DURING_TESTS')
        valid=valid and all(row['status']=='EXACT_COMPATIBILITY_OBSERVATION' for row in compatibility_results.values())
        valid=valid and len(compatibility_results)==len(COMPATIBILITY_SUITES)
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
    if continuation:
        receipt.update(schema='ACTIVE66_SELECTED_REPAIR_REGRESSION_V2',not_selected=[],
                       continuation=selector.continuation_identity(continuation[0]),
                       contract_lock_sha256=continuation[0]['contract']['sha256'],hud_sha256=sha(sources['client/HUD.client.luau']),
                       scope='Explicit versioned ACTIVE66 persistence continuation; immutable old contracts retained as separate observations.',
                       compatibility_observations={'required_suites':list(COMPATIBILITY_SUITES),'suites':compatibility_results,
                           'observed_passed':sum(row['passed'] for row in compatibility_results.values()),
                           'observed_failed':sum(row['failed'] for row in compatibility_results.values()),'positive_admission':False})
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
