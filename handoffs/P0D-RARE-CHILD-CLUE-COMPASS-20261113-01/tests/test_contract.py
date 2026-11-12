"""Kid-friendly source safety, original-source deltas and no fake Studio claims."""
from pathlib import Path
import json,sys,unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from verify_candidate_delta import verify as delta
C=(ROOT/"src/RareCluePolicy.luau").read_text("utf-8")
H=(ROOT/"src/RareClueHUD.luau").read_text("utf-8")
S=(ROOT/"src/RareDiscoveryCluePreview.server.luau").read_text("utf-8")
P=json.loads((ROOT/"default.project.json").read_text("utf-8"))
D=json.loads((ROOT/"docs/DiscoveryUXExperiment.json").read_text("utf-8"))
class ChildClueSource(unittest.TestCase):
 def test_exact_original_source_delta_only(self):
  self.assertEqual(delta(),4)
 def test_four_world_hints_and_actual_static_names(self):
  for id in ("SPACE","CELESTIAL","EMBER","ECLIPSE"):
   self.assertIn(id,C)
  self.assertIn("Clue.WORLD",C)
  self.assertIn("Book.NAMES[id]",C)
  self.assertIn("WORLD",C)
  self.assertIn("TEST_HUB",C)
 def test_nonproduction_hub_vs_world_truth(self):
  self.assertIn('Clue.STUDIO_HUB = "テスト: みどりの ひろばで そらをみよう"',C)
  self.assertIn('HintHUD.MODE = "TEST_HUB"',H)
  self.assertNotIn('HintHUD.MODE = "WORLD"',H)
 def test_no_daily_pressure_and_false_money(self):
  for t in (C,H,S):
   executable="\\n".join(line.split("--",1)[0] for line in t.splitlines())
   for forbidden in ("MarketplaceService","DataStoreService","RemoteEvent",
     "OnServerEvent","FireServer","Pay Robux","GamePass","dailyStreak",
     "awardCoins","leaderstats","workspace.Gravity","Humanoid:TakeDamage"):
    self.assertNotIn(forbidden,executable)
  self.assertIn("べつの みちも あるいてみよう",C)
  self.assertNotIn("まいにち",C)
  self.assertNotIn("コイン100",C)
 def test_only_one_hint_row(self):
  self.assertIn('panel:FindFirstChild("NextGentleClue")',H)
  self.assertIn("if not existing then",H)
  self.assertIn("clue.TextScaled=true",H)
  self.assertIn("clue.TextWrapped=true",H)
  self.assertIn("UDim2.fromOffset(222,244)",H)
  self.assertIn("Clue.next(book,HintHUD.MODE)",H)
 def test_server_ui_and_disabled_start(self):
  self.assertIn("ENABLE_RARE_DISCOVERY_STUDIO_BOOK = false",S)
  self.assertIn("RunService:IsStudio()",S)
  self.assertIn("RunService:IsServer()",S)
  self.assertIn('FindFirstChild("TRAP_RAIDERS_S1")',S)
  self.assertIn("ClueHUD.mount(player,books[player])",S)
  self.assertIn("ClueHUD.update(player,nextBook)",S)
  self.assertIn("Clue.validate()",S)
 def test_ten_scripts_previous_seven_unmodified(self):
  tree=P["tree"]["ServerScriptService"]
  self.assertEqual(len([k for k in tree if k!="$className"]),10)
  for k in ("RareRealmCatalog","RareRealmScene","RareEncounterModels",
      "RareEncounterPolicy","RareDiscoveryBook","RareDiscoveryHUD","RareDiscoveryQAPlan"):
   self.assertTrue(tree[k]["$path"].startswith("../P0D-"))
  self.assertEqual(tree["RareDiscoveryCluePreview"]["$path"],
      "src/RareDiscoveryCluePreview.server.luau")
 def test_truthful_product_hypotheses(self):
  self.assertEqual(D["status"],"S2PLUS_SOURCE_ONLY")
  self.assertEqual(D["hypothesis"]["observed"],"NOT_TESTED")
  self.assertEqual(D["safety"]["money_purchases_dailies"],"DISALLOWED")
  self.assertEqual(D["safety"]["real_Studio_two_client_mobile"],"NOT_TESTED")
  self.assertFalse(D["user_visible_features"][0]["reward"]!="NONE")
 def test_native_tool_reuses_original_server(self):
  body=(ROOT/"tools/build_native_clue_runner.py").read_text("utf-8")
  self.assertIn("P0D-RARE-BOOK-FULL-SERVER-QA",body)
  self.assertIn("base.TESTS",body)
  self.assertIn("TRIAL_SERVER",body)
  self.assertIn('BAD_SERVER_HINT_WRONG_PLAYER',body)
 def test_negative_hub_hint_mutant(self):
  self.assertIn("テスト: みどりの ひろば",C)
  self.assertNotIn("テスト: あかい おしろ",C)
 def test_negative_hud_compulsion_mutant(self):
  self.assertIn("4/4！みつけたね。",C)
  self.assertNotIn("きえちゃうよ",C)
if __name__=="__main__":unittest.main()
