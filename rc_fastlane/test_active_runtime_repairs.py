"""Actual generated66 contract tests, not a synthetic replacement source tree.

Set P0D_ACTIVE66_TEST_DIST to the existing producer's locked original66 dist.
Only temporary copies are mutated. Native gameplay fixtures remain separate.
"""
import importlib.util
import base64
from contextlib import redirect_stdout,redirect_stderr
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('active_runtime_repairs',HERE/'apply_active_runtime_repairs.py')
adapter=importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)

class Actual66SelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base=Path(os.environ['P0D_ACTIVE66_TEST_DIST'])
        cls.manifest,cls.patches=adapter.read_manifest()
        cls.original,cls.sources,_,_=adapter.validate_base(cls.base,cls.manifest)

    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory(prefix='active66-contract-')
        self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name)

    def select(self,game=True,evolution=True,base=None,out=None,recovery=False):
        return adapter.apply(base or self.base,out or self.root/'selected','rich51',game,evolution,recovery)

    def copied_base(self):
        target=self.root/'base'
        shutil.copytree(self.base,target)
        return target

    def assert_refused(self,base=None,out=None,reason=None):
        target=out or self.root/'selected'
        with self.assertRaisesRegex(ValueError,reason or '.'):
            self.select(base=base,out=target)
        self.assertFalse(target.exists())

    def test_both_off_keeps_every_byte_and_creates_nothing(self):
        before=adapter.file_map(self.base)
        result=self.select(False,False)
        self.assertFalse(result['applied'])
        self.assertEqual(result['selected_dist'],str(self.base))
        self.assertEqual(list(self.root.iterdir()),[])
        self.assertEqual(adapter.file_map(self.base),before)

    def test_off_and_fallback_do_not_require_an_active66_input(self):
        missing=self.root/'missing'
        for profile,game,evo in [('rich51',False,False),('rich47',True,True),('legacy21',True,True)]:
            with self.subTest(profile=profile):
                result=adapter.apply(missing,self.root/'no'/'selected',profile,game,evo)
                self.assertFalse(result['applied'])
                self.assertEqual(list(self.root.iterdir()),[])

    def test_game_only_leaves_store_and_other_64_sources_exact(self):
        self.select(True,False)
        sources=adapter.source_map(self.root/'selected')
        self.assertEqual({p for p in self.sources if self.sources[p]!=sources[p]}, {'server/Game.server.luau'})
        self.assertEqual(adapter.sha(sources['server/Game.server.luau']),'762d9623c1a6f9edaa91f1480f8d2353215a74b479557309566c4eac114b2406')
        self.assertEqual(sum(map(len,sources.values()))-sum(map(len,self.sources.values())),689)

    def test_evolution_only_leaves_game_and_other_64_sources_exact(self):
        self.select(False,True)
        sources=adapter.source_map(self.root/'selected')
        self.assertEqual({p for p in self.sources if self.sources[p]!=sources[p]}, {'server/PersistentHatchStore.luau'})
        self.assertEqual(adapter.sha(sources['server/PersistentHatchStore.luau']),'07129c211f25d62b399e6f125be4d7c7649a12e7dd313d98701a6bf89007b241')
        self.assertEqual(sum(map(len,sources.values()))-sum(map(len,self.sources.values())),96)

    def test_selected_manifests_describe_actual_bytes_and_rojo_names(self):
        result=self.select()
        selected=self.root/'selected'
        sources=adapter.source_map(selected)
        lock=json.loads((selected/'SOURCE_LOCK.json').read_bytes())
        feature=json.loads((selected/'RC_FEATURE_LOCK.json').read_bytes())
        manifest=json.loads((selected/adapter.SOURCE_MANIFEST).read_bytes())
        selection=json.loads((selected/adapter.SELECTION_FILE).read_bytes())
        self.assertEqual(selection,result['selection'])
        self.assertEqual(len(sources),66)
        self.assertEqual(selection['source_delta_bytes'],785)
        self.assertEqual(selection['selected_source_manifest_sha256'],adapter.sha((selected/adapter.SOURCE_MANIFEST).read_bytes()))
        self.assertEqual(lock['blobs'],feature['source_gitblobs'])
        for path,data in sources.items():
            self.assertEqual(lock['blobs'][path],adapter.blob(data))
            self.assertEqual(manifest['sources'][path]['sha256'],adapter.sha(data))
            self.assertEqual(manifest['sources'][path]['bytes'],len(data))
        self.assertEqual(manifest['sources']['client/FirstMinuteCoach.client.luau']['instance_path'],'StarterPlayer/StarterPlayerScripts/TrapRaidersCoach')
        self.assertEqual(manifest['sources']['client/HUD.client.luau']['instance_path'],'StarterPlayer/StarterPlayerScripts/TrapRaidersHUD')
        self.assertEqual((selected/'default.project.json').read_bytes(),self.original['default.project.json'])
        self.assertEqual(adapter.file_map(self.base),self.original)

    def test_inverse_reconstructs_all_original_files_for_each_selection(self):
        for game,evolution,recovery in [(True,False,False),(False,True,False),(True,True,False),(True,False,True),(True,True,True)]:
            with self.subTest(game=game,evolution=evolution,recovery=recovery):
                selected=self.root/f'selected-{game}-{evolution}-{recovery}'
                result=self.select(game,evolution,out=selected,recovery=recovery)
                for feature in reversed(result['selection']['selected_repairs']):
                    command=['patch','-p1','--fuzz=0','--batch','--reverse','--reject-file=-']
                    process=subprocess.run(command,cwd=selected/'src',input=self.patches[feature],capture_output=True)
                    self.assertEqual(process.returncode,0,process.stderr)
                for name,key,map_key in [('SOURCE_LOCK.json','rc_active_runtime_repairs','blobs'),('RC_FEATURE_LOCK.json','active_runtime_repairs','source_gitblobs')]:
                    data=json.loads((selected/name).read_bytes())
                    del data[key]
                    data[map_key]=self.manifest['source_gitblobs']
                    (selected/name).write_bytes(adapter.encoded(data))
                (selected/adapter.SELECTION_FILE).unlink()
                (selected/adapter.SOURCE_MANIFEST).unlink()
                self.assertEqual(adapter.file_map(selected),self.original)

    def test_forged_source_and_self_consistent_locks_cannot_replace_pinned_base(self):
        base=self.copied_base()
        target=base/'src/server/Game.server.luau'
        target.write_bytes(target.read_bytes()+b'\n-- unreviewed input\n')
        for name,key in [('SOURCE_LOCK.json','blobs'),('RC_FEATURE_LOCK.json','source_gitblobs')]:
            data=json.loads((base/name).read_bytes())
            data[key]['server/Game.server.luau']=adapter.blob(target.read_bytes())
            (base/name).write_bytes(adapter.encoded(data))
        self.assert_refused(base=base,reason='WRONG_66_SOURCE_DISTRIBUTION')

    def test_project_or_original_lock_drift_is_refused_before_output(self):
        base=self.copied_base()
        for name in ['default.project.json','SOURCE_LOCK.json','RC_FEATURE_LOCK.json']:
            with self.subTest(path=name):
                path=base/name
                original=path.read_bytes()
                path.write_bytes(original+b' ')
                self.assert_refused(base=base,reason='ORIGINAL_METADATA_DRIFT')
                path.write_bytes(original)

    def test_reviewed_patch_or_manifest_drift_is_refused(self):
        original_root=adapter.FEATURE_ROOT
        copied=self.root/'feature'
        shutil.copytree(original_root,copied)
        adapter.FEATURE_ROOT=copied
        self.addCleanup(setattr,adapter,'FEATURE_ROOT',original_root)
        for name,reason in [('game_lifecycle.patch','REPAIR_PATCH_DRIFT'),('MANIFEST.json','REPAIR_MANIFEST_DRIFT')]:
            with self.subTest(path=name):
                path=copied/name
                original=path.read_bytes()
                path.write_bytes(original+b' ')
                self.assert_refused(reason=reason)
                path.write_bytes(original)

    def test_selected_dist_is_not_silently_patched_again(self):
        self.select()
        self.assert_refused(base=self.root/'selected',out=self.root/'second',reason='WRONG_66_SOURCE_DISTRIBUTION')

    def test_output_inside_input_and_existing_output_are_refused(self):
        base=self.copied_base()
        self.assert_refused(base=base,out=base/'selected',reason='OUTPUT_INSIDE_INPUT')
        output=self.root/'selected'
        output.mkdir()
        sentinel=output/'keep.txt'
        sentinel.write_text('preserve caller output')
        with self.assertRaisesRegex(ValueError,'OUTPUT_ALREADY_EXISTS'):
            self.select(out=output)
        self.assertEqual(sentinel.read_text(),'preserve caller output')
        self.assertEqual(list(output.iterdir()),[sentinel])

    def test_identical_bytes_through_symlink_are_refused(self):
        base=self.copied_base()
        file=base/'src/server/Game.server.luau'
        file.unlink()
        file.symlink_to(self.base/'src/server/Game.server.luau')
        self.assert_refused(base=base,reason='SOURCE_SYMLINK_REFUSED')

    def test_non_boolean_or_unknown_profile_cannot_select(self):
        for args in [('rich51','false',True),('rich51',True,1),('unexpected',True,True),('rich51',True,False,'false')]:
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    adapter.apply(self.base,self.root/'selected',*args)
                self.assertEqual(list(self.root.iterdir()),[])

    def test_equipment_recovery_requires_game_fixes_before_input_or_output(self):
        for evolution in (False,True):
            with self.subTest(evolution=evolution):
                with self.assertRaisesRegex(ValueError,'EQUIP_RECOVERY_REQUIRES_GAME_FIXES'):
                    self.select(False,evolution,base=self.root/'missing',recovery=True)
                self.assertEqual(list(self.root.iterdir()),[])

    def test_recovery_after_game_fixes_matches_exact_reviewed_component_composition(self):
        result=self.select(True,False,recovery=True)
        sources=adapter.source_map(self.root/'selected')
        self.assertEqual({p for p in self.sources if self.sources[p]!=sources[p]},{'server/Game.server.luau'})
        self.assertEqual(adapter.sha(sources['server/Game.server.luau']),'e9d02785a806375d52202566da3a2ec7b0e650526e41ae7cca805f81ac4cb72e')
        self.assertEqual(result['selection']['source_delta_bytes'],1718)
        self.assertEqual(result['selection']['selected_repairs'],['game_lifecycle','equip_failure_recovery'])

    def test_all_three_selections_preserve_64_other_sources(self):
        result=self.select(recovery=True)
        sources=adapter.source_map(self.root/'selected')
        self.assertEqual({p for p in self.sources if self.sources[p]!=sources[p]},{'server/Game.server.luau','server/PersistentHatchStore.luau'})
        self.assertEqual(result['selection']['source_delta_bytes'],1814)
        self.assertEqual(result['selection']['selected_repairs'],['game_lifecycle','evolution_retry','equip_failure_recovery'])

