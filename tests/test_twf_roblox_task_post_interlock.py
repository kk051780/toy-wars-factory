"""A14 local interlock regression: no real network or cross-host authority."""
import hashlib
from pathlib import Path
import sys
import threading
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import twf_roblox_task_post_once as m
from test_twf_roblox_task_post_once import FakeOpener, FakeResponse, SCRIPT, KEY, T

class LocalInterlockTests(unittest.TestCase):
    def setUp(self):
        self.patch=patch.object(m,'SMOKE_SHA256',hashlib.sha256(SCRIPT).hexdigest())
        self.patch.start();self.addCleanup(self.patch.stop)

    def sender(self,opener,fence,target=T,script=SCRIPT):
        return m.OneShotPoster(m.prepare(target,script),target,script,api_key=KEY,
                               opener=opener,intent_fence=fence)

    def test_no_explicit_transport_blocks_before_post(self):
        with self.assertRaisesRegex(m.TaskHold,'UNTRUSTED_HOST_TRANSPORT_NOT_INSTALLED'):
            m.OneShotPoster(m.prepare(T,SCRIPT),T,SCRIPT,api_key=KEY,
                            intent_fence=m.LocalIntentFence())

    def test_no_local_fence_blocks_before_post(self):
        op=FakeOpener()
        with self.assertRaisesRegex(m.TaskHold,'LOCAL_FENCE_REQUIRED'):
            m.OneShotPoster(m.prepare(T,SCRIPT),T,SCRIPT,api_key=KEY,opener=op)
        self.assertEqual(op.requests,[])

    def test_second_sender_same_intent_denied(self):
        op=FakeOpener();f=m.LocalIntentFence()
        self.sender(op,f).submit_once()
        with self.assertRaisesRegex(m.TaskHold,'DUPLICATE_INTENT_DENIED'):
            self.sender(op,f).submit_once()
        self.assertEqual(len(op.requests),1)

    def test_unknown_ack_cannot_be_retried_via_second_object(self):
        op=FakeOpener(lambda u: (_ for _ in ()).throw(TimeoutError('secret')))
        f=m.LocalIntentFence()
        with self.assertRaisesRegex(m.TaskHold,'POST_OUTCOME_UNKNOWN_NO_RETRY'):
            self.sender(op,f).submit_once()
        with self.assertRaisesRegex(m.TaskHold,'DUPLICATE_INTENT_DENIED'):
            self.sender(op,f).submit_once()
        self.assertEqual(len(op.requests),1)

    def test_different_explicit_versions_are_different_intents(self):
        op=FakeOpener();f=m.LocalIntentFence()
        self.sender(op,f).submit_once()
        second=m.Target('123','456','8')
        # A different version's ACK needs matching path; no version conflation.
        def ack(url):
            resp=FakeResponse(url)
            resp.body=resp.body.replace(b'/versions/7/',b'/versions/8/')
            return resp
        op2=FakeOpener(ack)
        self.sender(op2,f,target=second).submit_once()
        self.assertEqual(len(op.requests)+len(op2.requests),2)

    def test_concurrent_two_same_fence_at_most_one_request(self):
        op=FakeOpener();f=m.LocalIntentFence()
        senders=[self.sender(op,f),self.sender(op,f)]
        barrier=threading.Barrier(3)
        results=[]
        def worker(sender):
            barrier.wait()
            try: sender.submit_once();results.append('sent')
            except m.TaskHold as err: results.append(str(err))
        threads=[threading.Thread(target=worker,args=(s,)) for s in senders]
        for t in threads:t.start()
        barrier.wait()
        for t in threads:t.join(timeout=5)
        self.assertEqual(results.count('sent'),1)
        self.assertEqual(results.count('DUPLICATE_INTENT_DENIED'),1)
        self.assertEqual(len(op.requests),1)

    def test_local_fence_scope_does_not_authenticate_global_ownership(self):
        op=FakeOpener()
        # Different in-memory fences do NOT share state. This intentionally
        # demonstrates the missing global CAS, not a production-ready proof.
        self.sender(op,m.LocalIntentFence()).submit_once()
        self.sender(op,m.LocalIntentFence()).submit_once()
        self.assertEqual(len(op.requests),2)

    def test_actual_pr175_pinned_script_bytes(self):
        raw=(Path(__file__).resolve().parents[1]/'fixtures'/'twf_open_cloud_smoke.luau').read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),
                         'fc343ede29c2466b0962689b183b5320d81122a807d65ad7f82e942a9268759d')
        with patch.object(m,'SMOKE_SHA256',
            'fc343ede29c2466b0962689b183b5320d81122a807d65ad7f82e942a9268759d'):
            req=m.prepare(T,raw)
            self.assertEqual(req.script_sha256,m.SMOKE_SHA256)
            self.assertTrue(req.url.endswith('/versions/7/luau-execution-session-tasks'))
            self.assertEqual(req.method,'POST')

if __name__=='__main__':unittest.main()
