"""Protect PR148's XML stage against recursion crashes; no Roblox calls."""
import unittest
from test_system_private_xml_saved import build_xml, config
import roblox_private_xml_saved as target


def nested_invalid_items(depth=1200):
    opens = [
        f'<Item class="Folder" referent="RBX{n + 5000:07X}">'
        '<Properties><string name="Name">extra</string></Properties>'
        for n in range(depth)
    ]
    return (''.join(opens) + '</Item>' * depth).encode('ascii')


class BoundedXmlInstanceTraversal(unittest.TestCase):
    def check_rejected(self, altered):
        self.assertLess(len(altered), target.MAX_XML_BYTES)
        # Even with a rehashed whole-file pin, unauthorized structure must fail.
        with self.assertRaisesRegex(target.XmlStageError, 'XML instance count not exactly approved'):
            target.check_rbxlx_bytes(altered, config(altered))

    def test_depth_1200_at_root_rejected_without_recursion_error(self):
        raw = build_xml()
        index = raw.find(b'<Item ')
        self.assertGreater(index, 0)
        self.check_rejected(raw[:index] + nested_invalid_items() + raw[index:])

    def test_depth_1200_inside_workspace_rejected_without_recursion_error(self):
        raw = build_xml()
        start = raw.find(b'<Item class="Workspace"')
        self.assertGreater(start, 0)
        index = raw.find(b'</Item>', start)
        self.assertGreater(index, start)
        self.check_rejected(raw[:index] + nested_invalid_items() + raw[index:])

    def test_shallow_extra_item_refused_by_count(self):
        raw = build_xml()
        index = raw.find(b'<Item ')
        self.assertGreater(index, 0)
        extra = b'<Item class="Folder" referent="RBXABCDEF"><Properties><string name="Name">extra</string></Properties></Item>'
        self.check_rejected(raw[:index] + extra + raw[index:])

    def test_exact_ten_item_artifact_keeps_expected_untrusted_verdict(self):
        raw = build_xml()
        result = target.check_rbxlx_bytes(raw, config(raw))
        self.assertEqual(result['instance_count'], 10)
        self.assertFalse(result['roblox_engine_verified'])
        self.assertFalse(result['roblox_upload_attested'])
