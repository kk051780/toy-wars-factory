"""GQ511 original source inline: one Host, strict source blobs, rollback and field UX."""
import unittest
from select_tell import author_inline,patch,unpatch,FEATURE,REQUIRE,START,START_PATCH,FILE
HOST='''--!strict
local RoundReplay=require(script.Parent:WaitForChild("EGGRUMBLE_RoundReplay"))
local isCurrent="session.isCurrentHuman=function(player:Player):boolean"
local b="session.rules="
local roster="session.roster"
local bot="session.botActors"
local world="session.world"
local arena="TacticalBattlefield"
 BotActors.start(session,Rules)
'''
POLICY=b'''--!strict
local Policy={}
Policy.MAX_WORLD_VIEW_DISTANCE=70
Policy.POLL_SECONDS=0.3
function Policy.inArenaXZ(...) return true end
function Policy.shouldShow(...) return true end
function Policy.caption(...) return "test" end
return Policy
'''
WORLD=b'''--!strict
local Players = game:GetService("Players")
local Policy = require(script.Parent:WaitForChild("EGGRUMBLE_CarrierTellPolicy"))
local Tell={}
function Tell.start(session:any):boolean
 if session.carrierWorldTellEnabled == false then return false end
 local field=session.world:FindFirstChild("TacticalBattlefield")
 gui.AlwaysOnTop = false
 gui.MaxDistance = Policy.MAX_WORLD_VIEW_DISTANCE
 task.wait(Policy.POLL_SECONDS)
 local castle=session.rules.castles[id]
 local a=Policy.inArenaXZ(0,0,0,0,890,1050)
 local b=Policy.shouldShow("ACTIVE",nil,castle,true)
 return true
end
return Tell
'''
# Unit marker tests must never pretend these fixtures match immutable author Git blob;
# they only test the reversible Host patch logic using a clearly fake inline specimen.
INLINE='local CarrierWorldTell=(function()\nlocal Policy={}\nlocal Tell={}\nreturn Tell\nend)()\n'
class TestOriginalTell(unittest.TestCase):
 def test_single_host_off_exact(self):
  after=patch(HOST,INLINE)
  self.assertEqual(unpatch(after,INLINE),HOST)
  self.assertEqual(after.count("CarrierWorldTell.start(session)"),1)
 def test_double_selection_fails_closed(self):
  with self.assertRaisesRegex(ValueError,"RED_GQ511_ALREADY_SELECTED"):
   patch(patch(HOST,INLINE),INLINE)
 def test_missing_lifecycle_anchor_fails_closed(self):
  with self.assertRaisesRegex(ValueError,"RED_GQ511_HOST_ANCHOR"):
   patch(HOST.replace(START,"NoBots.start(session,Rules)"),INLINE)
 def test_missing_roster_fails_closed(self):
  with self.assertRaisesRegex(ValueError,"RED_GQ511_MISSING_CURRENT_SESSION_DEP"):
   patch(HOST.replace("session.roster","not_a_roster"),INLINE)
 def test_source_class(self):self.assertTrue(FILE.endswith(".server.luau"))
 def test_one_new_start_call_only(self):
  self.assertEqual(START_PATCH.count("CarrierWorldTell.start(session)"),1)
 def test_strict_exact_original_author_policy(self):
  with self.assertRaisesRegex(ValueError,"RED_GQ511_ORIGINAL_POLICY_BLOB_CHANGED"):
   author_inline(POLICY,WORLD)
 def test_no_remote_coin_damage_authority(self):
  self.assertNotIn("RemoteEvent",INLINE)
  self.assertNotIn("DataStore",INLINE)
  self.assertNotIn("TakeDamage",INLINE)
 def test_existing_hit_chain_preserved(self):
  sample=HOST+'local currentHit="GQ81_CONFIRMED_HIT_042_V3_PORT"\n'
  self.assertIn("GQ81_CONFIRMED_HIT_042_V3_PORT",unpatch(patch(sample,INLINE),INLINE))
if __name__=="__main__":unittest.main()
