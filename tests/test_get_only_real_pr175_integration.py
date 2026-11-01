"""Actual PR175 typed contract + GET-only transport integration; MOCK HTTP only.

Uses the real accepted candidate modules, not a substituted/mock checker.
No Roblox API, real key, actual provider origin or engine proof.
"""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import test_twf_open_cloud_get_log_adapter as fixture_lib
import twf_roblox_get_only_probe as transport
import twf_get_only_pr175_bridge as bridge

TEST_KEY='NOT_A_REAL_ROBLOX_KEY'

class Response:
    def __init__(self, body, url):
        self.raw=json.dumps(body,ensure_ascii=False).encode('utf-8')
        self.url=url;self.status=200
        self.headers={'Content-Type':'application/json'}
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def geturl(self):return self.url
    def read(self,n):return self.raw[:n]

class Opener:
    def __init__(self,*payloads):
        self.payloads=list(payloads);self.requests=[]
    def open(self,req,timeout):
        self.requests.append((req,timeout))
        if not self.payloads:raise AssertionError('unexpected extra HTTP request')
        return Response(self.payloads.pop(0),req.full_url)

class RealContractTests(unittest.TestCase):
    def setUp(self):
        self.plan,self.task,self.logs=fixture_lib.fixture()
        self.ack={'path':self.task['path'],'state':'PROCESSING',
                  'script':self.task['script'],'timeout':'30s'}
        self.target=transport.TaskTarget(
            universe_id='12345',place_id='67890',saved_version_id='56',
            execution_session_id=fixture_lib.SESSION,
            task_id=fixture_lib.TASK,
            private_target_reviewed=True,original_create_receipt_reviewed=True)
    def call(self):
        opener=Opener(self.task,self.logs)
        value=bridge.get_existing_task_checked(
            self.target,TEST_KEY,self.plan,json.dumps(self.ack),opener=opener)
        return value,opener
    def refused(self):
        with self.assertRaises(transport.ProbeHold) as e:self.call()
        self.assertEqual(str(e.exception),'LOCAL_CONTRACT_REJECTED')
    def test_01_real_contract_2_get_complete_untrusted(self):
        result,opener=self.call()
        self.assertTrue(result['local_contract_checked_untrusted'])
        self.assertEqual(result['http_get_count'],2)
        self.assertEqual([r.get_method() for r,t in opener.requests],['GET','GET'])
        self.assertFalse(result['roblox_provider_authenticated'])
        self.assertFalse(result['engine_verified'])
    def test_02_mismatch_original_create_ack_task_id_rejected(self):
        self.ack['path']=self.ack['path'].replace(f'/tasks/{fixture_lib.TASK}',f'/tasks/{fixture_lib.SESSION}')
        self.refused()
    def test_03_mismatch_original_create_ack_saved_version_rejected(self):
        self.ack['path']=self.ack['path'].replace('/versions/56/','/versions/57/')
        self.refused()
    def test_04_mismatch_original_create_ack_script_rejected(self):
        self.ack['script']='return 1'
        self.refused()
    def test_05_mismatch_original_create_ack_timeout_rejected(self):
        self.ack['timeout']='300s'
        self.refused()
    def test_06_invalid_real_rule_output_rejected(self):
        self.task['output']['results'][0]['wave_nine']=999
        self.refused()
    def test_07_wrong_task_script_echo_rejected(self):
        self.task['script']='return true'
        self.refused()
    def test_08_incomplete_log_pagination_rejected(self):
        self.logs['nextPageToken']='more'
        with self.assertRaises(transport.ProbeHold):self.call()
    def test_09_log_foreign_task_rejected(self):
        self.logs['luauExecutionSessionTaskLogs'][0]['path']='foreign'
        with self.assertRaises(transport.ProbeHold):self.call()
    def test_10_pending_task_one_get_no_contract_upgrade(self):
        self.task['state']='PROCESSING'
        result,opener=self.call()
        self.assertEqual(result['status'],'UNTRUSTED_READ_ONLY_PENDING')
        self.assertEqual(result['http_get_count'],1)
        self.assertFalse(result['local_contract_checked_untrusted'])
        self.assertEqual(len(opener.requests),1)
    def test_11_raw_secret_logs_never_returned(self):
        self.logs['luauExecutionSessionTaskLogs'][0]['messages']=[
            'REDACT_THIS_PRIVATE_LOG_MESSAGE']
        result,_=self.call()
        self.assertNotIn('REDACT_THIS_PRIVATE_LOG_MESSAGE',str(result))
        self.assertNotIn(TEST_KEY,str(result))
        self.assertFalse(result['api_key_returned'])
    def test_12_forged_create_ack_authorization_flag_never_trusted(self):
        self.ack['provider_authenticated']=True
        result,_=self.call()
        self.assertFalse(result['roblox_provider_authenticated'])
        self.assertFalse(result['engine_verified'])
        self.assertFalse(result['may_publish'])
    def test_13_unchanged_source_script_identity(self):
        result,_=self.call()
        self.assertEqual(result['task_state_claim'],'COMPLETE')
        self.assertEqual(result['task_path_claim'],self.target.path())
        self.assertFalse(result['original_create_ack_authenticated'])
    def test_14_failed_task_never_runs_contract(self):
        self.task['state']='FAILED'
        result,_=self.call()
        self.assertFalse(result['local_contract_checked_untrusted'])
        self.assertFalse(result['engine_verified'])
    def test_15_no_opener_attempts_after_pending(self):
        self.task['state']='QUEUED'
        _,opener=self.call()
        self.assertEqual(len(opener.requests),1)

if __name__=='__main__':unittest.main()
