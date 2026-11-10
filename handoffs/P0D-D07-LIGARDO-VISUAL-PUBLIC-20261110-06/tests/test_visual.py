import math
import random
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'reference'))
from ligardo_policy import Visual, valid_id, part_budget


def payload(**kw):
    base = dict(roundId='round77', boss='LIGARDO', stage=2,
                eventId='event-1', seq=1, remainingMs=9000, phase='TELEGRAPH')
    base.update(kw)
    return base


class VisualPolicyTests(unittest.TestCase):
    def setUp(self):
        self.v = Visual('round77')

    def test_new_round_idle(self):
        self.assertEqual(self.v.phase, 'IDLE')
    def test_basic_start(self):
        self.assertEqual(self.v.snapshot(payload(), 1)['kind'], 'SPAWN')
    def test_stage4(self):
        self.assertEqual(self.v.snapshot(payload(stage=4), 1)['kind'], 'SPAWN')
    def test_reject_stage1(self):
        self.assertEqual(self.v.snapshot(payload(stage=1), 1)['kind'], 'IGNORE')
    def test_reject_stage3(self):
        self.assertEqual(self.v.snapshot(payload(stage=3), 1)['kind'], 'IGNORE')
    def test_reject_wrong_boss(self):
        self.assertEqual(self.v.snapshot(payload(boss='GOROGAN'), 1)['kind'], 'IGNORE')
    def test_reject_wrong_round(self):
        self.assertEqual(self.v.snapshot(payload(roundId='else'), 1)['kind'], 'IGNORE')
    def test_reject_active_first(self):
        self.assertEqual(self.v.snapshot(payload(phase='ACTIVE'), 1)['kind'], 'IGNORE')
    def test_reject_end_first(self):
        self.assertEqual(self.v.snapshot(payload(phase='END'), 1)['kind'], 'IGNORE')
    def test_reject_zero_remaining_first(self):
        self.assertEqual(self.v.snapshot(payload(remainingMs=0), 1)['kind'], 'IGNORE')
    def test_reject_huge_remaining(self):
        self.assertEqual(self.v.snapshot(payload(remainingMs=20001), 1)['kind'], 'IGNORE')
    def test_max_remaining(self):
        self.assertEqual(self.v.snapshot(payload(remainingMs=20000), 1)['kind'], 'SPAWN')
    def test_reject_fraction_remaining(self):
        self.assertEqual(self.v.snapshot(payload(remainingMs=8.25), 1)['kind'], 'IGNORE')
    def test_reject_bool_seq(self):
        self.assertEqual(self.v.snapshot(payload(seq=True), 1)['kind'], 'IGNORE')
    def test_reject_zero_seq(self):
        self.assertEqual(self.v.snapshot(payload(seq=0), 1)['kind'], 'IGNORE')
    def test_reject_negative_stage(self):
        self.assertEqual(self.v.snapshot(payload(stage=-2), 1)['kind'], 'IGNORE')
    def test_reject_missing_fields(self):
        self.assertEqual(self.v.snapshot({'boss':'LIGARDO'}, 1)['kind'], 'IGNORE')
    def test_reject_bad_id(self):
        self.assertEqual(self.v.snapshot(payload(eventId='../dir'), 1)['kind'], 'IGNORE')
    def test_reject_unicode_id(self):
        self.assertFalse(valid_id('イベント'))
    def test_reject_event_id_too_long(self):
        self.assertEqual(self.v.snapshot(payload(eventId='e'*65), 1)['kind'], 'IGNORE')
    def test_reject_event_id_empty(self):
        self.assertEqual(self.v.snapshot(payload(eventId=''), 1)['kind'], 'IGNORE')
    def test_reject_negative_time(self):
        self.assertEqual(self.v.snapshot(payload(), -1)['kind'], 'IGNORE')
    def test_reject_nan_time(self):
        self.assertEqual(self.v.snapshot(payload(), math.nan)['kind'], 'IGNORE')
    def test_reject_infinite_time(self):
        self.assertEqual(self.v.snapshot(payload(), math.inf)['kind'], 'IGNORE')
    def test_reject_payload_list(self):
        self.assertEqual(self.v.snapshot([1, 2, 3], 1)['kind'], 'IGNORE')
    def test_reject_payload_none(self):
        self.assertEqual(self.v.snapshot(None, 1)['kind'], 'IGNORE')
    def test_replay_first(self):
        self.v.snapshot(payload(), 1)
        self.assertEqual(self.v.snapshot(payload(), 1.1)['reason'], 'STALE_SEQUENCE')
    def test_new_event_same_round(self):
        self.v.snapshot(payload(), 1)
        self.assertEqual(self.v.snapshot(payload(eventId='event-2', seq=2), 2)['reason'], 'ALREADY_USED_THIS_ROUND')
    def test_active_change(self):
        self.v.snapshot(payload(), 1)
        self.assertEqual(self.v.snapshot(payload(seq=2, phase='ACTIVE', remainingMs=7000), 2)['kind'], 'UPDATE')
    def test_no_phase_rollback(self):
        self.v.snapshot(payload(), 1)
        self.v.snapshot(payload(seq=2, phase='ACTIVE'), 2)
        self.assertEqual(self.v.snapshot(payload(seq=3, phase='TELEGRAPH'), 2.1)['reason'], 'PHASE_ROLLBACK')
    def test_end_cleanup(self):
        self.v.snapshot(payload(), 1)
        self.assertEqual(self.v.snapshot(payload(seq=2, phase='END'), 2)['kind'], 'DESPAWN')
    def test_duplicate_end(self):
        self.v.snapshot(payload(), 1)
        self.v.snapshot(payload(seq=2, phase='END'), 2)
        self.assertEqual(self.v.snapshot(payload(seq=3, phase='END'), 3)['reason'], 'TERMINATED')
    def test_client_timeout(self):
        self.v.snapshot(payload(), 1)
        self.assertEqual(self.v.tick(9.9)['kind'], 'NOOP')
        self.assertEqual(self.v.tick(10)['kind'], 'DESPAWN')
    def test_timeout_is_final(self):
        self.v.snapshot(payload(), 1)
        self.v.tick(10)
        self.assertEqual(self.v.snapshot(payload(seq=2), 11)['reason'], 'TERMINATED')
    def test_late_update_doesnt_extend(self):
        self.v.snapshot(payload(), 1)
        self.v.snapshot(payload(seq=2,phase='ACTIVE',remainingMs=20000), 8)
        self.assertEqual(self.v.deadline, 10)
    def test_earlier_deadline_may_shorten(self):
        self.v.snapshot(payload(), 1)
        self.v.snapshot(payload(seq=2, phase='ACTIVE', remainingMs=500), 2)
        self.assertEqual(self.v.deadline, 2.5)
    def test_wrong_round_doesnt_mutate(self):
        self.v.snapshot(payload(), 1)
        prev = (self.v.phase, self.v.last_seq, self.v.deadline)
        self.v.snapshot(payload(roundId='wrong',seq=2), 2)
        self.assertEqual(prev, (self.v.phase,self.v.last_seq,self.v.deadline))
    def test_monotonic_clock_guard(self):
        self.v.snapshot(payload(), 1)
        self.assertEqual(self.v.snapshot(payload(seq=2,phase='ACTIVE'), 0.9)['kind'], 'IGNORE')
    def test_close_cleanup(self):
        self.assertEqual(self.v.close()['kind'], 'DESPAWN')
        self.assertEqual(self.v.snapshot(payload(), 1)['kind'], 'IGNORE')
    def test_close_idempotent(self):
        self.v.close()
        self.assertEqual(self.v.close()['kind'], 'DESPAWN')
    def test_reject_invalid_round_constructor(self):
        with self.assertRaises(ValueError): Visual('bad/round')
    def test_tick_nan(self):
        self.assertEqual(self.v.tick(math.nan)['kind'], 'IGNORE')
    def test_tick_backwards(self):
        self.v.tick(3)
        self.assertEqual(self.v.tick(2)['kind'], 'IGNORE')
    def test_low_part_budget(self):
        self.assertLessEqual(part_budget(True), 16)
    def test_full_part_budget(self):
        self.assertLessEqual(part_budget(False), 20)
    def test_random_replay_does_not_mutate(self):
        r = random.Random(941)
        self.v.snapshot(payload(), 1)
        self.v.snapshot(payload(seq=2,phase='ACTIVE',remainingMs=4000), 2)
        for _ in range(1000):
            seq = r.choice([0, 1, 2])
            t = r.uniform(2, 5)
            old = self.v.last_seq
            res = self.v.snapshot(payload(seq=seq,phase='ACTIVE'), t)
            self.assertEqual(res['kind'], 'IGNORE')
            self.assertEqual(self.v.last_seq, old)
    def test_fuzz_malformed(self):
        cases = [[],0,'payload',None,{},dict(phase='UNKNOWN')]
        for case in cases:
            with self.subTest(case=case):
                self.assertEqual(self.v.snapshot(case, 1)['kind'], 'IGNORE')

if __name__ == '__main__': unittest.main()
