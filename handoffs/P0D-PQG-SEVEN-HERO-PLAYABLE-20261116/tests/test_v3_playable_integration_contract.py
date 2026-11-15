"""EGGRUMBLE V3 integration source invariants. Run in CI; NOT actual Studio engine QA."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def source(file):
    return (ROOT/file).read_text(encoding="utf-8")

class EGGRUMBLEV3PlaytestSources(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mode=source("EGGRUMBLE_LobbyCastleModesPreview.server.luau")
        cls.rules=source("EGGRUMBLE_CastleMatchRules.luau")
        cls.bot=source("EGGRUMBLE_BotActors.luau")
        cls.swarm=source("EGGRUMBLE_SwarmCombat.luau")

    def test_bot_has_visible_physical_actor_and_distance_gate(self):
        for word in ("AI_Actor_","HumanoidRootPart","Humanoid",
                     "model:PivotTo(","steeringStep(","tryHeroAttack(",
                     "actualDist<=ACTION_DISTANCE","Rules.takeEggs(",
                     "Rules.depositEggs(","Rules.damageCastle(",
                     "session.releaseEggs(", "actor:Destroy()"):
            with self.subTest(word=word):
                self.assertIn(word, self.bot)

    def test_neutral_combat_tracks_actual_humanoid_deaths(self):
        for word in ('"HordeSoldier"','LIMIT=110',
                     "h.Died:Connect(function()",
                     'h:GetAttribute("LastAttackerId")',
                     "h:SetAttribute(\"LastAttackerId\",id)",
                     "credit(id)","NEUTRAL_HEALTH=32","MAX_HITS=24",
                     "EGGRUMBLE_NeutralKOs","EGGRUMBLE_SlashEvolution",
                     "damageFromPlayer","damageFromBot"):
            with self.subTest(word=word):
                self.assertIn(word, self.swarm)
        self.assertNotIn("credit(id,1000)",self.swarm)

    def test_two_mode_stage_uses_same_bot_and_swarm_rules(self):
        for word in ('BotActors=require(', 'SwarmCombat=require(',
                     'BotActors.start(session,Rules)','SwarmCombat.start(session)',
                     'session.swarm.damageFromPlayer(',
                     'EGGRUMBLE_TestBlade', 'EGGRUMBLE_Eliminated',
                     'CastleFrontLeft', 'door.CanCollide=false',
                     'TacticalRoute_', 'CentralRidge',
                     'ForestAmbushCover_', 'TEAM_PORTAL',
                     'BATTLE_ROYALE_PORTAL'):
            with self.subTest(word=word):
                self.assertIn(word,self.mode)
        self.assertNotIn("Bot slots participate in server rules;",self.mode)

    def test_server_authority_and_owner_contract(self):
        for text in (self.mode,self.bot,self.swarm):
            self.assertNotIn("MarketplaceService",text)
            self.assertNotIn("DataStoreService",text)
            self.assertNotIn("TeleportService",text)
            self.assertNotIn("RemoteEvent",text)
        self.assertIn("if not RunService:IsStudio() then return end",self.mode)
        self.assertIn('if not RunService:IsStudio() then return end',self.swarm) if 'if not RunService:IsStudio() then return end' in self.swarm else self.assertIn("assert(RunService:IsStudio()",self.swarm)
        self.assertIn("if c.hp<=0 then",self.rules)
        self.assertIn("m.fieldEggs+=released",self.rules)
        self.assertIn("only castle owner may decorate",self.rules)
        self.assertIn("friendly fire blocked",self.rules)

if __name__=="__main__":
    unittest.main()
