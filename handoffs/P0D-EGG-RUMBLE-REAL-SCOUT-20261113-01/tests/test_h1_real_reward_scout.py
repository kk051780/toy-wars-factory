"""Offline full source QA for actual original 2-mode H1 game + original #275 pure reward.

Tests DO NOT imply Roblox Studio actual physics, true 2 clients, persistence or FUN.
"""
from pathlib import Path
import json,hashlib,unittest
HERE=Path(__file__).resolve();REPO=HERE.parents[3];OWN=HERE.parents[1]
ORIG=REPO/"handoffs/P0D-EGG-RUMBLE-DUAL-MODE-LOBBY-20261113/dist/EGG_RAID_RUMBLE_SINGLE_GAME_TWO_MODES_PRIVATE_STUDIO"
NEW=OWN/"dist/EGG_RAID_RUMBLE_FREE_HATCH_EQUIP_REAL_3D_SCOUT_PRIVATE_STUDIO"
def script(d):
 return {p.relative_to(d/"src").as_posix():p.read_bytes() for p in sorted((d/"src").rglob("*.luau"))}
def blob(x):
 return hashlib.sha1(b"blob "+str(len(x)).encode()+b"\0"+x).hexdigest()
def contract(game,hud,reward):
 assert game.count('remote.Name = "TrapRaidersS1Remote"')==1
 assert game.count('remote.OnServerEvent:Connect(')==1
 assert game.count('RewardRules.finishRound(')==1
 assert game.count('RewardRules.claimFreeHatch(')==1
 assert game.count('RewardRules.equip(')==1
 assert game.count('RewardRules.requestScout(')==1
 assert game.count('Random.new()')==1
 assert 'rewardRng:NextInteger(1,10000)' in game
 assert 'RewardRules.startRound(rewardState,match.serial)' in game
 assert 'roundEligible[uid]=true' in game
 assert 'RewardRules.finishRound(rewardState,match.serial,eligible,rare)' in game
 assert 'lastFreeHatch[player]=item' in game
 assert 'rare[uid]=EXPERIMENTAL_FIVE_EGG_MODE and carry[player]=="N1" or false' in game
 assert 'h2Ids[player]=h2NextId' in game
 assert 'RewardRules.enroll(rewardState,h2NextId)' in game
 assert 'RewardRules.equip(rewardState,uid,item,ownScoutClass(player))' in game
 assert 'RewardRules.requestScout(rewardState,' in game
 assert 'math.floor(serverNow())' in game
 assert 'if not RunService:IsStudio() or match.phase~="ACTIVE" or not uid' in game
 assert 'or not alive or carry[player]~=nil' in game
 assert 'or getTeamName(player)=="NONE" or scoutModels[player]~=nil' in game
 assert 'if teamScouts>=SCOUT_MAX_TEAM then return end' in game
 assert 'if teamCountActive>=SCOUT_MAX_TEAM or scoutModels[player]~=nil then return false end' in game
 assert 'model.Name="EGG_RUMBLE_OWNED_REAL_SCOUT"' in game
 assert 'model.Parent=map.model' in game
 assert 'Instance.new("Highlight")' in game
 assert 'highlighted.DepthMode=Enum.HighlightDepthMode.Occluded' in game
 assert 'workspace:Raycast(root.Position,' in game
 assert '(enemyRoot.Position-root.Position).Magnitude<=SCOUT_MAX_LOS_DISTANCE' in game
 assert 'if ray==nil then return enemyRoot.Position,other.Character end' in game
 assert 'while t<SCOUT_DURATION and scoutModels[player]==model' in game
 assert 'match.serial==epoch and player.Parent==Players' in game
 assert 'cleanupScout(p)' in game and 'cleanupScout(player)' in game
 assert 'giveFreeHatchAtRealEnd() -- before any server egg owner drop/cleanup' in game
 assert 'if s.phase~="LOBBY" then return false, "LOBBY_ONLY" end' in reward
 assert 'if p.receipts[epoch] then return true, p.receipts[epoch], "ALREADY_GRANTED" end' in reward
 assert 'p.nextUseAt=now+COOLDOWN' in reward
 assert 'p.activeUntil=now+DURATION' in reward
 assert 'local DURATION = 5' in reward
 assert 'local COOLDOWN = 18' in reward
 assert 'owned={starter_scout=1}' in reward
 assert 'equipped="starter_scout"' in reward
 assert 'function Rules.export(s, uid)' in reward
 assert 'function Rules.restore(s, uid, record)' in reward
 assert 'DataStoreService' not in game and 'MarketplaceService' not in game
 assert 'local EXPERIMENTAL_FIVE_EGG_MODE = false' in game
 assert 'EXPERIMENTAL_FIVE_EGG_MODE=RunService:IsStudio() and chosenMode==ModeVote.SCORE' in game
 assert 'data.action == "MODE_VOTE"' in game
 assert game.count('elseif data.action == "EQUIP_SCOUT" then')==1
 assert game.count('elseif data.action == "ACTIVATE_SCOUT" then')==1
 assert game.count('elseif data.action == "WIND_BURST" then')==1
 assert game.count('elseif data.action == "PLACE_TRAP" then')==1
 assert 'ModeVote.tally(modeVotes,Players:GetPlayers())' in game
 assert 'H2Score.assertConserved(h2ScoreState)' in game
 assert 'FREE_HATCH' not in hud
 assert hud.count('local seq = 0')==1
 assert hud.count('remote:FireServer(')==3
 assert 'if kind == "MODE_VOTE" then' in hud
 assert 'elseif kind == "EQUIP_SCOUT" then' in hud
 assert 'itemId = role, seq = seq' in hud
 assert 'action("ACTIVATE_SCOUT",nil)' in hud
 assert 'action("EQUIP_SCOUT",entry.item)' in hud
 assert 'hatchLast' in hud and 'hatchOwned' in hud and 'hatchEquipped' in hud
 assert 'scoutCooldown' in hud and 'scoutActive' in hud
 assert 'BEAST_HATCH_EQUIP' in hud
 assert 'SummonRealScout' in hud and 'OwnedScoutsTitle' in hud
 assert 'modePanel.Visible=canChoose' in hud
 assert 'EGG RAID RUMBLE' in hud
 for bad in ('RemoteEvent','FireServer','DataStoreService','MarketplaceService','Instance.new('):
  assert bad not in reward,bad

