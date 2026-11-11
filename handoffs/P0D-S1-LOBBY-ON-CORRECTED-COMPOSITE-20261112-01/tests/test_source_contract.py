"""Source-package consistency checks; run after checkout of THIS fixed handoff.
This test is deliberately source-only and not a Roblox Luau parser.
"""
import unittest,hashlib,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
def sh(p):return hashlib.sha256(p.read_bytes()).hexdigest()
class SourceContract(unittest.TestCase):
 def test_manifest_exact_schema(self):
  m=json.loads((ROOT/"BUILD_MANIFEST.json").read_text(encoding="utf8"))
  self.assertEqual(set(m),{"format","game_id","work_id","packet_id","public_source_allowed","files"})
  self.assertEqual(m["format"],"P0D_PUBLIC_SOURCE_V1")
  self.assertEqual(m["game_id"],"TRAP_RAIDERS")
  self.assertEqual(m["work_id"],"p0d-siege-v19")
  self.assertEqual(len(m["files"]),6)
  for f in m["files"]:
   p=(ROOT/f["path"]).resolve()
   self.assertTrue(p.is_relative_to(ROOT.resolve()))
   self.assertEqual(p.stat().st_size,f["size"])
   self.assertEqual(sh(p),f["sha256"])
 def test_source_bytes_fixed(self):
  proof=json.loads((ROOT/"docs/SOURCE_PROOF.json").read_text(encoding="utf8"))
  self.assertEqual(sh(ROOT/"src/server/Game.server.luau"),proof["patched_game_sha256"])
  self.assertEqual(sh(ROOT/"src/server/LobbyTeamRecovery.luau"),proof["exact_planner_sha256"])
 def test_single_game_authority_and_boss_hooks(self):
  src=(ROOT/"src/server/Game.server.luau").read_text(encoding="utf8")
  for mark in ('local match = {','Instance.new("RemoteEvent")','local function tickRound()','local function rebalanceLobbyTeams()','        rebalanceLobbyTeams()','local CanonicalHost = require(','local BossBinding = require('):
   self.assertEqual(src.count(mark),1,mark)
  self.assertIn('if match.phase ~= "LOBBY" then return end',src)
  self.assertIn('teamCount("RED") == 0 or teamCount("BLUE") == 0',src)
 def test_source_guards(self):
  proof=json.loads((ROOT/"docs/SOURCE_PROOF.json").read_text(encoding="utf8"))
  self.assertTrue(proof["reverse_transform_bitwise_identical"])
  self.assertEqual(len(proof["only_four_changes"]),4)
  self.assertTrue(all(proof["source_guards"].values()))
if __name__=="__main__":unittest.main()
