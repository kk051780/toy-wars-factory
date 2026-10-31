"""Offline-only original-API-shape adapter tests; mock callback is untrusted."""
import base64
import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from system_owner_registry_snapshot import (API_ROOT, COORDINATOR_BRANCH,
    COORDINATOR_PATH, REPOSITORY, REPOSITORY_ID, SnapshotRejected,
    capture_snapshot, git_blob_sha, strict_json)

MAIN = 'a' * 40
CONTROL = 'b' * 40


def observed_state():
    return {'schema': 1, 'epoch': 341, 'holder': None,
            'last_completed': {'epoch': 341}, 'some_unrelated_field': True}


def file_response(state=None, raw=None):
    data = raw if raw is not None else json.dumps(state if state is not None else observed_state(),
                                                  ensure_ascii=False).encode()
    return {'type': 'file', 'path': COORDINATOR_PATH, 'encoding': 'base64',
            'size': len(data), 'sha': git_blob_sha(data),
            'content': base64.b64encode(data).decode()}


def ref(branch, sha):
    return {'ref': f'refs/heads/{branch}',
            'object': {'sha': sha, 'type': 'commit'}}


class FakeOriginalGitHub:
    def __init__(self):
        self.metadata = {'id': REPOSITORY_ID, 'full_name': REPOSITORY, 'private': True}
        self.head_main = MAIN
        self.head_coord = CONTROL
        self.contents = file_response()
        self.calls = []
        self.after = None

    def __call__(self, url):
        self.calls.append(url)
        if self.after:
            self.after(self, url)
        if url == API_ROOT:
            return copy.deepcopy(self.metadata)
        if url == f'{API_ROOT}/git/ref/heads/main':
            return ref('main', self.head_main)
        if url == f'{API_ROOT}/git/ref/heads/{COORDINATOR_BRANCH}':
            return ref(COORDINATOR_BRANCH, self.head_coord)
        if url == f'{API_ROOT}/contents/{COORDINATOR_PATH}?ref={CONTROL}':
            return copy.deepcopy(self.contents)
        raise AssertionError('unexpected URL (this test must not do any network call)')


