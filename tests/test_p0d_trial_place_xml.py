"""Verify P0-D offline XML candidate embeds the exact pinned Luau source.

Roblox Studio opening/engine Play is NOT performed by these checks.
"""
from pathlib import Path
from xml.etree import ElementTree as ET
import unittest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "examples" / "p0d_sorting_postoffice" / "P0D_RobotPostOffice_LOCAL_TEST_UNVERIFIED.rbxlx"
SOURCE = ROOT / "examples" / "p0d_sorting_postoffice" / "RobotPostOffice.server.lua"



def verify_exact_p0d_xml_shape(root: ET.Element, original_source: str) -> None:
    """Reject added services, script copies or property edits in the test Place.

    This is an OFFLINE artifact-shape check. It does not authenticate a Studio
    process, a Windows host, screenshots, live input, or engine behavior.
    """
    def require(ok: bool, reason: str) -> None:
        if not ok:
            raise ValueError("UNEXPECTED_P0D_XML_STRUCTURE: " + reason)

    require(root.tag == "roblox" and root.attrib == {"version": "4"}, "root")
    children = list(root)
    require([x.tag for x in children] ==
            ["External", "External", "Item", "Item"], "root child order")
    for index, expected in enumerate(("null", "nil")):
        ext = children[index]
        require(ext.attrib == {} and len(ext) == 0 and
                ext.text == expected, "External " + str(index))

    def check_item(el: ET.Element, klass: str, name: str,
                   ref: str, source: str | None = None) -> list[ET.Element]:
        require(el.tag == "Item" and el.attrib ==
                {"class": klass, "referent": ref}, "Item " + name)
        descendants = list(el)
        require(len(descendants) == (2 if klass == "ServerScriptService" else 1),
                "Item children " + name)
        props = descendants[0]
        require(props.tag == "Properties" and props.attrib == {}, "Properties " + name)
        values = list(props)
        expected_props = [("string", "Name", name)]
        if source is not None:
            expected_props.append(("ProtectedString", "Source", source))
        require(len(values) == len(expected_props), "properties count " + name)
        for item, (tag, attr, value) in zip(values, expected_props):
            require(item.tag == tag and item.attrib == {"name": attr} and
                    item.text == value and len(item) == 0, "property " + name + "/" + attr)
        return descendants

    check_item(children[2], "Workspace", "Workspace",
               "RBX00000000000000000000000000000001")
    descendants = check_item(children[3], "ServerScriptService", "ServerScriptService",
                             "RBX00000000000000000000000000000002")
    check_item(descendants[1], "Script", "P0D_RobotPostOfficeTrial",
               "RBX00000000000000000000000000000003", original_source)
    require(len(root.findall(".//Item")) == 3, "unexpected additional items")

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


    def test_exact_allowlist_rejects_added_xml_properties(self):
        verify_exact_p0d_xml_shape(self.root, SOURCE.read_text(encoding="utf-8"))

    def _altered_root(self):
        return ET.fromstring(self.raw)

    def _must_refuse(self, altered):
        with self.assertRaisesRegex(ValueError, "UNEXPECTED_P0D_XML_STRUCTURE"):
            verify_exact_p0d_xml_shape(altered, SOURCE.read_text(encoding="utf-8"))

    def test_rejects_workspace_gravity_override(self):
        root = self._altered_root()
        props = root.findall("./Item")[0].find("Properties")
        ET.SubElement(props, "float", {"name": "Gravity"}).text = "0"
        self._must_refuse(root)

    def test_rejects_unapproved_service_property(self):
        root = self._altered_root()
        props = root.findall("./Item")[1].find("Properties")
        ET.SubElement(props, "bool", {"name": "LoadStringEnabled"}).text = "true"
        self._must_refuse(root)

    def test_rejects_duplicate_script_item(self):
        root = self._altered_root()
        service = root.findall("./Item")[1]
        duplicate = ET.fromstring(ET.tostring(service.find("./Item")))
        service.append(duplicate)
        self._must_refuse(root)

    def test_rejects_tampered_gameplay_source(self):
        root = self._altered_root()
        tag = root.find(".//ProtectedString[@name='Source']")
        tag.text = (tag.text or "").replace("P0D_STATE_MACHINE_SMOKE_PASS",
                                             "P0D_FAKE_SUCCESS")
        self._must_refuse(root)

    def test_rejects_unexpected_root_tag_and_attribute(self):
        root = self._altered_root()
        root.attrib["allowRemote"] = "true"
        self._must_refuse(root)
        root = self._altered_root()
        root.append(ET.Element("Item", {"class": "HttpService", "referent": "new"}))
        self._must_refuse(root)

    def test_rejects_referent_reassignment(self):
        root = self._altered_root()
        root.findall("./Item")[1].attrib["referent"] = "RBX00000000000000000000000000000001"
        self._must_refuse(root)

    def test_rejects_script_property_injection(self):
        root = self._altered_root()
        props = root.find(".//Item[@class='Script']/Properties")
        ET.SubElement(props, "bool", {"name": "Disabled"}).text = "true"
        self._must_refuse(root)

    def test_rejects_reordered_external_or_extra_services(self):
        root = self._altered_root()
        root.insert(0, ET.Element("External"))
        self._must_refuse(root)
        root = self._altered_root()
        root.findall("./External")[1].text = "http://untrusted"
        self._must_refuse(root)

if __name__ == "__main__":
    unittest.main()
