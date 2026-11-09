import copy
import json
import os
import random
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import verify_v43a_trace as guard


def fixture():
    return json.loads((ROOT / 'fixtures/valid_s1_contest_capture.json').read_text())


def renumber(doc):
    for idx, ev in enumerate(doc['events'], 1):
        ev['seq'] = idx
    return doc


def drop(doc, i):
    del doc['events'][i]
    return renumber(doc)


class ContractTests(unittest.TestCase):
    def assert_reject(self, doc, expected):
        with self.assertRaises(guard.TraceContractError) as e:
            guard.check_trace(doc)
        self.assertEqual(e.exception.code, expected)

    def test_valid_fixture(self):
        v = guard.check_trace(fixture())
        self.assertTrue(v['ok'])
        self.assertEqual(v['captures'], 1)
        self.assertEqual(v['studio_qa'], 'NOT_VERIFIED_BY_THIS_TOOL')

    def test_valid_sanitized_label_does_not_claim_studio_pass(self):
        v = fixture(); v['source'] = 'studio_sanitized'
        self.assertEqual(guard.check_trace(v)['status'], 'TRACE_CONTRACT_PASS_NOT_STUDIO_QA')

    def test_legacy_owner_at_baseline(self):
        v = fixture(); v['events'][1]['legacy_owner'] = 'BLUE'
        self.assert_reject(v, 'LEGACY_OWNERSHIP_CONFLICT')

    def test_v43_owner_at_baseline(self):
        v = fixture(); v['events'][1]['v43_owner'] = 'RED'
        self.assert_reject(v, 'LEGACY_OWNERSHIP_CONFLICT')

    def test_dual_ownership_same_team(self):
        v = fixture(); v['events'][8]['legacy_owner'] = 'RED'
        self.assert_reject(v, 'DUAL_OWNER_OR_DESYNC')

    def test_dual_ownership_opp_team(self):
        v = fixture(); v['events'][8]['legacy_owner'] = 'BLUE'
        self.assert_reject(v, 'DUAL_OWNER_OR_DESYNC')

    def test_v43_wrong_team(self):
        v = fixture(); v['events'][8]['v43_owner'] = 'BLUE'
        self.assert_reject(v, 'DUAL_OWNER_OR_DESYNC')

    def test_claim_2_99_seconds(self):
        v = fixture(); v['events'][7]['t'] = 5.99
        self.assert_reject(v, 'CLAIM_BEFORE_3_SECONDS')

    def test_capture_stale_commit(self):
        v = fixture()
        v['events'][7]['t'] = 10
        # Later entries remain monotonic for a meaningful stale-capture rejection.
        for ev in v['events'][8:]:
            ev['t'] += 4
        self.assert_reject(v, 'STALE_CLAIM_COMMIT')

    def test_second_capture_after_cooldown_and_reset(self):
        v = fixture()
        v['events'] = v['events'][:12] + [
            {'type':'CLAIM_START','seq':0,'t':18,'npc':guard.NPC_ID,'actor':'C','team':'BLUE','alive':True,'egg_carrier':False,'near':True,'server_accepted':True},
            {'type':'CLAIM_COMMIT','seq':0,'t':21,'npc':guard.NPC_ID,'actor':'C','team':'BLUE'},
            {'type':'OWNER_SNAPSHOT','seq':0,'t':21,'npc':guard.NPC_ID,'legacy_owner':'NONE','v43_owner':'BLUE'},
            {'type':'MATCH_END','seq':0,'t':22},
            {'type':'OWNER_SNAPSHOT','seq':0,'t':22,'npc':guard.NPC_ID,'legacy_owner':'NONE','v43_owner':'NONE'},
            {'type':'FINAL','seq':0,'t':22},
        ]
        renumber(v)
        self.assertEqual(guard.check_trace(v)['captures'], 2)

    def test_claim_exact_3_seconds(self):
        self.assertTrue(guard.check_trace(fixture())['ok'])

    def test_lease_early(self):
        v = fixture(); v['events'][9]['t'] = 13.99; v['events'][10]['t'] = 13.99
        self.assert_reject(v, 'LEASE_END_TOO_EARLY_OR_INVALID')

    def test_cooldown_early(self):
        v = fixture(); v['events'][11]['t'] = 17.99
        self.assert_reject(v, 'COOLDOWN_TOO_EARLY_OR_INVALID')

    def test_remove_capture_snapshot(self):
        self.assert_reject(drop(fixture(), 8), 'MISSING_OWNER_SNAPSHOT')

    def test_remove_lease_snapshot(self):
        self.assert_reject(drop(fixture(), 10), 'MISSING_OWNER_SNAPSHOT')

    def test_remove_end_snapshot(self):
        self.assert_reject(drop(fixture(), 13), 'MISSING_OWNER_SNAPSHOT')

    def test_remove_match_start(self):
        self.assert_reject(drop(fixture(), 0), 'MISSING_MATCH_START')

    def test_no_baseline(self):
        self.assert_reject(drop(fixture(), 1), 'LEGACY_OWNERSHIP_CONFLICT')

    def test_wrong_work_id(self):
        v = fixture(); v['work_id'] = 'untrusted'
        self.assert_reject(v, 'IDENTITY_MISMATCH')

    def test_wrong_game(self):
        v = fixture(); v['game_id'] = 'TOY_WARS'
        self.assert_reject(v, 'IDENTITY_MISMATCH')

    def test_wrong_stage(self):
        v = fixture(); v['stage'] = 'S2'
        self.assert_reject(v, 'IDENTITY_MISMATCH')

    def test_unknown_doc_field_eg_real_user(self):
        v = fixture(); v['user_id'] = '12345'
        self.assert_reject(v, 'DOC_FIELDS_INVALID')

    def test_unknown_event_field_eg_ip(self):
        v = fixture(); v['events'][2]['ip'] = '1.2.3.4'
        self.assert_reject(v, 'EVENT_FIELDS_INVALID')

    def test_actor_raw_user_id_undesired(self):
        v = fixture(); v['events'][2]['actor'] = '1234567890'
        self.assert_reject(v, 'ACTOR_MUST_BE_PSEUDONYM')

    def test_invalid_event_type(self):
        v = fixture(); v['events'][4]['type'] = 'PURCHASE'
        self.assert_reject(v, 'UNKNOWN_EVENT')

    def test_invalid_source(self):
        v = fixture(); v['source'] = 'real_live_player_data'
        self.assert_reject(v, 'INVALID_SOURCE')

    def test_sequence_duplicate(self):
        v = fixture(); v['events'][5]['seq'] = 5
        self.assert_reject(v, 'NONMONOTONIC_SEQUENCE')

    def test_timestamp_backwards(self):
        v = fixture(); v['events'][6]['t'] = 1
        self.assert_reject(v, 'NONMONOTONIC_TIME')

    def test_timestamp_negative(self):
        v = fixture(); v['events'][0]['t'] = -0.01
        self.assert_reject(v, 'NONMONOTONIC_TIME')

    def test_timestamp_infinity(self):
        v = fixture(); v['events'][4]['t'] = float('inf')
        self.assert_reject(v, 'NONMONOTONIC_TIME')

    def test_timestamp_bool_not_numeric(self):
        v = fixture(); v['events'][4]['t'] = True
        self.assert_reject(v, 'NONMONOTONIC_TIME')

    def test_seq_bool_not_int(self):
        v = fixture(); v['events'][0]['seq'] = True
        self.assert_reject(v, 'NONMONOTONIC_SEQUENCE')

    def test_early_commit_wrong_actor(self):
        v = fixture(); v['events'][7]['actor'] = 'A'
        self.assert_reject(v, 'CLAIM_COMMIT_NOT_AUTHORIZED')

    def test_early_commit_wrong_team(self):
        v = fixture(); v['events'][7]['team'] = 'BLUE'
        self.assert_reject(v, 'CLAIM_COMMIT_NOT_AUTHORIZED')

    def test_same_team_cannot_contest(self):
        v = fixture(); v['events'][3]['team'] = 'BLUE'
        self.assert_reject(v, 'INVALID_CONTEST')

    def test_claim_after_contest_without_reset(self):
        self.assert_reject(drop(fixture(), 5), 'CLAIM_ILLEGAL_STATE')

    def test_claim_dead(self):
        v = fixture(); v['events'][2]['alive'] = False
        self.assert_reject(v, 'UNTRUSTED_CLAIM_ACCEPTED')

    def test_claim_egg_carrier(self):
        v = fixture(); v['events'][2]['egg_carrier'] = True
        self.assert_reject(v, 'UNTRUSTED_CLAIM_ACCEPTED')

    def test_claim_far_away(self):
        v = fixture(); v['events'][2]['near'] = False
        self.assert_reject(v, 'UNTRUSTED_CLAIM_ACCEPTED')

    def test_claim_server_not_accepted(self):
        v = fixture(); v['events'][2]['server_accepted'] = False
        self.assert_reject(v, 'UNTRUSTED_CLAIM_ACCEPTED')

    def test_claim_server_bool_no_int(self):
        v = fixture(); v['events'][2]['server_accepted'] = 1
        self.assert_reject(v, 'INVALID_SERVER_FLAGS')

    def test_wrong_team(self):
        v = fixture(); v['events'][2]['team'] = 'GREEN'
        self.assert_reject(v, 'INVALID_TEAM')

    def test_wrong_npc(self):
        v = fixture(); v['events'][7]['npc'] = 'S2_NEUTRAL_A'
        self.assert_reject(v, 'NPC_NOT_WHITELISTED')

    def test_capture_while_active(self):
        v = fixture()
        evt = dict(v['events'][6]); evt['t'] = 6.1
        v['events'].insert(9, evt); renumber(v)
        self.assert_reject(v, 'CLAIM_ILLEGAL_STATE')

    def test_denial_while_active_is_ok(self):
        v = fixture()
        v['events'].insert(9, {'type': 'CLAIM_DENIED', 't': 7, 'npc': guard.NPC_ID, 'reason': 'COOLDOWN'})
        renumber(v)
        self.assertTrue(guard.check_trace(v)['ok'])

    def test_denial_invalid_reason(self):
        v = fixture(); v['events'][4]['reason'] = 'ALLOW_ANYWAY'
        self.assert_reject(v, 'INVALID_DENIAL')

    def test_final_cannot_be_early(self):
        v = fixture(); v['events'][14], v['events'][13] = v['events'][13], v['events'][14]
        renumber(v)
        self.assert_reject(v, 'MISSING_OWNER_SNAPSHOT')

    def test_extra_after_final(self):
        v = fixture(); v['events'].append({'type': 'CLAIM_DENIED','t':20,'npc':guard.NPC_ID,'reason':'STALE_MATCH'})
        renumber(v)
        self.assert_reject(v, 'FINAL_WITHOUT_END_OR_NOT_LAST')

    def test_too_many_events(self):
        v = fixture()
        v['events'] = v['events'][:2] + [dict(v['events'][4]) for _ in range(300)] + v['events'][2:]
        self.assert_reject(v, 'EVENT_COUNT_INVALID')

    def test_randomized_denials_do_not_award_extra_capture(self):
        rng = random.Random(20261110)
        for _ in range(100):
            v = fixture()
            n = rng.randrange(0, 30)
            inserts = [{'type': 'CLAIM_DENIED', 't': 6 + i * 0.01,
                        'npc': guard.NPC_ID, 'reason': rng.choice(sorted(guard.REASONS))} for i in range(n)]
            for i, evt in enumerate(inserts):
                v['events'].insert(9 + i, evt)
            renumber(v)
            self.assertEqual(guard.check_trace(v)['captures'], 1)

    def test_ended_during_active_requires_neutral_snapshot(self):
        v = fixture()
        # Remove lease expiry/cooldown; end while captured.
        v['events'] = v['events'][:9] + [
            {'type': 'MATCH_END','seq':0,'t':7},
            {'type': 'OWNER_SNAPSHOT','seq':0,'t':7,'npc':guard.NPC_ID,'legacy_owner':'NONE','v43_owner':'NONE'},
            {'type':'FINAL','seq':0,'t':7},
        ]
        renumber(v)
        self.assertTrue(guard.check_trace(v)['ok'])

    def test_end_active_without_cleanup_fails(self):
        v = fixture()
        v['events'] = v['events'][:9] + [
            {'type': 'MATCH_END','seq':0,'t':7},
            {'type':'OWNER_SNAPSHOT','seq':0,'t':7,'npc':guard.NPC_ID,'legacy_owner':'NONE','v43_owner':'RED'},
            {'type':'FINAL','seq':0,'t':7},
        ]
        renumber(v)
        self.assert_reject(v, 'DUAL_OWNER_OR_DESYNC')


