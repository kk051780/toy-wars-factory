"""S1 launch balance math and provenance smoke tests; NOT Luau engine execution."""
from __future__ import annotations
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import balance_model as b


def contract():
    return json.loads((ROOT/'data/source_contract.json').read_text(encoding='utf-8'))


class ScenarioTests(unittest.TestCase):
    def setUp(self):
        self.doc=contract()
        self.arena=self.doc['arena']

    def calc(self, variant='baseline',team='RED',role='RAIDER', **kwargs):
        return b.calculate(self.arena,self.doc[variant],team,role,**kwargs)

    def test_01_exact_source_pinned(self):
        self.assertEqual(self.doc['baseline_commit'],b.SOURCE_SHA)
        self.assertEqual(self.doc['baseline_file_sha1']['releases/P0D_S1_KIDS_RC01/src/shared/Config.luau'],
                         'ef10e4288e4732588116cd3e55d3d871ca803ff4')

    def test_02_baseline_source_values(self):
        p=self.doc['baseline'];self.assertEqual((p['castle_hp'],p['castle_attack_damage']['RAIDER'],
                                                 p['attack_cooldown_seconds']), (300,14,.85))

    def test_03_model_finite(self):
        self.assertIs(b.validate_contract(self.doc),self.doc)

    def test_04_baseline_raider_castle_26_seconds(self):
        self.assertAlmostEqual(self.calc()['castle_total_lb_s'],26.11316,places=4)

    def test_05_baseline_raider_egg_35_seconds(self):
        self.assertAlmostEqual(self.calc()['egg_total_lb_s'],34.89332,places=4)

    def test_06_baseline_fast_castle(self):
        self.assertLess(self.calc()['castle_to_egg_lb_ratio'],.8)

    def test_07_candidate_closer_to_parity(self):
        self.assertGreater(self.calc('candidate')['castle_to_egg_lb_ratio'],1)
        self.assertLess(self.calc('candidate')['castle_to_egg_lb_ratio'],1.15)

    def test_08_candidate_guardian_closer_to_parity(self):
        r=self.calc('candidate',role='GUARDIAN')['castle_to_egg_lb_ratio']
        self.assertGreater(r,.95); self.assertLess(r,1.15)

    def test_09_both_teams_exactly_symmetric(self):
        for variant in ('baseline','candidate'):
            for role in b.ALLOWED_ROLES:
                x=self.calc(variant,'RED',role);y=self.calc(variant,'BLUE',role)
                for key in ('egg_total_lb_s','castle_total_lb_s','hits_required'):
                    self.assertEqual(x[key],y[key])

    def test_10_candidate_source_value_only(self):
        s=(ROOT/'src/S1LaunchBalanceProfile.luau').read_text(encoding='utf-8')
        for item in ('CastleMaxHp = 420','RAIDER = 12','GUARDIAN = 10','return table.freeze'):
            self.assertIn(item,s)
        for forbidden in ('FireServer(', 'OnServerEvent','GetService(','.TakeDamage(','.Health =', 'DataStore'):
            self.assertNotIn(forbidden,s)

    def test_11_required_hits_baseline(self):
        self.assertEqual(self.calc()['hits_required'],22)

    def test_12_required_hits_candidate(self):
        self.assertEqual(self.calc('candidate')['hits_required'],35)

    def test_13_both_within_round(self):
        for variant in ('baseline','candidate'):
            for role in b.ALLOWED_ROLES:
                r=self.calc(variant,role=role)
                self.assertLess(r['egg_total_lb_s'],self.doc[variant]['match_seconds'])
                self.assertLess(r['castle_total_lb_s'],self.doc[variant]['match_seconds'])

    def test_14_slow_movement_increases_both(self):
        old=self.calc('candidate')
        new=self.calc('candidate',walk_multiplier=.8)
        self.assertGreater(new['egg_total_lb_s'],old['egg_total_lb_s'])
        self.assertGreater(new['castle_total_lb_s'],old['castle_total_lb_s'])

    def test_15_slower_attacks_only_impact_castle(self):
        old=self.calc('candidate')
        new=self.calc('candidate',cooldown_multiplier=1.2)
        self.assertEqual(new['egg_total_lb_s'],old['egg_total_lb_s'])
        self.assertGreater(new['castle_total_lb_s'],old['castle_total_lb_s'])

    def test_16_longer_hold_only_impacts_eggs(self):
        old=self.calc('candidate')
        new=self.calc('candidate',prompt_multiplier=1.2)
        self.assertEqual(new['castle_total_lb_s'],old['castle_total_lb_s'])
        self.assertGreater(new['egg_total_lb_s'],old['egg_total_lb_s'])

    def test_17_more_hitpoints_slow_castle(self):
        hp=copy.deepcopy(self.doc['candidate']);hp['castle_hp']+=100
        self.assertGreater(b.calculate(self.arena,hp,'RED','RAIDER')['castle_total_lb_s'],
                           self.calc('candidate')['castle_total_lb_s'])

    def test_18_more_attack_damage_speeds_castle(self):
        p=copy.deepcopy(self.doc['candidate']);p['castle_attack_damage']['RAIDER']+=5
        self.assertLess(b.calculate(self.arena,p,'RED','RAIDER')['castle_total_lb_s'],
                        self.calc('candidate')['castle_total_lb_s'])

    def test_19_report_does_not_claim_studio(self):
        r=b.report(self.doc)
        self.assertIn('cannot establish empirical', ' '.join(r['limitations']).lower())
        self.assertEqual(r['format'],'P0D_S1_ANALYTIC_LOWER_BOUND_REPORT_V1')

    def test_20_report_sample_byte_identical(self):
        r=b.report(self.doc)
        expected=json.loads((ROOT/'docs/ANALYSIS_OUTPUT.json').read_text(encoding='utf-8'))
        self.assertEqual(expected,r)

    def test_21_egg_capture_count_increases_route(self):
        a=copy.deepcopy(self.arena); a['captures_to_win']=3
        self.assertGreater(b.calculate(a,self.doc['candidate'],'RED','RAIDER')['egg_total_lb_s'],
                           self.calc('candidate')['egg_total_lb_s'])


