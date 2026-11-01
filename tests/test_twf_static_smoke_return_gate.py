import copy
import json
import sys
import unittest
import pathlib

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import open_cloud_engine_preflight as cloud
import twf_static_smoke_return_gate as gate

SESSION = '7c31219e-5b87-4ce7-82d7-d084e8b2a702'
TASK = '9e88c178-00ea-46e5-8920-fd916c4bcda0'


def valid_plan():
    return cloud.readiness(
        repository=cloud.REPO, source_main=cloud.SOURCE_MAIN,
        producer_run=cloud.PRODUCER_RUN, artifact_id=cloud.PRODUCER_ARTIFACT,
        zip_sha256=cloud.ZIP_SHA256, xml_sha256=cloud.XML_SHA256,
        xml_bytes=cloud.XML_SIZE, universe_id=12345, place_id=67890,
        version_id=56, private_target_reviewed=True,
        saved_version_evidence_checked=True,
        script_path=ROOT/'tools'/'twf_open_cloud_smoke.luau'
    )


def valid_task():
    return {'path': f'universes/12345/places/67890/versions/56/luau-execution-sessions/{SESSION}/tasks/{TASK}',
        'state': 'COMPLETE',
        'output': {'results': [{
            'marker': cloud.MARKER,
            'source_main_sha': cloud.SOURCE_MAIN,
            'topology': cloud.EXPECTED_TOPOLOGY,
            'wave_one': 5,
            'wave_nine': 20,
            'server_player_session_verified': False,
            'two_client_verified': False,
            'mobile_verified': False,
            'publish_authorized': False,
        }]}}


class GateTests(unittest.TestCase):
    def setUp(self):
        self.plan=valid_plan()
        self.task=valid_task()

    def denied(self,mutate):
        plan=copy.deepcopy(self.plan)
        task=copy.deepcopy(self.task)
        mutate(plan,task)
        with self.assertRaises(gate.ResultHold):
            gate.inspect_untrusted_return(plan,task)

    def test_01_success_reports_not_provider_pass(self):
        outcome=gate.inspect_untrusted_return(self.plan,self.task)
        self.assertEqual(outcome['status'],'STATIC_SMOKE_RETURN_CONSISTENT_UNTRUSTED')
        self.assertTrue(outcome['all_expected_return_fields_match'])
        for key in ('roblox_provider_authenticated','real_roblox_engine_verified',
                    'play_mode_verified','mobile_verified','may_publish','may_spend'):
            self.assertIs(outcome[key],False)

    def test_02_strict_json_roundtrip(self):
        self.assertEqual(gate.inspect_untrusted_json(self.plan,json.dumps(self.task))['status'],
                         'STATIC_SMOKE_RETURN_CONSISTENT_UNTRUSTED')

    def test_03_marker_substring_in_wrong_table(self):
        self.denied(lambda p,t: t['output'].__setitem__('results',[{'msg':cloud.MARKER}]))

    def test_04_marker_substring_false_positive(self):
        self.denied(lambda p,t: t['output']['results'][0].__setitem__('marker','prefix_'+cloud.MARKER))

    def test_05_claimed_string_instead_of_table(self):
        self.denied(lambda p,t: t['output'].__setitem__('results',[cloud.MARKER]))

    def test_06_empty_return_list(self):
        self.denied(lambda p,t: t['output'].__setitem__('results',[]))

    def test_07_duplicate_result_tables(self):
        self.denied(lambda p,t: t['output']['results'].append(copy.deepcopy(t['output']['results'][0])))

    def test_08_additional_tricky_field(self):
        self.denied(lambda p,t: t['output']['results'][0].__setitem__('real_engine_verified',True))

    def test_09_missing_field(self):
        self.denied(lambda p,t: t['output']['results'][0].pop('mobile_verified'))

    def test_10_bool_not_integer_for_wave_size(self):
        self.denied(lambda p,t: t['output']['results'][0].__setitem__('wave_one',True))

    def test_11_wrong_wave_size(self):
        self.denied(lambda p,t: t['output']['results'][0].__setitem__('wave_nine',21))

    def test_12_source_sha_drift(self):
        self.denied(lambda p,t: t['output']['results'][0].__setitem__('source_main_sha','f'*40))

    def test_13_wrong_topology(self):
        self.denied(lambda p,t: t['output']['results'][0].__setitem__('topology','5_expected_game_objects'))

    def test_14_overcredit_mobile(self):
        self.denied(lambda p,t: t['output']['results'][0].__setitem__('mobile_verified',True))

    def test_15_overcredit_publication(self):
        self.denied(lambda p,t: t['output']['results'][0].__setitem__('publish_authorized',True))

    def test_16_wrong_saved_version(self):
        self.denied(lambda p,t: t.__setitem__('path',t['path'].replace('/versions/56/','/versions/57/')))

    def test_17_wrong_task_path(self):
        self.denied(lambda p,t: t.__setitem__('path',t['path'].replace('tasks/','task/')))

    def test_18_task_failed_but_marker_present(self):
        self.denied(lambda p,t: t.__setitem__('state','FAILED'))

    def test_19_task_processing_but_marker_present(self):
        self.denied(lambda p,t: t.__setitem__('state','PROCESSING'))

    def test_20_task_has_error(self):
        self.denied(lambda p,t: t.__setitem__('error',{'code':'FAULT'}))

    def test_21_claimed_origin_true_in_plan(self):
        self.denied(lambda p,t: p.__setitem__('provider_authenticated',True))

    def test_22_claimed_permission_in_plan(self):
        self.denied(lambda p,t: p.__setitem__('may_call_roblox',True))

    def test_23_unreviewed_script_pin(self):
        self.denied(lambda p,t: p.__setitem__('script_sha256','0'*64))

    def test_24_inconsistent_request_target(self):
        self.denied(lambda p,t: p['request'].__setitem__('path',p['request']['path'].replace('/versions/56/','/versions/57/')))

    def test_25_extra_output_logs(self):
        self.denied(lambda p,t: t['output'].__setitem__('log','OK'))

    def test_26_invalid_task_json_duplicate_keys(self):
        original=json.dumps(self.task)
        duplicated=original.replace('"state": "COMPLETE"','"state": "COMPLETE", "state": "COMPLETE"',1)
        with self.assertRaises(gate.ResultHold):
            gate.inspect_untrusted_json(self.plan,duplicated)

    def test_27_invalid_task_json_nan(self):
        raw=json.dumps(self.task).replace('"wave_one": 5','"wave_one": NaN')
        with self.assertRaises(gate.ResultHold):
            gate.inspect_untrusted_json(self.plan,raw)

    def test_28_wrong_script_body_digest(self):
        self.denied(lambda p,t: p['request'].__setitem__('body_contains_exact_reviewed_script',False))

    def test_29_boolean_false_not_integer_zero(self):
        self.denied(lambda p,t: t['output']['results'][0].__setitem__('two_client_verified',0))

    def test_30_no_task_output(self):
        self.denied(lambda p,t: t.pop('output'))

    def test_31_forged_body_sha(self):
        self.denied(lambda p,t: p['request'].__setitem__('body_sha256','f'*64))

    def test_32_wrong_script_byte_length(self):
        self.denied(lambda p,t: p.__setitem__('script_bytes',p['script_bytes']+1))

    def test_33_schema_bool_not_one(self):
        self.denied(lambda p,t: p.__setitem__('schema',True))

    def test_34_xml_size_bool_not_integer(self):
        self.denied(lambda p,t: p.__setitem__('xml_bytes',True))


if __name__=='__main__':unittest.main()
