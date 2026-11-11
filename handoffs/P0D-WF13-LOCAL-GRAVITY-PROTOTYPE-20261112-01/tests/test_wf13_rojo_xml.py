"""Negative probes on ACTUAL Rojo-generated WF13 RBXLX.
Requires WF13_REAL_ROJO_PLACE exported by CI; does not pretend this is Studio.
"""
from pathlib import Path
import copy
import os
import sys
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from verify_wf13_rojo_xml import IntegrityError, prop, verify

@unittest.skipUnless(os.environ.get("WF13_REAL_ROJO_PLACE"), "requires actually built Rojo XML")
class WF13RealXMLTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw = os.environ.get("WF13_REAL_ROJO_PLACE")
        if not raw:
            raise RuntimeError("Requires real Rojo output WF13_REAL_ROJO_PLACE, not synthetic fixture")
        cls.xml = Path(raw).read_bytes()

    @staticmethod
    def tamper(xml, mutator):
        doc = ET.fromstring(xml)
        mutator(doc)
        return ET.tostring(doc, encoding="utf-8")

    @staticmethod
    def find(doc, name):
        return next(x for x in doc.iter("Item") if prop(x, "Name") == name)

    @staticmethod
    def source_tag(item):
        return next(x for x in item.find("Properties") if x.get("name") == "Source")

    def test_actual_rojo_output_positive(self):
        receipt = verify(self.xml)
        self.assertEqual(receipt["script_count"], 4)
        self.assertFalse(receipt["demo_enabled"])
        self.assertEqual(receipt["executable_game_script_count"], 1)

    def test_missing_policy_module_rejected(self):
        def mutation(doc):
            item = self.find(doc, "WF13Policy")
            for parent in doc.iter():
                if item in parent:
                    parent.remove(item)
                    return
            raise AssertionError("policy parent not found")
        with self.assertRaises(IntegrityError):
            verify(self.tamper(self.xml, mutation))

    def test_duplicate_controller_script_rejected(self):
        def mutation(doc):
            item = self.find(doc, "WF13ZoneController")
            for parent in doc.iter():
                if item in parent:
                    parent.append(copy.deepcopy(item))
                    return
        with self.assertRaises(IntegrityError):
            verify(self.tamper(self.xml, mutation))

    def test_source_changed_rejected(self):
        def mutation(doc):
            self.source_tag(self.find(doc, "WF13Policy")).text = "return {}"
        with self.assertRaises(IntegrityError):
            verify(self.tamper(self.xml, mutation))

    def test_wrong_server_script_class_rejected(self):
        def mutation(doc):
            self.find(doc, "WF13Demo").set("class", "LocalScript")
        with self.assertRaises(IntegrityError):
            verify(self.tamper(self.xml, mutation))

    def test_enabled_demo_rejected(self):
        def mutation(doc):
            p = self.source_tag(self.find(doc, "WF13Demo"))
            self.assertIn("ENABLE_WF13_ISOLATED_DEMO = false", p.text)
            p.text = p.text.replace("ENABLE_WF13_ISOLATED_DEMO = false",
                                    "ENABLE_WF13_ISOLATED_DEMO = true")
        with self.assertRaises(IntegrityError):
            verify(self.tamper(self.xml, mutation))

    def test_unlisted_script_rejected(self):
        def mutation(doc):
            item = copy.deepcopy(self.find(doc, "WF13Demo"))
            next(p for p in item.find("Properties") if p.get("name") == "Name").text = "UnknownSecondGame"
            for parent in doc.iter():
                if self.find(doc, "WF13Demo") in parent:
                    parent.append(item)
                    return
        with self.assertRaises(IntegrityError):
            verify(self.tamper(self.xml, mutation))

    def test_malformed_xml_rejected(self):
        with self.assertRaises(IntegrityError):
            verify(b"<broken")

if __name__ == "__main__":
    unittest.main()
