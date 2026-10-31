"""Native PR143 -> PR144 output contract; no real Roblox provider access."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import rojo_build_receipt as receipt
import rojo_rbxl_gate as gate

WORKFLOW = ROOT / '.github/workflows/toy-wars-rojo-build-only.yml'
ENV = {
    'GITHUB_REPOSITORY': 'kk051780/toy-wars-factory',
    'GITHUB_REF': 'refs/heads/main',
    'GITHUB_EVENT_NAME': 'workflow_dispatch',
    'GITHUB_SHA': 'e5deff4d5681bca4823a3da0f848e01bc089ae6e',
}
EXPECTED_KEYS = {'repository', 'source_main_sha', 'rbxl_sha256', 'rbxl_bytes', 'build_only', 'engine_verified'}


def dummy_frame():
    raw = gate.MAGIC + struct.pack('<HIIQ', 0, 1, 5, 0)
    for kind in ('INST', 'PROP', 'PRNT', 'END'):
        data = b'</roblox>' if kind == 'END' else b'synthetic'
        raw += struct.pack('<4sIII', kind.encode().ljust(4, b'\0'), 0, len(data), 0) + data
    return raw


class CrossPrOutputTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.out = self.root / '.qa/rojo'
        self.out.mkdir(parents=True)
        self.binary = dummy_frame()
        (self.out / receipt.BINARY).write_bytes(self.binary)

    def test_latest_static_gate_accepts_synthetic_frame_only(self):
        self.assertEqual(gate.inspect(self.binary)['sha256'], hashlib.sha256(self.binary).hexdigest())
        self.assertFalse(gate.inspect(self.binary)['engine_verified'])

    def test_github_job_and_artifact_names_match_consumer(self):
        y = WORKFLOW.read_text()
        self.assertIn('    name: rojo-build-only\n', y)
        self.assertIn('name: twf-rojo-build-only-rbxl', y)
        self.assertIn('rojo build default.project.json -o .qa/rojo/toy-wars-private-test.rbxl', y)
        self.assertIn('python3 tools/rojo_build_receipt.py', y)

    def test_manual_only_read_only_workflow_preserved(self):
        y = WORKFLOW.read_text()
        for part in ('  workflow_dispatch:', '  contents: read', 'persist-credentials: false', 'timeout-minutes: 8'):
            self.assertIn(part, y)
        for part in ('  schedule:', '  push:', '  pull_request:', 'contents: write', 'id-token: write', 'secrets.'):
            self.assertNotIn(part, y)

    def test_exact_six_field_receipt_and_digest(self):
        result = receipt.make(self.root, ENV)
        self.assertEqual(set(result), EXPECTED_KEYS)
        self.assertEqual(result['repository'], ENV['GITHUB_REPOSITORY'])
        self.assertEqual(result['source_main_sha'], ENV['GITHUB_SHA'])
        self.assertEqual(result['rbxl_bytes'], len(self.binary))
        self.assertEqual(result['rbxl_sha256'], hashlib.sha256(self.binary).hexdigest())
        self.assertIs(result['build_only'], True)
        self.assertIs(result['engine_verified'], False)
        self.assertEqual(json.loads((self.out / receipt.RECEIPT).read_text()), result)

    def test_exact_two_flat_entries(self):
        receipt.make(self.root, ENV)
        self.assertEqual({x.name for x in self.out.iterdir()}, {'build-receipt.json', 'toy-wars-private-test.rbxl'})

    def test_wrong_repositories_and_event_rejected(self):
        for changes in ({'GITHUB_REPOSITORY': 'other/repo'}, {'GITHUB_REF': 'refs/heads/feature'},
                        {'GITHUB_EVENT_NAME': 'pull_request'}, {'GITHUB_SHA': 'bad'}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                receipt.make(self.root, {**ENV, **changes})
        self.assertFalse((self.out / receipt.RECEIPT).exists())

    def test_duplicate_receipt_rejected(self):
        receipt.make(self.root, ENV)
        with self.assertRaises(ValueError):
            receipt.make(self.root, ENV)

    def test_surplus_output_refused(self):
        (self.out / 'unreviewed.txt').write_text('x')
        with self.assertRaises(ValueError):
            receipt.make(self.root, ENV)

    def test_missing_binary_refused(self):
        (self.out / receipt.BINARY).unlink()
        with self.assertRaises(ValueError):
            receipt.make(self.root, ENV)

    def test_malformed_binary_refused(self):
        (self.out / receipt.BINARY).write_bytes(b'bad')
        with self.assertRaises(ValueError):
            receipt.make(self.root, ENV)

    def test_rbx_class_count_spoof_refused(self):
        raw = bytearray(self.binary)
        struct.pack_into('<I', raw, len(gate.MAGIC) + 2, 3)
        (self.out / receipt.BINARY).write_bytes(raw)
        with self.assertRaises(ValueError):
            receipt.make(self.root, ENV)

    def test_symlink_binary_refused(self):
        (self.out / receipt.BINARY).unlink()
        (self.out / receipt.BINARY).symlink_to(ROOT / 'rokit.toml')
        with self.assertRaises(ValueError):
            receipt.make(self.root, ENV)


if __name__ == '__main__':
    unittest.main()
