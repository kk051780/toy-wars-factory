import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import p0d_pc_qa_gate as g


def h(data: bytes):
    return hashlib.sha256(data).hexdigest()


class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'snapshots').mkdir()
        (self.root / 'qa').mkdir()
        self.place = b'RBXLX-FAKE-NO-REAL-GAME\x00'
        self.bundle = b'ZIP-FAKE-NO-REAL-GAME\x00'
        (self.root / 'snapshots' / 'game.rbxlx').write_bytes(self.place)
        (self.root / 'snapshots' / 'bundle.zip').write_bytes(self.bundle)
        self.report = dict(
            schema=g.SCHEMA, game_id=g.GAME_ID, work_id=g.WORK_ID,
            snapshot_id='local-qa-synthetic-001',
            files={
                'saved_place': {'path': 'snapshots/game.rbxlx', 'sha256': h(self.place)},
                'cumulative_zip': {'path': 'snapshots/bundle.zip', 'sha256': h(self.bundle)},
            },
            checks={key: {'status': 'NOT_TESTED', 'tested_place_sha256': h(self.place)} for key in g.CHECKS},
        )
        self.filename = 'qa/report.json'
        self.dump()

    def dump(self):
        (self.root / self.filename).write_text(json.dumps(self.report, indent=2) + '\n', 'utf-8')

    def pass_one(self, label):
        payload = (label + '\nPC_REPORTED_ONLY / Synthetic test fixture\n').encode()
        p = 'qa/' + label + '.txt'
        (self.root / p).write_bytes(payload)
        self.report['checks'][label] = dict(status='PASS', tested_place_sha256=h(self.place), evidence_path=p, evidence_sha256=h(payload))
        self.dump()

    def pass_critical(self):
        for label in g.CRITICAL:
            self.pass_one(label)

    def test_empty_qa_is_blocked(self):
        r = g.load_and_check(self.root, self.filename)
        self.assertEqual(r['v43a_review_gate'], 'WAIT_FOR_CRITICAL_QA')
        self.assertEqual(r['release_gate'], 'HOLD_NOT_FULLY_TESTED')

    def test_critical_evidence_ready_for_manual_review_only(self):
        self.pass_critical()
        r = g.load_and_check(self.root, self.filename)
        self.assertEqual(r['v43a_review_gate'], 'OWNER_REVIEW_ONLY_NO_AUTO_STUDIO')
        self.assertEqual(r['release_gate'], 'HOLD_NOT_FULLY_TESTED')
        self.assertTrue(r['qa_statuses_are_PC_REPORTED_not_independently_observed'])
        self.assertEqual(r['local_log_hashes_verified'], 3)

    def test_even_full_pass_requires_manual_approval(self):
        for key in g.CHECKS:
            self.pass_one(key)
        r = g.load_and_check(self.root, self.filename)
        self.assertEqual(r['release_gate'], 'REVIEW_ONLY_UNTIL_ALL_CHECKS_AND_OWNER_APPROVAL')
        self.assertNotIn('STUDIO_QA_PASS', json.dumps(r))

    def test_critical_failure_hard_stops(self):
        self.pass_critical()
        c = 'v39_reward_no_double'
        self.report['checks'][c]['status'] = 'FAIL'
        self.dump()
        self.assertEqual(g.load_and_check(self.root, self.filename)['v43a_review_gate'], 'STOP_FIX_CRITICAL_OR_OTHER_FAILURE')

    def test_noncritical_failure_stops_too(self):
        self.pass_critical()
        self.pass_one('v37_bell_real_listening')
        self.report['checks']['v37_bell_real_listening']['status'] = 'FAIL'
        self.dump()
        self.assertIn('v37_bell_real_listening:FAIL', g.load_and_check(self.root, self.filename)['failure_reasons'])

    def test_changed_saved_place_blocks_old_pass(self):
        self.pass_critical()
        (self.root / 'snapshots/game.rbxlx').write_bytes(b'changed')
        with self.assertRaisesRegex(g.QAError, 'SNAPSHOT_SHA_MISMATCH'):
            g.load_and_check(self.root, self.filename)

    def test_changed_bundle_blocks(self):
        (self.root / 'snapshots/bundle.zip').write_bytes(b'changed')
        with self.assertRaisesRegex(g.QAError, 'SNAPSHOT_SHA_MISMATCH'):
            g.load_and_check(self.root, self.filename)

    def test_qa_bound_to_wrong_place_blocks(self):
        self.pass_critical()
        self.report['checks']['v39_saved_place_2client']['tested_place_sha256'] = 'f' * 64
        self.dump()
        with self.assertRaisesRegex(g.QAError, 'STALE_QA_PLACE_BINDING'):
            g.load_and_check(self.root, self.filename)

    def test_log_modification_blocks(self):
        self.pass_critical()
        (self.root / 'qa/v39_saved_place_2client.txt').write_text('changed', 'utf-8')
        with self.assertRaisesRegex(g.QAError, 'TEST_LOG_SHA_MISMATCH'):
            g.load_and_check(self.root, self.filename)

    def test_false_pass_missing_log_blocks(self):
        self.report['checks']['v39_saved_place_2client']['status'] = 'PASS'
        self.dump()
        with self.assertRaisesRegex(g.QAError, 'MISSING_TEST_LOG'):
            g.load_and_check(self.root, self.filename)

    def test_untested_cannot_claim_log(self):
        self.report['checks']['v39_saved_place_2client']['evidence_path'] = 'qa/fake.txt'
        self.dump()
        with self.assertRaisesRegex(g.QAError, 'UNVERIFIED_LOG_ATTACHED_TO_UNTESTED'):
            g.load_and_check(self.root, self.filename)

    def test_duplicate_json_fields_rejected(self):
        with self.assertRaisesRegex(g.QAError, 'DUPLICATE_JSON_KEY'):
            g.strict_json(b'{"schema":1,"schema":2}')

    def test_wrong_game_or_work_rejected(self):
        for k in ('game_id', 'work_id', 'schema'):
            with self.subTest(k=k):
                x = copy.deepcopy(self.report)
                x[k] = 'other'
                with self.assertRaisesRegex(g.QAError, 'WRONG_SCHEMA_OR_GAME'):
                    g.validate(self.root, x)

    def test_unknown_test_name_rejected(self):
        self.report['checks']['made_up_test'] = {'status':'PASS'}
        self.dump()
        with self.assertRaisesRegex(g.QAError, 'WRONG_CHECK_SET'):
            g.load_and_check(self.root, self.filename)

    def test_missing_test_name_rejected(self):
        self.report['checks'].pop(g.CHECKS[0])
        self.dump()
        with self.assertRaisesRegex(g.QAError, 'WRONG_CHECK_SET'):
            g.load_and_check(self.root, self.filename)

    def test_bad_status_type_rejected(self):
        self.report['checks'][g.CHECKS[0]]['status'] = {'PASS':True}
        self.dump()
        with self.assertRaisesRegex(g.QAError, 'BAD_CHECK_STATUS'):
            g.load_and_check(self.root, self.filename)

    def test_path_traversal_rejected(self):
        for bad in ('../../root', 'snapshots/../game.rbxlx', '../game.rbxlx', 'C:/game.rbxlx', 'snapshots\\x', 'snapshots/%2e%2e/x', '/tmp/abc', 'https://evil/x'):
            with self.subTest(bad=bad):
                with self.assertRaises(g.QAError):
                    g.safe_relative(bad)

    def test_symlink_leaf_rejected(self):
        p = self.root / 'snapshots/shortcut.rbxlx'
        p.symlink_to('game.rbxlx')
        self.report['files']['saved_place']['path'] = 'snapshots/shortcut.rbxlx'
        self.dump()
        with self.assertRaisesRegex(g.QAError, 'SYMLINK_REJECTED'):
            g.load_and_check(self.root, self.filename)

    def test_symlink_directory_rejected(self):
        (self.root / 'alias').symlink_to('snapshots', target_is_directory=True)
        self.report['files']['saved_place']['path'] = 'alias/game.rbxlx'
        self.dump()
        with self.assertRaisesRegex(g.QAError, 'SYMLINK_REJECTED'):
            g.load_and_check(self.root, self.filename)

    def test_missing_file_blocks(self):
        (self.root / 'snapshots/game.rbxlx').unlink()
        with self.assertRaises(OSError):
            g.load_and_check(self.root, self.filename)

    def test_declared_place_wrong_sha_rejected(self):
        self.report['files']['saved_place']['sha256'] = 'XYZ'
        self.dump()
        with self.assertRaisesRegex(g.QAError, 'BAD_SNAPSHOT_SHA'):
            g.load_and_check(self.root, self.filename)

    def test_bad_snapshot_id_rejected(self):
        self.report['snapshot_id'] = '../secrets'
        self.dump()
        with self.assertRaisesRegex(g.QAError, 'BAD_SNAPSHOT_ID'):
            g.load_and_check(self.root, self.filename)

    def test_evidence_json_too_large_rejected(self):
        (self.root / self.filename).write_bytes(b' ' * (g.MAX_JSON_BYTES + 1))
        with self.assertRaisesRegex(g.QAError, 'EVIDENCE_JSON_TOO_LARGE'):
            g.load_and_check(self.root, self.filename)

    def test_cli_blocked_exit_code_two(self):
        with tempfile.TemporaryDirectory() as t:
            output = Path(t)/'out.json'
            self.assertEqual(g.main(['--workspace',str(self.root),'--evidence',self.filename,'--output',str(output)]), 2)
            self.assertTrue(output.exists())
            report = json.loads(output.read_text())
            self.assertEqual(report['release_gate'], 'HOLD_NOT_FULLY_TESTED')

    def test_cli_manual_ready_exit_code_zero(self):
        self.pass_critical()
        with tempfile.TemporaryDirectory() as t:
            output = Path(t)/'out.json'
            self.assertEqual(g.main(['--workspace',str(self.root),'--evidence',self.filename,'--output',str(output)]), 0)
            self.assertEqual(g.main(['--workspace',str(self.root),'--evidence',self.filename,'--output',str(output)]), 2)

    def test_cli_rejects_existing_output_without_clobber(self):
        with tempfile.TemporaryDirectory() as t:
            output = Path(t)/'out.json'
            output.write_text('PROTECTED', 'utf-8')
            self.assertEqual(g.main(['--workspace',str(self.root),'--evidence',self.filename,'--output',str(output)]), 2)
            self.assertEqual(output.read_text(), 'PROTECTED')

    def test_cli_rejects_output_symlink(self):
        with tempfile.TemporaryDirectory() as t:
            target = Path(t)/'victim'; target.write_text('KEEP', 'utf-8')
            output = Path(t)/'output'; output.symlink_to(target)
            self.assertEqual(g.main(['--workspace',str(self.root),'--evidence',self.filename,'--output',str(output)]),2)
            self.assertEqual(target.read_text(), 'KEEP')

    def test_does_not_attempt_network_subprocess_or_studio(self):
        with patch('subprocess.run',side_effect=AssertionError('subprocess used')):
            result = g.load_and_check(self.root,self.filename)
            self.assertEqual(result['v43a_review_gate'], 'WAIT_FOR_CRITICAL_QA')


if __name__ == '__main__':
    unittest.main()
