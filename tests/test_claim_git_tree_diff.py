"""Extra fail-closed review: controller claim must modify ONLY coordinator JSON.

This is strictly deterministic mock transport, not a live GitHub certificate.
"""
import unittest
from copy import deepcopy

from test_manual_claim_witness import Fake, CLAIM, PARENT, SRC, check, m


class GitTreeClaimTests(unittest.TestCase):
    def setUp(self):
        self.fake = Fake()
        self.before_key = '/git/trees/' + 'd'*40 + '?recursive=1'
        self.after_key = '/git/trees/' + 'e'*40 + '?recursive=1'

    def deny(self, expected):
        with self.assertRaises(m.WitnessHold) as caught:
            check(self.fake)
        self.assertEqual(str(caught.exception), expected)

    def test_fixture_tree_change_is_limited_to_json_and_ancestor_tree(self):
        out = check(self.fake)
        self.assertEqual(out['status'], 'CLAIM_OBSERVED_BRANCH_ABSENT_CANDIDATE_ONLY')
        self.assertEqual(len(self.fake.calls), 11)
        self.assertEqual(self.fake.calls[-1], ('/git/ref/heads/' + SRC, True))
        self.assertFalse(out['merge_authorized'])

    def test_unrelated_file_mutation_denied(self):
        self.fake.items[self.after_key]['tree'][1]['sha'] = '9'*40
        self.deny('CLAIM_CHANGED_OTHER_PATHS')

    def test_new_file_in_same_claim_denied(self):
        self.fake.items[self.after_key]['tree'].append({
            'path': 'docs/extra.md', 'type': 'blob', 'mode': '100644', 'sha': '9'*40,
        })
        self.deny('CLAIM_CHANGED_OTHER_PATHS')

    def test_deleted_file_denied(self):
        self.fake.items[self.after_key]['tree'] = [
            x for x in self.fake.items[self.after_key]['tree'] if x['path'] != 'README.md'
        ]
        self.deny('CLAIM_CHANGED_OTHER_PATHS')

    def test_unrelated_file_mode_change_denied(self):
        self.fake.items[self.after_key]['tree'][1]['mode'] = '100755'
        self.deny('CLAIM_CHANGED_OTHER_PATHS')

    def test_symlink_replacement_denied(self):
        target = [x for x in self.fake.items[self.after_key]['tree']
                  if x['path'] == 'ops/REPAIR_COORDINATOR.json'][0]
        target['mode'] = '120000'
        self.deny('COORDINATOR_FILE_PATH_OR_MODE_CHANGED')

    def test_changed_tree_ancestor_mode_denied(self):
        target = [x for x in self.fake.items[self.after_key]['tree'] if x['path'] == 'ops'][0]
        target['mode'] = '100644'
        self.deny('COORDINATOR_FILE_PATH_OR_MODE_CHANGED')

    def test_untrusted_claim_tree_sha_denied(self):
        self.fake.items[self.after_key]['sha'] = '0'*40
        self.deny('GIT_TREE_INCOMPLETE_OR_WRONG_SHA')

    def test_truncated_tree_denied(self):
        self.fake.items[self.before_key]['truncated'] = True
        self.deny('GIT_TREE_INCOMPLETE_OR_WRONG_SHA')

    def test_duplicate_tree_entry_denied(self):
        self.fake.items[self.after_key]['tree'].append(
            deepcopy(self.fake.items[self.after_key]['tree'][0]))
        self.deny('GIT_TREE_MALFORMED_OR_DUPLICATE')

    def test_wrong_blob_binding_denied(self):
        target = [x for x in self.fake.items[self.after_key]['tree']
                  if x['path'] == 'ops/REPAIR_COORDINATOR.json'][0]
        target['sha'] = '0'*40
        self.deny('CLAIM_TREE_BLOB_NOT_BOUND_TO_CONTENT')

    def test_parent_git_commit_wrong_tree_denied(self):
        self.fake.items['/git/commits/' + PARENT]['tree']['sha'] = 'broken'
        self.deny('CLAIM_GIT_COMMIT_TREE_UNPROVEN')

    def test_unchanged_ops_tree_fails_closed(self):
        before = [x for x in self.fake.items[self.before_key]['tree']
                  if x['path'] == 'ops'][0]
        after = [x for x in self.fake.items[self.after_key]['tree']
                 if x['path'] == 'ops'][0]
        after['sha'] = before['sha']
        self.deny('CLAIM_ANCESTOR_TREE_UNCHANGED')

    def test_route_may_only_request_recursive_true(self):
        get = m.ProviderReadOnly('TEST_TOKEN_ONLY_DONT_USE', opener=lambda *a, **kw: None).get
        with self.assertRaises(m.WitnessHold) as caught:
            get('/git/trees/' + 'e'*40 + '?recursive=0')
        self.assertEqual(str(caught.exception), 'INVALID_API_ROUTE')


if __name__ == '__main__':
    unittest.main()
