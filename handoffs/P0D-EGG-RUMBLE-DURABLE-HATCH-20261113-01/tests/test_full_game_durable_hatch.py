"""The ACTUAL unchanged original 33-game sources plus one persistence adapter.
These are source+mutation tests, NOT actual Roblox DataStore or human Studio QA.
"""
from pathlib import Path
import hashlib,json,unittest
HERE=Path(__file__).resolve();REPO=HERE.parents[3];OWN=HERE.parents[1]
OLD=REPO/"handoffs/P0D-EGG-RUMBLE-REAL-SCOUT-20261113-01/dist/EGG_RAID_RUMBLE_FREE_HATCH_EQUIP_REAL_3D_SCOUT_PRIVATE_STUDIO"
NEW=OWN/"dist/EGG_RAID_RUMBLE_TWO_MODES_FREE_HATCH_DATASTORE_PRIVATE_STUDIO"
def files(root):
 return {x.relative_to(root/"src").as_posix():x.read_bytes() for x in (root/"src").rglob("*.luau")}
def blob(b):
 return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def unsafe_contract(game,hud,store):
 assert 'DataStoreService:GetDataStore("EGG_RUMBLE_PRIVATE_STUDIO_HATCH_DEV_V1")' in game
 assert 'if RunService:IsStudio() then\n    local ok,result=pcall' in game
 assert 'DataStoreGetOptions.new()' in game
 assert 'option.UseCache=false' in game
 assert 'PersistentHatch.load(studioHatchStore,player.UserId,option)' in game
 assert 'PersistentHatch.grant(' in game and 'PersistentHatch.equip(' in game
 assert 'PersistentHatch.makeReceipt(hatchSessionGUID,match.serial)' in game
 assert 'RewardRules.finishRound(rewardState,match.serial,eligible,rare)' in game
 assert 'rewardRng:NextInteger(1,10000)' in game
 assert 'persistenceState[player]="SAVED"' in game
 assert 'persistenceState[player]="SAVE_FAILED"' in game
 assert 'persistenceState[player]="LOCAL_ONLY"' in game
 assert 'local snapshotFor: (Player) -> any' in game
 assert 'snapshotFor = function(player: Player)' in game
 assert 'hatchSaveStatus = persistenceState[player] or "LOCAL_ONLY"' in game
 assert 'hatchSaved = persistenceState[player]=="SAVED"' in game
 assert 'hatchSessionGUID=HttpService:GenerateGUID(false)' in game
 assert 'if not RunService:IsStudio() or player.UserId<=0 or not studioHatchStore then' in game
 assert 'remote.Name = "TrapRaidersS1Remote"' in game
 assert game.count('remote.Name = "TrapRaidersS1Remote"')==1
 assert game.count('remote.OnServerEvent:Connect(')==1
 assert game.count('RewardRules.claimFreeHatch(')==1
 assert 'model.Parent=map.model' in game
 assert 'H2Score.assertConserved(h2ScoreState)' in game
 assert 'EXPERIMENTAL_FIVE_EGG_MODE=RunService:IsStudio() and chosenMode==ModeVote.SCORE' in game
 assert 'outstandingWrites+=1' in game and 'outstandingWrites-=1' in game
 assert 'game:BindToClose(function()' in game
 assert 'lastFreeHatch[player]=grantedItem' in game
 assert 'if canWriteProfile(player) then' in game
 assert 'if persistenceState[player]=="LOADING" then return end' in game
 assert 'rewardState.phase~="LOBBY"' in game
 assert 'RewardRules.restore(rewardState,uid,canonical)' in game
 assert 'delayedRestore[player]=true' in game
 assert 'PersistentHatch.toRulesRecord(profile)' in game
 assert 'if not Store.validate(raw) then return nil end' in store
 assert 'function Store.makeReceipt(' in store
 assert 'function Store.load(' in store and 'store:GetAsync(key,options)' in store
 assert store.count('store:UpdateAsync(key,function(original)')==2
 assert 'if state.receipts[receipt] then' in store
 assert 'state.receipts[receipt]=item' in store
 assert 'if n>=Store.MAX_RECEIPTS then' in store
 assert 'return nil,"CORRUPT_RECORD"' in store
 assert 'if not Store.validate(updated)' in store
 assert 'if Store.ITEMS[confirmed]~=true then' in store
 assert 'if Store.ITEMS[raw.equipped]~=true' in store
 assert 'Store.MAX_RECEIPTS=2048' in store
 assert 'raw.owned.starter_scout~=1' in store
 assert 'DataStoreService' not in store
 assert 'store:SetAsync(' not in store
 assert not any("task.wait(" in line.split("--",1)[0] for line in store.splitlines())
 assert 'RemoteEvent' not in store
 assert 'FireServer' not in store
 assert 'MarketplaceService' not in store
 assert 'ActualSaveStatus' in hud
 assert 'SAVE_FAILED' in hud and 'LOCAL_ONLY' in hud and 'LOADING' in hud and 'SAVED' in hud
 assert '保存サーバー応答あり（再ログイン検証は別）' in hud
 assert '保存未確認' in hud
 assert hud.count('local seq = 0')==1 and hud.count('remote:FireServer(')==3
 assert 'BEAST_HATCH_EQUIP' in hud and 'modePanel.Visible=canChoose' in hud

