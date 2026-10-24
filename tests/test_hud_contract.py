"""Offline contract checks for HUD pricing/roster drift; not a Roblox UI test."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HUD = (ROOT / "src/ToyWarsHUD.client.lua").read_text(encoding="utf-8")
CHARACTERS = json.loads((ROOT / "config/characters.json").read_text(encoding="utf-8"))["characters"]


class HUDContractTests(unittest.TestCase):
    def test_hud_imports_shared_balance(self):
        self.assertIn('require(ReplicatedStorage:WaitForChild("ToyWarsBalance"))', HUD)

    def test_hud_selection_matches_canonical_roster(self):
        section = HUD.split("local choices=", 1)[1].split("for i,spec in ipairs(choices)", 1)[0]
        choices = re.findall(r'\{"([^"]+)","([^"]+)",Color3\.fromRGB', section)
        self.assertEqual(choices, [(u["id"], u["id"].upper()) for u in CHARACTERS])

    def test_hud_price_comes_from_balance_not_stale_literals(self):
        self.assertIn(
            'button.Text=string.format("%s | %d",spec[2],B.UNITS[spec[1]].cost)',
            HUD,
        )
        self.assertNotRegex(HUD, r'\b(?:PON|GUARDON|TANKURU)\s*\|\s*\d+')


if __name__ == "__main__":
    unittest.main()