class OriginalGitSnapshotTests(unittest.TestCase):
    def test_stable_six_get_snapshot(self):
        fake = FakeOriginalGitHub()
        result = capture_snapshot(fake)
        self.assertEqual(result['status'], 'CALLBACK_SNAPSHOT_NOT_PROVIDER_ATTESTED')
        self.assertEqual(result['capture_get_count'], 6)
        self.assertEqual(len(fake.calls), 6)
        self.assertEqual(result['snapshot']['main_sha'], MAIN)
        self.assertEqual(result['snapshot']['ref_sha'], CONTROL)
        self.assertEqual(result['snapshot']['state'], observed_state())
        self.assertEqual(fake.calls[3], f'{API_ROOT}/contents/{COORDINATOR_PATH}?ref={CONTROL}')
        self.assertFalse(result['work_registry_initialized'])

    def test_claim_write_merge_dispatch_and_provider_are_always_false(self):
        result = capture_snapshot(FakeOriginalGitHub())
        for field in ('github_authenticated', 'provider_run_authenticated',
                      'may_claim', 'may_write', 'may_dispatch', 'may_merge', 'cas_performed'):
            self.assertIs(result[field], False, field)

    def test_existing_registry_is_preserved_without_duplicated_validation(self):
        fake = FakeOriginalGitHub()
        state = observed_state()
        state['work_registrations'] = {'schema': 1, 'entries': []}
        fake.contents = file_response(state)
        out = capture_snapshot(fake)
        self.assertTrue(out['work_registry_initialized'])
        self.assertEqual(out['snapshot']['state']['work_registrations'], {'schema': 1, 'entries': []})

    def test_foreign_repo_id(self):
        fake = FakeOriginalGitHub()
        fake.metadata['id'] = 42
        with self.assertRaisesRegex(SnapshotRejected, 'REPOSITORY_IDENTITY_MISMATCH'):
            capture_snapshot(fake)

    def test_public_repo_denied(self):
        fake = FakeOriginalGitHub()
        fake.metadata['private'] = False
        with self.assertRaises(SnapshotRejected):
            capture_snapshot(fake)

    def test_repo_alias_denied(self):
        fake = FakeOriginalGitHub()
        fake.metadata['full_name'] = 'someone/else'
        with self.assertRaises(SnapshotRejected):
            capture_snapshot(fake)

    def test_bad_repo_id_type_denied(self):
        fake = FakeOriginalGitHub()
        fake.metadata['id'] = True
        with self.assertRaises(SnapshotRejected):
            capture_snapshot(fake)

    def test_ref_drift_main_denied(self):
        fake = FakeOriginalGitHub()
        count = [0]
        def on_call(_fake, url):
            if url == f'{API_ROOT}/git/ref/heads/main':
                count[0] += 1
                if count[0] == 2:
                    _fake.head_main = 'c' * 40
        fake.after = on_call
        with self.assertRaisesRegex(SnapshotRejected, 'REF_MOVED'):
            capture_snapshot(fake)

    def test_ref_drift_coordinator_denied(self):
        fake = FakeOriginalGitHub()
        count = [0]
        def on_call(_fake, url):
            if url == f'{API_ROOT}/git/ref/heads/{COORDINATOR_BRANCH}':
                count[0] += 1
                if count[0] == 2:
                    _fake.head_coord = 'c' * 40
        fake.after = on_call
        with self.assertRaisesRegex(SnapshotRejected, 'REF_MOVED'):
            capture_snapshot(fake)

    def test_coordinator_wrong_ref_name_denied(self):
        fake = FakeOriginalGitHub()
        def on_call(_fake, url):
            if url == f'{API_ROOT}/git/ref/heads/{COORDINATOR_BRANCH}':
                return None
        fake.after = on_call
        original = fake.__call__
        def bad(url):
            if url == f'{API_ROOT}/git/ref/heads/{COORDINATOR_BRANCH}':
                return ref('other', CONTROL)
            return original(url)
        with self.assertRaisesRegex(SnapshotRejected, 'INVALID_GIT_REF'):
            capture_snapshot(bad)

    def test_ref_wrong_object_type_denied(self):
        fake = FakeOriginalGitHub()
        def bad(url):
            if url == f'{API_ROOT}/git/ref/heads/main':
                return {'ref': 'refs/heads/main', 'object': {'sha': MAIN, 'type': 'tag'}}
            return fake(url)
        with self.assertRaises(SnapshotRejected):
            capture_snapshot(bad)

    def test_missing_ref_sha_denied(self):
        fake = FakeOriginalGitHub()
        def bad(url):
            if url == f'{API_ROOT}/git/ref/heads/main':
                return {'ref': 'refs/heads/main', 'object': {'type': 'commit'}}
            return fake(url)
        with self.assertRaises(SnapshotRejected):
            capture_snapshot(bad)

    def test_ref_bad_length_denied(self):
        fake = FakeOriginalGitHub()
        def bad(url):
            if url == f'{API_ROOT}/git/ref/heads/main':
                return ref('main', 'abc')
            return fake(url)
        with self.assertRaises(SnapshotRejected):
            capture_snapshot(bad)

    def test_bad_contents_encoding(self):
        fake = FakeOriginalGitHub()
        fake.contents['encoding'] = 'utf-8'
        with self.assertRaises(SnapshotRejected):
            capture_snapshot(fake)

    def test_bad_contents_path(self):
        fake = FakeOriginalGitHub()
        fake.contents['path'] = 'ops/OTHER.json'
        with self.assertRaises(SnapshotRejected):
            capture_snapshot(fake)

    def test_bad_base64(self):
        fake = FakeOriginalGitHub()
        fake.contents['content'] = '**nonsense**'
        with self.assertRaisesRegex(SnapshotRejected, 'INVALID_CONTENT_BASE64'):
            capture_snapshot(fake)

    def test_json_blob_hash_mismatch(self):
        fake = FakeOriginalGitHub()
        fake.contents['sha'] = 'f' * 40
        with self.assertRaisesRegex(SnapshotRejected, 'CONTENTS_HASH_MISMATCH'):
            capture_snapshot(fake)

    def test_json_blob_size_mismatch(self):
        fake = FakeOriginalGitHub()
        fake.contents['size'] += 1
        with self.assertRaisesRegex(SnapshotRejected, 'CONTENTS_HASH_MISMATCH'):
            capture_snapshot(fake)

    def test_duplicate_json_keys_rejected(self):
        fake = FakeOriginalGitHub()
        fake.contents = file_response(raw=b'{"schema":1,"schema":1,"epoch":42,"holder":null}')
        with self.assertRaisesRegex(SnapshotRejected, 'DUPLICATE_JSON_KEY'):
            capture_snapshot(fake)

    def test_nonfinite_json_rejected(self):
        fake = FakeOriginalGitHub()
        fake.contents = file_response(raw=b'{"schema":1,"epoch":NaN,"holder":null}')
        with self.assertRaisesRegex(SnapshotRejected, 'NONFINITE_JSON'):
            capture_snapshot(fake)

    def test_missing_state_holder_rejected(self):
        fake = FakeOriginalGitHub()
        fake.contents = file_response({'schema': 1, 'epoch': 42})
        with self.assertRaisesRegex(SnapshotRejected, 'COORDINATOR_SHAPE_INVALID'):
            capture_snapshot(fake)

    def test_bool_schema_rejected(self):
        fake = FakeOriginalGitHub()
        fake.contents = file_response({'schema': True, 'epoch': 42, 'holder': None})
        with self.assertRaises(SnapshotRejected):
            capture_snapshot(fake)

    def test_registry_shape_rejected(self):
        for bad in ({}, [], {'schema': True, 'entries': []},
                    {'schema': 1, 'entries': {}}):
            with self.subTest(registry=bad):
                fake = FakeOriginalGitHub()
                s = observed_state()
                s['work_registrations'] = bad
                fake.contents = file_response(s)
                with self.assertRaises(SnapshotRejected):
                    capture_snapshot(fake)

    def test_explicit_null_work_registry_is_not_equivalent_to_absent(self):
        fake = FakeOriginalGitHub()
        state = observed_state()
        state['work_registrations'] = None
        fake.contents = file_response(state)
        with self.assertRaisesRegex(SnapshotRejected, 'WORK_REGISTRY_SHAPE_INVALID'):
            capture_snapshot(fake)

    def test_registry_row_limit_refused(self):
        fake = FakeOriginalGitHub()
        state = observed_state()
        state['work_registrations'] = {'schema': 1, 'entries': [{}] * 513}
        fake.contents = file_response(state)
        with self.assertRaisesRegex(SnapshotRejected, 'WORK_REGISTRY_SHAPE_INVALID'):
            capture_snapshot(fake)

    def test_coordinator_does_not_gain_registry_key(self):
        fake = FakeOriginalGitHub()
        output = capture_snapshot(fake)
        self.assertNotIn('work_registrations', output['snapshot']['state'])
        self.assertFalse(output['cas_performed'])

    def test_callback_error_sanitized(self):
        def explode(url):
            raise RuntimeError('secret-sentinel-do-not-print')
        with self.assertRaisesRegex(SnapshotRejected, '^GITHUB_GET_FAILED$') as e:
            capture_snapshot(explode)
        self.assertNotIn('sentinel', str(e.exception))

    def test_callback_returning_list_is_denied(self):
        with self.assertRaisesRegex(SnapshotRejected, 'INVALID_API_RESPONSE'):
            capture_snapshot(lambda u: [])

    def test_missing_callback_denied(self):
        with self.assertRaises(SnapshotRejected):
            capture_snapshot(None)

    def test_no_network_or_mutation_symbol_in_module(self):
        src = (Path(__file__).resolve().parents[1] / 'tools' / 'system_owner_registry_snapshot.py').read_text()
        for marker in ('urllib', 'http.client', 'requests.', 'urlopen(', 'create_blob(', 'update_ref(',
                       'method="POST"', 'method="PATCH"', 'method="PUT"', 'run_now('):
            self.assertNotIn(marker, src)

    def test_strict_parser_rejects_nonobject(self):
        with self.assertRaisesRegex(SnapshotRejected, 'NOT_JSON_OBJECT'):
            strict_json(b'[]')

    def test_bad_blob_input_rejected(self):
        with self.assertRaises(SnapshotRejected):
            git_blob_sha('text')

    def test_large_file_envelope_rejected(self):
        fake = FakeOriginalGitHub()
        fake.contents['size'] = 1_000_001
        with self.assertRaises(SnapshotRejected):
            capture_snapshot(fake)

    def test_ref_payload_malformed_field_types(self):
        for invalid in (None, [], 'bad'):
            with self.subTest(value=invalid):
                fake = FakeOriginalGitHub()
                def bad(url):
                    if url == f'{API_ROOT}/git/ref/heads/main':
                        return invalid
                    return fake(url)
                with self.assertRaises(SnapshotRejected):
                    capture_snapshot(bad)

    def test_untrusted_callback_can_forge_consistent_data_not_authenticate(self):
        fake = FakeOriginalGitHub()
        result = capture_snapshot(fake)
        self.assertFalse(result['github_authenticated'])
        self.assertFalse(result['provider_run_authenticated'])


if __name__ == '__main__':
    unittest.main()
