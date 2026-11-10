import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from trace_qa import validate, TraceError

BASE = json.loads((ROOT / 'fixtures' / 's1_positive.synthetic.json').read_text())

class TraceContractTests(unittest.TestCase):
    def good(self, data=None, **kw):
        return validate(copy.deepcopy(data or BASE), **kw)

    def bad(self, mutate, code):
        doc = copy.deepcopy(BASE)
        mutate(doc)
        with self.assertRaisesRegex(TraceError, code):
            validate(doc)

    def test_complete_2client_round(self):
        stats = self.good()
        self.assertEqual(stats['rounds_ended'], 1)
        self.assertEqual(stats['client_warning_views'], 2)

    def test_synthetic_rejected_release(self):
        with self.assertRaisesRegex(TraceError, 'BLOCKED_NO_REAL_CAPTURE'):
            self.good(real=True)

    def test_release_metadata_not_proof_of_live_engine(self):
        d = copy.deepcopy(BASE)
        d['meta'].update(capture_mode='STUDIO_CAPTURE', studio_session='sessionA',
                         place_id='place1', source_commit='a' * 40)
        self.assertEqual(self.good(d, real=True)['rounds_ended'], 1)

    def test_wrong_schema(self): self.bad(lambda d: d['meta'].update(schema='old'), 'wrong_schema')
    def test_missing_done(self): self.bad(lambda d: d['events'].pop(), 'missing_done')
    def test_duplicate_seq(self): self.bad(lambda d: d['events'][4].update(seq=4), 'seq_not_contiguous')
    def test_stale_epoch(self): self.bad(lambda d: d['events'][5].update(epoch=6), 'stale_or_wrong_epoch')
    def test_nan_time(self): self.bad(lambda d: d['events'][5].update(t=float('nan')), 'clock_not_monotonic')
    def test_reverse_time(self): self.bad(lambda d: d['events'][5].update(t=0.1), 'clock_not_monotonic')
    def test_replay_receipt(self): self.bad(lambda d: d['events'][9].update(receipt_id='attack-1'), 'duplicate_receipt')
    def test_forged_friendly_fire(self): self.bad(lambda d: d['events'][4].update(actor='playerR'), 'friendly_or_untrusted')
    def test_hp_tamper(self): self.bad(lambda d: d['events'][4].update(after_hp=60), 'hp_mismatch')
    def test_untrusted_boss_hit(self): self.bad(lambda d: d['events'][9].update(event_id='fakeboss'), 'boss_hit_before')
    def test_attack_during_windup(self): self.bad(lambda d: d['events'][9].update(t=2.0), 'boss_hit_before_warning')
    def test_wrong_warning_deadline(self): self.bad(lambda d: d['events'][6].update(deadline=4.2), 'boss_deadline')
    def test_one_client_short_warning(self): self.bad(lambda d: d['events'][7].update(shown_remaining=0.93), 'not_deadline_synced')
    def test_short_warning_actual_delivery(self):
        d = copy.deepcopy(BASE)
        d['events'][7].update(t=2.07, shown_remaining=0.93)
        d['events'][8].update(t=2.09, shown_remaining=0.91)
        d['events'][9].update(t=3.0)
        with self.assertRaisesRegex(TraceError, 'warning_ux_too_short'):
            self.good(d)
    def test_bad_client_warning_projection(self): self.bad(lambda d: d['events'][8].update(shown_remaining=1.64), 'not_deadline_synced')
    def test_duplicate_viewer(self): self.bad(lambda d: d['events'][8].update(viewer='playerR'), 'duplicate_or_unknown_client')
    def test_bad_score_team(self): self.bad(lambda d: d['events'][11].update(home_team='blue'), 'illegal_score')
    def test_forged_winner(self): self.bad(lambda d: d['events'][12].update(winner='blue'), 'false_egg_win')
    def test_reset_wrong_epoch(self): self.bad(lambda d: d['events'][13].update(next_epoch=9), 'reset_without_end')
    def test_future_event_after_done(self):
        def mutate(d):
            d['events'].append(dict(seq=16, t=5., epoch=8, kind='DONE'))
        self.bad(mutate, 'event_after_done')
    def test_source_boss_hit_cannot_be_double(self):
        self.bad(lambda d: d['events'][9].update(receipt_id='remote-1'), 'duplicate_receipt')
    def test_missing_reject_coverage(self):
        d = copy.deepcopy(BASE)
        d['events'][5].update(kind='LEAVE', actor='playerN')
        with self.assertRaises(TraceError): self.good(d)
    def test_reject_overlong_trace(self):
        d = copy.deepcopy(BASE); d['events'] *= 1000
        with self.assertRaisesRegex(TraceError, 'oversize'): self.good(d)
    def test_nofull_mode_accepts_early_done(self):
        d = copy.deepcopy(BASE)
        d['events'] = [d['events'][0], d['events'][1], d['events'][2],
                       {"seq": 4, "t": 0.3, "epoch": 7, "kind": "LEAVE", "actor": "playerB"},
                       {"seq": 5, "t": 0.4, "epoch": 7, "kind": "END", "winner": "red", "reason": "forfeit"},
                       {"seq": 6, "t": 0.5, "epoch": 7, "kind": "DONE"}]
        self.assertEqual(self.good(d, require_full=False)['rounds_ended'], 1)
        with self.assertRaisesRegex(TraceError, 'missing_coverage'): self.good(d)

if __name__ == '__main__': unittest.main()
