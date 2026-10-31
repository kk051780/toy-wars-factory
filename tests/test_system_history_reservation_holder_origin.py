"""Exact PR157 source adversarial cases: internally inconsistent lease origin metadata.

These tests do not grant write authority or simulate provider attestation.
"""
from test_system_history_reservation import state, call, OWNER
import unittest

class HolderOriginTests(unittest.TestCase):
    def assert_hold(self, s, role, *, work_branch=None):
        branch = work_branch or s['holder']['work_branch']
        result = call(s, work_branch=branch)
        self.assertNotEqual(result['status'], 'PREPARE_SINGLE_PARENT_CAS_ONLY_NOT_AUTHORIZED',
                            f'{role} inconsistent metadata should not prepare an allocatable CAS')
        self.assertNotIn('proposed_state', result)
        self.assertFalse(result['may_write'])
        self.assertFalse(result['provider_attested'])
    def test_controller_cannot_reuse_worker_task_id(self):
        s=state();s['holder']['task_id']=s['authorized_tasks']['WORKER']
        self.assert_hold(s,'controller with worker task ID')
    def test_controller_origin_not_worker(self):
        s=state();s['holder']['origin']='worker'
        self.assert_hold(s,'controller with worker origin')
    def test_controller_origin_must_not_be_missing(self):
        s=state();del s['holder']['origin']
        self.assert_hold(s,'controller missing origin')
    def test_worker_origin_cannot_be_controller(self):
        s=state();s['holder'].update(kind='WORKER',task_id=s['authorized_tasks']['WORKER'],work_branch='auto/twf-game-repair-'+OWNER,origin='controller')
        self.assert_hold(s,'worker with controller origin',work_branch=s['holder']['work_branch'])
    def test_meta_origin_cannot_be_controller(self):
        s=state();s['authorized_tasks']['META']='6add445e4138819197d9cf2b1a02534d'
        s['holder'].update(kind='META',task_id=s['authorized_tasks']['META'],work_branch='auto/twf-system-review-'+OWNER,origin='controller')
        self.assert_hold(s,'meta with controller origin',work_branch=s['holder']['work_branch'])
    def test_valid_controller_remains_non_authorizing_advice(self):
        r=call();self.assertEqual(r['status'],'PREPARE_SINGLE_PARENT_CAS_ONLY_NOT_AUTHORIZED')
        self.assertFalse(r['may_write'])
    def test_valid_manual_adopted_worker_origin_can_be_reviewed(self):
        s=state();s['holder'].update(kind='WORKER',task_id=s['authorized_tasks']['WORKER'],work_branch='auto/twf-game-repair-'+OWNER,origin='manual')
        r=call(s,work_branch=s['holder']['work_branch'])
        self.assertEqual(r['status'],'PREPARE_SINGLE_PARENT_CAS_ONLY_NOT_AUTHORIZED')
        self.assertFalse(r['may_write'])
if __name__=='__main__':unittest.main()

# Additional negative controls run at import discovery time via separate class.
class ExtraHolderOriginTests(unittest.TestCase):
    def test_controller_boolean_task_id_blocked(self):
        s=state();s['holder']['task_id']=True
        self.assertEqual(call(s)['status'],'BLOCK_CONTROLLER_HOLDER_SHAPE')
    def test_worker_none_origin_blocked(self):
        s=state();s['holder'].update(kind='WORKER',task_id=s['authorized_tasks']['WORKER'],work_branch='auto/twf-game-repair-'+OWNER,origin=None)
        self.assertEqual(call(s,work_branch=s['holder']['work_branch'])['status'],'BLOCK_WORKER_HOLDER_ORIGIN')
    def test_meta_non_string_origin_blocked(self):
        s=state();s['authorized_tasks']['META']='6add445e4138819197d9cf2b1a02534d'
        s['holder'].update(kind='META',task_id=s['authorized_tasks']['META'],work_branch='auto/twf-system-review-'+OWNER,origin=False)
        self.assertEqual(call(s,work_branch=s['holder']['work_branch'])['status'],'BLOCK_META_HOLDER_ORIGIN')
    def test_valid_ordinary_worker_origin(self):
        s=state();s['holder'].update(kind='WORKER',task_id=s['authorized_tasks']['WORKER'],work_branch='auto/twf-game-repair-'+OWNER,origin='worker')
        self.assertEqual(call(s,work_branch=s['holder']['work_branch'])['status'],'PREPARE_SINGLE_PARENT_CAS_ONLY_NOT_AUTHORIZED')
