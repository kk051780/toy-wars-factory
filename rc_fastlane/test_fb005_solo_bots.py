"""Source contracts for FB-005 private Studio team bots. Engine physics NOT tested."""
from pathlib import Path
from tempfile import TemporaryDirectory
import ast, unittest
import apply_fb005_solo_bots as mod

class Fb005SoloBotContracts(unittest.TestCase):
    def test_python_syntax_and_module_pin(self):
        ast.parse(Path(mod.__file__).read_text("utf8"))
        self.assertEqual(mod.blob(mod.MODULE.read_bytes()),mod.MODULE_BLOB)

    def test_real_intent_ai_and_five_egg_exclusion(self):
        script=mod.MODULE.read_text("utf8")
        for marker in ('PathfindingService:CreatePath(', 'Bot.start(', 'Bot.stop()',
                       'Bot.tick(', 'Bot.tryHumanHit(', 'callbacks.steal(',
                       'callbacks.deposit(', 'callbacks.drop(', 'callbacks.attackHuman(',
                       'callbacks.attackBot(', 'MAX_BOTS=5', 'HumanoidRootPart',
                       'GuardianShield', 'RAIDER', 'GUARD',
                       'VISUAL_CARRIED_ENEMY_EGG', 'showCarriedEgg(', 'epoch==token'):
            self.assertIn(marker, script)
        for forbidden in ('Instance.new("RemoteEvent")','OnServerEvent:Connect(',
                          'UpdateAsync(', 'DataStoreService',
                          'PromptProductPurchase('):
            self.assertNotIn(forbidden,script)

    def test_server_game_all_score_and_damage_writers(self):
        source=Path(mod.__file__).read_text("utf8")
        self.assertIn('botEggOwners[eggTeam]=bot.id',source)
        self.assertIn('match.scores[homeTeam]+=1',source)
        self.assertIn('Rules.winner(',source)
        self.assertIn('hum:TakeDamage(',source)
        self.assertIn('EXPERIMENTAL_FIVE_EGG_MODE',source)
        self.assertIn('studioSoloRoundStarted',source)
        self.assertIn('SoloTeamBots.stop()',source)
        self.assertIn('pcall(SoloTeamBots.tick,now)',source)
        self.assertIn('pcall(SoloTeamBots.start,map,',source)
        self.assertIn("original",source.lower())

    def test_off_zero_writes(self):
        with TemporaryDirectory() as folder:
            root=Path(folder)/"missing"
            self.assertFalse(mod.apply(root,False))
            self.assertFalse(root.exists())

    def test_missing_source66_rejected_before_writes(self):
        with TemporaryDirectory() as folder:
            root=Path(folder)
            with self.assertRaises(AssertionError):
                mod.apply(root,True)
            self.assertEqual(list(root.iterdir()),[])

    def test_duplicate_game_anchors_rejected(self):
        with self.assertRaises(AssertionError):
            mod.sub("a a", "a", "b")
        with self.assertRaises(AssertionError):
            mod.patch_game("--!strict\n")
if __name__=="__main__":
    unittest.main()
