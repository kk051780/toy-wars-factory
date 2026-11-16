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
        cls.router=source("EGGRUMBLE_BotPathRouter.luau")
        cls.swarm=source("EGGRUMBLE_SwarmCombat.luau")
        cls.hero=source("EGGRUMBLE_SevenRoleCombat.luau")

    def test_bot_has_visible_physical_actor_and_distance_gate(self):
        for word in ("AI_Actor_","HumanoidRootPart","Humanoid",
                     "spawnActor(","Router.navigate(","tryHeroAttack(",
                     "actualDist<=ACTION_DISTANCE","Rules.takeEggs(",
                     "Rules.depositEggs(","Rules.damageCastle(",
                     "session.releaseEggs(", "actor:Destroy()"):
            with self.subTest(word=word):
                self.assertIn(word, self.bot)

    def test_navigation_quality_and_bounded_real_pathfinding(self):
        for token in ('PathfindingService', 'PathfindingService:CreatePath(',
                      'path:ComputeAsync(', 'path:GetWaypoints()', 'path.Blocked:Connect(',
                      'MAX_COMPUTES_IN_FLIGHT=2', 'RECOMPUTE_SECONDS=2.8',
                      'routeClear(', 'if not routeClear(', 'Router.clear('):
            with self.subTest(token=token):
                self.assertIn(token, self.router)
        self.assertIn('Router.navigate(mode..":"..id,actor,goal,AI_TICK*slow,actors)', self.bot)
        self.assertNotIn('local function steeringStep(', self.bot)

    def test_world_egg_tokens_are_not_duplicable(self):
        for token in ('m.fieldEggTokens[eggId]=nil', 'function M.takeFieldEgg(',
                      'function M.auditEggConservation(', 'field egg pickup must reference',
                      'releasedEggIds=', 'CARRIER_DROP_'):
            with self.subTest(token=token):
                self.assertIn(token, self.rules)
        self.assertIn('Rules.takeFieldEgg(session.rules,tostring(p.UserId),eggId)', self.mode)
        self.assertIn('res.releasedEggIds', self.mode)
        self.assertIn('result.releasedEggIds', self.bot)

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
                     'SevenRoleCombat=require(',
                     'SevenRoleCombat.equip(session,p,role)', 'EGGRUMBLE_Eliminated',
                     'CastleFrontLeft', 'door.CanCollide=false',
                     'TacticalRoute_', 'CentralRidge',
                     'ForestAmbushCover_', 'TEAM_PORTAL',
                     'BATTLE_ROYALE_PORTAL'):
            with self.subTest(word=word):
                self.assertIn(word,self.mode)
        self.assertNotIn("Bot slots participate in server rules;",self.mode)

    def test_seven_roles_same_match_and_server_authority(self):
        for role in ('WARRIOR','MAGE','NINJA','TRAPPER','BUILDER','BEAST','ZOMBIE'):
            with self.subTest(role=role):
                self.assertIn(role+'={name=',self.hero)
        for text in ('EGGRUMBLE_SKILL_','Tool','ToolTip','CombatBalance.skill(role,slot)',
                     'session.swarm.damageFromPlayer(', 'h:TakeDamage(damage*duel*mark)',
                     'owner.heldEggs==0','session.rules.phase~="ACTIVE"',
                     'if tool.Parent~=p.Character then return end',
                     'lineClear(', 'RaycastParams.new()'):
            with self.subTest(text=text):
                self.assertIn(text,self.hero)
        self.assertIn('"武神"',self.hero)
        self.assertIn('"暗殺者"',self.hero)
        self.assertIn('["職業選択"]=0.4',source("EGGRUMBLE_InteractionGuard.luau"))
        self.assertNotIn('EGGRUMBLE_TestBlade',self.mode)

    def test_server_authority_and_owner_contract(self):
        for text in (self.mode,self.bot,self.swarm,self.hero):
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
