"""Synthetic-only host adversaries; no real incident, Git write or auth proof."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tools'), str(ROOT / 'tests')]
from test_system_alert_persistence import Host, target, set_holder
from test_system_alert_ledger import fence

ACQUIRED = '2026-10-27T12:29:30Z'
AFTER = '2026-10-27T12:29:40Z'


def host(*, second=False, role='meta', failure=True):
    h = Host(second, failure=failure)
    if role == 'reviewer':
        row = h.s[h.p['roles'][role]]['run_details']
        row['last_run'].update(recorded_status='in_progress', completed_at=None)
        row['latest_result']['run_id'] = 'ffffffff-aaaa-4bbb-8ccc-dddddddddddd'
        h.actor = {'role': role, 'task_id': h.p['roles'][role], 'run_id': row['last_run']['id']}
        holder = fence(h.p, role=role)['holder']
        holder['base_main_sha'] = h.b['main_sha']
        set_holder(h.p, {'github': h.b}, h.d, holder)
    return h


def started(h, at):
    h.s[h.actor['task_id']]['run_details']['last_run']['started_at'] = at


class PersistenceActorChronologyTests(unittest.TestCase):
    def rejected_before_writes(self, h, *, writer=True, peek=None):
        out = h.run(writer=writer, peek=peek)
        self.assertEqual(out['state'], 'NOT_PERSISTED')
        self.assertEqual(out['reason'], 'ACTOR_NOT_CURRENT')
        self.assertEqual(out['ref_outcome'], 'NO_REF_UPDATE_ATTEMPTED')
        self.assertEqual(h.calls, [])
        self.assertFalse(any(out['authority'].values()))
        self.assertFalse(out['a12_verified'])
        return out

    def test_meta_lease_cannot_predate_run_start_in_two_games(self):
        for second in (False, True):
            with self.subTest(second=second):
                h = host(second=second); started(h, AFTER)
                self.rejected_before_writes(h)

    def test_reviewer_lease_cannot_predate_run_start(self):
        h = host(role='reviewer'); started(h, AFTER)
        self.rejected_before_writes(h)

    def test_microsecond_after_acquire_is_not_rounded_into_ownership(self):
        h = host(); started(h, '2026-10-27T12:29:30.000001Z')
        self.rejected_before_writes(h)

    def test_no_writer_does_not_prepare_backdated_actor_operation(self):
        h = host(); started(h, AFTER)
        out = self.rejected_before_writes(h, writer=False)
        self.assertNotIn('prepared', out)

    def test_healthy_observation_does_not_bypass_actor_chronology(self):
        h = host(failure=False); started(h, AFTER)
        self.rejected_before_writes(h)

    def drifting_peek(self, h, at_call):
        count = 0
        def peek(task):
            nonlocal count
            if task == h.actor['task_id']:
                count += 1
                if count >= at_call: started(h, AFTER)
            return h.provider.peek(task)
        return peek

    def test_start_changes_after_observation_stops_before_objects(self):
        h = host()
        self.rejected_before_writes(h, peek=self.drifting_peek(h, 3))

    def test_start_changes_at_final_fence_never_updates_ref(self):
        h = host(); out = h.run(peek=self.drifting_peek(h, 5))
        self.assertFalse(out['persisted'])
        self.assertEqual(out['stage'], 'FINAL_FENCE')
        self.assertEqual(out['reason'], 'ACTOR_NOT_CURRENT')
        self.assertFalse(out['cas_attempted'])
        self.assertEqual([name for name, _ in h.calls], ['create_tree', 'create_commit'])

    def test_start_changes_at_readback_does_not_claim_persistence_or_retry(self):
        h = host(); out = h.run(peek=self.drifting_peek(h, 6))
        self.assertFalse(out['persisted'])
        self.assertEqual(out['stage'], 'READBACK')
        self.assertEqual(out['reason'], 'ACTOR_NOT_CURRENT')
        self.assertEqual(out['ref_outcome'], 'UNCONFIRMED_POSSIBLE_WRITE')
        self.assertEqual([name for name, _ in h.calls], ['create_tree', 'create_commit', 'update_ref'])

    def test_equal_and_earlier_starts_remain_valid_for_both_roles_two_games(self):
        for second in (False, True):
            for role in ('meta', 'reviewer'):
                for at in (ACQUIRED, '2026-10-27T12:29:29Z'):
                    with self.subTest(second=second, role=role, at=at):
                        h = host(second=second, role=role); started(h, at)
                        out = h.run()
                        self.assertEqual(out['state'], 'PERSISTED_READBACK')
                        self.assertFalse(any(out['authority'].values()))
                        self.assertEqual(out['verification'], 'NOT_VERIFIED')

    def test_timezone_equivalent_start_is_not_rejected(self):
        h = host(); started(h, '2026-10-27T14:29:30+02:00')
        self.assertTrue(h.run()['persisted'])

    def test_real_call_path_preserves_input_and_never_claims_auth_or_delivery(self):
        h = host(); before = deepcopy((h.p, h.b, h.actor))
        out = h.run()
        self.assertEqual((h.p, h.b, h.actor), before)
        self.assertEqual(out['verification'], 'NOT_VERIFIED')
        self.assertEqual(out['delivery'], 'NOT_ATTEMPTED')
        self.assertEqual(out['recovery_verification'], 'NOT_VERIFIED')
        self.assertFalse(out['a12_verified'])

    def test_malformed_missing_and_future_start_remain_fail_closed(self):
        for value in (None, 'not-a-timestamp', '2026-10-27T12:31:00Z'):
            h = host(); started(h, value); out = h.run()
            self.assertFalse(out['persisted'])
            self.assertFalse(out['cas_attempted'])
            self.assertEqual(h.calls, [])


if __name__ == '__main__': unittest.main()
