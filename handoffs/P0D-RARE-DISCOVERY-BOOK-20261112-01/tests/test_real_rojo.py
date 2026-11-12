"""Seven dangerous XML mutations against an ACTUAL compiled Rojo file, not fake Studio."""
from pathlib import Path
import copy,os,sys,unittest,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from verify_real_rojo import Reject,prop,verify
@unittest.skipUnless(os.environ.get("RARE_BOOK_REAL_ROJO_PLACE"),
    "requires actual checked in-run Rojo binary; no invented QA pass")
class ActualRojoBinary(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.raw=Path(os.environ["RARE_BOOK_REAL_ROJO_PLACE"]).read_bytes()
 @staticmethod
 def node(root,name):
  return next(x for x in root.iter("Item") if prop(x,"Name")==name)
 @staticmethod
 def source(node):
  return next(x for x in node.find("Properties") if x.get("name")=="Source")
 def mutate(self,fn):
  root=ET.fromstring(self.raw)
  fn(root)
  return ET.tostring(root,encoding="utf-8")
 def test_01_real_full_8_positive(self):
  r=verify(self.raw)
  self.assertEqual(r["embedded_original_sources_exact"],8)
  self.assertFalse(r["actual_roblox_studio_2client"])
 def test_02_remove_frozen_world_module(self):
  def f(root):
   target=self.node(root,"RareRealmScene")
   for parent in root.iter():
    if target in parent:parent.remove(target);return
  with self.assertRaises(Reject):verify(self.mutate(f))
 def test_03_duplicate_server_source(self):
  def f(root):
   target=self.node(root,"RareDiscoveryStudio")
   for parent in root.iter():
    if target in parent:parent.append(copy.deepcopy(target));return
  with self.assertRaises(Reject):verify(self.mutate(f))
 def test_04_enable_autorun(self):
  def f(root):
   t=self.source(self.node(root,"RareDiscoveryStudio"))
   t.text=t.text.replace("ENABLE_RARE_DISCOVERY_STUDIO_BOOK = false",
                         "ENABLE_RARE_DISCOVERY_STUDIO_BOOK = true")
  with self.assertRaises(Reject):verify(self.mutate(f))
 def test_05_remove_studio_guard(self):
  def f(root):
   t=self.source(self.node(root,"RareDiscoveryStudio"))
   t.text=t.text.replace("RunService:IsStudio()","true",1)
  with self.assertRaises(Reject):verify(self.mutate(f))
 def test_06_corrupt_original_book(self):
  def f(root):
   self.source(self.node(root,"RareDiscoveryBook")).text="return {}"
  with self.assertRaises(Reject):verify(self.mutate(f))
 def test_07_inject_client_script_authority(self):
  def f(root):self.node(root,"RareDiscoveryStudio").set("class","LocalScript")
  with self.assertRaises(Reject):verify(self.mutate(f))
 def test_08_broken_xml(self):
  with self.assertRaises(Reject):verify(b"<bad")
if __name__=="__main__":unittest.main()
