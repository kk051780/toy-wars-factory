"""Out-of-root XML comments/PIs are otherwise silently ignored by ElementTree.
Uses the existing PR148 source-pinned XML fixture; original PR147 artifact
is separately verified in the local owner evidence package. No network calls.
"""
from __future__ import annotations
import unittest
from test_system_private_xml_saved import build_xml, config
import roblox_private_xml_saved as module

def real_xml():
    # CI reconstructs the source-pinned ten-instance native producer topology.
    # Separately, the local owner evidence package checks actual PR147 artifact.
    return build_xml()


class OutsideRootMarkup(unittest.TestCase):
    def reject(self, before=b'', after=b''):
        original = real_xml()
        start = original.index(b'?>') + 2
        altered = original[:start] + before + original[start:] + after
        # Allow updating caller-supplied digest to isolate grammar defenses.
        with self.assertRaisesRegex(module.XmlStageError, 'unreviewed XML processing markup'):
            module.check_rbxlx_bytes(altered, config(altered))

    def test_comment_between_xml_decl_and_root(self):
        self.reject(before=b'<!--OUTSIDE_ROOT_COMMENT-->')

    def test_comment_after_root(self):
        self.reject(after=b'<!--OUTSIDE_ROOT_COMMENT-->')

    def test_processing_instruction_between_decl_and_root(self):
        self.reject(before=b'<?probe outside-root?>')

    def test_processing_instruction_after_root(self):
        self.reject(after=b'<?probe outside-root?>')

    def test_xml_stylesheet_pi_cannot_impersonate_xml_declaration(self):
        original = real_xml()
        start = original.index(b'?>') + 2
        altered = b'<?xml-stylesheet href="style.css"?>' + original[start:]
        with self.assertRaisesRegex(module.XmlStageError, 'unreviewed XML processing markup'):
            module.check_rbxlx_bytes(altered, config(altered))

    def test_native_original_artifact_accepted(self):
        original = real_xml()
        result = module.check_rbxlx_bytes(original, config(original))
        self.assertEqual(result['instance_count'], 10)
        self.assertEqual(len(result['source_sha256']), 4)
        self.assertFalse(result['github_authenticated'])
        self.assertFalse(result['roblox_engine_verified'])


if __name__ == '__main__':
    unittest.main()
