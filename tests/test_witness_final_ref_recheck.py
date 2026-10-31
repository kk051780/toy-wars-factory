"""Separate future-only reconciliation tests; no GitHub, Roblox or writes."""
import unittest
from test_manual_claim_witness import Fake, check, m, CLAIM, MAIN, SRC

COORD = '/git/ref/heads/twf-repair-coordinator'
MAIN_REF = '/git/ref/heads/main'
SOURCE = '/git/ref/heads/'+SRC

class MutableSnapshot(Fake):
    """Synthetic provider changes a mutable ref BETWEEN initial and final reads."""
    def __init__(self, path, second):
        super().__init__()
        self.change_path=path
        self.second=second
        self.count=0
    def get(self,path,*,allow_missing=False):
        if path == self.change_path:
            self.count += 1
            if self.count == 2:
                self.calls.append((path, allow_missing))
                return self.second
        return super().get(path,allow_missing=allow_missing)

class FinalFenceTests(unittest.TestCase):
    def assert_blocked(self,provider,message):
        with self.assertRaises(m.WitnessHold) as ctx:check(provider)
        self.assertEqual(str(ctx.exception),message)
        self.assertEqual(provider.calls[-1][0],provider.change_path)
        self.assertNotIn(SOURCE,[p for p,_ in provider.calls])

    def test_complete_unchanged_snapshot_preserves_candidacy_only(self):
        f=Fake()
        r=check(f)
        self.assertEqual(len(f.calls),11)
        self.assertEqual(f.calls[-1],(SOURCE,True))
        self.assertEqual(r['status'],'CLAIM_OBSERVED_BRANCH_ABSENT_CANDIDATE_ONLY')
        self.assertIs(r['merge_authorized'],False)
        self.assertIs(r['provider_authenticated'],False)

    def test_coordinator_released_mid_witness_is_hold(self):
        f=MutableSnapshot(COORD,{'ref':'refs/heads/twf-repair-coordinator','object':{'sha':'b'*40}})
        self.assert_blocked(f,'CLAIM_MOVED_DURING_WITNESS')

    def test_coordinator_missing_object_mid_witness_is_hold(self):
        f=MutableSnapshot(COORD,{'ref':'refs/heads/twf-repair-coordinator','object':None})
        self.assert_blocked(f,'CLAIM_MOVED_DURING_WITNESS')

    def test_coordinator_foreign_ref_mid_witness_is_hold(self):
        f=MutableSnapshot(COORD,{'ref':'refs/heads/unrelated','object':{'sha':CLAIM}})
        self.assert_blocked(f,'CLAIM_MOVED_DURING_WITNESS')

    def test_main_advanced_mid_witness_is_hold(self):
        f=MutableSnapshot(MAIN_REF,{'ref':'refs/heads/main','object':{'sha':'b'*40}})
        self.assert_blocked(f,'MAIN_MOVED_DURING_WITNESS')

    def test_main_missing_object_mid_witness_is_hold(self):
        f=MutableSnapshot(MAIN_REF,{'ref':'refs/heads/main','object':None})
        self.assert_blocked(f,'MAIN_MOVED_DURING_WITNESS')

    def test_main_foreign_ref_mid_witness_is_hold(self):
        f=MutableSnapshot(MAIN_REF,{'ref':'refs/heads/feature','object':{'sha':MAIN}})
        self.assert_blocked(f,'MAIN_MOVED_DURING_WITNESS')

    def test_initial_main_wrong_ref_is_hold_even_with_same_sha(self):
        f=Fake()
        f.items[MAIN_REF]={'ref':'refs/heads/not-main','object':{'sha':MAIN}}
        with self.assertRaises(m.WitnessHold) as ctx:check(f)
        self.assertEqual(str(ctx.exception),'BASE_MAIN_MOVED')

    def test_source_404_always_last_after_two_mutable_ref_checks(self):
        f=Fake();check(f)
        self.assertEqual([p for p,_ in f.calls][-3:],[COORD,MAIN_REF,SOURCE])
        self.assertLessEqual(len(f.calls),12)

if __name__=='__main__':unittest.main()
