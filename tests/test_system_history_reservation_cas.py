"""Simulated CAS competition only, NOT original provider-backed proof."""
from test_system_history_reservation import state,call,SHA,REF,OWNER,BRANCH
from system_history_reservation import advise
import copy,hashlib,json,unittest

class FakeGitRef:
    def __init__(self, state):
        self.data=copy.deepcopy(state);self.ref=REF;self.updates=0
    def write(self,expected_ref, proposed):
        if expected_ref!=self.ref:return False
        newsha=hashlib.sha1(json.dumps(proposed,sort_keys=True).encode()).hexdigest()
        self.data=copy.deepcopy(proposed);self.ref=newsha;self.updates+=1
        return True

class CasSimulation(unittest.TestCase):
    def test_two_independent_plans_one_cas_wins(self):
        f=FakeGitRef(state());a=call(f.data);b=call(f.data,work_id='SECOND_JOB_000001')
        self.assertEqual(a['suggested_ids'],b['suggested_ids'])
        self.assertTrue(f.write(a['expected_ref'],a['proposed_state']))
        self.assertFalse(f.write(b['expected_ref'],b['proposed_state']))
        self.assertEqual(f.updates,1)
    def test_loser_gets_new_distinct_ids_after_fresh_ref(self):
        f=FakeGitRef(state());a=call(f.data);self.assertTrue(f.write(a['expected_ref'],a['proposed_state']))
        b=call(f.data,work_id='SECOND_JOB_000001',expected_ref=f.ref,occupied_ids=['C00172'])
        self.assertEqual(b['suggested_ids'],['C00175','C00176'])
        self.assertTrue(f.write(b['expected_ref'],b['proposed_state']))
        self.assertEqual(len(f.data['history_id_reservations']['entries']),4)
    def test_same_work_replay_reuses_record_without_write(self):
        f=FakeGitRef(state());a=call(f.data);self.assertTrue(f.write(a['expected_ref'],a['proposed_state']))
        b=call(f.data,expected_ref=f.ref,occupied_ids=['C00172'])
        self.assertEqual(b['status'],'JOIN_RESERVED_NO_REISSUE')
        self.assertNotIn('proposed_state',b)
        self.assertFalse(b['may_retry'])
    def test_ack_loss_no_auto_retry(self):
        f=FakeGitRef(state());a=call(f.data)
        f.write(a['expected_ref'],a['proposed_state'])
        self.assertFalse(f.write(a['expected_ref'],a['proposed_state']))
        self.assertEqual(f.updates,1)
    def test_reservation_preserves_other_state(self):
        s=state();s['other_payload']={'owner_delegation':True,'release_holds':['Gemini','Roblox']}
        p=call(s)['proposed_state']
        self.assertEqual(p['other_payload'],s['other_payload'])
        self.assertEqual(p['holder'],s['holder'])
    def test_no_state_with_no_owner(self):
        s=state();s['holder']=None
        self.assertEqual(call(s)['status'],'BLOCK_NO_AUTHOR_LEASE')
if __name__=='__main__':unittest.main()
