"""Real Studio V3 bot field egg collection source QA (not runtime proof)."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
BOT=(ROOT/"EGGRUMBLE_BotActors.luau").read_text(encoding="utf-8")
LOBBY=(ROOT/"EGGRUMBLE_LobbyCastleModesPreview.server.luau").read_text(encoding="utf-8")
RULES=(ROOT/"EGGRUMBLE_CastleMatchRules.luau").read_text(encoding="utf-8")

def breaches(bot=BOT,lobby=LOBBY,rules=RULES):
    c={
      "real server token only":'session.rules.fieldEggTokens[eggId]==true' in bot,
      "initial physical eggs":'part.Name:match("^FieldEgg_(%d+)$")' in bot,
      "released physical eggs":'part.Name:match("^ReleasedEgg_(RELEASE_%d+)$")' in bot,
      "carrier drop physical eggs":'part.Name:match("^ReleasedEgg_(CARRIER_DROP_%d+)$")' in bot,
      "world parts":'part:IsA("BasePart")' in bot,
      "bounded search":'FIELD_EGG_SEARCH_RADIUS=145' in bot,
      "no extra item ownership":'EGGRUMBLE_FieldItemPickups' not in bot,
      "real field goal":'fieldPart.Position' in bot and '"FIELD_EGG"' in bot,
      "real proximity":'actualDist<=ACTION_DISTANCE' in bot,
      "real sight":'clearActionPath(actor,actors,actualTarget)' in bot,
      "no stolen model destruction":'if ok then fieldPart:Destroy() end' in bot,
      "atomic server pickup":'Rules.takeFieldEgg(session.rules,id,fieldId)' in bot,
      "token fresh on action":'session.rules.fieldEggTokens[fieldId]==true' in bot,
      "own physical world only":'fieldPart.Parent==session.world' in bot,
      "real inventory capacity":'actor.heldEggs<3' in rules and 'actor.heldEggs+=1' in rules,
      "only server can consume":'m.fieldEggTokens[eggId]=nil' in rules,
      "home deposit":'Rules.depositEggs(session.rules,id,me.heldEggs)' in bot,
      "carry returns home":'local goHome=me.heldEggs>0' in bot,
      "no invisible ghost pickup":'Rules.takeFieldEgg(session.rules,id,"FIELD_1")' not in bot,
      "balanced map egg height":'worldX+(col-3.5)*93,-1.35,290+row*200' in lobby,
      "same lobby 24 eggs":'for i=1,24 do' in lobby,
      "AI duels preserved":'targetHumanoid:TakeDamage(BOT_HERO_DAMAGE)' in bot,
    }
    return [n for n,ok in c.items() if not ok]

class TestFieldEggBotWorldIntegration(unittest.TestCase):
    def test_authored_contract(self): self.assertEqual([],breaches())
    def test_no_fake_token(self):
        self.assertIn("real server token only",breaches(bot=BOT.replace("session.rules.fieldEggTokens[eggId]==true","true")))
    def test_no_field_spawn_references(self):
        self.assertIn("initial physical eggs",breaches(bot=BOT.replace('part.Name:match("^FieldEgg_(%d+)$")',"nil")))
    def test_no_carrier_drop(self):
        self.assertIn("carrier drop physical eggs",breaches(bot=BOT.replace('part.Name:match("^ReleasedEgg_(CARRIER_DROP_%d+)$")',"nil")))
    def test_virtual_pickup(self):
        self.assertIn("real proximity",breaches(bot=BOT.replace("actualDist<=ACTION_DISTANCE","true")))
    def test_ghost_through_wall(self):
        self.assertIn("real sight",breaches(bot=BOT.replace("clearActionPath(actor,actors,actualTarget)","true")))
    def test_destroy_before_result(self):
        self.assertIn("no stolen model destruction",breaches(bot=BOT.replace("if ok then fieldPart:Destroy() end","fieldPart:Destroy()")))
    def test_wrong_egg_id(self):
        self.assertIn("atomic server pickup",breaches(bot=BOT.replace("Rules.takeFieldEgg(session.rules,id,fieldId)","Rules.takeFieldEgg(session.rules,id,nil)")))
    def test_no_unique_token_guard(self):
        self.assertIn("token fresh on action",breaches(bot=BOT.replace("session.rules.fieldEggTokens[fieldId]==true","true")))
    def test_no_home_trip(self):
        self.assertIn("carry returns home",breaches(bot=BOT.replace("local goHome=me.heldEggs>0","local goHome=false")))
    def test_floating_field_collectible(self):
        self.assertIn("balanced map egg height",breaches(lobby=LOBBY.replace(",-1.35,290+row*200",",3,290+row*200")))
    def test_deposit_missing(self):
        self.assertIn("home deposit",breaches(bot=BOT.replace("Rules.depositEggs(session.rules,id,me.heldEggs)","-- missing")))
    def test_avoid_item_conflict(self):
        self.assertIn("no extra item ownership",breaches(bot=BOT+"\n-- EGGRUMBLE_FieldItemPickups duplicated"))
    def test_no_bot_duel_regression(self):
        self.assertIn("AI duels preserved",breaches(bot=BOT.replace("targetHumanoid:TakeDamage(BOT_HERO_DAMAGE)","-- fake KO")))
if __name__=="__main__": unittest.main()
