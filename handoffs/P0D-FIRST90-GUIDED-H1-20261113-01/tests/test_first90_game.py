#!/usr/bin/env python3
"""Source-layer anti-regression: real FIRST90 Game, HUD and upstream #288 v5."""
from pathlib import Path
import hashlib,unittest
ROOT=Path(__file__).resolve().parents[1]
src=lambda s:(ROOT/"inputs"/s).read_text("utf8")
G=src("Game.server.luau");H=src("HUD.client.luau")
M=src("MusouHorde.luau");P=src("First90GuideRules.luau");W=src("First90WaypointRules.luau")
def blob(s):
 b=(ROOT/"inputs"/s).read_bytes()
 return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
class First90OriginalSource(unittest.TestCase):
 def test_01_v5_exact_horde(self):self.assertEqual(blob("MusouHorde.luau"),"8c147c801e7fa1ff362922d66c9a6fd432fc8b6e")
 def test_02_exact_policy(self):self.assertEqual(blob("First90GuideRules.luau"),"0cbf26aaebf66a7548d4299fb6ede4bee47cfa70")
 def test_03_v5_red_disk_real(self):self.assertIn("ELITE_SWEEP_DANGER_RADIUS",M)
 def test_04_v5_warning_server_calculated(self):self.assertIn("function Horde:eliteWarningSeconds(now: number)",M)
 def test_05_v5_floor(self):self.assertIn("MUSOU_SOURCE_MAP_ARENA_REQUIRED",M)
 def test_06_v5_respawn(self):self.assertIn("m.attackAt=now+1.5 -- fair re-entry",M)
 def test_07_v5_elite_kill(self):self.assertIn("m.tellUntil=0",M)
 def test_08_v5_radius(self):self.assertIn("Combat.ELITE_MELEE_RANGE*2",M)
 def test_09_one_remote(self):self.assertEqual(G.count("remote.OnServerEvent:Connect("),1)
 def test_10_one_game_damage(self):self.assertEqual(G.count("local function applyAttack("),1)
 def test_11_one_round_tick(self):self.assertEqual(G.count("local function tickRound("),1)
 def test_12_readonly_policy(self):self.assertEqual(G.count("local First90Guide = require("),1)
 def test_13_real_mark_objectives(self):self.assertIn("First90Guide.mark(guideProgress[player],match.serial,kind,true)",G)
 def test_14_real_hit(self):self.assertIn('First90Guide.mark(guideProgress[player],match.serial,"HIT",true)',G)
 def test_15_real_scout(self):self.assertIn('First90Guide.mark(guideProgress[player],match.serial,"SCOUT",true)',G)
 def test_16_reset_new_round(self):self.assertIn("guideProgress[p] = First90Guide.newRound(match.serial)",G)
 def test_17_no_cross_user_guide(self):self.assertIn("guideProgress[player]=nil",G)
 def test_18_actual_v5_warning_dto(self):self.assertIn("musouEliteWarningSeconds = eliteWarning",G)
 def test_19_actual_hud_elite_cue(self):self.assertIn("s.musouEliteWarningSeconds",H)
 def test_20_actual_first90_hud(self):self.assertIn("First90RealObjectiveGuide",H)
 def test_21_no_cloned_hud(self):self.assertEqual(H.count('gui.Name = "TrapRaidersS1HUD"'),1)
 def test_22_no_client_milestone(self):self.assertNotIn("First90Guide.mark(",H)
 def test_23_no_new_bonus(self):self.assertNotIn("Guide.grantXp(",G)
 def test_24_no_buy(self):self.assertNotIn("PromptProductPurchase",G)
 def test_25_old_egg_protection(self):self.assertIn("if mobHits>0 then return end",G)
 def test_26_old_level_preserved(self):self.assertIn('Power.beginAwaken(state,powerSecond()',G)
 def test_27_old_evolution(self):self.assertIn('Evolution.nextEvolution(evo,profile.equipped,profile.owned,',G)
 def test_28_studio_only(self):self.assertIn("RunService:IsStudio()",G)
 def test_29_90_boundary(self):self.assertIn("elapsed>=Guide.WINDOW_SECONDS",P)
 def test_30_guard_urgent(self):self.assertIn('return cue("DODGE",',P)
 def test_31_carry_urgent(self):self.assertIn('return cue("RETURN",',P)
 def test_32_no_endless_attack(self):self.assertIn("elapsed<24",P)
 def test_33_no_endless_egg(self):self.assertIn("elapsed<60",P)
 def test_34_no_false_carry(self):self.assertIn("carrying=carry[player]~=nil",G)
 def test_35_one_client_seq(self):self.assertEqual(H.count("local seq = 0"),1)
 def test_36_no_new_stores(self):self.assertEqual(G.count("DataStoreService:GetDataStore("),1)
 def test_37_guard_duration_matches_actual_token(self):
  self.assertIn("evolutionGuards[player]={untilAt=serverNow()+SCOUT_DURATION,",G)
  self.assertNotIn("evolutionGuards[player]={untilAt=serverNow()+8,",G)
 def test_38_one_assault_only_after_real_hit(self):
  self.assertIn("local evolvedStrikeUsed=false",G)
  self.assertIn("and not evolvedStrikeUsed then",G)
  self.assertIn("if hits>0 then\n                    evolvedStrikeUsed=true",G)
  self.assertNotIn("nextEvolvedStrike=serverNow()+12",G)
 def test_39_original_5sec_scout_token(self):
  self.assertIn("local SCOUT_DURATION=5",G)
  self.assertIn("token.duration~=SCOUT_DURATION",G)
  self.assertIn("while t<SCOUT_DURATION and scoutModels[player]==model",G)

 def test_40_real_beast_hit_uses_body_level(self):
  self.assertIn("local hits=horde:hit(currentRoot.Position,currentRoot.CFrame.LookVector,",G)
  self.assertNotIn("local hits=horde:hit(anchor,currentRoot.CFrame.LookVector,",G)
 def test_41_waypoint_exact_blob(self):
  self.assertEqual(blob("First90WaypointRules.luau"),"69c81d82eac5189d34eed801099ab52b559f2b52")
 def test_42_server_chooses_live_egg(self):
  self.assertIn('def.prompt.Enabled and def.part.Transparency<.9',G)
  self.assertIn('match.eggOwners[enemy]==nil',G)
  self.assertIn("First90Waypoint.select(match.phase",G)
 def test_43_no_client_goal_authority(self):
  self.assertIn("first90Target = first90Target",G)
  self.assertIn("setWaypoint(s.first90Target)",H)
  self.assertNotIn("action(\"NAV",H)
 def test_44_90s_client_waypoint_cleanup(self):
  self.assertIn("if f90.step==\"PICKUP\" or f90.step==\"RETURN\" then",H)
  self.assertIn("waypointAnchor:Destroy()",H)
  self.assertIn("clearWaypoint()",H)
 def test_45_no_physical_touch_or_collide(self):
  self.assertIn("anchor.CanCollide=false",H)
  self.assertIn("anchor.CanTouch=false",H)
  self.assertIn("anchor.CanQuery=false",H)
 def test_46_no_duplicate_render_authority(self):
  self.assertEqual(H.count("RunService.RenderStepped:Connect("),1)
  self.assertEqual(G.count('remote.OnServerEvent:Connect('),1)
 def test_47_real_home_map(self):
  self.assertIn("map.teams[team].scorePad.Position",G)
  self.assertIn("owner=def.owner",G)
 def test_48_no_fake_missing_egg_score(self):
  self.assertIn('cue("PICKUP","🥚 卵を落としたら、もう一度ひろおう！")',P)
  self.assertIn('cue("RECOVER","⚠ 自陣の卵も盗まれた！仲間と取り戻そう")',P)
 def test_49_no_live_waypoint(self):
  self.assertIn('if RunService:IsStudio() and first90.visible==true then',G)
 def test_50_mobile_arrow_outside_thumb_buttons(self):
  self.assertIn("UDim2.fromOffset(17,178)",H)
  self.assertIn('First90ActualWaypointArrow',H)
if __name__=="__main__":unittest.main(verbosity=1)