class RepairFailureProtocolTests(unittest.TestCase):
    """Python failure protocol only: no native/gameplay/CI admission evidence."""
    @classmethod
    def setUpClass(cls):
        spec=importlib.util.spec_from_file_location('active66_failure_protocol',HERE/'features/active_runtime_repairs/regression/run_selected.py')
        cls.runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.runner)
        cls.lock,_=cls.runner.read_fixtures()

    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory(prefix='active66-failure-protocol-')
        self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name)

    def passed_output(self,suite):
        return ''.join('CASE\t'+row['name']+'\t'+row['status']+'\tprotocol-only 雪\r\n'
                       for row in self.lock['vectors'][suite]['candidate']).encode('utf-8')

    def scenario(self,name,response=None,source_changed=False,ci=False,diagnostic_write_error=False,
                 runtime_changed=False,existing_output=False):
        runner=self.runner;root=self.root/name;root.mkdir();dist=root/'dist';dist.mkdir();out=root/'out'
        binary=root/'never-executed-luau';binary.write_bytes(b'protocol-only mock; not an ELF')
        if existing_output:out.mkdir();(out/'sentinel').write_bytes(b'caller-owned output')
        flags={'game_fixes':True,'evolution_retry':True,'equip_recovery':True}
        snapshot={'protocol-input':b'unchanged'}
        source_read=Mock(return_value={'protocol-input':b'changed'} if source_changed else snapshot)
        selector=SimpleNamespace(file_map=source_read)
        sources={'server/Game.server.luau':b'protocol Game','server/PersistentHatchStore.luau':b'protocol Store'}
        profile='ci-pinned-source-build' if ci else 'local-pinned-binary'
        runtime={'profile':profile,'runtime_sha256':'protocol-runtime','build_dir':str(root/'build'),
                 'CMakeCache_sha256':'protocol-cache'}
        calls=[dict(runtime) for _ in range(3 if ci else 2)]
        if runtime_changed:calls[-1]['runtime_sha256']='different-protocol-runtime'
        required=runner.required_suites(flags)
        responses=[subprocess.CompletedProcess([],0,self.passed_output(suite),b'') for suite in required]
        if ci:responses.insert(0,subprocess.CompletedProcess([],0,b'protocol build\r\n',b''))
        if response is not None:responses[0]=response
        argv=['run_selected.py','--dist',str(dist),'--out',str(out),'--luau',str(binary),
              '--runtime-profile',profile]
        if ci:argv+=['--luau-source-dir',str(root/'source'),'--luau-build-dir',runtime['build_dir']]
        binding={'complete_modules':{},'literal_Game_excerpts':{},'superseded_observations':[]}
        console=io.StringIO();errors=io.StringIO();original_write=runner.write_json
        def write_json(path,value):
            if diagnostic_write_error and path.name=='FAILURE_DIAGNOSTIC.json':
                raise OSError('injected diagnostic disk failure')
            return original_write(path,value)
        with patch.object(sys,'argv',argv), \
             patch.object(runner,'selected_input',return_value=(selector,snapshot,sources,flags,'protocol-manifest')) as selected, \
             patch.object(runner,'runtime_provenance',side_effect=calls), \
             patch.object(runner,'render',side_effect=lambda suite,*_: (('-- protocol '+suite+'\n').encode(),dict(binding))), \
             patch.object(runner.subprocess,'run',side_effect=responses) as native, \
             patch.object(runner,'write_json',side_effect=write_json), \
             redirect_stdout(console),redirect_stderr(errors):
            exit_code=runner.cli()
        return {'exit':exit_code,'out':out,'console':console.getvalue(),'errors':errors.getvalue(),
                'calls':native.call_args_list,'required':required,'sources':sources,'runtime':runtime,
                'source_read':source_read,'selected_calls':selected.call_count}

    def diagnostic(self,result):
        prefix='ACTIVE66_REPAIR_FAILURE '
        rows=[json.loads(line[len(prefix):]) for line in result['console'].splitlines() if line.startswith(prefix)]
        self.assertEqual(len(rows),1)
        value=rows[0];self.assertEqual(value['status'],'FAIL_DIAGNOSTIC_ONLY');self.assertFalse(value['native_admission'])
        self.assertEqual(value['runner_exit'],result['exit'])
        if result['selected_calls'] and 'diagnostic_file_error' not in value:
            self.assertEqual(json.loads((result['out']/'FAILURE_DIAGNOSTIC.json').read_bytes()),value)
        streams={}
        prefix='ACTIVE66_REPAIR_FAILURE_STREAM '
        for line in result['console'].splitlines():
            if not line.startswith(prefix):continue
            stream=json.loads(line[len(prefix):]);raw=base64.b64decode(stream['base64'],validate=True)
            self.assertEqual(self.runner.ident(raw),{key:stream[key] for key in ('bytes','sha256')})
            self.assertEqual(stream['utf8_display'],raw.decode('utf-8',errors='backslashreplace'))
            stored=result['out']/value['processes'][stream['process_index']][stream['stream']]['file']
            self.assertEqual(stored.read_bytes(),raw)
            streams[(stream['process_index'],stream['stream'])]=raw
        return value,streams

    def assert_single_process_stop(self,result,error_type):
        self.assertEqual(result['exit'],2);self.assertEqual(len(result['calls']),1)
        diagnostic,streams=self.diagnostic(result)
        self.assertEqual(diagnostic['exception_type'],error_type)
        self.assertIsNone(diagnostic['source_inputs_unchanged'])
        self.assertFalse((result['out']/'receipt.json').exists())
        for suite in result['required'][1:]:self.assertFalse((result['out']/suite).exists())
        return diagnostic,streams

    def test_success_keeps_receipts_output_files_and_no_failure_diagnostic(self):
        for ci in (False,True):
            with self.subTest(ci=ci):
                result=self.scenario('success-'+str(ci),ci=ci)
                self.assertEqual(result['exit'],0);self.assertEqual(result['errors'],'')
                self.assertNotIn('ACTIVE66_REPAIR_FAILURE',result['console'])
                receipt=json.loads((result['out']/'receipt.json').read_bytes())
                self.assertEqual(receipt['status'],'PASS');self.assertEqual(receipt['passed'],54);self.assertEqual(receipt['failed'],0)
                self.assertTrue(receipt['selected_distribution_bytes_unchanged'])
                self.assertEqual(list(receipt['suites']),result['required'])
                self.assertEqual(result['console'],json.dumps({'status':'PASS','passed':54,'failed':0,
                    'suites':{'spawn12':12,'equip9':9,'evolution19':19,'recovery14':14},
                    'runtime_profile':'ci-pinned-source-build' if ci else 'local-pinned-binary'},indent=2)+'\n')
                files={'receipt.json',*result['required']}
                if ci:files.update({'runtime_build.stdout.txt','runtime_build.stderr.txt'})
                self.assertEqual({p.name for p in result['out'].iterdir()},files)
                for index,suite in enumerate(result['required']):
                    folder=result['out']/suite
                    self.assertEqual({p.name for p in folder.iterdir()},{'generated.luau','stdout.txt','stderr.txt','receipt.json'})
                    self.assertEqual((folder/'stdout.txt').read_bytes(),self.passed_output(suite).replace(b'\r\n',b'\n'))
                    call=result['calls'][index+int(ci)]
                    self.assertEqual(call.args[0],[str((self.root/('success-'+str(ci))/'never-executed-luau').resolve()),str(folder/'generated.luau')])
                    self.assertEqual(call.kwargs,{'capture_output':True,'timeout':40})
                if ci:self.assertEqual(result['calls'][0].kwargs,{'capture_output':True,'timeout':180})

    def test_completed_failures_keep_all_suite_order_and_explain_predicates(self):
        passed=self.passed_output('spawn12');lines=passed.splitlines(keepends=True)
        controls={
            'process':(subprocess.CompletedProcess([],7,passed,b'native failed\n'),'native_exit_zero'),
            'vector':(subprocess.CompletedProcess([],0,b''.join([lines[1],lines[0],*lines[2:]]),b''),'expected_vector_exact'),
            'duplicate':(subprocess.CompletedProcess([],0,b''.join([lines[0],lines[0],*lines[2:]]),b''),'case_names_unique'),
            'observation':(subprocess.CompletedProcess([],0,passed+b'OBSERVATION|unexpected|PASS|protocol\n',b''),'observations_valid')}
        for name,(response,predicate) in controls.items():
            with self.subTest(name=name):
                result=self.scenario(name,response=response)
                self.assertEqual(result['exit'],1);self.assertEqual(len(result['calls']),4)
                diagnostic,streams=self.diagnostic(result)
                self.assertTrue(diagnostic['source_inputs_unchanged'])
                self.assertFalse(diagnostic['suite_predicates']['spawn12'][predicate])
                self.assertEqual(diagnostic['processes'][0]['exit_code'],response.returncode)
                self.assertEqual(streams[(0,'stdout')],response.stdout);self.assertEqual(streams[(0,'stderr')],response.stderr)
                self.assertEqual([row['suite'] for row in diagnostic['processes']],result['required'])
                self.assertEqual(json.loads((result['out']/'receipt.json').read_bytes())['status'],'FAIL')

    def test_source_change_is_explicit_even_when_all_54_cases_pass(self):
        result=self.scenario('source',source_changed=True)
        self.assertEqual(result['exit'],1);self.assertEqual(len(result['calls']),4)
        diagnostic,_=self.diagnostic(result)
        self.assertFalse(diagnostic['source_inputs_unchanged']);self.assertIsNone(diagnostic['suite'])
        self.assertTrue(all(all(row.values()) for row in diagnostic['suite_predicates'].values()))
        receipt=json.loads((result['out']/'receipt.json').read_bytes())
        self.assertEqual(receipt['passed'],54);self.assertEqual(receipt['failed'],0);self.assertEqual(receipt['status'],'FAIL')

    def test_timeout_keeps_partial_bytes_and_stops_at_original_suite(self):
        stdout=b'partial\n::error::inert bytes\n\xff';stderr=b'partial error\n'
        result=self.scenario('timeout',response=subprocess.TimeoutExpired(['protocol'],40,output=stdout,stderr=stderr))
        diagnostic,streams=self.assert_single_process_stop(result,'TimeoutExpired')
        self.assertTrue(diagnostic['processes'][0]['timed_out']);self.assertIsNone(diagnostic['processes'][0]['exit_code'])
        self.assertEqual(streams[(0,'stdout')],stdout);self.assertEqual(streams[(0,'stderr')],stderr)
        self.assertEqual((result['out']/'FAILURE_PROCESS_00_STDOUT.bin').read_bytes(),stdout)
        self.assertFalse((result['out']/'spawn12/stdout.txt').exists())
        self.assertFalse(any(line.startswith('::error::') for line in result['console'].splitlines()))
        missing=self.scenario('timeout-unavailable',response=subprocess.TimeoutExpired(['protocol'],40))
        diagnostic,streams=self.assert_single_process_stop(missing,'TimeoutExpired')
        self.assertEqual(streams,{})
        for channel in ('stdout','stderr'):
            self.assertEqual(diagnostic['processes'][0][channel],{'available':False,'bytes':None,'sha256':None,'file':None})

    def test_invalid_encoding_keeps_both_raw_streams_without_retry(self):
        for channel in ('stdout','stderr'):
            with self.subTest(channel=channel):
                stdout=b'\xff' if channel=='stdout' else self.passed_output('spawn12')
                stderr=b'\xff' if channel=='stderr' else b'known error stream\n'
                result=self.scenario('invalid-'+channel,response=subprocess.CompletedProcess([],0,stdout,stderr))
                diagnostic,streams=self.assert_single_process_stop(result,'UnicodeDecodeError')
                self.assertEqual(diagnostic['processes'][0]['exit_code'],0)
                self.assertEqual(diagnostic['processes'][0]['phase'],channel.upper()+'_DECODE')
                self.assertEqual(streams[(0,'stdout')],stdout);self.assertEqual(streams[(0,'stderr')],stderr)
                self.assertFalse((result['out']/'spawn12/stdout.txt').exists())

    def test_malformed_case_keeps_written_text_and_raw_evidence(self):
        raw=b'CASE\tmissing fields\n'
        result=self.scenario('malformed',response=subprocess.CompletedProcess([],0,raw,b''))
        diagnostic,streams=self.assert_single_process_stop(result,'ValueError')
        self.assertEqual(diagnostic['phase'],'SUITE_PARSE');self.assertEqual(streams[(0,'stdout')],raw)
        self.assertEqual((result['out']/'spawn12/stdout.txt').read_bytes(),raw)
        self.assertFalse((result['out']/'spawn12/receipt.json').exists())

    def test_build_failures_keep_evidence_and_do_not_start_native_suites(self):
        controls={'nonzero':subprocess.CompletedProcess([],9,b'build log\n',b'build error\n'),
                  'timeout':subprocess.TimeoutExpired(['protocol'],180,output=b'partial build\n',stderr=b'partial build error\n'),
                  'encoding':subprocess.CompletedProcess([],0,b'\xff',b'build error\n')}
        for name,response in controls.items():
            with self.subTest(name=name):
                result=self.scenario('build-'+name,response=response,ci=True)
                self.assertEqual(result['exit'],2);self.assertEqual(len(result['calls']),1)
                diagnostic,streams=self.diagnostic(result)
                self.assertEqual(diagnostic['processes'][0]['kind'],'RUNTIME_BUILD')
                self.assertEqual(result['calls'][0].kwargs,{'capture_output':True,'timeout':180})
                self.assertEqual(streams[(0,'stdout')],response.stdout);self.assertEqual(streams[(0,'stderr')],response.stderr)
                self.assertTrue(all(not (result['out']/suite).exists() for suite in result['required']))

    def test_diagnostic_disk_failure_cannot_change_original_failure_exit(self):
        controls={'nonzero':(subprocess.CompletedProcess([],8,self.passed_output('spawn12'),b'error'),1,4),
                  'timeout':(subprocess.TimeoutExpired(['protocol'],40,output=b'partial',stderr=b'error'),2,1)}
        for name,(response,exit_code,count) in controls.items():
            with self.subTest(name=name):
                result=self.scenario('disk-'+name,response=response,diagnostic_write_error=True)
                self.assertEqual(result['exit'],exit_code);self.assertEqual(len(result['calls']),count)
                diagnostic,streams=self.diagnostic(result)
                self.assertEqual(diagnostic['diagnostic_file_error']['type'],'OSError')
                self.assertEqual(streams[(0,'stdout')],response.stdout);self.assertEqual(streams[(0,'stderr')],response.stderr)

    def test_post_runtime_refusal_retains_completed_evidence_and_original_exit(self):
        result=self.scenario('runtime',runtime_changed=True)
        self.assertEqual(result['exit'],2);self.assertEqual(len(result['calls']),4)
        diagnostic,_=self.diagnostic(result)
        self.assertEqual(diagnostic['exception'],'RUNTIME_CHANGED_DURING_TESTS')
        self.assertTrue(diagnostic['source_inputs_unchanged'])
        self.assertFalse((result['out']/'receipt.json').exists())
        self.assertTrue(all((result['out']/suite/'receipt.json').is_file() for suite in result['required']))

    def test_existing_output_refusal_does_not_write_diagnostics_into_callers_files(self):
        result=self.scenario('existing',existing_output=True)
        self.assertEqual(result['exit'],2);self.assertEqual(len(result['calls']),0);self.assertEqual(result['selected_calls'],0)
        diagnostic,streams=self.diagnostic(result)
        self.assertEqual(diagnostic['exception'],'FRESH_OUTPUT_OUTSIDE_DIST_REQUIRED');self.assertEqual(streams,{})
        self.assertEqual({p.name for p in result['out'].iterdir()},{'sentinel'})
        self.assertEqual((result['out']/'sentinel').read_bytes(),b'caller-owned output')

if __name__=='__main__': unittest.main()
