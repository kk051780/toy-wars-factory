"""Offline source-integrity gate for the full S1 lobby-deadlock patch.
Run: python -m unittest discover -s tests -p 'test_*.py' -v
Does not simulate Roblox gameplay or compile Luau.
"""
import hashlib, json, pathlib, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
def sha(b):return hashlib.sha256(b).hexdigest()
class SourceContract(unittest.TestCase):
 def test_package_hashes(self):
  m=json.loads((ROOT/"BUILD_MANIFEST.json").read_text(encoding="utf8"))
  self.assertEqual(set(m),{"format","game_id","work_id","packet_id","public_source_allowed","files"})
  self.assertEqual(m["format"],"P0D_PUBLIC_SOURCE_V1")
  for x in m["files"]:
   b=(ROOT/x["path"]).read_bytes();self.assertEqual(len(b),x["size"]);self.assertEqual(sha(b),x["sha256"])
 def test_patched_full_game_hash(self):
  p=json.loads((ROOT/"docs/FULL_SOURCE_DIFF_PROOF.json").read_text(encoding="utf8"))
  self.assertEqual(sha((ROOT/"src/server/Game.server.luau").read_bytes()),p["patched_game_sha256"])
  self.assertEqual(sha((ROOT/"src/server/LobbyTeamRecovery.luau").read_bytes()),p["original_planner_sha256"])
 def test_single_authority_structural(self):
  s=(ROOT/"src/server/Game.server.luau").read_text(encoding="utf8")
  for needle in ["local match = {",'Instance.new("RemoteEvent")',"local function tickRound()","local function rebalanceLobbyTeams()",'        rebalanceLobbyTeams()']:
   self.assertEqual(s.count(needle),1,needle)
  self.assertIn('if match.phase ~= "LOBBY" then return end',s)
  self.assertIn('count < Config.MinPlayers or teamCount("RED") == 0 or teamCount("BLUE") == 0',s)
if __name__=="__main__":unittest.main()
