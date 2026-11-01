"""Offline mock-backed connector/contract integration regressions.

Does not simulate real Roblox network authentication or engine execution.
"""
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import twf_roblox_get_only_probe as p
import twf_get_only_pr175_bridge as bridge

KEY='SECRET_INJECTED_FOR_MOCK'
TASK_PATH=('universes/12345/places/67890/versions/56/luau-execution-sessions/'
           'a3499fa8-645a-4856-b929-106dd1420b31/tasks/'
           '6b5e8f92-7aa6-43d9-b732-f3c88a189af5')

class Response:
    def __init__(self,obj,url):
        self.raw=json.dumps(obj).encode();self.url=url
        self.status=200;self.headers={'Content-Type':'application/json'}
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def geturl(self):return self.url
    def read(self,n):return self.raw[:n]

class Opener:
    def __init__(self,state='COMPLETE'):
        self.state=state;self.requests=[]
    def open(self,req,timeout):
        self.requests.append((req,timeout))
        if len(self.requests)==1:
            return Response({'path':TASK_PATH,'state':self.state,'script':'script','timeout':'30s',
                             'output':{'results':[{'marker':'TWF'}]}},req.full_url)
        return Response({'luauExecutionSessionTaskLogs':[{'path':TASK_PATH+'/logs/1','messages':['PRIVATE_TOKEN_IN_LOG']}],
                         'nextPageToken':''},req.full_url)

def target():
    return p.TaskTarget(universe_id='12345',place_id='67890',saved_version_id='56',
                        execution_session_id='a3499fa8-645a-4856-b929-106dd1420b31',
                        task_id='6b5e8f92-7aa6-43d9-b732-f3c88a189af5',
                        private_target_reviewed=True, original_create_receipt_reviewed=True)

def consistent(path=TASK_PATH, **fields):
    return {'status':'UNTRUSTED_OPEN_CLOUD_GET_LOGS_CONSISTENT',
            'task_path_claim':path, 'create_response_path_matches_get':True,
            'create_ack_authenticated':False,'provider_authenticated':False,
            'engine_verified':False,'may_post':False,'may_publish':False, **fields}

