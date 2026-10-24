"""Static regression for server-authoritative toy selector prompts.

This is NOT Roblox Studio or network penetration-test evidence.
"""
import re
import unittest
from pathlib import Path

SERVER = (Path(__file__).resolve().parents[1] / "src/ToyWarsServer.server.lua").read_text(encoding="utf-8")
SELECTORS = SERVER.split('local choices = {{"pon", x+8}', 1)[1].split('local station = part(', 1)[0]


class SelectorAuthorityTests(unittest.TestCase):
    def test_actor_identity_and_active_session_checked(self):
        self.assertIn("if actor ~= player or not state.active then return end", SELECTORS)

    def test_prompt_distance_is_validated_on_server(self):
        self.assertRegex(
            SELECTORS,
            r'root=character and character:FindFirstChild\("HumanoidRootPart"\)',
        )
        self.assertIn(
            "if not root or (root.Position-pad.Position).Magnitude > 13 then return end",
            SELECTORS,
        )

    def test_validation_precedes_selection_mutation(self):
        self.assertLess(SELECTORS.index("if actor ~= player"), SELECTORS.index("state.selected=id"))
        self.assertLess(SELECTORS.index("(root.Position-pad.Position).Magnitude"), SELECTORS.index("state.selected=id"))

    def test_remote_selection_still_checks_unit_and_rate(self):
        remote = SERVER.split("selectEvent.OnServerEvent:Connect(", 1)[1]
        self.assertIn("if not B.isUnit(selected) then return end", remote)
        self.assertIn("state.lastSelection=os.clock()", remote)


if __name__ == "__main__":
    unittest.main()
