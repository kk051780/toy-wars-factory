import pathlib
import sys
import unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from select_deposit import BLOCK, REPLACEMENT, transform, git_blob_sha
HEAD = b'--!strict\nlocal X=1\n'
TAIL = b'\n if c.alive and c.heldEggs>0 then foo() end\n'
class SelectionTests(unittest.TestCase):
    def original(self): return HEAD + BLOCK + TAIL
    def test_exact_single_callback_modified(self):
        self.assertEqual(transform(self.original()), HEAD + REPLACEMENT + TAIL)
    def test_byte_exact_inverse(self):
        self.assertEqual(transform(transform(self.original()), inverse=True), self.original())
    def test_other_bytes_identical(self):
        chosen=transform(self.original())
        self.assertEqual(chosen[:len(HEAD)], HEAD)
        self.assertEqual(chosen[-len(TAIL):], TAIL)
    def test_no_double_selection(self):
        with self.assertRaises(ValueError): transform(transform(self.original()))
    def test_missing_anchor_rejected(self):
        with self.assertRaises(ValueError): transform(HEAD + TAIL)
    def test_duplicate_anchor_rejected(self):
        with self.assertRaises(ValueError): transform(self.original()+BLOCK)
    def test_non_deposit_guard_rejected(self):
        with self.assertRaises(ValueError): transform(self.original().replace(b'prompt(deposit,',b'prompt(vault,'))
    def test_stale_selected_inverse_rejected(self):
        with self.assertRaises(ValueError): transform(self.original(),inverse=True)
    def test_match_and_same_session_both_required(self):
        result=transform(self.original())
        self.assertIn(b'joined[p.UserId]~=session.mode',result)
        self.assertIn(b'sessions[session.mode]~=session',result)
        self.assertIn(b'tostring(p.UserId)~=entry.id',result)
        self.assertIn(b'not session.rules',result)
    def test_git_blob_deterministic(self):
        self.assertEqual(git_blob_sha(b'test\n'),'9daeafb9864cf43055ae93beb0afd6c7d144bfa4')
    def test_crlf_source_refused_to_prevent_byte_drift(self):
        with self.assertRaises(ValueError): transform(self.original().replace(b'\n',b'\r\n'))
    def test_no_new_deposit_authority(self):
        chosen=transform(self.original())
        self.assertEqual(chosen.count(b'prompt(deposit,'),1)
if __name__=='__main__':unittest.main()