class RealFullGamePersistentHatchQA(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.old=files(OLD);cls.new=files(NEW)
  cls.g=cls.new["server/Game.server.luau"].decode()
  cls.h=cls.new["client/HUD.client.luau"].decode()
  cls.s=cls.new["server/PersistentHatchStore.luau"].decode()
 def test_original_complete33(self):self.assertEqual(len(self.old),33)
 def test_new_complete34(self):self.assertEqual(len(self.new),34)
 def test_unique_new_store(self):self.assertEqual(set(self.new)-set(self.old),{"server/PersistentHatchStore.luau"})
 def test_only_2_original_overlays(self):
  self.assertEqual({p for p in self.old if self.old[p]!=self.new[p]},
                   {"server/Game.server.luau","client/HUD.client.luau"})
 def test_other31_byte_identical(self):
  for name,raw in self.old.items():
   if name not in ("server/Game.server.luau","client/HUD.client.luau"):
    self.assertEqual(raw,self.new[name],name)
 def test_original_owner_pure_reward_untouched(self):
  self.assertEqual(blob(self.new["server/RewardEquipRules.luau"]),
                   "0edf0993e41785b1e206b6ad09955a9984a346e5")
 def test_original_h2_scoring_untouched(self):
  self.assertEqual(blob(self.new["server/H2FiveEggRules.luau"]),
                   "0999d69391c176b9b95b04c5444d822e63d7ce04")
 def test_one_authority_game_and_remote(self):
  self.assertEqual(len([p for p in self.new if p.endswith("/Game.server.luau")]),1)
  self.assertEqual(self.g.count('remote.OnServerEvent:Connect('),1)
 def test_full_genuine_game_source_security_contract(self):unsafe_contract(self.g,self.h,self.s)
 def test_only_studio_private_store(self):
  self.assertIn('if RunService:IsStudio() then\n    local ok,result=pcall',self.g)
  self.assertIn('EGG_RUMBLE_PRIVATE_STUDIO_HATCH_DEV_V1',self.g)
 def test_owner_status_never_auto_certifies_reconnect(self):
  x=json.loads((NEW/"SOURCE_LOCK.json").read_text())
  self.assertFalse(x["real_Studio_API_save_reconnect_verified"])
  self.assertFalse(x["actual_FUN_gate_accepted"])
 def test_2_game_modes_remain_untouched(self):
  self.assertIn('ModeVote.tally(modeVotes,Players:GetPlayers())',self.g)
  self.assertIn('EXPERIMENTAL_FIVE_EGG_MODE=RunService:IsStudio() and chosenMode==ModeVote.SCORE',self.g)
 def test_no_paid_or_client_reward_remote(self):
  self.assertNotIn('data.roll',self.g)
  self.assertNotIn('data.rewardId',self.g)
  self.assertNotIn('data.receiptId',self.g)
  self.assertNotIn('SetAsync(',self.g)
 def test_mutant_setasync_overwrites_rejected(self):
  with self.assertRaises(AssertionError):
   unsafe_contract(self.g,self.h,self.s.replace('store:UpdateAsync(key,function(original)','store:SetAsync(key,function(original)'))
 def test_mutant_unguarded_store_live_access_rejected(self):
  with self.assertRaises(AssertionError):
   unsafe_contract(self.g.replace('if RunService:IsStudio() then\n    local ok,result=pcall',
                                   'if true then\n    local ok,result=pcall'),self.h,self.s)
 def test_mutant_fake_saved_banner_rejected(self):
  with self.assertRaises(AssertionError):
   unsafe_contract(self.g,self.h.replace('保存サーバー応答あり（再ログイン検証は別）','ずっと保存済！'),self.s)
 def test_mutant_remove_global_receipt_rejected(self):
  with self.assertRaises(AssertionError):
   unsafe_contract(self.g.replace('PersistentHatch.makeReceipt(hatchSessionGUID,match.serial)',
                                  'tostring(match.serial)'),self.h,self.s)
 def test_mutant_duplicate_rewards_rejected(self):
  with self.assertRaises(AssertionError):
   unsafe_contract(self.g+'RewardRules.claimFreeHatch(rewardState,11,1,3)',self.h,self.s)
 def test_mutant_receipt_replay_allowed_rejected(self):
  with self.assertRaises(AssertionError):
   unsafe_contract(self.g,self.h,self.s.replace('if state.receipts[receipt] then',
                                                   'if false then'))
 def test_mutant_stale_hud_forged_ok_rejected(self):
  with self.assertRaises(AssertionError):
   unsafe_contract(self.g.replace('hatchSaved = persistenceState[player]=="SAVED"',
                                  'hatchSaved = true'),self.h,self.s)
 def test_mutant_corrupt_overwrite_rejected(self):
  with self.assertRaises(AssertionError):
   unsafe_contract(self.g,self.h,self.s.replace('if not Store.validate(raw) then return nil end',
                                   'if not Store.validate(raw) then return Store.blank() end'))
 def test_mutant_unrestricted_client_score_rejected(self):
  with self.assertRaises(AssertionError):
   unsafe_contract(self.g.replace('RunService:IsStudio() and chosenMode==ModeVote.SCORE',
                                   'chosenMode==ModeVote.SCORE'),self.h,self.s)
 def test_mutant_client_second_seq_rejected(self):
  with self.assertRaises(AssertionError):
   unsafe_contract(self.g,self.h+'local seq = 0',self.s)
 def test_mutant_no_receipt_cap_rejected(self):
  with self.assertRaises(AssertionError):
   unsafe_contract(self.g,self.h,self.s.replace('if n>=Store.MAX_RECEIPTS then','if false then'))
 def test_mutant_bypass_datastore_validation_rejected(self):
  with self.assertRaises(AssertionError):
   unsafe_contract(self.g,self.h,self.s.replace('if not Store.validate(updated)','if false'))
if __name__=="__main__":unittest.main()
