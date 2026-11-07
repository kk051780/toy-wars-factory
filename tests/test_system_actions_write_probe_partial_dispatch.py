"""PR163: source-attempt telemetry after ambiguous GitHub mutations.

Synthetic transport and lease mocks only: neither GitHub auth nor live writes.
"""
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch
import sys
import types
import unittest

TOOLS = Path(__file__).resolve().parents[1] / 'tools'
sys.path.insert(0, str(TOOLS))
try:
    import repair_control  # Real repository module in GitHub CI.
except ImportError:
    # Local fixture only, never a stand-in for an authenticated provider run.
    shim = types.ModuleType('repair_control')
    for symbol in ('acquire', 'owns', 'release', 'validate'):
        setattr(shim, symbol, lambda *a, **kw: None)
    sys.modules['repair_control'] = shim
import system_actions_write_probe as p

SHA = 'a'*40
CLAIM = 'b'*40
EPOCH = 99
SCOPE = {'owner': '2ae5b6d5-0e01-4ca5-91cc-889cae7c444f',
         'branch': 'controller/gha-write-probe-777-a1', 'main': SHA,
         'run_id': 777, 'attempt': 1}
ENV = {'PROBE_CONSENT': p.CONSENT, 'GITHUB_RUN_ID': '777'}


class Host:
    def __init__(self, fail_at=None, cleanup_fail=False, mode='DRAFT_PR'):
        self.fail_at = fail_at
        self.cleanup_fail = cleanup_fail
        self.dispatched = []
        self.release_count = 0
        self.cas_count = 0
        self.mode = mode
        self.scope = dict(SCOPE)
        if mode == 'BRANCH_ONLY':
            self.scope['branch_only'] = True
    def call(self, method, path, body=None):
        if method == 'GET':
            return {'id': 777}
        self.dispatched.append((method, path))
        if self.fail_at == len(self.dispatched):
            raise p.ProbeError('GITHUB_TRANSPORT_FAILED')
        if path == '/pulls':
            return {'number': 55}
        return {}
    def sha(self, api, which):
        return SHA if which == 'main' else CLAIM
    def state(self, api, sha):
        return {'holder': {'kind': 'CONTROLLER', 'owner_id': SCOPE['owner'],
                           'epoch': EPOCH}, 'epoch': EPOCH}
    def acquire(self, state, *args, **kw):
        return {'action': 'ACQUIRE', 'write': True,
                'state': {'epoch': EPOCH, 'holder': {'owner_id': SCOPE['owner']}}}
    def cas(self, api, oldref, state):
        self.cas_count += 1
        if self.cas_count == 2 and self.cleanup_fail:
            raise p.ProbeError('RELEASE_CAS_FAILED')
        return CLAIM
    def release(self, state, *args, **kwargs):
        self.release_count += 1
        return {'holder': None, 'epoch': EPOCH}
    def execute(self, no_source=False):
        env = dict(ENV)
        if self.mode == 'BRANCH_ONLY':
            env.update({'PROBE_MODE': 'BRANCH_ONLY', 'PROBE_CONSENT': p.BRANCH_CONSENT})
        with ExitStack() as stack:
            objects = [
                ('checked_context', lambda *args: self.scope),
                ('sha_ref', self.sha),
                ('state_at', self.state),
                ('acquire', self.acquire),
                ('cas_state', self.cas),
                ('owns', lambda *args: True),
                ('release', self.release),
                ('verify_created_probe', lambda *args: 55),
                ('verify_staged_probe', lambda *args: SHA),
            ]
            for key, val in objects:
                stack.enter_context(patch.object(p, key, val))
            stack.enter_context(patch.object(p._PerWriteLeaseFence, '_check_live', lambda *args: None))
            if no_source:
                stack.enter_context(patch.object(p, 'create_branch_probe',
                     lambda *args: (_ for _ in ()).throw(p.ProbeError('MAIN_CHANGED'))))
            return p.run(self, env)


class PartialWriteDiagnostics(unittest.TestCase):
    def test_failure_before_first_dispatch_has_no_partial_write_marker(self):
        h = Host()
        with self.assertRaisesRegex(p.ProbeError, '^MAIN_CHANGED$'):
            h.execute(no_source=True)
        self.assertEqual(h.dispatched, [])
        self.assertEqual(h.release_count, 1)

    def test_ambiguous_first_dispatch_reports_one_attempt(self):
        h = Host(fail_at=1)
        with self.assertRaisesRegex(p.ProbeError,
             '^GITHUB_TRANSPORT_FAILED__SOURCE_MUTATIONS_ATTEMPTED_1__PARTIAL_WRITE_POSSIBLE$'):
            h.execute()
        self.assertEqual(h.dispatched, [('POST', '/git/refs')])
        self.assertEqual(h.release_count, 1)

    def test_ambiguous_second_dispatch_keeps_evidence_and_never_retries(self):
        h = Host(fail_at=2)
        with self.assertRaisesRegex(p.ProbeError,
             '^GITHUB_TRANSPORT_FAILED__SOURCE_MUTATIONS_ATTEMPTED_2__PARTIAL_WRITE_POSSIBLE$'):
            h.execute()
        self.assertEqual(len(h.dispatched), 2)
        self.assertEqual(h.dispatched[1][0], 'PUT')
        self.assertEqual(h.release_count, 1)

    def test_failed_pr_create_reports_three_attempts_no_cleanup_mutation(self):
        h = Host(fail_at=3)
        with self.assertRaisesRegex(p.ProbeError,
             '^GITHUB_TRANSPORT_FAILED__SOURCE_MUTATIONS_ATTEMPTED_3__PARTIAL_WRITE_POSSIBLE$'):
            h.execute()
        self.assertEqual(h.dispatched[-1], ('POST', '/pulls'))
        self.assertEqual(len(h.dispatched), 3)
        self.assertEqual(h.release_count, 1)

    def test_cleanup_error_retains_attempt_count_and_primary_error(self):
        h = Host(fail_at=2, cleanup_fail=True)
        with self.assertRaisesRegex(p.ProbeError,
             '^GITHUB_TRANSPORT_FAILED__SOURCE_MUTATIONS_ATTEMPTED_2__PARTIAL_WRITE_POSSIBLE__RELEASE_UNCONFIRMED$'):
            h.execute()
        self.assertEqual(len(h.dispatched), 2)

    def test_successful_branch_only_probe_has_no_error_marker(self):
        h = Host(mode='BRANCH_ONLY')
        o = h.execute()
        self.assertEqual(o['status'], 'BRANCH_VERIFIED_NO_PR_REQUEST')
        self.assertEqual(len(h.dispatched), 2)
        self.assertEqual(h.release_count, 1)

    def test_successful_draft_probe_has_no_error_marker(self):
        h = Host()
        o = h.execute()
        self.assertEqual(o['status'], 'DRAFT_PR_CREATED_NOT_MERGED')
        self.assertEqual(len(h.dispatched), 3)
        self.assertEqual(h.release_count, 1)


if __name__ == '__main__':
    unittest.main()