class FileAndCliTests(unittest.TestCase):
    def test_duplicate_json_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'bad.json'
            path.write_text('{"schema":"x","schema":"y"}')
            with self.assertRaises(guard.TraceContractError) as e:
                guard.load_trace(path)
            self.assertEqual(e.exception.code, 'DUPLICATE_JSON_KEY')

    def test_symlink_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'ok.json'; path.write_text(json.dumps(fixture()))
            link = Path(tmp) / 'link.json'
            try:
                link.symlink_to(path)
            except OSError:
                self.skipTest('symlinks disabled')
            with self.assertRaises(guard.TraceContractError) as e:
                guard.load_trace(link)
            self.assertEqual(e.exception.code, 'INPUT_SIZE_OR_SYMLINK_INVALID')

    def test_large_file_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'large.json'; path.write_bytes(b'x' * (guard.MAX_FILE_BYTES + 1))
            with self.assertRaises(guard.TraceContractError):
                guard.load_trace(path)

    def test_cli_good(self):
        script = ROOT / 'tools/verify_v43a_trace.py'; f = ROOT / 'fixtures/valid_s1_contest_capture.json'
        p = subprocess.run([sys.executable, str(script), str(f)], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0)
        self.assertEqual(json.loads(p.stdout)['studio_qa'], 'NOT_VERIFIED_BY_THIS_TOOL')

    def test_cli_bad(self):
        with tempfile.TemporaryDirectory() as tmp:
            pth = Path(tmp) / 'bad.json'; pth.write_text('{}')
            p = subprocess.run([sys.executable, str(ROOT / 'tools/verify_v43a_trace.py'), str(pth)], capture_output=True, text=True)
            self.assertEqual(p.returncode, 2)
            self.assertFalse(json.loads(p.stdout)['ok'])


if __name__ == '__main__':
    unittest.main()