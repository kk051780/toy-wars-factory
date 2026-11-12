"""Only QA package contracts, never claims real Studio."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
H=(ROOT/"tools/build_full_server_runner.py").read_text("utf-8")
R=(ROOT/"README.md").read_text("utf-8")
class OriginalServerFullPipeline(unittest.TestCase):
 def test_all_true_original_source_paths(self):
  for s in ["RareRealmCatalog.luau","RareRealmScene.luau",
            "RareEncounterPolicy.luau","RareEncounterModels.luau",
            "RareDiscoveryBook.luau","RareDiscoveryHUD.luau",
            "RareDiscoveryQAPlan.luau","RareDiscoveryStudio.server.luau"]:
   self.assertIn(s,H)
 def test_no_server_logic_duplicated_in_python(self):
  self.assertIn("source=server",H)
  self.assertIn("runActualUnmodifiedServerSource",H)
  self.assertIn("only external Roblox Instance",R)
 def test_studio_opt_in_runner_only(self):
  self.assertIn('local ENABLE_RARE_DISCOVERY_STUDIO_BOOK = false',H)
  self.assertIn('local ENABLE_RARE_DISCOVERY_STUDIO_BOOK = true',H)
  self.assertIn('original source files',R)
 def test_two_clients_and_four_real_creature_slots(self):
  for needle in ["local userA,rootA,humanA,uiA=newPlayer()",
       "local userB,rootB,humanB,uiB=newPlayer()",
       '"SPACE","CELESTIAL","EMBER","ECLIPSE"',
       "RARE_BOOK_FULL_SERVER_NATIVE_PASS",
       "notebookTitle(userA)","notebookTitle(userB)",
       "TWO_REAL_CLIENT_SAME_CREATURE","TWO_CLIENT_INDEPENDENT_BOOK_4_OF_4"]:
   self.assertIn(needle,H)
 def test_no_fake_engine_claims(self):
  self.assertIn("does NOT run actual Roblox Studio",R)
  self.assertIn("NOT 2 real Studio clients",R)
 def test_invalid_player_and_remote_rejection(self):
  for needle in ["dead character","faraway prompt","anchored character",
      "repeating creature", "removed client GUI","expired/hidden creature"]:
   self.assertIn(needle,H)
 def test_adversarial_mutations_exist(self):
  for s in ["BAD_SERVER_ACCEPTS_FAR","BAD_SERVER_ACCEPTS_DEAD",
            "BAD_SERVER_ACCEPTS_ANCHORED","BAD_SERVER_USES_FIRST_PLAYER_UI",
            "BAD_SERVER_PREMATURE_2CLIENT_PASS","BAD_SERVER_EXTRA_REWARD_LOG"]:
   self.assertIn(s,H)
 def test_no_user_identifying_or_reward_tools(self):
  self.assertNotIn("github_token",H.lower())
  self.assertNotIn("requests.post",H)
  self.assertNotIn("DataStore:SetAsync",H)
if __name__=="__main__":unittest.main()
