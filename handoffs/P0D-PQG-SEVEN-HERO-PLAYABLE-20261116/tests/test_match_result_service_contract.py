"""Isolated match result UI must show real server data and leave game view clear.

SOURCE regression only. Native Luau parser and actual Studio screen QA are separate gates.
"""
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
RESULT=ROOT/"EGGRUMBLE_MatchResultService.luau"
LOBBY=ROOT/"EGGRUMBLE_LobbyCastleModesPreview.server.luau"
PROJECT=ROOT/"EGGRUMBLE_V3_STUDIO.project.json"


class MatchResultContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result=RESULT.read_text(encoding="utf-8")
        cls.lobby=LOBBY.read_text(encoding="utf-8")
        cls.project=json.loads(PROJECT.read_text(encoding="utf-8"))

    def test_rojo_and_finished_round_only_wiring(self):
        scripts=self.project["tree"]["ServerScriptService"]
        self.assertEqual(scripts["EGGRUMBLE_MatchResultService"]["$path"], RESULT.name)
        self.assertIn('local ResultService=require(script.Parent:WaitForChild("EGGRUMBLE_MatchResultService"))', self.lobby)
        self.assertIn("ResultService.showIfFinished(session,queue,mode)", self.lobby)
        self.assertIn('session.rules.phase~="FINISHED"', self.result)
        self.assertIn("session.rules.winner==nil", self.result)

    def test_once_only_and_leaving_players_not_reached(self):
        source=self.result
        self.assertIn("if session.resultsDelivered or", source)
        self.assertIn("session.resultsDelivered=true", source)
        self.assertIn("if player.Parent==Players then", source)
        self.assertIn("if castle then", source)
        self.assertIn('assert(RunService:IsStudio()', source)

    def test_real_ko_egg_and_castle_score(self):
        source=self.result
        self.assertIn("session.swarm.kills[id] or 0", source)
        self.assertIn("castle.depositedEggs or 0", source)
        self.assertIn('event.type=="CASTLE_FALL" and event.attacker==attackerId', source)
        self.assertIn('session.rules.winner==castle.team', source)
        self.assertIn('session.rules.winner==id', source)
        for bogus in ('NeutralKOs" +', 'os.time()', "random(", "math.random"):
            self.assertNotIn(bogus, source)

    def test_small_transient_panel_cannot_block_play(self):
        source=self.result
        self.assertIn("local DISPLAY_SECONDS=8", source)
        self.assertIn("task.delay(DISPLAY_SECONDS,function()", source)
        self.assertIn("if gui.Parent then gui:Destroy() end", source)
        self.assertIn("frame.AnchorPoint=Vector2.new(.5,1)", source)
        self.assertIn("frame.Size=UDim2.new(.82,0,0,94)", source)
        self.assertIn('gui.Name="EGGRUMBLE_MatchResult"', source)
        self.assertIn('if old then old:Destroy() end', source)
        self.assertNotIn("while true do", source)

    def test_no_public_or_paid_or_saved_side_effects(self):
        source=self.result
        for banned in ("MarketplaceService", "DataStoreService", "TeleportService",
                       "PromptProductPurchase", "RemoteEvent", "RemoteFunction",
                       "SetAsync", "UpdateAsync", "PlayerAdded:Connect"):
            with self.subTest(banned=banned):
                self.assertNotIn(banned, source)


if __name__=="__main__":
    unittest.main()
