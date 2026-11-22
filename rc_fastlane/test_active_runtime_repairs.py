"""Actual generated66 contract tests, not a synthetic replacement source tree.

Set P0D_ACTIVE66_TEST_DIST to the existing producer's locked original66 dist.
Only temporary copies are mutated. Native gameplay fixtures remain separate.
"""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

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

if __name__=='__main__': unittest.main()
