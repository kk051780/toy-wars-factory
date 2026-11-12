"""Run 8 positive/negative tests against an ACTUAL Rojo-built RBXLX, never synthetic."""
from pathlib import Path
import copy,os,sys,unittest,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from verify_real_rojo_xml import AuditError,prop,verify
@unittest.skipUnless(os.environ.get("RARE4_REAL_ROJO_PLACE"),"requires actual compiled Rojo Place")
class RealBinaryAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=Path(os.environ["RARE4_REAL_ROJO_PLACE"]).read_bytes()
    def node(self,root,name):
        return next(n for n in root.iter("Item") if prop(n,"Name")==name)
    def source(self,node):
        return next(n for n in node.find("Properties") if n.get("name")=="Source")
    def mutant(self,fn):
        root=ET.fromstring(self.raw)
        fn(root)
        return ET.tostring(root,encoding="utf-8")
    def test_actual_rojo_build_positive(self):
        r=verify(self.raw)
        self.assertTrue(r["four_source_modules_byte_exact"])
        self.assertFalse(r["real_studio_2client"])
    def test_bad_missing_scene_rejected(self):
        def f(root):
            x=self.node(root,"RareRealmScene")
            for p in root.iter():
                if x in p:p.remove(x);break
        with self.assertRaises(AuditError):verify(self.mutant(f))
    def test_bad_duplicate_game_authority_rejected(self):
        def f(root):
            x=self.node(root,"RareRealmDemo")
            for p in root.iter():
                if x in p:p.append(copy.deepcopy(x));break
        with self.assertRaises(AuditError):verify(self.mutant(f))
    def test_bad_enabled_demo_rejected(self):
        def f(root):
            s=self.source(self.node(root,"RareRealmDemo"))
            s.text=s.text.replace("ENABLE_FOUR_RARE_REALMS_DEMO = false",
                                  "ENABLE_FOUR_RARE_REALMS_DEMO = true",1)
        with self.assertRaises(AuditError):verify(self.mutant(f))
    def test_bad_turn_off_studio_guard_rejected(self):
        def f(root):
            s=self.source(self.node(root,"RareRealmDemo"))
            s.text=s.text.replace("RunService:IsStudio()","true",1)
        with self.assertRaises(AuditError):verify(self.mutant(f))
    def test_bad_original_scene_changed_rejected(self):
        def f(root):self.source(self.node(root,"RareRealmScene")).text="return {}"
        with self.assertRaises(AuditError):verify(self.mutant(f))
    def test_bad_client_authority_rejected(self):
        def f(root):self.node(root,"RareRealmDemo").set("class","LocalScript")
        with self.assertRaises(AuditError):verify(self.mutant(f))
    def test_bad_xml_rejected(self):
        with self.assertRaises(AuditError):verify(b"<wrong")
if __name__=="__main__":unittest.main()
