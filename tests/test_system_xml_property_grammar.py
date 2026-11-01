"""Reject unreviewed markup/text around source-pinned Roblox XML properties."""
import unittest
from xml.etree import ElementTree as ET
from test_system_private_xml_saved import build_xml, config
import roblox_private_xml_saved as xmlstage


class XmlPropertyGrammarRegression(unittest.TestCase):
    def assert_refused(self, edit):
        root = ET.fromstring(build_xml())
        edit(root)
        data = ET.tostring(root, encoding='utf-8', xml_declaration=True)
        with self.assertRaises(xmlstage.XmlStageError):
            xmlstage.check_rbxlx_bytes(data, config(data))

    def test_nested_unknown_element_inside_script_source(self):
        self.assert_refused(lambda root: ET.SubElement(
            root.find('.//ProtectedString[@name="Source"]'), 'Unknown'))

    def test_nested_unknown_element_inside_name_string(self):
        self.assert_refused(lambda root: ET.SubElement(
            root.find('.//string[@name="Name"]'), 'Unknown'))

    def test_properties_container_nonwhitespace_text(self):
        self.assert_refused(lambda root: setattr(root.find('.//Properties'), 'text', 'unreviewed'))

    def test_property_tail_nonwhitespace_text(self):
        self.assert_refused(lambda root: setattr(root.find('.//string[@name="Name"]'), 'tail', 'unreviewed'))

    def test_instance_container_nonwhitespace_text(self):
        self.assert_refused(lambda root: setattr(root.find('./Item'), 'text', 'unreviewed'))

    def test_instance_child_nonwhitespace_tail(self):
        self.assert_refused(lambda root: setattr(root.find('./Item/Properties'), 'tail', 'unreviewed'))

    def test_root_container_nonwhitespace_text(self):
        self.assert_refused(lambda root: setattr(root, 'text', 'unreviewed'))

    def test_root_child_nonwhitespace_tail(self):
        self.assert_refused(lambda root: setattr(root.find('./Item'), 'tail', 'unreviewed'))

    def test_comment_inside_source_not_silently_dropped(self):
        self.assert_refused(lambda root: root.find('.//ProtectedString[@name="Source"]').append(ET.Comment('hidden')))

    def test_processing_instruction_inside_source_not_dropped(self):
        self.assert_refused(lambda root: root.find('.//ProtectedString[@name="Source"]').append(ET.ProcessingInstruction('injected', 'payload')))

    def test_original_game_xml_still_passes(self):
        payload = build_xml()
        outcome = xmlstage.check_rbxlx_bytes(payload, config(payload))
        self.assertEqual(outcome['instance_count'], 10)
        self.assertFalse(outcome['roblox_engine_verified'])


if __name__ == '__main__':
    unittest.main()
