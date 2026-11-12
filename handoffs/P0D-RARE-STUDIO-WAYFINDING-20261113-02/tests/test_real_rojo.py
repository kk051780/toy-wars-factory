"""Positive real Rojo 11-source .rbxlx and malicious original XML mutations."""
from pathlib import Path
import copy,os,sys,unittest,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/"tools"))
from verify_real_rojo import Reject,prop,verify
@unittest.skipUnless(os.environ.get("P0D_WAYFINDING_REAL_ROJO_PLACE"),
    "only real pinned Rojo .rbxlx may be called real binary QA")
class ActualSourceBinary(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.raw=Path(os.environ["P0D_WAYFINDING_REAL_ROJO_PLACE"]).read_bytes()
 def item(self,root,name):
  return next(v for v in root.iter("Item") if prop(v,"Name")==name)
 def source(self,node):
  return next(v for v in node.find("Properties") if v.get("name")=="Source")
 def changed(self,change):
  root=ET.fromstring(self.raw);change(root)
  return ET.tostring(root,encoding="utf-8")
 def test_positive_all_eleven_byte_exact_original(self):
  r=verify(self.raw)
  self.assertEqual(r["source_byte_exact_count"],11)
  self.assertFalse(r["actual_studio_2client"])
 def test_missing_original_scene_rejected(self):
  def edit(root):
   target=self.item(root,"RareRealmScene")
   for p in root.iter():
    if target in p:p.remove(target);return
  with self.assertRaises(Reject):verify(self.changed(edit))
 def test_duplicate_server_rejected(self):
  def edit(root):
   item=self.item(root,"RareDiscoveryWayfindingPreview")
   for p in root.iter():
    if item in p:p.append(copy.deepcopy(item));return
  with self.assertRaises(Reject):verify(self.changed(edit))
 def test_enable_preview_rejected(self):
  def edit(root):
   node=self.source(self.item(root,"RareDiscoveryWayfindingPreview"))
   node.text=node.text.replace("ENABLE_RARE_DISCOVERY_STUDIO_BOOK = false",
                               "ENABLE_RARE_DISCOVERY_STUDIO_BOOK = true",1)
  with self.assertRaises(Reject):verify(self.changed(edit))
 def test_replace_server_with_client_authority_rejected(self):
  def edit(root):
   self.item(root,"RareDiscoveryWayfindingPreview").set("class","LocalScript")
  with self.assertRaises(Reject):verify(self.changed(edit))
 def test_server_guard_removed_rejected(self):
  def edit(root):
   node=self.source(self.item(root,"RareDiscoveryWayfindingPreview"))
   node.text=node.text.replace("RunService:IsStudio()","true",1)
  with self.assertRaises(Reject):verify(self.changed(edit))
 def test_wrong_sign_position_original_source_rejected(self):
  def edit(root):
   node=self.source(self.item(root,"RareStudioGuides"))
   node.text=node.text.replace("marker.Position=Vector3.new(base.X,5,base.Z)",
                               "marker.Position=Vector3.new(0,5,0)",1)
  with self.assertRaises(Reject):verify(self.changed(edit))
 def test_colliding_sign_original_source_rejected(self):
  def edit(root):
   node=self.source(self.item(root,"RareStudioGuides"))
   node.text=node.text.replace("marker.CanCollide=false","marker.CanCollide=true",1)
  with self.assertRaises(Reject):verify(self.changed(edit))
 def test_hidden_misleading_source_rejected(self):
  def edit(root):
   self.source(self.item(root,"RareStudioGuides")).text="return {show=function()return true end}"
  with self.assertRaises(Reject):verify(self.changed(edit))
 def test_malformed_binary_rejected(self):
  with self.assertRaises(Reject):verify(b"<not-rojo")
if __name__=="__main__":unittest.main()