class NegativeTests(unittest.TestCase):
    def setUp(self):self.doc=contract()

    def assertInvalidContract(self,selector,value):
        c=copy.deepcopy(self.doc)
        target,key=selector(c);target[key]=value
        with self.assertRaises(b.ModelError): b.validate_contract(c)

    def test_22_negative_hp(self):self.assertInvalidContract(lambda d:(d['candidate'],'castle_hp'),-1)
    def test_23_zero_hp(self):self.assertInvalidContract(lambda d:(d['candidate'],'castle_hp'),0)
    def test_24_boolean_hp(self):self.assertInvalidContract(lambda d:(d['candidate'],'castle_hp'),True)
    def test_25_float_hp(self):self.assertInvalidContract(lambda d:(d['candidate'],'castle_hp'),420.5)
    def test_26_nan_speed(self):self.assertInvalidContract(lambda d:(d['baseline']['role_walk_speed'],'RAIDER'),float('nan'))
    def test_27_inf_damage(self):self.assertInvalidContract(lambda d:(d['candidate']['castle_attack_damage'],'RAIDER'),float('inf'))
    def test_28_zero_cooldown(self):self.assertInvalidContract(lambda d:(d['candidate'],'attack_cooldown_seconds'),0)
    def test_29_negative_hold(self):self.assertInvalidContract(lambda d:(d['arena'],'prompt_hold_seconds'),-.001)
    def test_30_negative_z_allowed(self):self.assertIs(b.validate_contract(self.doc),self.doc)
    def test_31_infinite_z_rejected(self):self.assertInvalidContract(lambda d:(d['arena'],'egg_z'),float('inf'))
    def test_32_boolean_z_rejected(self):self.assertInvalidContract(lambda d:(d['arena'],'egg_z'),False)
    def test_33_bad_team(self):
        with self.assertRaises(b.ModelError):b.calculate(self.doc['arena'],self.doc['baseline'],'GREEN','RAIDER')
    def test_34_bad_role(self):
        with self.assertRaises(b.ModelError):b.calculate(self.doc['arena'],self.doc['baseline'],'RED','TANK')
    def test_35_zero_walk_mult(self):
        with self.assertRaises(b.ModelError):b.calculate(self.doc['arena'],self.doc['baseline'],'RED','RAIDER',walk_multiplier=0)
    def test_36_unknown_keys(self):
        c=copy.deepcopy(self.doc);c['extra']='forbidden'
        with self.assertRaises(b.ModelError):b.validate_contract(c)
    def test_37_wrong_source(self):
        c=copy.deepcopy(self.doc);c['baseline_commit']='a'*40
        with self.assertRaises(b.ModelError):b.validate_contract(c)
    def test_38_bad_capture_count(self):self.assertInvalidContract(lambda d:(d['arena'],'captures_to_win'),1000000)
    def test_39_bad_blob_sha(self):
        c=copy.deepcopy(self.doc);c['baseline_file_sha1']['a']='not a hash'
        with self.assertRaises(b.ModelError):b.validate_contract(c)
    def test_40_own_role_overpowered(self):
        c=copy.deepcopy(self.doc);c['candidate']['castle_attack_damage']['GUARDIAN']=50
        with self.assertRaises(b.ModelError):b.validate_contract(c)
    def test_41_negative_walk_speed(self):self.assertInvalidContract(lambda d:(d['candidate']['role_walk_speed'],'GUARDIAN'),-2)
    def test_42_boolean_interact_radius(self):self.assertInvalidContract(lambda d:(d['arena'],'interaction_distance'),True)


if __name__=='__main__':unittest.main()