class BridgeTests(unittest.TestCase):
    def call(self,callback=None,state='COMPLETE'):
        op=Opener(state)
        if callback is None:callback=lambda *args:consistent()
        result=p.probe_existing_task(target(), KEY, opener=op,contract_checker=callback)
        return result,op
    def deny(self,cb):
        with self.assertRaises(p.ProbeHold):self.call(cb)
    def test_01_consistent_complete_bound_but_untrusted(self):
        r,o=self.call()
        self.assertIs(r['local_contract_checked_untrusted'],True)
        self.assertFalse(r['roblox_provider_authenticated'])
        self.assertFalse(r['engine_verified'])
        self.assertEqual(len(o.requests),2)
    def test_02_pending_one_get_no_callback(self):
        def forbidden(*args):raise AssertionError('must not check pending')
        r,o=self.call(forbidden,'PROCESSING')
        self.assertEqual(len(o.requests),1)
        self.assertFalse(r['local_contract_checked_untrusted'])
    def test_03_queued_one_get_no_callback(self):
        r,o=self.call(lambda *args:1/0,'QUEUED')
        self.assertEqual(len(o.requests),1)
    def test_04_failed_terminal_must_not_assert_consistency(self):
        r,o=self.call(lambda *args:1/0,'FAILED')
        self.assertEqual(len(o.requests),2)
        self.assertFalse(r['local_contract_checked_untrusted'])
    def test_05_cancelled_terminal_must_not_assert_consistency(self):
        r,_=self.call(lambda *args:1/0,'CANCELLED')
        self.assertFalse(r['local_contract_checked_untrusted'])
    def test_06_missing_contract_callback_keeps_untrusted(self):
        r=p.probe_existing_task(target(),KEY,opener=Opener())
        self.assertFalse(r['local_contract_checked_untrusted'])
    def test_07_invalid_callback_type_blocks_before_get(self):
        with self.assertRaises(p.ProbeHold):p.probe_existing_task(target(),KEY,opener=Opener(),contract_checker=True)
    def test_08_true_is_not_a_proof_dict(self):
        self.deny(lambda *args:True)
    def test_09_foreign_path_rejected(self):
        self.deny(lambda *args:consistent('foreign'))
    def test_10_spoofed_provider_flag_rejected(self):
        self.deny(lambda *args:dict(consistent(),provider_authenticated=True))
    def test_11_spoofed_engine_flag_rejected(self):
        self.deny(lambda *args:dict(consistent(),engine_verified=True))
    def test_12_spoofed_create_auth_rejected(self):
        self.deny(lambda *args:dict(consistent(),create_ack_authenticated=True))
    def test_13_spoofed_write_flag_rejected(self):
        self.deny(lambda *args:dict(consistent(),may_post=True))
    def test_14_spoofed_publish_flag_rejected(self):
        self.deny(lambda *args:dict(consistent(),may_publish=True))
    def test_15_injected_checker_sees_no_api_key(self):
        called=[]
        def checker(task,logs,path):
            called.append((task,logs,path));return consistent()
        r,o=self.call(checker)
        self.assertEqual(len(called),1)
        self.assertNotIn(KEY,str(called))
        self.assertEqual(called[0][2],TASK_PATH)
        self.assertEqual([q.get_method() for q,t in o.requests],['GET','GET'])
    def test_16_opaque_callback_exception_sanitized(self):
        def leaked(*args):raise ValueError(KEY+' PRIVATE_TOKEN_IN_LOG')
        with self.assertRaises(p.ProbeHold) as ctx:self.call(leaked)
        self.assertEqual(str(ctx.exception),'LOCAL_CONTRACT_REJECTED')
    def test_17_raw_log_content_not_returned(self):
        r,_=self.call()
        self.assertNotIn('PRIVATE_TOKEN_IN_LOG',str(r))
        self.assertNotIn(KEY,str(r))
    def test_18_bridge_requires_pr175_contract_module(self):
        with patch.dict(sys.modules,{'twf_open_cloud_get_log_adapter':None}):
            with self.assertRaises(p.ProbeHold) as ctx:
                bridge.get_existing_task_checked(target(),KEY,{},'{}',opener=Opener())
        self.assertEqual(str(ctx.exception),'REVIEWED_CONTRACT_NOT_INSTALLED')
    def test_19_bridge_accepts_mocked_pr175_contract_on_immutable_path(self):
        calls=[]
        def contract(plan,ack,task,logs):
            calls.append((plan,ack,json.loads(task),json.loads(logs)))
            return consistent()
        with patch.dict(sys.modules,{'twf_open_cloud_get_log_adapter':SimpleNamespace(inspect_untrusted_create_get_and_logs=contract)}):
            result=bridge.get_existing_task_checked(target(),KEY,{'schema':1},'CREATION_ACK',opener=Opener())
        self.assertEqual(len(calls),1)
        self.assertTrue(result['local_contract_checked_untrusted'])
        self.assertEqual(calls[0][1],'CREATION_ACK')
        self.assertEqual(calls[0][2]['path'],TASK_PATH)
    def test_20_bad_pr175_verdict_fail_closed(self):
        def contract(*args):return consistent('different')
        with patch.dict(sys.modules,{'twf_open_cloud_get_log_adapter':SimpleNamespace(inspect_untrusted_create_get_and_logs=contract)}):
            with self.assertRaises(p.ProbeHold):
                bridge.get_existing_task_checked(target(),KEY,{},'{}',opener=Opener())
    def test_21_secret_in_verifier_exception_does_not_leak(self):
        def contract(*args):raise RuntimeError(KEY)
        with patch.dict(sys.modules,{'twf_open_cloud_get_log_adapter':SimpleNamespace(inspect_untrusted_create_get_and_logs=contract)}):
            with self.assertRaises(p.ProbeHold) as ctx:
                bridge.get_existing_task_checked(target(),KEY,{},'{}',opener=Opener())
        self.assertEqual(str(ctx.exception),'LOCAL_CONTRACT_REJECTED')
    def test_22_invalid_bridge_input_rejected_before_network(self):
        with self.assertRaises(p.ProbeHold):
            bridge.get_existing_task_checked(target(),KEY,{},None,opener=Opener())
    def test_23_pending_bridge_skips_orig_get_validation_and_logs(self):
        def forbidden(*a):raise AssertionError('should not run checker')
        with patch.dict(sys.modules,{'twf_open_cloud_get_log_adapter':SimpleNamespace(inspect_untrusted_create_get_and_logs=forbidden)}):
            o=Opener('PROCESSING')
            r=bridge.get_existing_task_checked(target(),KEY,{},'{}',opener=o)
        self.assertEqual(len(o.requests),1)
        self.assertFalse(r['local_contract_checked_untrusted'])
    def test_24_result_rejects_boolean_authority(self):
        self.deny(lambda *args:dict(consistent(),engine_verified=0))

if __name__=='__main__':unittest.main()
