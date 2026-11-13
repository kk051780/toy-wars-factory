"""Run the real Lua-compatible reward policy with Lua 5.4 via lupa.
NOT a Roblox/Luau native compiler or Studio 2-client test.
Requires: pip install lupa
"""
from pathlib import Path
import unittest
from lupa import LuaRuntime

SOURCE = Path(__file__).resolve().parents[1] / "src" / "RewardEquipRules.luau"

class RewardPolicyTests(unittest.TestCase):
    def setUp(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.r = self.lua.execute(SOURCE.read_text(encoding="utf-8"))
        self.s = self.r.new()
        self.assertTrue(self.r.enroll(self.s, 10))
        self.assertTrue(self.r.enroll(self.s, 20))
        self.assertTrue(self.r.startRound(self.s, 1))

    def finish(self, special=False):
        return self.r.finishRound(
            self.s, 1,
            self.lua.table_from({10: True, 20: True}),
            self.lua.table_from({10: special})
        )

    def test_basic_free_reward_and_discovery(self):
        self.assertTrue(self.finish())
        self.assertEqual(self.r.claimFreeHatch(self.s, 10, 1, 200),
                         (True, "forest_scout", "GRANTED"))
        record = self.r.export(self.s, 10)
        self.assertEqual(record["owned"]["forest_scout"], 1)
        self.assertTrue(record["discovered"]["forest_scout"])

    def test_rare_threshold_normal(self):
        self.finish()
        self.assertEqual(self.r.claimFreeHatch(self.s, 10, 1, 50)[1], "star_scout")
        self.assertEqual(self.r.claimFreeHatch(self.s, 20, 1, 51)[1], "forest_scout")

    def test_phantom_threshold(self):
        self.finish(True)
        self.assertEqual(self.r.claimFreeHatch(self.s, 10, 1, 500)[1], "star_scout")
        self.assertEqual(self.r.claimFreeHatch(self.s, 20, 1, 500)[1], "forest_scout")

    def test_idempotent_same_epoch_despite_reroll(self):
        self.finish()
        before = self.r.claimFreeHatch(self.s, 10, 1, 1)
        after = self.r.claimFreeHatch(self.s, 10, 1, 9999)
        self.assertEqual(before[1], after[1])
        self.assertEqual(after[2], "ALREADY_GRANTED")
        self.assertEqual(self.r.export(self.s, 10)["owned"]["star_scout"], 1)

    def test_ineligible_and_old_epoch(self):
        self.finish()
        self.assertEqual(self.r.claimFreeHatch(self.s, 10, 2, 1)[1], "NOT_ELIGIBLE")
        self.assertEqual(self.r.claimFreeHatch(self.s, 999, 1, 1)[1], "NOT_ENROLLED")

    def test_invalid_roll_rejected_without_receipt(self):
        self.finish()
        for roll in (0, 10001, 2.5, "20", None):
            self.assertEqual(self.r.claimFreeHatch(self.s, 10, 1, roll)[1],
                             "INVALID_SERVER_ROLL")
        self.assertIsNone(self.r.export(self.s, 10)["receipts"][1])

    def test_basic_starter_owned_without_purchase(self):
        self.assertEqual(self.r.export(self.s, 10)["owned"]["starter_scout"], 1)
        self.assertEqual(self.r.export(self.s, 10)["equipped"], "starter_scout")

    def test_unowned_and_invalid_class_cannot_equip(self):
        self.assertEqual(self.r.equip(self.s, 10, "star_scout", "MAGE")[1], "LOBBY_ONLY")
        self.finish()
        self.assertEqual(self.r.equip(self.s, 10, "star_scout", "MAGE")[1], "NOT_OWNED")
        self.assertEqual(self.r.equip(self.s, 10, "starter_scout", "ADMIN")[1], "UNKNOWN_CLASS")
        self.assertTrue(self.r.equip(self.s, 10, "starter_scout", "NINJA"))

    def test_equipped_after_hatch_is_real_ability_permission(self):
        self.finish(True)
        self.r.claimFreeHatch(self.s, 10, 1, 100)
        self.assertTrue(self.r.equip(self.s, 10, "star_scout", "BEASTMASTER"))
        self.assertTrue(self.r.startRound(self.s, 2))
        success, token = self.r.requestScout(self.s, 10, 2, 0)
        self.assertTrue(success)
        self.assertEqual(token["ability"], "SCOUT")
        self.assertEqual(token["cosmetic"], "star")
        self.assertEqual(token["duration"], 5)
        self.assertEqual(token["cooldown"], 18)

    def test_cooldown_blocks_spam_and_old_epoch(self):
        ok,token = self.r.requestScout(self.s, 10, 1, 0)
        self.assertTrue(ok)
        self.assertEqual(self.r.requestScout(self.s, 10, 1, 5)[1], "COOLDOWN")
        self.assertEqual(self.r.requestScout(self.s, 10, 0, 18)[1], "STALE_ROUND")
        self.assertTrue(self.r.requestScout(self.s, 10, 1, 18)[0])

    def test_lobby_prevents_ability_and_round_overlap(self):
        self.finish()
        self.assertEqual(self.r.requestScout(self.s, 10, 1, 30)[1], "STALE_ROUND")
        self.assertEqual(self.r.finishRound(self.s, 1, self.lua.table(), self.lua.table())[1],
                         "ROUND_NOT_ACTIVE")
        self.assertTrue(self.r.startRound(self.s, 2))
        self.assertEqual(self.r.startRound(self.s, 2)[1], "INVALID_EPOCH")

    def test_save_restore_owned_and_receipt(self):
        self.finish()
        self.r.claimFreeHatch(self.s, 10, 1, 1)
        self.r.equip(self.s, 10, "star_scout", "WARRIOR")
        saved=self.r.export(self.s, 10)
        s2=self.r.new()
        self.assertTrue(self.r.restore(s2, 10, saved))
        saved2=self.r.export(s2, 10)
        self.assertEqual(saved2["equipped"], "star_scout")
        self.assertEqual(saved2["receipts"][1], "star_scout")
        self.assertEqual(saved2["owned"]["star_scout"], 1)

    def test_forbid_forged_save_items(self):
        s2=self.r.new()
        record=self.lua.table_from({"owned":self.lua.table_from({"admin_dragon":1}),
                                    "receipts":self.lua.table()})
        self.assertEqual(self.r.restore(s2, 10, record)[1], "INVALID_SAVE")

    def test_forbid_corrupt_receipt_and_inventory(self):
        s2=self.r.new()
        record=self.lua.table_from({"owned":self.lua.table_from({"star_scout":-1}),
                                    "receipts":self.lua.table()})
        self.assertEqual(self.r.restore(s2, 10, record)[1], "INVALID_SAVE")
        record=self.lua.table_from({"owned":self.lua.table_from({"star_scout":1}),
                                    "receipts":self.lua.table_from({-1:"star_scout"})})
        self.assertEqual(self.r.restore(s2, 10, record)[1], "INVALID_SAVE")

    def test_invalid_snapshot_atomic(self):
        self.assertEqual(self.r.finishRound(self.s, 1,
            self.lua.table_from({0:True}), self.lua.table())[1], "INVALID_SNAPSHOT")
        self.assertEqual(self.s["phase"], "ACTIVE")
        self.assertIsNone(self.s["rounds"][1])

    def test_invalid_time_rejected(self):
        for t in (-1,1.25,"100"):
            self.assertEqual(self.r.requestScout(self.s,10,1,t)[1],"INVALID_TIME")

if __name__ == "__main__":
    unittest.main(verbosity=2)