class FullGameRewardAndScout(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.base=script(ORIG);cls.new=script(NEW)
  cls.game=cls.new["server/Game.server.luau"].decode()
  cls.hud=cls.new["client/HUD.client.luau"].decode()
  cls.reward=cls.new["server/RewardEquipRules.luau"].decode()
 def test_real32_original_scripts(self):self.assertEqual(len(self.base),32)
 def test_real33_scout_game_scripts(self):self.assertEqual(len(self.new),33)
 def test_new_module_only_one(self):self.assertEqual(set(self.new)-set(self.base),{"server/RewardEquipRules.luau"})
 def test_two_originals_only_overlaid(self):
  self.assertEqual({p for p in self.base if self.new[p]!=self.base[p]},
                   {"server/Game.server.luau","client/HUD.client.luau"})
 def test_thirty_original_game_sources_byte_unchanged(self):
  for p,v in self.base.items():
   if p not in ("server/Game.server.luau","client/HUD.client.luau"):
    self.assertEqual(v,self.new[p],p)
 def test_author_original_reward_module_unchanged(self):
  self.assertEqual(blob(self.new["server/RewardEquipRules.luau"]),
                   "0edf0993e41785b1e206b6ad09955a9984a346e5")
 def test_original_server_score_module_unchanged(self):
  self.assertEqual(blob(self.new["server/H2FiveEggRules.luau"]),
                   "0999d69391c176b9b95b04c5444d822e63d7ce04")
 def test_one_game_and_remote(self):
  self.assertEqual([p for p in self.new if p.endswith("/Game.server.luau")],["server/Game.server.luau"])
  self.assertEqual(self.game.count('remote.Name = "TrapRaidersS1Remote"'),1)
  self.assertEqual(self.game.count('remote.OnServerEvent:Connect('),1)
 def test_original_modes_unchanged(self):
  self.assertIn('ModeVote.tally(modeVotes,Players:GetPlayers())',self.game)
  self.assertIn('H2Score.assertConserved(h2ScoreState)',self.game)
 def test_full_authored_actual_game_contract(self):contract(self.game,self.hud,self.reward)
 def test_real_world_spawn_not_client_billboard_only(self):
  self.assertIn('model.Parent=map.model',self.game)
  self.assertIn('Instance.new("Model")',self.game)
  self.assertIn('Instance.new("Part")',self.game)
  self.assertIn('Instance.new("Highlight")',self.game)
  self.assertNotIn('local function spawnActualScout',self.hud)
 def test_round_finish_before_original_drop_for_rare_check(self):
  start=self.game.index("local function stopRound(")
  end=self.game.index("local function resetRound()",start)
  x=self.game[start:end]
  self.assertLess(x.index("giveFreeHatchAtRealEnd()"),x.index("dropEgg(p)"))
 def test_server_only_random_roll_never_remote(self):
  self.assertIn("rewardRng:NextInteger(1,10000)",self.game)
  self.assertNotIn('data.roll',self.game)
  self.assertNotIn('data.rare',self.game)
  self.assertNotIn('data.receipt',self.game)
 def test_session_only_not_persisted_receipt_is_honest(self):
  rec=json.loads((NEW/"SOURCE_LOCK.json").read_text())
  self.assertFalse(rec["DataStore_actual_persistence_implemented"])
  self.assertTrue(rec["free_hatch_items_lost_on_reconnect"])
  self.assertFalse(rec["real_Studio_2client_played"])
  self.assertFalse(rec["published"])
 def test_only_actual_beast_category_done(self):
  rec=json.loads((NEW/"SOURCE_LOCK.json").read_text())
  self.assertEqual(rec["current_actual_gameplay_category"],"BEAST ONLY")
  self.assertTrue(rec["other_five_categories_not_implemented"])
 def test_scanning_enemy_carrier_not_stolen_egg_authority(self):
  self.assertIn('if other~=player and carry[other]~=nil',self.game)
  self.assertIn('highlighted.DepthMode=Enum.HighlightDepthMode.Occluded',self.game)
  self.assertNotIn('remote:FireClient(player,{score=',self.game)
 def test_scout_cleanup_on_character_death_resets(self):
  self.assertIn('player.CharacterAdded:Connect(function(character)\n        cleanupScout(player)',self.game)
  self.assertIn('stopCanonical("ROUND_END")\n    giveFreeHatchAtRealEnd()',self.game)
  self.assertIn('dropEgg(player)\n    cleanupScout(player)',self.game)
 def test_starter_free_and_rare_only_cosmetic(self):
  self.assertIn('owned={starter_scout=1}',self.reward)
  self.assertIn('local DURATION = 5',self.reward)
  self.assertIn('local COOLDOWN = 18',self.reward)
 def test_equip_phase_before_game_active(self):
  self.assertIn('(match.phase~="LOBBY" and match.phase~="COUNTDOWN")',self.game)
  self.assertIn('if s.phase~="LOBBY" then return false, "LOBBY_ONLY" end',self.reward)
 def test_mutant_new_remote_rejected(self):
  with self.assertRaises(AssertionError):
   contract(self.game+'remote.Name = "TrapRaidersS1Remote"',self.hud,self.reward)
 def test_mutant_client_fakes_hatch_rejected(self):
  with self.assertRaises(AssertionError):
   contract(self.game.replace('rewardRng:NextInteger(1,10000)','data.roll'),self.hud,self.reward)
 def test_mutant_premature_live_score_rejected(self):
  with self.assertRaises(AssertionError):
   contract(self.game.replace('RunService:IsStudio() and chosenMode==ModeVote.SCORE',
                              'chosenMode==ModeVote.SCORE'),self.hud,self.reward)
 def test_mutant_no_carry_limit_rejected(self):
  with self.assertRaises(AssertionError):
   contract(self.game.replace('or not alive or carry[player]~=nil','or not alive'),self.hud,self.reward)
 def test_mutant_no_fog_or_wall_los_rejected(self):
  with self.assertRaises(AssertionError):
   contract(self.game.replace('if ray==nil then return enemyRoot.Position,other.Character end',
                              'return enemyRoot.Position,other.Character'),self.hud,self.reward)
 def test_mutant_scout_client_grants_rejected(self):
  with self.assertRaises(AssertionError):
   contract(self.game,self.hud+"remote:FireServer({action='FREE_HATCH'})",self.reward)
 def test_mutant_duplicate_reward_grant_rejected(self):
  with self.assertRaises(AssertionError):
   contract(self.game+'RewardRules.claimFreeHatch(rewardState,123,1,12)',self.hud,self.reward)
 def test_mutant_delete_cooldown_rejected(self):
  with self.assertRaises(AssertionError):
   contract(self.game,self.hud,self.reward.replace('p.nextUseAt=now+COOLDOWN','p.nextUseAt=now'))
 def test_mutant_server_physical_model_missing_rejected(self):
  with self.assertRaises(AssertionError):
   contract(self.game.replace('model.Parent=map.model','model.Parent=nil'),self.hud,self.reward)
if __name__=="__main__":unittest.main()
