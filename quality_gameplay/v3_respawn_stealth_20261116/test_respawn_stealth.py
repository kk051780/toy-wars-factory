"""Source-exact regression for an Assassin's stealth ending when their old avatar dies.

This is NOT a Roblox engine / Studio / Android pass.  It checks the actual
existing V3 server Host and BotActors without adding a second game authority.
"""
from pathlib import Path
import subprocess
import unittest

BASE_SHA = "6b52eaf1f2725496277998fe0c5532b7a8fcaab5"
ROOT = Path(__file__).resolve().parents[2]
DIR = "handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116"
HOST = f"{DIR}/EGGRUMBLE_LobbyCastleModesPreview.server.luau"
BOT = f"{DIR}/EGGRUMBLE_BotActors.luau"
ORIGINAL = '      if castle and castle.alive then SevenRoleCombat.equip(session,p,role) end'
REPLACEMENT = """      if castle and castle.alive then
       -- New life must never inherit the previous avatar's Assassin stealth window.
       -- BotActors reads this Player attribute before its server-side damage.
       p:SetAttribute("EGGRUMBLE_StealthUntil",nil)
       SevenRoleCombat.equip(session,p,role)
      end"""


def fenced(source: str) -> bool:
    """One exact, session-guarded respawn callback; no unconditional stealth clear."""
    anchor = 'p.CharacterAdded:Connect(function(character)'
    begin = source.find(anchor)
    if begin == -1 or source.find(anchor, begin + 1) != -1:
        return False
    block = source[begin:begin + 1000]
    needles = [
        'p.Character==character',
        'session.rules.phase=="ACTIVE"',
        'local castle=session.rules.castles[tostring(p.UserId)]',
        'if castle and castle.alive then',
        'p:SetAttribute("EGGRUMBLE_StealthUntil",nil)',
        'SevenRoleCombat.equip(session,p,role)',
    ]
    positions = [block.find(k) for k in needles]
    return all(i >= 0 for i in positions) and positions == sorted(positions)


class RespawnStealthSourceContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.host = (ROOT / HOST).read_text(encoding="utf-8")
        cls.bot = (ROOT / BOT).read_text(encoding="utf-8")
        cls.original = subprocess.check_output(
            ["git", "show", f"{BASE_SHA}:{HOST}"], cwd=ROOT, text=True
        )

    def test_original_exact_byte_rollback(self):
        self.assertEqual(self.host.count(REPLACEMENT), 1)
        self.assertEqual(self.host.replace(REPLACEMENT, ORIGINAL), self.original)

    def test_new_avatar_only_and_active_home_castle(self):
        self.assertTrue(fenced(self.host))

    def test_real_bot_hit_uses_stealth(self):
        self.assertIn('player:GetAttribute("EGGRUMBLE_StealthUntil")', self.bot)
        self.assertIn("h.Health>0", self.bot)
        self.assertIn("BOT_HERO_DAMAGE", self.bot)

    def test_negative_missing_cleanup_does_not_pass(self):
        self.assertFalse(fenced(self.host.replace(
            '       p:SetAttribute("EGGRUMBLE_StealthUntil",nil)\n', ""
        )))

    def test_negative_cleanup_outside_live_character_guard_does_not_pass(self):
        # Simulates putting the clear before the current avatar and active-phase checks.
        modified = self.host.replace(
            '       p:SetAttribute("EGGRUMBLE_StealthUntil",nil)\n', "", 1
        ).replace(
            '     task.delay(.8,function()\n',
            '     p:SetAttribute("EGGRUMBLE_StealthUntil",nil)\n     task.delay(.8,function()\n',
            1,
        )
        self.assertFalse(fenced(modified))


if __name__ == "__main__":
    unittest.main()
