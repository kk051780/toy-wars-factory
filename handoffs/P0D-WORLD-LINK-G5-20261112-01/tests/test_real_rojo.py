"""Actually generated Rojo XML positive / destructive mutations (not synthetic claim)."""
import copy
import os
from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from verify_rojo_xml import AuditError,prop,verify

@unittest.skipUnless(os.environ.get("WORLD_G5_REAL_ROJO_PLACE"),
                     "requires actual Rojo output; no fake success")
class TestActualRojo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.xml=Path(os.environ["WORLD_G5_REAL_ROJO_PLACE"]).read_bytes()

    def item(self,doc,name):
        return next(x for x in doc.iter("Item") if prop(x,"Name")==name)

    def replace(self,fn):
        doc=ET.fromstring(self.xml)
        fn(doc)
        return ET.tostring(doc,encoding="utf-8")

    def test_real_positive(self):
        r=verify(self.xml)
        self.assertTrue(r["three_source_bytes_match"])
        self.assertFalse(r["real_roblox_studio"])

    def test_module_missing_rejected(self):
        def f(doc):
            module=self.item(doc,"WorldLinkRoutes")
            for parent in doc.iter():
                if module in parent:
                    parent.remove(module)
                    break
        with self.assertRaises(AuditError): verify(self.replace(f))

    def test_duplicate_script_rejected(self):
        def f(doc):
            target=self.item(doc,"WorldLinkDemo")
            for parent in doc.iter():
                if target in parent:
                    parent.append(copy.deepcopy(target))
                    break
        with self.assertRaises(AuditError): verify(self.replace(f))

    def test_original_source_corrupted_rejected(self):
        def f(doc):
            target=self.item(doc,"WorldLinkScene")
            src=next(x for x in target.find("Properties") if x.get("name")=="Source")
            src.text="return {}"
        with self.assertRaises(AuditError): verify(self.replace(f))

    def test_auto_demo_enabled_rejected(self):
        def f(doc):
            target=self.item(doc,"WorldLinkDemo")
            src=next(x for x in target.find("Properties") if x.get("name")=="Source")
            src.text=src.text.replace("ENABLE_WORLD_G5_DEMO = false",
                                      "ENABLE_WORLD_G5_DEMO = true")
        with self.assertRaises(AuditError): verify(self.replace(f))

    def test_client_conversion_rejected(self):
        def f(doc):
            self.item(doc,"WorldLinkDemo").set("class","LocalScript")
        with self.assertRaises(AuditError): verify(self.replace(f))

    def test_invalid_xml_rejected(self):
        with self.assertRaises(AuditError): verify(b"<xml broken")

if __name__=="__main__":
    unittest.main()
