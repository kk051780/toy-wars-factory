"""Synthetic GitHub source/commit-provenance mechanics; NOT provider authentication."""
import copy
import importlib.util
from pathlib import Path
import threading
import unittest
from test_cloud_global_intent_integration import state, request, OWNER, AT

spec=importlib.util.spec_from_file_location(
    "cloud_global_intent_fence",Path(__file__).resolve().parents[1]/"tools"/"cloud_global_intent_fence.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

PARENT = '1' * 40
FIRST = '6' * 40
SECOND = '7' * 40

class GitHubFake:
    def __init__(self):
        self.lock = threading.Lock()
        self.s = state()
        self.ref = PARENT
        self.cas_calls = []
        self.read_count = 0
        self.lie_parent = None
        self.lie_after = False
        self.lie_repo = False
        self.lie_commit = False
        self.fail_ack = False
        self.fail_read = False
        self.fail_commit = False

    def read(self, repo, branch, path):
        with self.lock:
            self.read_count += 1
            if self.fail_read: raise ConnectionError('UNTRUSTED SECRET in endpoint')
            return {'repository': 'wrong/x' if self.lie_repo else repo,
                    'branch':branch, 'ref': self.ref,
                    'state': copy.deepcopy(state() if self.lie_after and self.read_count > 1 else self.s)}

    def cas(self, repo, branch, *, expected_sha, state, force):
        with self.lock:
            self.cas_calls.append((repo,branch,expected_sha,force))
            if self.ref != expected_sha: raise ValueError('CAS race: concurrent other winner')
            self.ref = FIRST
            self.s = copy.deepcopy(state)
            if self.fail_ack: raise ConnectionError('lost ACK despite completed GitHub state change')
            return self.ref

    def commit(self, repo, ref):
        with self.lock:
            if self.fail_commit: raise ConnectionError('provider commit metadata outage')
            return {'sha': '0' * 40 if self.lie_commit else ref,
                    'parents': [SECOND if self.lie_parent else PARENT]}

def call(g, **extra):
    return m.persist_proposal_via_trusted_callbacks(
        request=extra.pop('request',request()),owner_id=extra.pop('owner_id',OWNER),
        epoch=extra.pop('epoch',306),now=extra.pop('now',AT),
        read=g.read,cas=g.cas,read_commit=g.commit,**extra)

class GitHubCallbacksContract(unittest.TestCase):
    def check_block(self, f, expected=None):
        with self.assertRaises(m.Blocked) as err:f()
        if expected:self.assertEqual(str(err.exception),expected)

    def test_actual_callback_path_requires_exact_parent_and_preserves_history(self):
        g=GitHubFake();before=copy.deepcopy(g.s)
        outcome=call(g)
        self.assertEqual(outcome['status'],'EXACT_PARENT_CAS_READBACK_STRUCTURAL_ONLY')
        self.assertEqual(outcome['source_ref'],PARENT)
        self.assertEqual(outcome['observed_ref'],FIRST)
        self.assertEqual(g.cas_calls,[(m.REPO,m.CONTROL_BRANCH,PARENT,False)])
        self.assertEqual(g.s['administrative_revocations'], before['administrative_revocations'])
        self.assertFalse(outcome['post_authorized'])
        self.assertFalse(outcome['github_provider_authenticated'])
        self.assertFalse(outcome['roblox_engine_verified'])

    def test_duplicate_same_version_blocked_before_new_CAS(self):
        g=GitHubFake();call(g)
        self.check_block(lambda:call(g),'ALREADY_CONSUMED_NO_RETRY')
        self.assertEqual(len(g.cas_calls),1)

    def test_changed_script_same_place_version_blocked(self):
        g=GitHubFake();call(g)
        self.check_block(lambda:call(g,request=request(luau_sha256='5'*64)),'ALREADY_CONSUMED_NO_RETRY')
        self.assertEqual(len(g.cas_calls),1)

    def test_missing_callback(self):
        g=GitHubFake();self.check_block(lambda:m.persist_proposal_via_trusted_callbacks(
            request=request(),owner_id=OWNER,epoch=306,now=AT,read=None,cas=g.cas,read_commit=g.commit),'TRUSTED_CALLBACKS_MISSING')

    def test_foreign_gitHub_repo_refused(self):
        g=GitHubFake();g.lie_repo=True
        self.check_block(lambda:call(g),'INVALID_GITHUB_SNAPSHOT');self.assertEqual(g.cas_calls,[])

    def test_expired_lease_refused_before_cas(self):
        g=GitHubFake();self.check_block(lambda:call(g,now='2026-10-31T02:00:00Z'),'LEASE_NOT_LIVE');self.assertEqual(g.cas_calls,[])

    def test_cas_ack_loss_no_retry(self):
        g=GitHubFake();g.fail_ack=True
        self.check_block(lambda:call(g),'CAS_ACK_UNKNOWN_HOLD_NO_RETRY')
        self.assertEqual(len(g.cas_calls),1)
        self.assertEqual(g.ref,FIRST)

    def test_readback_outage_no_retry(self):
        g=GitHubFake();g.fail_read=True
        self.check_block(lambda:call(g),'READBACK_UNAVAILABLE_HOLD');self.assertEqual(g.cas_calls,[])

    def test_false_single_parent_refused(self):
        g=GitHubFake();g.lie_parent=True
        self.check_block(lambda:call(g),'COMMIT_PARENT_NOT_PROVEN_HOLD')
        self.assertEqual(len(g.cas_calls),1)

    def test_wrong_git_commit_sha_refused(self):
        g=GitHubFake();g.lie_commit=True
        self.check_block(lambda:call(g),'COMMIT_PARENT_NOT_PROVEN_HOLD')

    def test_commit_meta_unavailable_after_write_holds(self):
        g=GitHubFake();g.fail_commit=True
        self.check_block(lambda:call(g),'COMMIT_PARENT_NOT_PROVEN_HOLD')
        self.assertEqual(len(g.cas_calls),1)

    def test_corrupted_readback_holds(self):
        g=GitHubFake();g.lie_after=True
        self.check_block(lambda:call(g),'READBACK_MISMATCH')
        self.assertEqual(len(g.cas_calls),1)

    def test_invalid_caller_owner_refuses_before_cas(self):
        g=GitHubFake();self.check_block(lambda:call(g,owner_id='bad'),'INVALID_ACTOR');self.assertEqual(g.cas_calls,[])

    def test_malformed_plan_empty_ledger_refused_not_indexerror(self):
        bad = {'status':'CANDIDATE_ONLY_NO_WRITE', 'expected_sha':PARENT,
               'next_state':state(), 'record':{'owner_id':OWNER,'epoch':306}}
        self.check_block(lambda:m.confirm_readback(
            bad,actual_ref=FIRST,cas_ack_ref=FIRST,actual_state=state(),
            current_holder_state=state(),owner_id=OWNER,epoch=306,now=AT),
            'HISTORY_OR_HOLDER_CHANGED')

    def test_two_host_race_max_one_commit(self):
        g=GitHubFake();out=[];barrier=threading.Barrier(6)
        def worker():
            barrier.wait()
            try:out.append(('ok',call(g)))
            except m.Blocked as exc:out.append(('held',str(exc)))
        workers=[threading.Thread(target=worker) for _ in range(6)]
        for w in workers:w.start()
        for w in workers:w.join()
        self.assertEqual([x[0] for x in out].count('ok'),1)
        self.assertEqual(len(g.s[m.FIELD]),1)
        self.assertTrue(all(not x[1]['post_authorized'] for x in out if x[0]=='ok'))

    def test_post_is_never_an_action_return_value(self):
        g=GitHubFake();x=call(g)
        for name in ['post_authorized','roblox_engine_verified',
                     'github_provider_authenticated','merge_authorized','replay_authorized']:
            self.assertIs(x[name],False)
if __name__=='__main__':unittest.main()
