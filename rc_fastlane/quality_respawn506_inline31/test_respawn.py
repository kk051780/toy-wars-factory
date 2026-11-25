"""GQ506 original R13 existing Host integration: inverse, one authority, ticket security."""
from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
from select_respawn import orig,patch,unpatch,addition,blob,AUTHOR_BLOB,MARK

AUTHOR=Path("_gq506_original/handoffs/P0D-GQ-RESPAWN-GRACE-20261116-R13/EGGRUMBLE_RespawnGrace.server.luau")
BASE='''--!strict
local Players=game:GetService("Players")
local WORLD_NAME="EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW"
-- GQ8_HUMAN_SIEGE_PACING_BEGIN
local check="or session.isCurrentHuman(p)~=true then return end"
session.isCurrentHuman(p)
'''
class RespawnSelected(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.source=orig(AUTHOR)
 def test_01_pin_exact_source(self):
  self.assertEqual(blob(AUTHOR.read_bytes()),AUTHOR_BLOB)
 def test_02_host_single_scoped_append(self):
  changed=patch(BASE,self.source)
  self.assertEqual(changed,BASE+addition(self.source))
  self.assertEqual(unpatch(changed,self.source),BASE)
 def test_03_cannot_install_twice(self):
  with self.assertRaisesRegex(ValueError,"ALREADY_PRESENT"):patch(patch(BASE,self.source),self.source)
 def test_04_preserve_existing_cas_match_guard(self):
  with self.assertRaisesRegex(ValueError,"EXISTING_HOST_GUARD_LOST"):
   patch(BASE.replace("session.isCurrentHuman","session.isPastHuman"),self.source)
 def test_05_strict_single_source_marker(self):
  s=patch(BASE,self.source)
  self.assertEqual(s.count(MARK),1)
  self.assertEqual(s.count('Instance.new("ForceField")'),1)
 def test_06_real_died_ticket(self):
  for name in ("humanoid.Died:Connect(function()","tickets[player] = {",
               "if not ticket or os.clock() > ticket.expiresAt then return end",
               "currentArena(player, character) ~= ticket.arena"):
   self.assertIn(name,self.source)
 def test_07_transient_and_cancel_before_attacks(self):
  for name in ("local GRACE_SECONDS = 2.25", "if instance:IsA(\"Tool\") then revoke() end",
               "ProximityPromptService.PromptTriggered:Connect",
               "task.delay(GRACE_SECONDS, revoke)"):
   self.assertIn(name,self.source)
 def test_08_no_lobby_or_wrong_team(self):
  for name in ('"EGGRUMBLE_Eliminated"', 'mode ~= "TEAM" and mode ~= "BATTLE_ROYALE"',
               "MAX_HOME_DISTANCE = 85", "FALLEN_CORE_COLOR"):
   self.assertIn(name,self.source)
 def test_09_no_new_game_authority(self):
  for name in ("RemoteEvent","FireServer(","InvokeServer(","DataStore","TakeDamage(","MarketplaceService"):
   self.assertNotIn(name,self.source)
 def test_10_roll_back_rejects_malformed(self):
  altered=patch(BASE,self.source).replace("RESPAWN_TICKET_SECONDS = 12","RESPAWN_TICKET_SECONDS = 15",1)
  with self.assertRaisesRegex(ValueError,"OFF_SCOPE_DRIFT"):unpatch(altered,self.source)
if __name__=="__main__":unittest.main()
