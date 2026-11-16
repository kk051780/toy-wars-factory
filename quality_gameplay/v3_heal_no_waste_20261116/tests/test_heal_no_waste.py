import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import patch_heal_item as fix

ORIGINAL=Path("_item_original/handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116/EGGRUMBLE_FieldItemPickups.luau")
GENERATED=Path("artifacts/EGGRUMBLE_FieldItemPickups.luau")
class HealNoWasteSourceContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=ORIGINAL.read_bytes()
        cls.before=cls.raw.decode("utf-8")
        cls.after=GENERATED.read_text(encoding="utf-8")
    def test_original_source_is_exact_author_git_blob(self):
        self.assertEqual(fix.git_blob_sha(self.raw),fix.ORIGINAL_ITEM_GIT_BLOB)
    def test_no_duplicate_policy_in_original(self):
        self.assertNotIn("healUseful(",self.before)
    def test_patch_is_reproducible_and_exactly_two_additions(self):
        self.assertEqual(self.after,fix.patch(self.before))
        self.assertEqual(self.after.replace(fix.HELPER,"",1).replace(fix.CALL,"",1),self.before)
    def test_only_one_real_item_author(self):
        for token in ("function Items.start(session:any,positions:{Vector3}):()",
                      'if kind~="HEAL" and carryingEnemyEggs(player,session) then return end',
                      'interactionGuard.allow(player,part,"拾う",part.Name)',
                      "task.delay(RESPAWN_SECONDS,function()",
                      "return Items"):
            self.assertIn(token,self.after)
    def test_full_hp_rejected_before_any_resource_spending(self):
        guard=self.after.index("if not healUseful(kind,hum.Health,hum.MaxHealth) then return end")
        for downstream in ("local key=tostring(player.UserId)", "interactionGuard.allow(player,part",
                           "consumed[id]=true;lastUse[key]=now","prompt.Enabled=false"):
            self.assertLess(guard,self.after.index(downstream))
    def test_original_egg_cargo_guard_still_applies(self):
        self.assertIn('if kind~="HEAL" and carryingEnemyEggs(player,session) then return end',self.after)
    def test_original_dashed_speed_round_epoch_preserved(self):
        self.assertIn("if not matchActive() or player.Character~=buffCharacter then return end",self.after)
    def test_original_item_respawn_35_seconds_preserved(self):
        self.assertIn("local RESPAWN_SECONDS=35",self.after)
        self.assertIn("task.delay(RESPAWN_SECONDS,function()",self.after)
    def test_no_new_game_remote_store_or_reward_authority(self):
        delta=fix.HELPER+fix.CALL
        for bad in ("RemoteEvent","DataStore", "TakeDamage", "SetAsync","leaderstats", "Instance.new", "task.spawn"):
            self.assertNotIn(bad,delta)
    def test_fail_closed_when_upstream_source_changed(self):
        self.assertRaises(AssertionError,fix.patch,self.before.replace(fix.CALL_ANCHOR,"-- new anchor\n"))
        self.assertRaises(AssertionError,fix.patch,self.before+fix.HELPER)
    def test_source_remains_single_script(self):
        self.assertEqual(self.after.count("function Items.start("),1)
        self.assertEqual(self.after.count("return Items"),1)

if __name__=="__main__":unittest.main()
