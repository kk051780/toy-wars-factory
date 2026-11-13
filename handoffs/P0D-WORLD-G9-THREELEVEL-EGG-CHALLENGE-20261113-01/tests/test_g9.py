import json,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from verify_g9 import lock,contract
S=(ROOT/"src/G9EggGame.server.luau").read_text(encoding="utf8")
R=(ROOT/"src/G9EggRules.luau").read_text(encoding="utf8")
W=(ROOT/"src/G8World.server.luau").read_text(encoding="utf8")
class G9QA(unittest.TestCase):
 def test_7_source_git_sha_manifest(self):self.assertTrue(lock())
 def test_actual_rules_server_contract(self):self.assertTrue(contract())
 def test_original_g8_two_real_sources_untouched(self):
  self.assertEqual(W.count('prompt.Triggered:Connect(function(player)'),1)
 def test_red_blue_symmetric_coordinates(self):
  self.assertIn('if team=="RED" then -22 else 22',S)
  self.assertIn('Vector3.new(x,-23.8,168)',S)
  self.assertIn('Vector3.new(x,-27.4,136)',S)
 def test_no_h1_game(self):
  self.assertNotIn("TrapRaidersS1Remote",S)
  self.assertNotIn('RemoteEvent',S)
 def test_3_stage_studio_game_not_published(self):
  self.assertIn('if not RunService:IsStudio() then return end',S)
 def test_score_requires_own_egg(self):
  self.assertIn('if not state.home[team] then return false,"OWN_EGG_MISSING" end',R)
 def test_defender_tag_not_damage(self):
  self.assertIn('tag.Triggered:Connect(function(rescuer)',S)
  self.assertNotIn('TakeDamage',S)
 def test_g8_separate_true_real_portals(self):
  self.assertIn('Rules.validate(link.from,link.to',W)
 def test_reject_fake_new_remote(self):
  with self.assertRaises(ValueError):contract(server=S+'\nInstance.new("RemoteEvent")')
 def test_reject_client_forged_position(self):
  with self.assertRaises(ValueError):contract(server=S.replace('dist2(hrp.Position,egg.Position)','0'))
 def test_reject_fake_score_distance(self):
  with self.assertRaises(ValueError):contract(server=S.replace('dist2(hrp.Position,pad.Position)','0'))
 def test_reject_fake_tag_distance(self):
  with self.assertRaises(ValueError):contract(server=S.replace('dist2(rescueRoot.Position,carrierRoot.Position)','0'))
 def test_reject_missing_defender_tag(self):
  with self.assertRaises(ValueError):contract(server=S.replace('tag.Triggered:Connect(function(rescuer)','tag.PromptShown:Connect(function(rescuer)'))
 def test_reject_missing_studio_gate(self):
  with self.assertRaises(ValueError):contract(server=S.replace('RunService:IsStudio()','true'))
 def test_reject_attacker_damage(self):
  with self.assertRaises(ValueError):contract(server=S+'\nHumanoid:TakeDamage(100)')
 def test_reject_paid_reward(self):
  with self.assertRaises(ValueError):contract(server=S+'\ngame:GetService("MarketplaceService")')
 def test_reject_dangerous_persistence(self):
  with self.assertRaises(ValueError):contract(server=S+'\ngame:GetService("DataStoreService")')
 def test_reject_change_to_g8_parent(self):
  with self.assertRaises(ValueError):contract(world=W.replace('Rules.validate(link.from,link.to','false and ('))
 def test_reject_infinite_capture(self):
  with self.assertRaises(ValueError):contract(rule=R.replace('R.CARRY_LIMIT=45','R.CARRY_LIMIT=99999'))
 def test_reject_negative_capture_range(self):
  with self.assertRaises(ValueError):contract(rule=R.replace('R.MAX_DISTANCE_SQUARED=144','R.MAX_DISTANCE_SQUARED=999'))
 def test_reject_score_without_own_home(self):
  with self.assertRaises(ValueError):contract(rule=R.replace('if not state.home[team] then return false,"OWN_EGG_MISSING" end',''))
 def test_reject_no_human_round_limit(self):
  with self.assertRaises(ValueError):contract(rule=R.replace('R.WIN_SCORE=3','R.WIN_SCORE=1000'))
 def test_reject_all_studio_teams_red(self):
  with self.assertRaises(ValueError):contract(server=S.replace('teamSizes.RED<=teamSizes.BLUE','true'))
 def test_reject_live_release(self):
  with self.assertRaises(ValueError):contract(server=S.replace('if not RunService:IsStudio() then return end',''))
 def test_reject_egg_carry_indefinite(self):
  with self.assertRaises(ValueError):contract(server=S.replace('Rules.expire(state,os.clock())','0'))
 def test_reject_no_death_return(self):
  with self.assertRaises(ValueError):contract(server=S.replace('Rules.release(state,player.UserId)','0'))
 def test_reject_no_real_lookout_cooldown(self):
  with self.assertRaises(ValueError):contract(server=S.replace('if now-lastScout<10 then return end','if false then return end'))
 def test_reject_infinite_lookout(self):
  with self.assertRaises(ValueError):contract(server=S.replace('lookoutUntil=now+7','lookoutUntil=math.huge'))
 def test_reject_rojo_game_mount_missing(self):
  p=json.loads((ROOT/"default.project.json").read_text(encoding="utf8"))
  p["tree"]["ServerScriptService"]["G9_Three_Level_Play"].pop("G9EggGame")
  with self.assertRaises(ValueError):contract(project=p)
 def test_source_game_objectives_are_visible(self):
  self.assertIn('G9_"..team.."_REAL_EGG',S)
  self.assertIn('G9_"..team.."_SCORE_PAD',S)
 def test_genuine_two_player_team_logic(self):
  self.assertIn('Players.PlayerAdded:Connect(assignPlayer)',S)
  self.assertIn('Players.PlayerRemoving:Connect(function(player)',S)
if __name__=="__main__":unittest.main()

