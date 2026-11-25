"""Mutation and rollback tests for the nonoverlapping GQ8 V3 role admission."""
import unittest

from select_role_ready import (
    FEATURE, JOIN, JOIN_PATCH, ROLE, ROLE_PATCH, PROMPTS, apply, revert,
)


def fixture():
    return (
        "local chosenRole:{[number]:string}={}\n"
        "local queueEpoch:{[string]:number}={}\n"
        "-- GQ646_LOBBY_SAFE_SPAWN_BEGIN\n"
        + JOIN
        + " joined[p.UserId]=mode\n"
        + " task.delay(COUNTDOWN,function() end)\n"
        + "end\n"
        + ROLE
        + "\n"
        + 'prompt(gateTeam,"参加する","チーム戦（再操作で解除）",function(p) joinQueue("TEAM",p) end)\n'
        + 'prompt(gateBR,"参加する","BR戦（再操作で解除）",function(p) joinQueue("BATTLE_ROYALE",p) end)\n'
    )


class RoleAckTests(unittest.TestCase):
    def test_real_change_is_one_host_and_byte_exact_off(self):
        before = fixture()
        after = apply(before)
        self.assertNotEqual(before, after)
        self.assertEqual(before, revert(after))
        self.assertTrue(FEATURE.startswith("GQ8_"))
        self.assertIn(JOIN_PATCH, after)
        self.assertIn(ROLE_PATCH, after)

    def test_both_mode_prompts_explain_role_selection(self):
        after = apply(fixture())
        for before, replacement in PROMPTS:
            self.assertNotIn(before, after)
            self.assertIn(replacement, after)

    def test_explicit_selection_guard_before_queue_mutation(self):
        after = apply(fixture())
        self.assertLess(after.index('if chosenRole[p.UserId]==nil then'),
                        after.index('joined[p.UserId]=mode'))
        self.assertIn('p:SetAttribute("EGGRUMBLE_RoleSelectionRequired",true)', after)
        self.assertIn('p:SetAttribute("EGGRUMBLE_RoleSelectionRequired",nil)', after)
        self.assertNotIn('Instance.new("ScreenGui")', after)

    def test_no_duplicate_apply(self):
        with self.assertRaisesRegex(ValueError, "DUPLICATE"):
            apply(apply(fixture()))

    def test_missing_prior_safe_lobby_is_red(self):
        with self.assertRaisesRegex(ValueError, "SAFE_LOBBY"):
            apply(fixture().replace("-- GQ646_LOBBY_SAFE_SPAWN_BEGIN", "-- missing"))

    def test_missing_role_owner_is_red(self):
        with self.assertRaisesRegex(ValueError, "ROLE_AND_QUEUE"):
            apply(fixture().replace("local chosenRole:", "local notChosenRole:"))

    def test_join_anchor_drift_is_red(self):
        with self.assertRaisesRegex(ValueError, "ANCHOR"):
            apply(fixture().replace(" if sessions[mode] then return end", " if false then return end"))

    def test_gate_prompt_drift_is_red(self):
        with self.assertRaisesRegex(ValueError, "MODE_GATE"):
            apply(fixture().replace("BR戦（再操作で解除）", "別の文字"))

    def test_modified_patch_not_reversible_is_red(self):
        altered = apply(fixture()).replace(
            'p:SetAttribute("EGGRUMBLE_RoleSelectionRequired",true)',
            'p:SetAttribute("EGGRUMBLE_RoleSelectionRequired",false)',
        )
        with self.assertRaisesRegex(ValueError, "REVERSION_DRIFT"):
            revert(altered)

    def test_original_queue_timer_count_preserved(self):
        original = fixture()
        after = apply(original)
        self.assertEqual(original.count("task.delay(COUNTDOWN,"), after.count("task.delay(COUNTDOWN,"))


if __name__ == "__main__":
    unittest.main()
