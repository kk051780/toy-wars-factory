"""SOURCE-only regression: no castle-wall piercing AI hero strike.

Does not imply Luau engine, Studio, Android, or gameplay quality acceptance.
"""
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BOT=ROOT/"EGGRUMBLE_BotActors.luau"
PREVIEW=ROOT/"EGGRUMBLE_LobbyCastleModesPreview.server.luau"
HERO=ROOT/"EGGRUMBLE_SevenRoleCombat.luau"


class TestBotHeroLineOfSight(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src=BOT.read_text(encoding="utf-8")

    def test_castle_wall_blocks_bot_melee(self):
        s=self.src
        self.assertIn("local function clearHeroStrike(",s)
        self.assertIn("params.FilterDescendantsInstances={actor,target}",s)
        self.assertIn("params.RespectCanCollide=true",s)
        self.assertIn("return workspace:Raycast(origin,delta,params)==nil",s)
        self.assertIn("and clearHeroStrike(actor,character,",s)

    def test_alive_in_range_and_los_are_all_required(self):
        s=self.src
        self.assertIn("if character and root and h and h.Health>0 and (root.Position-at).Magnitude<11",s)
        guard=s.index("and clearHeroStrike(actor,character,")
        hit=s.index("h:TakeDamage(BOT_HERO_DAMAGE)")
        self.assertLess(guard,hit)
        self.assertIn("lastHit[my.id]=now",s[guard:hit])

    def test_seven_hero_weapons_cannot_hit_bot_through_wall(self):
        src=HERO.read_text(encoding="utf-8")
        self.assertIn("ray.RespectCanCollide=true",src)
        self.assertIn("ray.FilterDescendantsInstances={first,second}",src)
        self.assertIn("return workspace:Raycast(source,delta,ray)==nil",src)
        self.assertIn("and count<5 and lineClear(",src)
        ray=src.index("and count<5 and lineClear(")
        hit=src.index("h:TakeDamage(damage*duel*mark)")
        self.assertLess(ray,hit)
        self.assertNotIn("EGGRUMBLE_TestBlade",PREVIEW.read_text(encoding="utf-8"))

    def test_preview_only_no_unapproved_external_io(self):
        s=self.src
        self.assertIn("assert(RunService:IsStudio()",s)
        for forbidden in ("DataStoreService","MarketplaceService","PromptProductPurchase",
                          "MessagingService","TeleportService"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden,s)


if __name__=="__main__":
    unittest.main()
