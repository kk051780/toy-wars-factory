"""EGGRUMBLE V3 carried egg drop source integration contract.

Reviewable static/integration-wiring checks and deliberate mutated negatives.
These do NOT substitute for actual native Luau Game or Studio / Android runtime.
"""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]


def inspect(preview: str, bot: str, rules: str) -> list[str]:
    issues=[]
    required={
        "RULE_STOCK": 'm.fieldEggs+=dropped' in rules and 'c.heldEggs=0' in rules,
        "IDEMPOTENT": 'carrier.heldEggs<=0 then return 0' in preview,
        "ACTIVE_ONLY": 'session.rules.phase~="ACTIVE" then return 0' in preview,
        "AUTHORITATIVE_DROP": 'Rules.onCarrierEliminated(session.rules,ownerId)' in preview,
        "PHYSICAL_DROP": ('local dropped,dropIds=Rules.onCarrierEliminated(session.rules,ownerId)' in preview
                          and 'session.releaseEggs(ownerId,landing,dropIds)' in preview
                          and 'Rules.takeFieldEgg(session.rules,tostring(p.UserId),eggId)' in preview),
        "HUMAN_DIED": 'humanoid.Died:Connect(function()' in preview,
        "RESPAWN_HOOK": 'player.CharacterAdded:Connect(bindCarrierLife)' in preview,
        "HUMAN_INVOKES_DROP": 'session.dropCarrierEggs(tostring(player.UserId)' in preview,
        "DISCONNECT_INVOKES_DROP": 'scene.dropCarrierEggs(tostring(p.UserId)' in preview,
        "BOT_DEATH_GUARD": 'if not deaths[id] then' in bot,
        "BOT_DROPS_BEFORE_REBIRTH": (
            bot.find('session.dropCarrierEggs(id,actor:GetPivot().Position)')!=-1
            and bot.find('session.dropCarrierEggs(id,actor:GetPivot().Position)')
                < bot.find('deaths[id]=now+BOT_REBIRTH')
        ),
        "NO_EXTRA_GAME_REMOTE": 'Instance.new("RemoteEvent")' not in preview+bot,
    }
    for code,condition in required.items():
        if not condition: issues.append(code)
    return issues


class TestCarrierDrop(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.preview=(ROOT/"EGGRUMBLE_LobbyCastleModesPreview.server.luau").read_text(encoding="utf-8")
        cls.bot=(ROOT/"EGGRUMBLE_BotActors.luau").read_text(encoding="utf-8")
        cls.rules=(ROOT/"EGGRUMBLE_CastleMatchRules.luau").read_text(encoding="utf-8")

    def test_original_source_wiring(self):
        self.assertEqual(inspect(self.preview,self.bot,self.rules),[])

    def test_negative_missing_human_death(self):
        mutant=self.preview.replace("humanoid.Died:Connect(function()","humanoid.Destroying:Connect(function()")
        self.assertIn("HUMAN_DIED",inspect(mutant,self.bot,self.rules))

    def test_negative_missing_physical_pickup(self):
        mutant=self.preview.replace("session.releaseEggs(ownerId,landing,dropIds)","-- physical spawn intentionally removed")
        self.assertIn("PHYSICAL_DROP",inspect(mutant,self.bot,self.rules))

    def test_negative_double_drop_risk(self):
        mutant=self.preview.replace("carrier.heldEggs<=0 then return 0","carrier.heldEggs<0 then return 0")
        self.assertIn("IDEMPOTENT",inspect(mutant,self.bot,self.rules))

    def test_negative_bot_respawn_without_drop(self):
        mutant=self.bot.replace("session.dropCarrierEggs(id,actor:GetPivot().Position)","-- drop removed")
        self.assertIn("BOT_DROPS_BEFORE_REBIRTH",inspect(self.preview,mutant,self.rules))

    def test_negative_disconnect_invisible_egg(self):
        mutant=self.preview.replace("scene.dropCarrierEggs(tostring(p.UserId)","scene.missingDrop(tostring(p.UserId)")
        self.assertIn("DISCONNECT_INVOKES_DROP",inspect(mutant,self.bot,self.rules))

    def test_negative_rules_destroys_dropped_stock(self):
        mutant=self.rules.replace("m.fieldEggs+=dropped","m.fieldEggs-=dropped")
        self.assertIn("RULE_STOCK",inspect(self.preview,self.bot,mutant))


if __name__=="__main__":
    unittest.main()
