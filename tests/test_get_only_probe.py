import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
import twf_roblox_get_only_probe as p

S='a3499fa8-645a-4856-b929-106dd1420b31'
T='6b5e8f92-7aa6-43d9-b732-f3c88a189af5'
KEY='TEST_SECRET_DO_NOT_LOG'
def target(**kwargs):
    x=dict(universe_id='12345',place_id='67890',saved_version_id='56',
           execution_session_id=S,task_id=T,private_target_reviewed=True,
           original_create_receipt_reviewed=True)
    x.update(kwargs)
    return p.TaskTarget(**x)

class Response:
    def __init__(self, body, url, *, status=200, ctype='application/json'):
        self.body=body if isinstance(body,bytes) else json.dumps(body).encode()
        self.url=url;self.status=status;self.headers={'Content-Type':ctype}
    def __enter__(self):return self
    def __exit__(self,*a):return False
    def geturl(self):return self.url
    def read(self, n):return self.body[:n]

class FakeOpener:
    def __init__(self, responses):self.responses=responses;self.requests=[]
    def open(self,req,timeout):
        self.requests.append((req,timeout))
        answer=self.responses.pop(0)
        if isinstance(answer,Exception):raise answer
        if callable(answer):return answer(req.full_url)
        return Response(answer,req.full_url)

def fixture():
    path=target().path()
    task={'path':path,'state':'COMPLETE','output':{'results':[]}}
    logs={'luauExecutionSessionTaskLogs':[{'path':path+'/logs/1','messages':['SECRET_LOG']}],
          'nextPageToken':''}
    return task,logs

