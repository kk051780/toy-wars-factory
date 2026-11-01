"""Fakes only: never issue a live Roblox request or prove engine operation."""
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import twf_roblox_task_post_once as m

SCRIPT=b'return {sample = true}'
KEY='test-placeholder-key-not-real'
SESSION='11223344-5566-7788-99aa-bbccddeeff00'
TASK='abcdef12-3456-7890-abcd-ef1234567890'
T=m.Target('123','456','7')

class FakeResponse:
    status=200
    headers={'Content-Type':'application/json'}
    def __init__(self,url,body=None,status=200,ctype=None):
        self.url=url; self.status=status
        if ctype is not None:self.headers={'Content-Type':ctype}
        self.body=body if body is not None else json.dumps({
            'path':f'universes/123/places/456/versions/7/luau-execution-sessions/{SESSION}/tasks/{TASK}',
            'script':SCRIPT.decode(),'timeout':'30s','state':'QUEUED'}).encode()
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def geturl(self):return self.url
    def read(self,n):return self.body[:n]
class FakeOpener:
    def __init__(self, fn=None):self.requests=[];self.fn=fn or (lambda url:FakeResponse(url))
    def open(self,request,timeout):
        self.requests.append((request,timeout))
        return self.fn(request.full_url)

class TransportTests(unittest.TestCase):
    def setUp(self):
        self.pin=patch.object(m,'SMOKE_SHA256',hashlib.sha256(SCRIPT).hexdigest())
        self.pin.start();self.addCleanup(self.pin.stop)
    def sender(self, *args, **kwargs):
        kwargs.setdefault('intent_fence',m.LocalIntentFence())
        return m.OneShotPoster(*args,**kwargs)
    def test_01_build_pinned_fixed_post(self):
        req=m.prepare(T,SCRIPT)
        self.assertEqual(req.method,'POST')
        self.assertEqual(req.url,'https://apis.roblox.com/cloud/v2/universes/123/places/456/versions/7/luau-execution-session-tasks')
        self.assertEqual(json.loads(req.body),{'script':SCRIPT.decode(),'timeout':'30s'})
    def test_02_response_always_untrusted(self):
        fake=FakeOpener();r=self.sender(m.prepare(T,SCRIPT),T,SCRIPT,api_key=KEY,opener=fake).submit_once()
        self.assertEqual(r['post_attempts'],1)
        self.assertEqual(fake.requests[0][0].get_method(),'POST')
        self.assertEqual(fake.requests[0][1],8)
        for k in ('provider_authenticated','private_target_authenticated','saved_version_authenticated',
                  'intent_reserved_authenticated','engine_verified','may_publish','may_merge',
                  'api_key_returned','raw_ack_returned','may_retry_post'):
            self.assertIs(r[k],False)
        self.assertNotIn(KEY,str(r))
    def test_03_repeated_submission_denied(self):
        sender=self.sender(m.prepare(T,SCRIPT),T,SCRIPT,api_key=KEY,opener=FakeOpener())
        sender.submit_once()
        with self.assertRaisesRegex(m.TaskHold,'DUPLICATE_POST_DENIED'):sender.submit_once()
    def test_04_transport_error_redacted_and_consumes_attempt(self):
        op=FakeOpener(lambda u:(_ for _ in ()).throw(RuntimeError('secret-error')))
        sender=self.sender(m.prepare(T,SCRIPT),T,SCRIPT,api_key=KEY,opener=op)
        with self.assertRaisesRegex(m.TaskHold,'POST_OUTCOME_UNKNOWN_NO_RETRY') as e:sender.submit_once()
        self.assertNotIn('secret-error',str(e.exception));self.assertEqual(len(op.requests),1)
        with self.assertRaisesRegex(m.TaskHold,'DUPLICATE_POST_DENIED'):sender.submit_once()
    def test_05_tampered_body_denied_preflight(self):
        original=m.prepare(T,SCRIPT)
        altered=m.FixedRequest('POST',original.url,b'{}',original.script_sha256,original.body_sha256)
        with self.assertRaisesRegex(m.TaskHold,'MODIFIED_FIXED_REQUEST'):
            self.sender(altered,T,SCRIPT,api_key=KEY,opener=FakeOpener())
    def test_06_different_version_denied_preflight(self):
        req=m.prepare(T,SCRIPT)
        with self.assertRaisesRegex(m.TaskHold,'MODIFIED_FIXED_REQUEST'):
            self.sender(req,m.Target('123','456','8'),SCRIPT,api_key=KEY,opener=FakeOpener())
    def test_07_invalid_target_ids_denied(self):
        for v in ('0','01','1/2','1%2','-3','',123):
            with self.subTest(v=v),self.assertRaisesRegex(m.TaskHold,'INVALID_EXPLICIT_PRIVATE_VERSION_TARGET'):
                m.prepare(m.Target('123','456',v),SCRIPT)
    def test_08_script_pin_required(self):
        with self.assertRaisesRegex(m.TaskHold,'UNREVIEWED_SCRIPT_BYTES'):
            m.prepare(T,b'evil-script')
    def test_09_key_missing_or_control_denied(self):
        for key in ('short',KEY+'\n',KEY+'\r',KEY+'\x00',123):
            with self.subTest(key=str(key)[:4]),self.assertRaisesRegex(m.TaskHold,'INVALID_SCOPED_KEY'):
                self.sender(m.prepare(T,SCRIPT),T,SCRIPT,api_key=key,opener=FakeOpener())
    def test_10_wrong_task_version_rejected(self):
        f=FakeOpener(lambda u:FakeResponse(u,body=json.dumps({'path':f'universes/123/places/456/versions/8/luau-execution-sessions/{SESSION}/tasks/{TASK}','script':SCRIPT.decode(),'timeout':'30s','state':'QUEUED'}).encode()))
        with self.assertRaisesRegex(m.TaskHold,'ACK_TARGET_VERSION_MISMATCH'):
            self.sender(m.prepare(T,SCRIPT),T,SCRIPT,api_key=KEY,opener=f).submit_once()
    def test_11_wrong_task_universe_rejected(self):
        f=FakeOpener(lambda u:FakeResponse(u,body=json.dumps({'path':f'universes/555/places/456/versions/7/luau-execution-sessions/{SESSION}/tasks/{TASK}','script':SCRIPT.decode(),'timeout':'30s','state':'QUEUED'}).encode()))
        with self.assertRaisesRegex(m.TaskHold,'ACK_TARGET_VERSION_MISMATCH'):
            self.sender(m.prepare(T,SCRIPT),T,SCRIPT,api_key=KEY,opener=f).submit_once()
    def test_12_wrong_script_echo_rejected(self):
        f=FakeOpener(lambda u:FakeResponse(u,body=json.dumps({'path':f'universes/123/places/456/versions/7/luau-execution-sessions/{SESSION}/tasks/{TASK}','script':'evil','timeout':'30s','state':'QUEUED'}).encode()))
        with self.assertRaisesRegex(m.TaskHold,'ACK_SCRIPT_TIMEOUT_MISMATCH'):
            self.sender(m.prepare(T,SCRIPT),T,SCRIPT,api_key=KEY,opener=f).submit_once()
    def test_13_missing_ack_key_rejected(self):
        f=FakeOpener(lambda u:FakeResponse(u,body=b'{}'))
        with self.assertRaisesRegex(m.TaskHold,'MISSING_TYPED_ACK_FIELD'):
            self.sender(m.prepare(T,SCRIPT),T,SCRIPT,api_key=KEY,opener=f).submit_once()
    def test_14_wrong_state_rejected(self):
        d={'path':f'universes/123/places/456/versions/7/luau-execution-sessions/{SESSION}/tasks/{TASK}','script':SCRIPT.decode(),'timeout':'30s','state':'FAILED'}
        f=FakeOpener(lambda u:FakeResponse(u,body=json.dumps(d).encode()))
        with self.assertRaisesRegex(m.TaskHold,'ACK_FAILED_OR_UNKNOWN_STATE'):
            self.sender(m.prepare(T,SCRIPT),T,SCRIPT,api_key=KEY,opener=f).submit_once()
    def test_15_duplicate_ack_json_rejected(self):
        f=FakeOpener(lambda u:FakeResponse(u,body=b'{"path":"x","path":"x"}'))
        with self.assertRaisesRegex(m.TaskHold,'DUPLICATE_ACK_JSON_KEY'):
            self.sender(m.prepare(T,SCRIPT),T,SCRIPT,api_key=KEY,opener=f).submit_once()
    def test_16_nonfinite_ack_json_rejected(self):
        f=FakeOpener(lambda u:FakeResponse(u,body=b'{"z":NaN}'))
        with self.assertRaisesRegex(m.TaskHold,'NONFINITE_ACK_JSON'):
            self.sender(m.prepare(T,SCRIPT),T,SCRIPT,api_key=KEY,opener=f).submit_once()
    def test_17_oversized_ack_rejected(self):
        f=FakeOpener(lambda u:FakeResponse(u,body=b'Z'*32769))
        with self.assertRaisesRegex(m.TaskHold,'INVALID_ACK_SIZE'):
            self.sender(m.prepare(T,SCRIPT),T,SCRIPT,api_key=KEY,opener=f).submit_once()
    def test_18_redirect_denied(self):
        f=FakeOpener(lambda u:FakeResponse('https://evil.example/redirect'))
        with self.assertRaisesRegex(m.TaskHold,'REDIRECT_DENIED'):
            self.sender(m.prepare(T,SCRIPT),T,SCRIPT,api_key=KEY,opener=f).submit_once()
    def test_19_non_200_rejected(self):
        f=FakeOpener(lambda u:FakeResponse(u,status=201))
        with self.assertRaisesRegex(m.TaskHold,'UNEXPECTED_POST_STATUS'):
            self.sender(m.prepare(T,SCRIPT),T,SCRIPT,api_key=KEY,opener=f).submit_once()
    def test_20_nonjson_rejected(self):
        f=FakeOpener(lambda u:FakeResponse(u,ctype='text/html'))
        with self.assertRaisesRegex(m.TaskHold,'UNEXPECTED_ACK_CONTENT_TYPE'):
            self.sender(m.prepare(T,SCRIPT),T,SCRIPT,api_key=KEY,opener=f).submit_once()
    def test_21_no_implicit_env_proxy_or_redirect(self):
        with patch.object(m.urllib.request,'build_opener',return_value=object()) as op:
            m.hardened_opener()
            names=[type(a).__name__ for a in op.call_args.args]
        self.assertIn('ProxyHandler',names)
        self.assertIn('NoRedirect',names)
        self.assertIn('HTTPSHandler',names)
    def test_22_opaque_transport_without_open_denied(self):
        with self.assertRaisesRegex(m.TaskHold,'INVALID_TRANSPORT'):
            self.sender(m.prepare(T,SCRIPT),T,SCRIPT,api_key=KEY,opener=object())
    def test_23_invalid_target_object_denied(self):
        with self.assertRaisesRegex(m.TaskHold,'INVALID_TARGET'):
            m.prepare({'universe_id':'123'},SCRIPT)
    def test_24_ack_raw_content_not_in_report(self):
        f=FakeOpener()
        out=self.sender(m.prepare(T,SCRIPT),T,SCRIPT,api_key=KEY,opener=f).submit_once()
        self.assertNotIn(SCRIPT.decode(),str(out))
        self.assertFalse(out['raw_ack_returned'])

if __name__=='__main__':unittest.main()
