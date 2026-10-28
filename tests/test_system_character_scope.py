"""The new character metadata path is exact and retains regression requirements."""
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from check_auto_diff import violations
from check_meta_diff import violations as meta_violations

class CharacterScopeTests(unittest.TestCase):
    def setUp(self):self.p=json.loads((ROOT/'config/autonomous_repair.json').read_text())
    def test_new_character_metadata_still_requires_a_new_executable_regression(self):
        self.assertTrue(violations([('M','config/characters.json')],self.p))
        self.assertEqual(violations([('M','config/characters.json'),('A','tests/auto/new_character_spec.lua')],self.p),[])
    def test_new_permission_is_exact_not_a_config_directory_wildcard(self):
        for path in ['config/autonomous_repair.json','config/quality_policy.json','config/characters_extra.json','config/progress_milestones.json']:
            with self.subTest(path=path):self.assertTrue(violations([('M',path),('A','tests/auto/new_character_spec.lua')],self.p))
    def test_deleting_or_replacing_the_catalog_is_not_authorized(self):
        for status in ['A','D','R100']:
            with self.subTest(status=status):self.assertTrue(violations([(status,'config/characters.json'),('A','tests/auto/new_character_spec.lua')],self.p))
    def test_original_controls_and_source_paths_are_preserved(self):
        self.assertTrue({'src/ToyWarsBalance.lua','src/ToyWarsServer.server.lua','src/ToyWarsHUD.client.lua'}<=set(self.p['source_paths']))
        self.assertFalse(self.p['roblox_publish_authorized'])
        self.assertFalse(self.p['external_provider_inference_authorized'])
        self.assertFalse(self.p['worker_may_merge'])
        self.assertTrue(self.p['integration']['require_independent_task_and_run'])
    def test_character_pipeline_document_does_not_gain_meta_edit_permission(self):
        self.assertNotIn('docs/CHARACTER_PIPELINE.md',self.p['system_review']['allowed_document_paths'])
        entries=[('A','tools/system_next_fixture.py'),('A','tests/test_system_next_fixture.py'),
                 ('A','history/C99999_fixture.json'),('M','docs/CHARACTER_PIPELINE.md')]
        self.assertTrue(any('docs/CHARACTER_PIPELINE.md' in e for e in meta_violations(entries,self.p)))

if __name__=='__main__':unittest.main()