class ReadOnlyTests(unittest.TestCase):
    def run_probe(self,task=None,logs=None,tgt=None,api_key=KEY):
        a,b=fixture();o=FakeOpener([a if task is None else task,b if logs is None else logs]);
        return p.probe_existing_task(tgt or target(),api_key,opener=o),o
    def test_01_valid_two_gets_and_no_post(self):
        result,o=self.run_probe()
        self.assertEqual([r.get_method() for r,t in o.requests],['GET','GET'])
        self.assertEqual(result['http_post_count'],0)
        self.assertEqual([t for r,t in o.requests],[8,8])
    def test_02_task_url_and_logs_url_are_version_pinned(self):
        _,o=self.run_probe();urls=[r.full_url for r,t in o.requests]
        self.assertEqual(urls[0],'https://apis.roblox.com/cloud/v2/'+target().path())
        self.assertEqual(urls[1],urls[0]+'/logs')
    def test_03_header_key_passed_but_not_returned(self):
        result,o=self.run_probe()
        self.assertEqual(o.requests[0][0].get_header('X-api-key'),KEY)
        self.assertNotIn(KEY,str(result))
        self.assertNotIn('SECRET_LOG',str(result))
    def test_04_no_engine_or_publish_attribution(self):
        r,_=self.run_probe()
        for f in ('roblox_provider_authenticated','engine_verified','mobile_verified','may_publish','may_merge','may_spend','original_create_ack_authenticated'):
            self.assertIs(r[f],False)
    def test_05_unknown_target_or_nonpublic_review_denied(self):
        for t in (target(private_target_reviewed=False),target(original_create_receipt_reviewed=False)):
            with self.assertRaises(p.ProbeHold):self.run_probe(tgt=t)
    def test_06_invalid_ids_denied_before_network(self):
        for kw in ({'universe_id':'0'},{'place_id':'../1'},{'saved_version_id':'0'},
                   {'task_id':'../evil'},{'execution_session_id':'x'},
                   {'universe_id':'0012'}):
            with self.assertRaises(p.ProbeHold):self.run_probe(tgt=target(**kw))
    def test_07_missing_api_key_denied(self):
        for key in ('','\rBAD','x\nmalicious'):
            with self.assertRaises(p.ProbeHold):self.run_probe(api_key=key)
    def test_08_foreign_task_path_denied_after_one_get(self):
        task,logs=fixture();task['path']=task['path'].replace('/versions/56/','/versions/57/')
        o=FakeOpener([task,logs]);
        with self.assertRaises(p.ProbeHold):p.probe_existing_task(target(),KEY,opener=o)
        self.assertEqual(len(o.requests),1)
    def test_09_foreign_log_path_denied(self):
        a,b=fixture();b['luauExecutionSessionTaskLogs'][0]['path']='evil/logs/1'
        with self.assertRaises(p.ProbeHold):self.run_probe(logs=b)
    def test_10_missing_next_page_rejected(self):
        a,b=fixture();b.pop('nextPageToken')
        with self.assertRaises(p.ProbeHold):self.run_probe(logs=b)
    def test_11_unfinished_pagination_rejected(self):
        a,b=fixture();b['nextPageToken']='notdone'
        with self.assertRaises(p.ProbeHold):self.run_probe(logs=b)
    def test_12_no_hidden_automatic_retries_after_transport_error(self):
        o=FakeOpener([OSError('LEAK_MY_SECRET')]);
        with self.assertRaises(p.ProbeHold) as cm:p.probe_existing_task(target(),KEY,opener=o)
        self.assertEqual(len(o.requests),1)
        self.assertEqual(str(cm.exception),'GET_FAILED_NO_RETRY')
    def test_13_unexpected_status_rejected(self):
        a,b=fixture();o=FakeOpener([lambda url:Response(a,url,status=429)])
        with self.assertRaises(p.ProbeHold):p.probe_existing_task(target(),KEY,opener=o)
        self.assertEqual(len(o.requests),1)
    def test_14_redirect_to_other_url_rejected(self):
        a,b=fixture();o=FakeOpener([lambda url:Response(a,'https://evil.example/a')])
        with self.assertRaises(p.ProbeHold):p.probe_existing_task(target(),KEY,opener=o)
    def test_15_non_json_response_rejected(self):
        a,b=fixture();o=FakeOpener([lambda url:Response(a,url,ctype='text/html')])
        with self.assertRaises(p.ProbeHold):p.probe_existing_task(target(),KEY,opener=o)
    def test_16_json_duplicate_keys_rejected(self):
        a,b=fixture();raw=json.dumps(a).replace('"state": "COMPLETE"','"state": "COMPLETE", "state": "COMPLETE"')
        with self.assertRaises(p.ProbeHold):self.run_probe(task=raw.encode())
    def test_17_json_nan_rejected(self):
        a,b=fixture();raw=json.dumps(a).replace('"state": "COMPLETE"','"state": NaN')
        with self.assertRaises(p.ProbeHold):self.run_probe(task=raw.encode())
    def test_18_response_oversize_rejected(self):
        with self.assertRaises(p.ProbeHold):self.run_probe(task=b' '*70000)
    def test_19_message_not_string_rejected(self):
        a,b=fixture();b['luauExecutionSessionTaskLogs'][0]['messages']=[True]
        with self.assertRaises(p.ProbeHold):self.run_probe(logs=b)
    def test_20_invalid_state_denied(self):
        a,b=fixture();a['state']='HACKED'
        with self.assertRaises(p.ProbeHold):self.run_probe(task=a)
    def test_21_explicit_no_proxy_handler_even_if_env_set(self):
        with patch.dict(os.environ,{'HTTPS_PROXY':'https://evil.example:443','https_proxy':'https://evil.example:443','ALL_PROXY':'socks5://evil.example:1080'}):
            o=p.hardened_get_opener()
            handler=[h for h in o.handlers if isinstance(h,p.urllib.request.ProxyHandler)]
            self.assertTrue(all(not h.proxies for h in handler))
    def test_22_redirect_handler_returns_none(self):
        self.assertIsNone(p.NoRedirect().redirect_request(None,None,302,'redirect',{},'https://evil.example'))
    def test_23_valid_pending_still_no_engine_credit(self):
        a,b=fixture();a['state']='PROCESSING';r,_=self.run_probe(task=a)
        self.assertEqual(r['task_state_claim'],'PROCESSING')
        self.assertEqual(r['http_get_count'],1)
        self.assertEqual(r['status'],'UNTRUSTED_READ_ONLY_PENDING')
        self.assertFalse(r['engine_verified'])
    def test_24_get_response_content_never_returned(self):
        r,_=self.run_probe()
        self.assertNotIn('output',r)
        self.assertNotIn('messages',r)
        self.assertTrue(r['raw_log_content_returned'] is False)
    def test_25_log_multiple_records_scope(self):
        a,b=fixture();b['luauExecutionSessionTaskLogs'].append({'path':a['path']+'/logs/2','messages':[]})
        r,_=self.run_probe(logs=b)
        self.assertEqual(r['log_record_count'],2)
    def test_26_bad_json_utf8_denied(self):
        with self.assertRaises(p.ProbeHold):self.run_probe(task=b'\xff\xfe')

if __name__=='__main__':unittest.main()
