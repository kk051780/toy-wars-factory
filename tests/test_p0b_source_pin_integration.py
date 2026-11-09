"""Actual PR209 source -> source-pinned .rbxlx -> R7 byte/schema verifier, static only."""
from __future__ import annotations
import hashlib
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT / "tools"))
sys.path.insert(0,str(ROOT / "tools" / "p0b_engine_receipt"))
import export_accepted_rbxlx as exporter
import validate_receipt as verifier

class OfficialSourceArtifactContract(unittest.TestCase):
    def test_exact_pr209_four_lua_blobs_are_exported_and_byte_verified(self):
        # Important: this test requires the full GitHub checkout at pinned PR209.
        xml, export_receipt = exporter.build_place(ROOT)
        self.assertEqual(verifier.verify_xml_bytes(xml), [], "canonical exporter output failed source/layout verifier")
        self.assertEqual(hashlib.sha256(xml).hexdigest(), export_receipt['rbxlx_sha256'])
        self.assertEqual(export_receipt['rbxlx_bytes'], len(xml))
        self.assertEqual(len(export_receipt['sources']),4)
        self.assertEqual({value['git_blob_sha1'] for value in export_receipt['sources'].values()},
                         {blob for _, blob in verifier.SOURCE_BLOBS.values()})
        self.assertEqual(export_receipt['unmerged_source_branch_head_sha'],
                         'cd104e3a6766ad0e37c763dd1e4d49624234276e')
        self.assertFalse(export_receipt['roblox_engine_verified'])
        self.assertFalse(export_receipt['roblox_upload_attested'])
        self.assertFalse(export_receipt['public_publish_authorized'])

if __name__=='__main__':
    unittest.main()
