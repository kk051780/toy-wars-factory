#!/usr/bin/env python3
"""Real-original source bridge audit (source-only, no Roblox Studio or network)."""
from pathlib import Path
import unittest,hashlib,difflib,re
root=Path(__file__).resolve().parents[1]
repo=root.parents[1]
base=repo/"handoffs/P0D-MUSOU-CHAOS-H1-20261113-01/inputs"
data={p:(root/"inputs"/p).read_text(encoding="utf8")
      for p in ("Game.server.luau","HUD.client.luau","PowerFantasyRules.luau")}
game=data["Game.server.luau"]
hud=data["HUD.client.luau"]
policy=data["PowerFantasyRules.luau"]
orig=(base/"Game.server.luau").read_text(encoding="utf8")
def blob(p):
 b=(root/"inputs"/p).read_bytes()
 return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
class TestPowerActualIntegration(unittest.TestCase):
 def test_01_original_game_preserved_order(self):
  a=orig.splitlines();b=game.splitlines()
  matching=sum(x.size for x in difflib.SequenceMatcher(None,a,b,autojunk=False).get_matching_blocks())
  self.assertGreaterEqual(matching,len(a)-3)
 def test_02_policy_original_byte_exact(self):
  self.assertEqual(blob("PowerFantasyRules.luau"),"86e79877cf0e58603a4de67db29155bf98cc511d")
 def test_03_original_game_source(self):self.assertGreater(len(orig),75000)
 def test_04_no_second_game(self):self.assertEqual(game.count("local function applyAttack("),1)
 def test_05_one_remote_listener(self):self.assertEqual(game.count("remote.OnServerEvent:Connect("),1)
 def test_06_one_server_tick(self):self.assertEqual(game.count("local function tickRound("),1)
 def test_07_source_authority(self):self.assertEqual(game.count("local Power = require("),1)
 def test_08_pve_damage_really_wired(self):self.assertIn('*earnedDamageMultiplier(player,"MINION")',game)
 def test_09_pvp_damage_really_wired(self):self.assertIn('*earnedDamageMultiplier(player,"PLAYER")',game)
 def test_10_awaken_actual_game_dispatch(self):self.assertIn('elseif data.action == "AWAKEN_POWER" then applyEarnedAwaken(player,data)',game)
 def test_11_awaken_server_policy(self):self.assertIn('Power.beginAwaken(state,powerSecond(),carry[player]~=nil,true)',game)
 def test_12_integer_time_from_match(self):self.assertIn('return math.max(0,math.floor(serverNow()-match.startedAt))',game)
 def test_13_never_pass_unix_clock(self):self.assertNotIn('Power.combat(state,targetType,serverNow())',game)
 def test_14_objective_same_certified(self):self.assertIn('Power.recordObjective(state,eventId,kind,true)',game)
 def test_15_certified_xp_original(self):self.assertIn('if Progression.recordEvent(round,eventId,kind,true) then',game)
 def test_16_no_player_level_payload(self):self.assertNotIn("data.powerLevel",game)
 def test_17_no_client_damage(self):self.assertNotIn("data.powerDamage",game)
 def test_18_no_client_charge(self):self.assertNotIn("data.powerCharge",game)
 def test_19_no_paid_power(self):self.assertNotIn("PromptProductPurchase",game)
 def test_20_once_one_round(self):self.assertIn("Power.endRound(state)",game)
 def test_21_studio_only(self):self.assertIn('if not RunService:IsStudio() or match.phase~="ACTIVE" or not ok or not hum',game)
 def test_22_existing_horde_source(self):self.assertIn("horde:hit(root.Position,look,",game)
 def test_23_existing_bind_source(self):self.assertIn('elseif data.action == "NET_THROW" then applyNet(player,data)',game)
 def test_24_no_new_collect_reward(self):self.assertNotIn('recordServerProgress(player,"KILL")',game)
 def test_25_hud_action(self):self.assertIn('action("AWAKEN_POWER",nil)',hud)
 def test_26_hud_keyboard(self):self.assertIn("Enum.KeyCode.V",hud)
 def test_27_hud_server_read_only(self):self.assertIn("s.powerCharge",hud)
 def test_28_hud_does_not_scale_damage(self):self.assertNotIn("Power.combat(",hud)
 def test_29_hud_single_seq(self):self.assertEqual(hud.count("local seq = 0"),1)
 def test_30_original_policy_stage(self):self.assertIn("Power.AWAKEN_LEVEL = 10",policy)
 def test_31_original_policy_2_8(self):self.assertIn("Power.TELEGRAPH_SECONDS = 2",policy);self.assertIn("Power.AWAKEN_SECONDS = 8",policy)
 def test_32_original_policy_not_p2w(self):self.assertIn("canBuyPower=false",policy)
 def test_33_no_carry_awakening(self):self.assertIn('carryingEgg~=false',policy)
 def test_34_mode_unchanged(self):self.assertIn('EXPERIMENTAL_FIVE_EGG_MODE=RunService:IsStudio() and chosenMode==ModeVote.SCORE',game)
 def test_35_no_schema_modification(self):
  self.assertNotIn("function Store.settleProgress(",game)
 def test_36_ui_visible_telegraph(self):self.assertIn('P0D_EarnedAwakenTell',game)
if __name__=="__main__":unittest.main(verbosity=1)
