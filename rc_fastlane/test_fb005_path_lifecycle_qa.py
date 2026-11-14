"""FB005 async pathfinding lifetime QA child of #378; real Studio still NOT tested."""
from pathlib import Path
import re
import unittest
import json
import apply_fb005_solo_bots as parent

ROOT = Path(__file__).resolve().parent
BOT = ROOT / "features/fb005_solo/SoloTeamBots.luau"
LOCK = ROOT / "features/fb005_solo/SOURCE_LOCK.json"

class TestBotPathRaceFix(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = BOT.read_text("utf8")

    def test_all_pins_match_exact_authored_bytes(self):
        doc = json.loads(LOCK.read_text("utf8"))
        self.assertEqual(parent.blob(BOT.read_bytes()),parent.MODULE_BLOB)
        self.assertEqual(doc["authored_module"]["source_gitblob"],parent.MODULE_BLOB)
        self.assertEqual(doc["adapter"]["source_gitblob"],parent.blob(Path(parent.__file__).read_bytes()))

    def test_yielding_computeasync_is_generation_and_root_bounded(self):
        s=self.src
        self.assertIn("local generation=bot.pathGeneration",s)
        self.assertIn("local planningRoot=bot.root",s)
        self.assertIn("p:ComputeAsync(planningRoot.Position,goal)",s)
        self.assertIn("epoch==token and bot.pathGeneration==generation",s)
        self.assertIn("bot.root==planningRoot and alive(bot)",s)
        self.assertIn("bot.lastGoal~=nil and (bot.lastGoal-goal).Magnitude<=8",s)
        self.assertIn("if current then",s)
        self.assertIn("if bot.pathGeneration==generation and bot.root==planningRoot then",s)
        self.assertNotIn("p:ComputeAsync(bot.root.Position,goal)",s)
        guard=s.index("if current then")
        update=s.index("bot.path=path:GetWaypoints()",guard)
        self.assertLess(guard,update)

    def test_same_tick_egg_and_dynamic_guard_target_rerouted(self):
        s=self.src
        self.assertNotIn("local target=if bot.carry then",s)
        self.assertIn("local waypoint=if bot.carry then map.teams[bot.team].scorePad.Position",s)
        self.assertIn('if bot.lastGoal==nil or (bot.lastGoal-goal).Magnitude>8 then',s)
        self.assertIn('bot.lastGoal=goal',s)
        self.assertIn('invalidatePath(bot)\n    end\n    bot.lastGoal=goal\n    pathTo(bot,goal,now)',s)

    def test_egg_goal_switch_both_events_revoke_old_path(self):
        s=self.src
        self.assertEqual(s.count("                    invalidatePath(bot)"),2)
        i=s.index("if callbacks.steal(bot,enemy) then")
        self.assertIn("invalidatePath(bot)",s[i:i+450])
        j=s.index("if callbacks.deposit(bot,bot.team,bot.carry) then")
        self.assertIn("invalidatePath(bot)",s[j:j+500])
        section=s[s.index("local function invalidatePath(bot)"):s.index("local function respawn(bot)")]
        for x in ("bot.pathGeneration+=1","bot.path={}","bot.pathIndex=1","bot.nextRepath=0","bot.planning=false"):
            self.assertIn(x,section)

    def test_respawn_invalidates_old_planners_and_new_agent_identity(self):
        s=self.src
        i=s.index("local function respawn(bot)")
        sub=s[i:s.index("local function showCarriedEgg",i)]
        self.assertIn("local nextGeneration=bot.pathGeneration+1",sub)
        self.assertIn("local fresh=makeActor",sub)
        self.assertIn("bot.pathGeneration=nextGeneration",sub)
        self.assertLess(sub.index("local nextGeneration"),sub.index("makeActor"))
        self.assertGreater(sub.index("bot.pathGeneration=nextGeneration"),sub.index("for key,value in pairs(fresh)"))

    def test_stop_resets_ghost_tick_and_match_epoch(self):
        s=self.src
        stop=s[s.index("function Bot.stop()"):s.index("function Bot.start(")]
        self.assertIn("epoch+=1",stop)
        self.assertIn("active=false",stop)
        self.assertIn("lastTick=-math.huge",stop)
        self.assertIn("callbacks=nil",stop)

    def test_bot_start_soft_fail_and_exception_exit_empty_match(self):
        adapter=Path(parent.__file__).read_text("utf8")
        self.assertEqual(adapter.count("local ok,started=pcall(SoloTeamBots.start,map,"),1)
        self.assertIn("if not ok or started~=true then",adapter)
        self.assertIn('stopRound("DRAW","SOLO_BOTS_NOT_READY")',adapter)
        self.assertIn('if match.phase=="ACTIVE" and studioSoloRoundStarted',adapter)
        self.assertIn('and #Players:GetPlayers()==1 then',adapter)
        self.assertIn('SoloTeamBots.stop()',adapter)
        self.assertNotIn('if not ok then\n                    warn("FB005_SOLO_START_FAIL_CLOSED"',adapter)

    def test_unchanged_single_game_owner_and_bot_is_not_player(self):
        s=self.src
        self.assertNotIn('Instance.new("RemoteEvent")',s)
        self.assertNotIn("DataStoreService",s)
        self.assertNotIn('Instance.new("Player")',s)
        self.assertNotIn("MarketplaceService",s)
        g=Path(parent.__file__).read_text("utf8")
        self.assertIn('match.scores[homeTeam]+=1',g)
        self.assertIn('botEggOwners[eggTeam]=bot.id',g)
        self.assertIn('SoloTeamBots.stop()',g)

if __name__ == "__main__":
    unittest.main()
