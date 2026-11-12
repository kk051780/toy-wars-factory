"""Original 4-character UI and two-client evidence source contracts, not a Studio run."""
from pathlib import Path
import json,unittest
ROOT=Path(__file__).resolve().parents[1]
B=(ROOT/"src/RareDiscoveryBook.luau").read_text("utf-8")
H=(ROOT/"src/RareDiscoveryHUD.luau").read_text("utf-8")
P=(ROOT/"src/RareDiscoveryQAPlan.luau").read_text("utf-8")
S=(ROOT/"src/RareDiscoveryStudio.server.luau").read_text("utf-8")
PROJ=json.loads((ROOT/"default.project.json").read_text("utf-8"))
class BookContracts(unittest.TestCase):
 def test_default_off_owner_private(self):
  self.assertIn("ENABLE_RARE_DISCOVERY_STUDIO_BOOK = false",S)
  self.assertIn("if not ENABLE_RARE_DISCOVERY_STUDIO_BOOK then return end",S)
  self.assertIn("RunService:IsStudio()",S)
  self.assertIn("RunService:IsServer()",S)
  self.assertIn('FindFirstChild("TRAP_RAIDERS_S1")',S)
 def test_serial_is_server_protected_and_session_only(self):
  self.assertIn("Book.fresh()",B)
  self.assertIn("book.count+1",B)
  self.assertIn("serial<book.lastSerial",B)
  self.assertIn("serial==book.lastSerial",B)
  self.assertIn('return book,"ALREADY_SEEN"',B)
  self.assertIn('return book,"INVALID"',B)
  self.assertIn('return book,"STALE"',B)
  self.assertIn('return book,"FULL"',B)
  self.assertIn("Book.accept(previous,id,serial)",S)
 def test_four_only_noncanonical(self):
  for id in ("SPACE","CELESTIAL","EMBER","ECLIPSE"):
   self.assertIn(id,B)
   self.assertIn(id,P)
  self.assertIn("0/4",B)
  self.assertIn("4/4",B) if "4/4" in B else self.assertIn("found={},count=0",B)
 def test_user_owned_mobile_screen(self):
  self.assertIn('Instance.new("ScreenGui")',H)
  self.assertIn('ScreenGui',H)
  self.assertIn('gui.ResetOnSpawn=false',H)
  self.assertIn('title.Text=Book.progress(book)',H)
  self.assertIn('TextScaled=true',H)
  self.assertIn("HUD.update(player,nextBook)",S)
  self.assertIn('TextColor3=item.found',H)
 def test_no_user_gift_or_paid(self):
  for source in (B,H,P,S):
   for forbidden in ("DataStoreService","MarketplaceService","PublishAsync",
        "OnServerEvent","RemoteEvent","FireServer","leaderstats","GrantRobux",
        "Coins.Value","workspace.Gravity","GiveReward","SetNetworkOwner("):
    self.assertNotIn(forbidden,source,forbidden)
 def test_two_real_clients_reception_requires_server_distance(self):
  self.assertIn("activeUserCount()<2",S)
  self.assertIn("count>=2",S)
  self.assertIn("TWO_REAL_CLIENT_SAME_CREATURE",S)
  self.assertIn("TWO_CLIENT_INDEPENDENT_BOOK_4_OF_4",S)
  self.assertIn("humanoid.Health<=0",S)
  self.assertIn("not root:IsA",S)
  self.assertIn("root.Anchored",S)
  self.assertIn("Policy.MIN_INTERACTION_DISTANCE",S)
  self.assertIn("prompt.Triggered:Connect",S)
  self.assertIn("not active.visual.prompt.Enabled",S)
  self.assertIn("current.serial~=serial",S)
 def test_no_user_identifiers_logging(self):
  self.assertNotIn("tostring(player.UserId)",S)
  self.assertNotIn("player.Name",S)
  self.assertNotIn("HttpService",S)
  self.assertIn("no_stored_user_ids=true",S)
 def test_four_clearly_synthetic_qas_not_real_spawn(self):
  self.assertIn("Plan.SLOT_SECONDS = 26",P)
  self.assertIn("Plan.EXPOSURE_SECONDS = 23",P)
  self.assertIn("Plan.PROMPT_DELAY_SECONDS = 2",P)
  self.assertIn('return nil,slot',P)
  self.assertIn("deterministic_QA_bench=true",S)
  self.assertIn("not_real_rarity=true",S)
  self.assertIn('source-only', (ROOT/"README.md").read_text("utf-8").lower())
 def test_disconnect_lifecycle(self):
  self.assertIn("PlayerRemoving:Connect",S)
  self.assertIn("books[player]=nil",S)
  self.assertIn("CharacterRemoving:Connect",S)
  self.assertIn("game:BindToClose",S)
  self.assertIn("clearActive()",S)
 def test_velocity_does_not_move_players(self):
  self.assertIn("Magnitude/seconds>80",S)
  self.assertIn("eligibleAt[player]=now+2",S)
  self.assertNotIn("root.CFrame =",S)
  self.assertNotIn("root.Position =",S)
  self.assertNotIn("PivotTo(CFrame.new(",S)
 def test_original_source_pinned_cross_root(self):
  data=PROJ["tree"]["ServerScriptService"]
  self.assertEqual({k for k in data if k!="$className"},
      {"RareRealmCatalog","RareRealmScene","RareEncounterPolicy","RareEncounterModels",
       "RareDiscoveryBook","RareDiscoveryHUD","RareDiscoveryQAPlan","RareDiscoveryStudio"})
  for name in ("RareRealmCatalog","RareRealmScene","RareEncounterPolicy","RareEncounterModels"):
   self.assertTrue(data[name]["$path"].startswith("../P0D-WORLD-RARE-"))
 def test_negative_untrusted_on_enable_detected(self):
  def ok(s):return "ENABLE_RARE_DISCOVERY_STUDIO_BOOK = false" in s
  self.assertTrue(ok(S))
  self.assertFalse(ok(S.replace("ENABLE_RARE_DISCOVERY_STUDIO_BOOK = false",
                                "ENABLE_RARE_DISCOVERY_STUDIO_BOOK = true",1)))
 def test_negative_missing_proximity_guard_detected(self):
  def ok(s):return "Policy.MIN_INTERACTION_DISTANCE" in s
  self.assertTrue(ok(S))
  self.assertFalse(ok(S.replace("Policy.MIN_INTERACTION_DISTANCE","math.huge",1)))
if __name__=="__main__":unittest.main()
