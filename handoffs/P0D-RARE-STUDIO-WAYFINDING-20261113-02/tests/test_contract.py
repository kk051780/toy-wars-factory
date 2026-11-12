"""Source-only gate. Native Luau and real binary tests are separate."""
from pathlib import Path
import json,sys,unittest
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/"tools"))
from verify_candidate_delta import verify
G=(R/"src/RareStudioGuides.luau").read_text("utf-8")
S=(R/"src/RareDiscoveryWayfindingPreview.server.luau").read_text("utf-8")
P=json.loads((R/"default.project.json").read_text("utf-8"))
class CurrentWaypointContracts(unittest.TestCase):
 def test_only_five_additive_server_hunks(self):self.assertEqual(verify(),5)
 def test_guide_current_only(self):
  self.assertIn("markers[id].gui.Enabled=found and id==currentId",G)
  self.assertIn("markers[id].gui.Enabled=false",G)
  self.assertIn("self.lastId=found and currentId or nil",G)
 def test_same_true_four_plan_positions(self):
  self.assertIn("local base=Plan.point(id)",G)
  self.assertIn("marker.Position=Vector3.new(base.X,5,base.Z)",G)
  self.assertIn("math.abs(p.x)>40",G)
  self.assertIn("math.abs(p.z)>40",G)
 def test_nonblocking_and_readable(self):
  for t in ("marker.Anchored=true","marker.Transparency=1","marker.CanCollide=false",
            "marker.CanTouch=false","marker.CanQuery=false","label.TextScaled=true",
            "label.TextWrapped=true","gui.AlwaysOnTop=true","gui.MaxDistance=140"):
   self.assertIn(t,G)
  self.assertIn("いまは ここ！",G)
 def test_server_studio_guards_and_witness(self):
  for t in ("ENABLE_RARE_DISCOVERY_STUDIO_BOOK = false","RunService:IsStudio()",
            "RunService:IsServer()",'FindFirstChild("TRAP_RAIDERS_S1")',
            "guides:show(id)","guides:clear()","Guides.mount(map.folder)"):
   self.assertIn(t,S)
 def test_no_paid_or_network_effects(self):
  for text in (G,S):
   executable="\n".join(line.split("--",1)[0] for line in text.splitlines())
   for forbidden in ("MarketplaceService","DataStoreService","OnServerEvent","FireServer",
       'Instance.new("RemoteEvent")',"Coins.Value","SetNetworkOwner("):
    self.assertNotIn(forbidden,executable)
 def test_all_11_script_sources(self):
  tree=P["tree"]["ServerScriptService"]
  self.assertEqual(len([x for x in tree if x!="$className"]),11)
  self.assertEqual(tree["RareStudioGuides"]["$path"],"src/RareStudioGuides.luau")
  self.assertEqual(tree["RareDiscoveryWayfindingPreview"]["$path"],
                   "src/RareDiscoveryWayfindingPreview.server.luau")
  for key in ("RareRealmCatalog","RareRealmScene","RareEncounterPolicy",
              "RareEncounterModels","RareDiscoveryBook","RareDiscoveryHUD",
              "RareDiscoveryQAPlan","RareCluePolicy","RareClueHUD"):
   self.assertTrue(tree[key]["$path"].startswith("../P0D-"))
 def test_positive_negative_real_luau_test_targets(self):
  tool=(R/"tools/build_native_wayfinder_runner.py").read_text("utf-8")
  for x in ("BAD_ALL_SIGNS_VISIBLE","BAD_COLLIDING_SIGN",
            "BAD_SIGNS_ALL_AT_HUB_CENTER","BAD_EXPIRY_SIGN_NOT_CLEARED",
            "BAD_FALSE_REWARD_ADVERT","BAD_SERVER_HIGHLIGHTS_WRONG_CREATURE",
            "BAD_SERVER_SKIPS_CLEAR"):
   self.assertIn(x,tool)
 def test_no_studio_pass_misattribution(self):
  readme=(R/"README.md").read_text("utf-8")
  self.assertIn("does **NOT**",readme)
  self.assertIn("2 clients",readme)
if __name__=="__main__":unittest.main()
