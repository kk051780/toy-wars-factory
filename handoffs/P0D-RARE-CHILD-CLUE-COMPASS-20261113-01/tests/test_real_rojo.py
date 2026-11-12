"""Actual compiled genuine Rojo .rbxlx positive and seven harmful binary edits."""
from pathlib import Path
import copy,os,sys,unittest,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from verify_real_rojo import Reject,prop,verify
@unittest.skipUnless(os.environ.get("P0D_CLUE_REAL_ROJO_PLACE"),
   "only genuine compiled Rojo Place allows binary claims")
class RealRojoBinary(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.raw=Path(os.environ["P0D_CLUE_REAL_ROJO_PLACE"]).read_bytes()
 def item(self,root,name):
  return next(x for x in root.iter("Item") if prop(x,"Name")==name)
 def source(self,node):
  return next(x for x in node.find("Properties") if x.get("name")=="Source")
 def mutate(self,fn):
  root=ET.fromstring(self.raw)
  fn(root)
  return ET.tostring(root,encoding="utf-8")
 def test_real_genuine_ten_original_sources(self):
  r=verify(self.raw)
  self.assertEqual(r["source_byte_exact_count"],10)
  self.assertFalse(r["actual_studio_2client"])
 def test_missing_immutable_ancestor_world(self):
  def f(root):
   target=self.item(root,"RareRealmScene")
   for p in root.iter():
    if target in p:p.remove(target);return
  with self.assertRaises(Reject):verify(self.mutate(f))
 def test_duplicate_server_script(self):
  def f(root):
   target=self.item(root,"RareDiscoveryCluePreview")
   for p in root.iter():
    if target in p:p.append(copy.deepcopy(target));return
  with self.assertRaises(Reject):verify(self.mutate(f))
 def test_default_autostart_enabled_rejected(self):
  def f(root):
   s=self.source(self.item(root,"RareDiscoveryCluePreview"))
   s.text=s.text.replace("ENABLE_RARE_DISCOVERY_STUDIO_BOOK = false",
                          "ENABLE_RARE_DISCOVERY_STUDIO_BOOK = true",1)
  with self.assertRaises(Reject):verify(self.mutate(f))
 def test_live_studio_guard_deleted_rejected(self):
  def f(root):
   s=self.source(self.item(root,"RareDiscoveryCluePreview"))
   s.text=s.text.replace("RunService:IsStudio()","true",1)
  with self.assertRaises(Reject):verify(self.mutate(f))
 def test_fake_client_script_authority_rejected(self):
  def f(root):self.item(root,"RareDiscoveryCluePreview").set("class","LocalScript")
  with self.assertRaises(Reject):verify(self.mutate(f))
 def test_hint_source_coins_injected_rejected(self):
  def f(root):
   self.source(self.item(root,"RareCluePolicy")).text="return {ALL_DONE='100 COINS'}"
  with self.assertRaises(Reject):verify(self.mutate(f))
 def test_hud_source_corrupt_rejected(self):
  def f(root):
   self.source(self.item(root,"RareClueHUD")).text="return {}"
  with self.assertRaises(Reject):verify(self.mutate(f))
 def test_bad_xml_rejected(self):
  with self.assertRaises(Reject):verify(b"<not-rojo")
if __name__=="__main__":unittest.main()
