"""Synthetic GET fixtures exercise the accepted collector, never provider proof."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tools'), str(ROOT / 'tests')]
from test_system_github_evidence import fixtures, FakeGET, mutate, NOW, RUN, CTREE, target


def held(epoch, *, generation=1, kind='META', second=False):
    p, b, data = fixtures(second)
    state = json.loads(data['/git/blobs/' + b['coordinator_blob_sha']].text)
    tasks = {'META': p['roles']['meta'], 'WORKER': p['roles']['author'],
             'REVIEWER': p['roles']['reviewer']}
    state.update(epoch=generation, holder={'kind': kind, 'epoch': epoch,
        'task_id': tasks.get(kind), 'owner_id': RUN,
        'acquired_at': '2026-10-27T11:30:00Z', 'expires_at': '2026-10-27T12:00:00Z'})
    raw = json.dumps(state, sort_keys=True).encode()
    digest = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
    data['/git/blobs/' + digest] = target.Response(200, raw.decode())
    b.update(coordinator_blob_sha=digest, coordinator_epoch=generation)
    mutate(data, '/git/trees/' + CTREE + '?recursive=1', lambda v: v['tree'][0].update(sha=digest))
    return p, b, data


class EvidenceHolderGenerationTests(unittest.TestCase):
    def reject(self, value, **kwargs):
        p, b, data = held(value, **kwargs)
        get = FakeGET(p, data)
        with self.assertRaisesRegex(target.EvidenceError, '^INVALID_HOLDER$'):
            target.collect([p], b, get, lambda: NOW)
        self.assertFalse(any('/pulls/' in u or '/actions/' in u for u in get.calls))

    def test_bool_one_rejected_for_two_games(self):
        for second in (False, True):
            with self.subTest(second=second): self.reject(True, second=second)

    def test_float_one_rejected_for_two_games(self):
        for second in (False, True):
            with self.subTest(second=second): self.reject(1.0, second=second)

    def test_bool_zero_rejected(self): self.reject(False, generation=0)
    def test_float_zero_rejected(self): self.reject(0.0, generation=0)
    def test_float_larger_generation_rejected(self): self.reject(7.0, generation=7)

    def test_each_accepted_holder_kind_requires_integer(self):
        for kind in ('META', 'WORKER', 'REVIEWER', 'CONTROLLER', 'DISPATCH'):
            with self.subTest(kind=kind): self.reject(1.0, kind=kind)

    def test_string_and_none_generation_remain_rejected(self):
        for value in ('1', None):
            with self.subTest(value=value): self.reject(value)

    def test_wrong_integer_generation_remains_rejected(self): self.reject(2)

    def test_bad_generation_never_reaches_pr_or_ci_even_with_green_fixtures(self):
        self.reject(True)

    def test_strict_integer_positive_for_all_kinds_and_two_games(self):
        for second in (False, True):
            for kind in ('META', 'WORKER', 'REVIEWER', 'CONTROLLER', 'DISPATCH'):
                p, b, data = held(1, kind=kind, second=second)
                out = target.collect([p], b, FakeGET(p, data), lambda: NOW)
                self.assertIs(type(out['coordinator']['holder']['epoch']), int)
                self.assertEqual(out['main_ci']['qa'], 'PASS')
                self.assertEqual(out['verification'], 'NOT_VERIFIED')
                self.assertFalse(any(out['authority'].values()))

    def test_null_holder_keeps_no_pr_relaxation_and_denied_authority(self):
        p, b, data = fixtures()
        out = target.collect([p], b, FakeGET(p, data), lambda: NOW)
        self.assertIsNone(out['coordinator']['holder'])
        self.assertFalse(any(out['authority'].values()))
        mutate(data, '/pulls/9', lambda row: row.update(state='closed'))
        with self.assertRaises(target.EvidenceError):
            target.collect([p], b, FakeGET(p, data), lambda: NOW)

    def test_input_integrity_and_no_new_recovery_or_write_api(self):
        p, b, data = held(1)
        before = deepcopy((p, b, data))
        out = target.collect([p], b, FakeGET(p, data), lambda: NOW)
        self.assertEqual((p, b, data), before)
        self.assertEqual(out['service_run_verification'], 'NOT_COLLECTED')
        self.assertFalse(any(out['authority'].values()))


if __name__ == '__main__': unittest.main()
