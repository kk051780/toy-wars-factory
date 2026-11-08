"""Verify P0-D offline XML candidate embeds the exact pinned Luau source.

Roblox Studio opening/engine Play is NOT performed by these checks.
"""
from pathlib import Path
from xml.etree import ElementTree as ET
import unittest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "examples" / "p0d_sorting_postoffice" / "P0D_RobotPostOffice_LOCAL_TEST_UNVERIFIED.rbxlx"
SOURCE = ROOT / "examples" / "p0d_sorting_postoffice" / "RobotPostOffice.server.lua"


class P0DXmlCandidate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = PACKAGE.read_bytes()
        cls.root = ET.fromstring(cls.raw)

    def test_xml_is_valid_utf8_and_roblox_version_4(self):
        self.assertLess(len(self.raw), 200_000)
        self.assertEqual(self.root.tag, "roblox")
        self.assertEqual(self.root.get("version"), "4")
        self.assertIn(b'encoding="utf-8"', self.raw[:100])

    def test_only_isolated_roots_and_single_script(self):
        items = self.root.findall("./Item")
        self.assertEqual([(x.get("class"), x.findtext("./Properties/string[@name='Name']")) for x in items],
                         [("Workspace", "Workspace"), ("ServerScriptService", "ServerScriptService")])
        self.assertEqual(items[0].findall("./Item"), [])
        nested = items[1].findall("./Item")
        self.assertEqual(len(nested), 1)
        self.assertEqual(nested[0].get("class"), "Script")
        self.assertEqual(nested[0].findtext("./Properties/string[@name='Name']"),
                         "P0D_RobotPostOfficeTrial")
        self.assertEqual(len(self.root.findall(".//Item")), 3)

    def test_embedded_source_equals_reviewable_original(self):
        elements = self.root.findall(".//ProtectedString[@name='Source']")
        self.assertEqual(len(elements), 1)
        self.assertEqual(elements[0].text, SOURCE.read_text(encoding="utf-8"))
        self.assertIn("P0D_STATE_MACHINE_SMOKE_PASS", elements[0].text)
        self.assertIn("P0D_BLOCKED_NOT_UNPUBLISHED_LOCAL_STUDIO", elements[0].text)

    def test_no_external_roblox_assets_or_unapproved_services(self):
        self.assertNotIn(b"<BinaryString", self.raw)
        self.assertNotIn(b"<Content", self.raw)
        self.assertNotIn(b"<token", self.raw)
        self.assertNotIn(b"<int64 name=\"PlaceId\"", self.raw)
        self.assertEqual([e.text for e in self.root.findall("./External")], ["null", "nil"])


if __name__ == "__main__":
    unittest.main()
