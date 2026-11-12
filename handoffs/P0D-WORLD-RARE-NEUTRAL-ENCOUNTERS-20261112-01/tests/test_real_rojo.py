"""Positive and adversarial tests on real, just-built Rojo binary only."""
from pathlib import Path
import copy,os,sys,unittest,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from verify_real_rojo import AuditError,prop,verify
@unittest.skipUnless(os.environ.get("RARE_NEUTRAL_ACTUAL_ROJO_PLACE"),
                     "requires authentic Rojo .rbxlx; no manufactured Studio pass")
class CompiledRojoChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=Path(os.environ["RARE_NEUTRAL_ACTUAL_ROJO_PLACE"]).read_bytes()
    def item(self,root,name):
        return next(n for n in root.iter("Item") if prop(n,"Name")==name)
    def source(self,node):
        return next(n for n in node.find("Properties") if n.get("name")=="Source")
    def modified(self,change):
        root=ET.fromstring(self.raw);change(root)
        return ET.tostring(root,encoding="utf-8")
    def test_actual_byte_for_byte_source_positive(self):
        proof=verify(self.raw)
        self.assertTrue(proof["all_five_sources_exact"])
        self.assertFalse(proof["real_roblox_studio_2client"])
    def test_original_world_source_missing_rejected(self):
        def mut(root):
            node=self.item(root,"RareRealmScene")
            for parent in root.iter():
                if node in parent:parent.remove(node);return
        with self.assertRaises(AuditError):verify(self.modified(mut))
    def test_duplicate_game_script_authority_rejected(self):
        def mut(root):
            node=self.item(root,"RareEncounterPreview")
            for parent in root.iter():
                if node in parent:parent.append(copy.deepcopy(node));return
        with self.assertRaises(AuditError):verify(self.modified(mut))
    def test_preview_on_by_default_rejected(self):
        def mut(root):
            source=self.source(self.item(root,"RareEncounterPreview"))
            source.text=source.text.replace("ENABLE_RARE_NEUTRAL_STUDIO_PREVIEW = false",
                                            "ENABLE_RARE_NEUTRAL_STUDIO_PREVIEW = true")
        with self.assertRaises(AuditError):verify(self.modified(mut))
    def test_studio_only_guard_removed_rejected(self):
        def mut(root):
            source=self.source(self.item(root,"RareEncounterPreview"))
            source.text=source.text.replace("RunService:IsStudio()","true",1)
        with self.assertRaises(AuditError):verify(self.modified(mut))
    def test_original_models_changed_rejected(self):
        def mut(root):
            self.source(self.item(root,"RareEncounterModels")).text="return {}"
        with self.assertRaises(AuditError):verify(self.modified(mut))
    def test_client_script_override_rejected(self):
        def mut(root):
            self.item(root,"RareEncounterPreview").set("class","LocalScript")
        with self.assertRaises(AuditError):verify(self.modified(mut))
    def test_corrupt_xml_rejected(self):
        with self.assertRaises(AuditError):verify(b"<bad")
if __name__=="__main__":
    unittest.main()
