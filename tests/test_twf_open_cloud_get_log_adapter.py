"""Tests are local spoofable fixtures, NEVER authentic Roblox API calls."""
import copy
import json
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import open_cloud_engine_preflight as cloud
import twf_open_cloud_get_log_adapter as adapter

SESSION='7c31219e-5b87-4ce7-82d7-d084e8b2a702'
TASK='9e88c178-00ea-46e5-8920-fd916c4bcda0'

def fixture():
    script=cloud.pin_script(ROOT/'tools'/'twf_open_cloud_smoke.luau')
    plan=cloud.readiness(
        repository=cloud.REPO,source_main=cloud.SOURCE_MAIN,
        producer_run=cloud.PRODUCER_RUN,artifact_id=cloud.PRODUCER_ARTIFACT,
        zip_sha256=cloud.ZIP_SHA256,xml_sha256=cloud.XML_SHA256,
        xml_bytes=cloud.XML_SIZE,universe_id=12345,place_id=67890,version_id=56,
        private_target_reviewed=True,saved_version_evidence_checked=True,
        script_path=ROOT/'tools'/'twf_open_cloud_smoke.luau')
    path=f'universes/12345/places/67890/versions/56/luau-execution-sessions/{SESSION}/tasks/{TASK}'
    task={'path':path,'state':'COMPLETE','script':script,'timeout':'30s',
          'output':{'results':[{
              'marker':cloud.MARKER,'source_main_sha':cloud.SOURCE_MAIN,
              'topology':cloud.EXPECTED_TOPOLOGY,'wave_one':5,'wave_nine':20,
              'server_player_session_verified':False,'two_client_verified':False,
              'mobile_verified':False,'publish_authorized':False,
          }]}}
    logs={'luauExecutionSessionTaskLogs':[{'path':path+'/logs/1','messages':['ok']}],
          'nextPageToken':''}
    return plan,task,logs

class AdapterTests(unittest.TestCase):
    def check(self, mutate=None):
        p,t,l=fixture()
        if mutate:mutate(p,t,l)
        return adapter.inspect_untrusted_get_and_logs(p,json.dumps(t),json.dumps(l))
    def denied(self, mutate):
        with self.assertRaises(adapter.ReceiptHold):
            self.check(mutate)
    def test_01_valid_raw_task_and_logs_untrusted(self):
        r=self.check()
        self.assertEqual(r['status'],'UNTRUSTED_OPEN_CLOUD_GET_LOGS_CONSISTENT')
        self.assertFalse(r['provider_authenticated'])
    def test_02_no_logs_allowed_but_never_provider_proof(self):
        r=self.check(lambda p,t,l:l['luauExecutionSessionTaskLogs'].clear())
        self.assertEqual(r['log_record_count'],0)
        self.assertFalse(r['engine_verified'])
    def test_03_fake_script_echo_rejected(self):
        self.denied(lambda p,t,l:t.__setitem__('script','return true'))
    def test_04_missing_script_echo_rejected(self):
        self.denied(lambda p,t,l:t.pop('script'))
    def test_05_wrong_timeout_echo_rejected(self):
        self.denied(lambda p,t,l:t.__setitem__('timeout','300s'))
    def test_06_missing_timeout_echo_rejected(self):
        self.denied(lambda p,t,l:t.pop('timeout'))
    def test_07_log_path_foreign_task_rejected(self):
        self.denied(lambda p,t,l:l['luauExecutionSessionTaskLogs'][0].__setitem__('path','universes/1/logs/1'))
    def test_08_log_path_foreign_version_rejected(self):
        self.denied(lambda p,t,l:l['luauExecutionSessionTaskLogs'][0].__setitem__('path',l['luauExecutionSessionTaskLogs'][0]['path'].replace('/versions/56/','/versions/57/')))
    def test_09_missing_pagination_token_rejected(self):
        self.denied(lambda p,t,l:l.pop('nextPageToken'))
    def test_10_nonempty_pagination_token_rejected(self):
        self.denied(lambda p,t,l:l.__setitem__('nextPageToken','another'))
    def test_11_second_log_wrong_sequence_rejected(self):
        self.denied(lambda p,t,l:l['luauExecutionSessionTaskLogs'].append(copy.deepcopy(l['luauExecutionSessionTaskLogs'][0])))
    def test_12_nontext_flat_messages_rejected(self):
        self.denied(lambda p,t,l:l['luauExecutionSessionTaskLogs'][0].__setitem__('messages',[False]))
    def test_13_unbounded_flat_message_rejected(self):
        self.denied(lambda p,t,l:l['luauExecutionSessionTaskLogs'][0].__setitem__('messages',['X'*3000]))
    def test_14_structured_log_sample_accepted_without_persisting_text(self):
        def add(p,t,l):
            l['luauExecutionSessionTaskLogs'][0]['structuredMessages']=[{
                'message':'private details','createTime':'2025-02-13T20:32:41.069Z',
                'messageType':'WARNING'}]
        r=self.check(add)
        self.assertNotIn('private details',str(r))
        self.assertFalse(r['raw_provider_payload_stored'])
    def test_15_forged_structured_log_type_rejected(self):
        self.denied(lambda p,t,l:l['luauExecutionSessionTaskLogs'][0].__setitem__('structuredMessages',[{'message':'x','createTime':True,'messageType':'WARNING'}]))
    def test_16_extra_logs_payload_rejected(self):
        self.denied(lambda p,t,l:l.__setitem__('taskId','spoof'))
    def test_17_false_success_failed_task_rejected(self):
        self.denied(lambda p,t,l:t.__setitem__('state','FAILED'))
    def test_18_wrong_game_rules_rejected(self):
        self.denied(lambda p,t,l:t['output']['results'][0].__setitem__('wave_nine',999))
    def test_19_duplicate_json_keys_rejected(self):
        p,t,l=fixture()
        raw=json.dumps(l).replace('"nextPageToken": ""','"nextPageToken": "", "nextPageToken": ""')
        with self.assertRaises(adapter.ReceiptHold):
            adapter.inspect_untrusted_get_and_logs(p,json.dumps(t),raw)
    def test_20_success_flags_never_grant_authority(self):
        r=self.check()
        self.assertFalse(r['may_post'])
        self.assertFalse(r['may_publish'])
        self.assertFalse(r['may_merge'])
        self.assertFalse(r['may_spend'])
        self.assertFalse(r['origin_authenticated'])
    def test_21_multiple_valid_log_records(self):
        def add(p,t,l):
            second=copy.deepcopy(l['luauExecutionSessionTaskLogs'][0])
            second['path']=t['path']+'/logs/2'
            l['luauExecutionSessionTaskLogs'].append(second)
        self.assertEqual(self.check(add)['log_record_count'],2)
    def test_22_very_large_response_rejected(self):
        p,t,l=fixture()
        with self.assertRaises(adapter.ReceiptHold):
            adapter.inspect_untrusted_get_and_logs(p,json.dumps(t),json.dumps(l)+' '*130000)
    def test_23_malformed_task_json_rejected(self):
        p,t,l=fixture()
        with self.assertRaises(adapter.ReceiptHold):
            adapter.inspect_untrusted_get_and_logs(p,'{not json}',json.dumps(l))

if __name__=='__main__':unittest.main()
