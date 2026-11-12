"""Negative source mutation tests against REAL Rojo .rbxlx build (not synthetic)."""
import copy
import os
from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from verify_studio_rojo_xml import GateError,prop,verify

@unittest.skipUnless(os.environ.get("G5_STUDIO_REAL_ROJO_PLACE"),
                     "requires REAL pinned Rojo binary")
class RealStudioPlaceSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=Path(os.environ["G5_STUDIO_REAL_ROJO_PLACE"]).read_bytes()

    def mutate(self,fn):
        root=ET.fromstring(self.raw)
        fn(root)
        return ET.tostring(root,encoding="utf-8")

    @staticmethod
    def find(root,name):
        return next(v for v in root.iter("Item") if prop(v,"Name")==name)

    @staticmethod
    def source(node):
        return next(x for x in node.find("Properties") if x.get("name")=="Source")

    def test_true_binary_positive(self):
        proof=verify(self.raw)
        self.assertEqual(proof["original_module_sources_exact"],2)
        self.assertEqual(proof["probe_and_plan_sources_exact"],2)
        self.assertFalse(proof["actual_roblox_studio_play_2clients"])

    def test_missing_original_scene_rejected(self):
        def change(root):
            node=self.find(root,"WorldLinkScene")
            for parent in root.iter():
                if node in parent:
                    parent.remove(node);return
        with self.assertRaises(GateError):verify(self.mutate(change))

    def test_extra_game_server_rejected(self):
        def change(root):
            node=self.find(root,"WorldG5StudioEvidence")
            for parent in root.iter():
                if node in parent:
                    parent.append(copy.deepcopy(node));return
        with self.assertRaises(GateError):verify(self.mutate(change))

    def test_user_cannot_turn_on_real_scene_in_committed_source(self):
        def change(root):
            node=self.find(root,"WorldG5StudioEvidence")
            src=self.source(node)
            src.text=src.text.replace("ENABLE_G5_STUDIO_EVIDENCE = false",
                                      "ENABLE_G5_STUDIO_EVIDENCE = true",1)
        with self.assertRaises(GateError):verify(self.mutate(change))

    def test_cannot_remove_studio_guard(self):
        def change(root):
            node=self.find(root,"WorldG5StudioEvidence")
            src=self.source(node)
            src.text=src.text.replace("RunService:IsStudio()","true",1)
        with self.assertRaises(GateError):verify(self.mutate(change))

    def test_original_scene_source_corruption_rejected(self):
        def change(root):self.source(self.find(root,"WorldLinkScene")).text="return {}"
        with self.assertRaises(GateError):verify(self.mutate(change))

    def test_untrusted_local_script_rejected(self):
        def change(root):self.find(root,"WorldG5StudioEvidence").set("class","LocalScript")
        with self.assertRaises(GateError):verify(self.mutate(change))

    def test_invalid_xml_rejected(self):
        with self.assertRaises(GateError):verify(b"<bad")

if __name__=="__main__":
    unittest.main()
