"""Adversarial character admission tests; acquisition scores are hypotheses."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from system_character_pipeline import catalog_errors,assess


class CharacterPipelineTests(unittest.TestCase):
    def setUp(self):
        self.catalog=json.loads((ROOT/'config/characters.json').read_text())
        self.balance=(ROOT/'src/ToyWarsBalance.lua').read_text()
        self.required=json.loads((ROOT/'config/quality_policy.json').read_text())['character_required']

    def errors(self,c=None,b=None):
        return catalog_errors(self.catalog if c is None else c,self.balance if b is None else b,self.required)

    def test_active_and_planned_rosters_are_consistent(self):
        self.assertEqual(self.errors(),[])
        active={c['id'] for c in self.catalog['characters']}
        planned={c['id'] for c in self.catalog['candidates']}
        self.assertTrue({'pon','guardon','tankuru'} <= active)
        self.assertFalse(active & planned)
        self.assertEqual(len(active | planned),len(self.catalog['characters'])+len(self.catalog['candidates']))

    def test_baseline_character_cannot_be_removed(self):
        self.catalog['characters']=[c for c in self.catalog['characters'] if c['id']!='pon']
        self.assertIn('baseline characters removed',self.errors())

    def test_metadata_alone_cannot_promote_a_character(self):
        c=self.catalog['candidates'].pop(0);c['status']='prototype';self.catalog['characters'].append(c)
        self.assertIn('catalog and executable balance roster disagree',self.errors())

    def test_unregistered_catalog_and_duplicate_source_keys_fail_closed(self):
        self.assertTrue(self.errors(b=self.balance.replace('    curebo =','    impostor =')))
        self.assertTrue(self.errors(b=self.balance.replace('    curebo =','    pon =')))

    def test_late_literal_and_dynamic_roster_reassignment_fail_closed(self):
        for write in ('B.UNITS = { impostor = {}, junk = {} }',
                      'B.UNITS = getNewUnits()',
                      'B . UNITS = {}'):
            with self.subTest(write=write):
                self.assertIn('B.UNITS', ' '.join(self.errors(
                    b=self.balance + "\n" + write + "\n")))

    def test_bracket_alias_direct_field_and_nested_field_writes_rejected(self):
        for write in ('B["UNITS"] = {}', "B['UNITS'] = {}",
                      'B.UNITS.curebo = nil', 'B.UNITS["pon"] = nil',
                      'B.UNITS.curebo.cost = 0', 'B.UNITS.curebo.cost += 1',
                      'B.UNITS[id] = nil'):
            with self.subTest(write=write):
                self.assertTrue(self.errors(b=self.balance + "\n" + write))

    def test_rawset_and_table_helpers_cannot_replace_roster(self):
        for write in ('rawset(B, "UNITS", {})',
                      "rawset(B, 'UNITS', {})",
                      'rawset(B.UNITS, "pon", nil)',
                      'table.clear(B.UNITS)',
                      'table.insert(B.UNITS, "intruder")',
                      'setmetatable(B.UNITS, {})'):
            with self.subTest(write=write):
                self.assertTrue(self.errors(b=self.balance + "\n" + write))

    def test_reassigned_module_table_cannot_bypass_roster(self):
        self.assertIn("balance module reassignment is forbidden",
                      self.errors(b=self.balance + "\nB = {UNITS = {}}\n"))

    def test_comments_and_quoted_examples_do_not_trigger_false_writes(self):
        examples = (
            '-- B.UNITS = { intruder = {} }',
            '--[[ B.UNITS.pon = nil ]]',
            'local example = "B.UNITS.curebo = nil"',
            "local example2 = 'B[\"UNITS\"] = {}'",
        )
        for example in examples:
            with self.subTest(example=example):
                self.assertEqual(self.errors(b=self.balance + "\n" + example), [])

    def test_fake_first_roster_in_comment_cannot_override_real_source(self):
        prefix = '-- B.UNITS = {\n--     intruder = {},\n-- }\n'
        self.assertEqual(self.errors(b=prefix + self.balance), [])


    def test_duplicates_across_live_and_planned_are_rejected(self):
        self.catalog['candidates'].append(deepcopy(self.catalog['characters'][0]))
        self.assertTrue(self.errors())

    def test_npc_is_never_a_collectible_character(self):
        self.catalog['candidates'][0]['id']='junk'
        self.assertIn('duplicate/player-NPC identity',self.errors())

    def test_candidate_cannot_claim_implementation_or_native_visuals(self):
        self.catalog['candidates'][0]['status']='prototype'
        self.catalog['candidates'][0]['visual_contract']['native_render_verified']=True
        self.assertGreaterEqual(len(self.errors()),2)

    def test_missing_role_or_distinguishing_shape_is_rejected(self):
        self.catalog['candidates'][0]['role']=''
        self.catalog['candidates'][0]['shape']=self.catalog['characters'][0]['shape']
        self.assertGreaterEqual(len(self.errors()),2)

    def test_boolean_cost_and_out_of_range_appeal_are_rejected(self):
        b=self.catalog['candidates'][0]['business_case']
        b['effort_points']['qa']=True;b['appeal_scores']['acquisition']=6
        self.assertGreaterEqual(len(self.errors()),2)

    def test_unsupported_measured_business_claim_is_rejected(self):
        self.catalog['candidates'][0]['business_case']['evidence_status']='CUSTOMER_GROWTH_PROVEN'
        self.assertTrue(self.errors())

    def test_heavy_geometry_and_missing_reference_are_rejected(self):
        c=self.catalog['candidates'][0];c['visual_contract']['primitive_part_budget']=200
        c['source_review']=[]
        self.assertGreaterEqual(len(self.errors()),2)

    def test_ranking_is_deterministic_and_does_not_count_skins(self):
        a=assess(self.catalog);b=deepcopy(self.catalog);b['candidates'].reverse()
        self.assertEqual(a,assess(b))
        self.assertEqual({c['id'] for c in a},{c['id'] for c in self.catalog['candidates']})
        self.assertEqual(len(a),len(self.catalog['candidates']))
        self.assertTrue(all(c['market_effect']=='NOT_MEASURED' and c['native_visuals']=='NOT_RUN' for c in a))

    def test_next_character_promotion_keeps_catalog_and_ranking_valid(self):
        before={c['id'] for c in self.catalog['characters']}
        total=len(self.catalog['characters'])+len(self.catalog['candidates'])
        candidate=self.catalog['candidates'].pop(0)
        candidate['status']='prototype'
        self.catalog['characters'].append(candidate)
        registration=f"    {candidate['id']} = {{name = \"NEXT FIXTURE\", cost = 40}},\n"
        self.balance=self.balance.replace('    junk =',registration+'    junk =',1)
        self.balance=self.balance.replace(
            'B.PLAYABLE_IDS = {"pon", "guardon", "tankuru", "curebo"}',
            'B.PLAYABLE_IDS = {"pon", "guardon", "tankuru", "curebo", "'+candidate['id']+'"}')
        self.assertEqual(self.errors(),[])
        self.assertEqual({c['id'] for c in self.catalog['characters']},before | {candidate['id']})
        self.assertEqual(len(self.catalog['characters'])+len(self.catalog['candidates']),total)
        self.assertNotIn(candidate['id'],{c['id'] for c in assess(self.catalog)})
        self.test_active_and_planned_rosters_are_consistent()
        self.test_ranking_is_deterministic_and_does_not_count_skins()

    def test_additional_original_candidate_is_valid_without_freezing_roster_size(self):
        extra=deepcopy(self.catalog['candidates'][0])
        extra.update(id='future_fixture',shape='fixture_new_shape',color='#010203')
        self.catalog['candidates'].append(extra)
        self.assertEqual(self.errors(),[])
        self.assertIn('future_fixture',{c['id'] for c in assess(self.catalog)})
        self.test_active_and_planned_rosters_are_consistent()
        self.test_ranking_is_deterministic_and_does_not_count_skins()


    def test_playable_roster_matches_all_active_characters(self):
        self.assertEqual(self.errors(), [])
        hud=(ROOT/'src/ToyWarsHUD.client.lua').read_text()
        self.assertIn('local unitOrder=B.PLAYABLE_IDS', hud)
        self.assertIn('local id=unitOrder[(page-1)*3+i]', hud)
        self.assertIn('visibleIds[i]=id', hud)

    def test_missing_or_unknown_playable_unit_fails_closed(self):
        before='B.PLAYABLE_IDS = {"pon", "guardon", "tankuru", "curebo"}'
        self.assertEqual(self.balance.count(before), 1)
        for after in (
            'B.PLAYABLE_IDS = {"pon", "guardon", "tankuru"}',
            'B.PLAYABLE_IDS = {"pon", "guardon", "tankuru", "impostor"}',
        ):
            with self.subTest(after=after):
                self.assertIn('catalog and playable HUD roster disagree',
                              self.errors(b=self.balance.replace(before, after)))

    def test_duplicate_npc_and_dynamic_playable_roster_fail_closed(self):
        before='B.PLAYABLE_IDS = {"pon", "guardon", "tankuru", "curebo"}'
        for after in (
            'B.PLAYABLE_IDS = {"pon", "guardon", "pon", "curebo"}',
            'B.PLAYABLE_IDS = {"pon", "guardon", "junk", "curebo"}',
            'B.PLAYABLE_IDS = getCharacterList()',
            'B.PLAYABLE_IDS = {"pon", "guardon", "tankuru", curebo}',
        ):
            with self.subTest(after=after):
                self.assertTrue(self.errors(b=self.balance.replace(before, after)))

    def test_multiple_playable_assignments_are_not_accepted(self):
        mutated=self.balance+'\nB.PLAYABLE_IDS = {"pon", "guardon", "tankuru", "curebo"}\n'
        self.assertIn('playable roster missing or ambiguous',self.errors(b=mutated))


if __name__=='__main__':unittest.main()
