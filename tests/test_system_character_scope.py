"""Only canonical game Lua remains scheduled-WORKER writable; catalog edits need manual review."""
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
    def test_unattended_worker_cannot_edit_character_catalog_even_with_a_regression(self):
        # A new regression is not a grant of permission to edit trusted metadata.
        for changes in ([('M','config/characters.json')],
                        [('M','config/characters.json'),('A','tests/auto/new_character_spec.lua')]):
            with self.subTest(changes=changes):
                self.assertTrue(any('outside repair scope' in error
                                    for error in violations(changes,self.p)))
    def test_no_protected_config_path_is_worker_writable(self):
        for path in ['config/autonomous_repair.json','config/quality_policy.json','config/characters_extra.json','config/progress_milestones.json']:
            with self.subTest(path=path):self.assertTrue(violations([('M',path),('A','tests/auto/new_character_spec.lua')],self.p))
    def test_deleting_or_replacing_the_catalog_is_not_authorized(self):
        for status in ['A','D','R100']:
            with self.subTest(status=status):self.assertTrue(violations([(status,'config/characters.json'),('A','tests/auto/new_character_spec.lua')],self.p))
    def test_original_controls_and_source_paths_are_preserved(self):
        self.assertEqual(set(self.p['source_paths']), {
            'src/ToyWarsBalance.lua','src/ToyWarsServer.server.lua','src/ToyWarsHUD.client.lua'})
        self.assertNotIn('config/characters.json', self.p.get('additional_source_paths', []))
        self.assertFalse(self.p['roblox_publish_authorized'])
        self.assertFalse(self.p['external_provider_inference_authorized'])
        self.assertFalse(self.p['worker_may_merge'])
        self.assertTrue(self.p['integration']['require_independent_task_and_run'])
    def test_canonical_game_source_with_new_lua_regression_remains_worker_writable(self):
        for source in self.p['source_paths']:
            with self.subTest(source=source):
                self.assertEqual(violations([('M',source),
                                             ('A','tests/auto/new_game_spec.lua')],self.p),[])

    def test_character_pipeline_document_does_not_gain_meta_edit_permission(self):
        self.assertNotIn('docs/CHARACTER_PIPELINE.md',self.p['system_review']['allowed_document_paths'])
        entries=[('A','tools/system_next_fixture.py'),('A','tests/test_system_next_fixture.py'),
                 ('A','history/C99999_fixture.json'),('M','docs/CHARACTER_PIPELINE.md')]
        self.assertTrue(any('docs/CHARACTER_PIPELINE.md' in e for e in meta_violations(entries,self.p)))

if __name__=='__main__':unittest.main()
