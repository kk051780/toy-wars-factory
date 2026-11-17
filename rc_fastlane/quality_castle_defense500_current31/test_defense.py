"""Source rollback and original castle defense no duplicate server authority."""
import unittest
from select_defense import patch,undo,inline,HOST_REQUIRE,BOT_START,CLOSE_ANCHOR,FEATURE
SAMPLE='''--!strict
local BotActors=require(script.Parent:WaitForChild("EGGRUMBLE_BotActors"))
local obj = "session.castleLocations / session.castleModels / Rules.loadDefense("
session.closeRound=function(abandoned:boolean?)
 if session.world.Parent then session.world:Destroy() end
end
 BotActors.start(session,Rules)
'''
BODY='local CastleDefense=(function()\nlocal Policy={}\nlocal Defense={}\nreturn Defense\nend)()\n'
class TestAuthorDefense(unittest.TestCase):
 def test_source_exact_inverse(self):
  self.assertEqual(undo(patch(SAMPLE,BODY),BODY),SAMPLE)
 def test_double_prevented(self):
  with self.assertRaisesRegex(ValueError,"ALREADY_SELECTED"):patch(patch(SAMPLE,BODY),BODY)
 def test_host_requires_bots(self):
  with self.assertRaisesRegex(ValueError,"MISSING_HOST_ANCHOR"):patch(SAMPLE.replace("Rules.loadDefense(","NO_RULES("),BODY)
 def test_cleanup_never_omitted(self):
  after=patch(SAMPLE,BODY)
  self.assertEqual(after.count("session.castleDefenseStop()"),2)
 def test_start_once_only(self):
  self.assertEqual(patch(SAMPLE,BODY).count("CastleDefense.start(session)"),1)
 def test_guarded_optional_failure(self):
  self.assertIn("local defenseOK,defenseError=pcall",patch(SAMPLE,BODY))
 def test_original_author_pinned(self):
  with self.assertRaisesRegex(ValueError,"ORIGINAL_POLICY_BLOB_CHANGED"):
   inline(b"--!strict\nlocal Policy={}\nreturn Policy\n",b"bad")
 def test_no_host_replacement(self):
  self.assertIn(BOT_START,undo(patch(SAMPLE,BODY),BODY))
  self.assertIn(CLOSE_ANCHOR,undo(patch(SAMPLE,BODY),BODY))
if __name__=="__main__":unittest.main()
