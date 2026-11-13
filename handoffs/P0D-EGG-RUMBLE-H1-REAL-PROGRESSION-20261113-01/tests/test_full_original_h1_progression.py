"""Actual full H1 game provenance and adversarial source/authority QA.
No Roblox Engine, real DataStore service or Android claims.
"""
from pathlib import Path
import hashlib,json,unittest
H=Path(__file__).resolve()
REPO=H.parents[3];OWN=H.parents[1]
OLD=REPO/"handoffs/P0D-EGG-RUMBLE-DURABLE-HATCH-20261113-01/dist/EGG_RAID_RUMBLE_TWO_MODES_FREE_HATCH_DATASTORE_PRIVATE_STUDIO"
NEW=OWN/"dist/EGG_RAID_RUMBLE_H1_TWO_MODES_XP_MASTERY_DEV_STUDIO_ONLY"
def sources(root):
 return {p.relative_to(root/"src").as_posix():p.read_bytes() for p in (root/"src").rglob("*.luau")}
def blob(b):
 return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def security_contract(g,h,store,xp):
 assert g.count('remote.Name = "TrapRaidersS1Remote"')==1
 assert g.count('remote.OnServerEvent:Connect(')==1
 assert 'Progression = require(script.Parent:WaitForChild("ProgressionRules"))' in g
 assert 'Progression.recordEvent(round,eventId,kind,true)' in g
 assert 'Progression.previewXp(round,outcome,duration,true)' in g
 assert 'Progression.commit(profile,round,outcome,duration,true)' in g
 assert 'Progression.newRound(id,uid,mode,' in g
 assert 'if not RunService:IsStudio() or match.phase~="ACTIVE" then return end' in g
 assert 'local eventId=tostring(match.serial)..":E"..tostring(progressionEventSerial)' in g
 assert 'recordServerProgress(player,"PICKUP")' in g
 assert 'recordServerProgress(player,"DEPOSIT")' in g
 assert 'recordServerProgress(rec.owner,"DEFEND")' in g
 assert 'recordServerProgress(player,"EQUIP_USE")' in g
 assert 'if carry[player]~=nil and rec.owner~=nil then' in g
 assert '    settleProgressAtRealEnd(winner)' in g
 assert '    giveFreeHatchAtRealEnd()' in g
 assert g.index('settleProgressAtRealEnd(winner)\n    giveFreeHatchAtRealEnd()')>=0
 assert 'if proposal>0 then' in g
 assert 'reward.grantedXp<=Progression.XP_CAP_PER_ROUND' in g
 assert 'if canWriteProfile(player) and player.Parent==Players then' in g
 assert 'progressionStatus[player]="SAVE_FAILED"' in g
 assert 'progressionStatus[player]="SAVED"' in g
 assert 'progressionLastAward[player]=reward.grantedXp' in g
 assert 'PersistentHatch.settleProgress(' in g
 assert 'PersistentHatch.toProgressProfile(' in g
 assert 'ImmutableFakeServerEvents' not in g
 assert "data.xp" not in g and "data.level" not in g and "data.mastery" not in g
 assert "data.progress" not in g and "data.grantedXp" not in g
 assert 'modeVote' in g and 'RewardRules.finishRound(' in g
 assert 'EXPERIMENTAL_FIVE_EGG_MODE=RunService:IsStudio() and chosenMode==ModeVote.SCORE' in g
 assert 'local function spawnActualScout(' in g and 'model.Parent=map.model' in g
 assert 'DataStoreService:GetDataStore("EGG_RUMBLE_PRIVATE_STUDIO_HATCH_DEV_V1")' in g
 assert 'progress=cloneProgress(raw.progress)' in store
 assert 'function Store.toProgressProfile(' in store
 assert 'function Store.settleProgressTransition(' in store
 assert 'function Store.settleProgress(' in store
 assert 'store:UpdateAsync(key,function(original)' in store
 assert store.count('store:UpdateAsync(key,function(original)')==3
 assert 'Progression.commit(profile,round,data.outcome,data.duration,true)' in store
 assert 'Progression.recordEvent(round,event.id,event.kind,true)' in store
 assert 'if state.equipped==data.itemId then data.itemId else nil' in store or 'and state.equipped==data.itemId then data.itemId else nil' in store
 assert 'profile.claimedRoundIds[data.id]==true' in store
 assert 'if profile.settledCount>=Store.MAX_PROGRESS_ROUNDS then' in store
 assert 'if not Store.validate(state) then return nil,"POST_UPDATE_CORRUPT" end' in store
 assert 'if not Store.validate(updated) or not updated.progress' in store
 assert 'updated.progress.claimedRoundIds[data.id]~=true' in store
 assert 'Store.MAX_PROGRESS_ROUNDS=Progression.MAX_RECORDED_ROUNDS' in store
 assert 'if not safeProgressRecord(raw.progress) then return false end' in store
 assert 'SetAsync(' not in store.splitlines()[-120:] or 'store:SetAsync(' not in store
 assert not any('store:SetAsync(' in ln.split("--",1)[0] for ln in store.splitlines())
 assert 'P.XP_CAP_PER_ROUND = 150' in xp
 assert 'P.MATCH_COMPLETION_XP = 50' in xp
 assert 'P.MIN_ELIGIBLE_SECONDS = 60' in xp
 assert 'if round.objectiveEvents<1 then return 0 end' in xp
 assert 'if profile.claimedRoundIds[round.id]~=nil then return nil end' in xp or 'profile.claimedRoundIds[round.id]~=nil then return nil end' in xp
 assert 'gameplayStatsIncreased=false' in xp and 'requiresPaidPurchase=false' in xp
 assert 'RealH1ServerLevel' in h and 'progressLastAward' in h
 assert 'progressSaveStatus' in h and '保存未確認' in h
 assert h.count("local seq = 0")==1 and h.count("remote:FireServer(")==3

class TestRealGameXPAndPersistence(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.old=sources(OLD);cls.all=sources(NEW)
  cls.g=cls.all["server/Game.server.luau"].decode()
  cls.h=cls.all["client/HUD.client.luau"].decode()
  cls.store=cls.all["server/PersistentHatchStore.luau"].decode()
  cls.xp=cls.all["server/ProgressionRules.luau"].decode()
 def test_base34(self):self.assertEqual(len(self.old),34)
 def test_result35(self):self.assertEqual(len(self.all),35)
 def test_only_original_281_module_added(self):
  self.assertEqual(set(self.all)-set(self.old),{"server/ProgressionRules.luau"})
 def test_exactly_three_game_overlay_files(self):
  self.assertEqual({k for k in self.old if self.all[k]!=self.old[k]},
   {"server/Game.server.luau","client/HUD.client.luau","server/PersistentHatchStore.luau"})
 def test_original_other31_byte_identical(self):
  for k,v in self.old.items():
   if k not in ("server/Game.server.luau","client/HUD.client.luau","server/PersistentHatchStore.luau"):
    self.assertEqual(self.all[k],v,k)
 def test_imported_progression_author_exact(self):
  self.assertEqual(blob(self.all["server/ProgressionRules.luau"]),
   "a72830b039a46ca02d02f6aab7d6a4805bec8860")
 def test_original_275_reward_exact(self):
  self.assertEqual(blob(self.all["server/RewardEquipRules.luau"]),
   "0edf0993e41785b1e206b6ad09955a9984a346e5")
 def test_original_five_egg_score_exact(self):
  self.assertEqual(blob(self.all["server/H2FiveEggRules.luau"]),
   "0999d69391c176b9b95b04c5444d822e63d7ce04")
 def test_all_server_security_contract(self):
  security_contract(self.g,self.h,self.store,self.xp)
 def test_one_original_game_and_remote(self):
  self.assertEqual([k for k in self.all if k.endswith("/Game.server.luau")],["server/Game.server.luau"])
  self.assertEqual(self.g.count('remote.OnServerEvent:Connect('),1)
 def test_saved_inventory_atomic_progress(self):
  self.assertIn('progress=cloneProgress(raw.progress)',self.store)
  self.assertIn('Store.grantTransition(original,receipt,item)',self.store)
  self.assertIn('Store.equipTransition(original,item)',self.store)
  self.assertIn('Store.settleProgressTransition(original,uid,fixed)',self.store)
 def test_players_not_given_xp_for_scout_only(self):
  self.assertIn('if round.objectiveEvents<1 then return 0 end',self.xp)
 def test_no_xp_chasing_damage_or_kills(self):
  self.assertNotIn('recordServerProgress(player,"ATTACK")',self.g)
  self.assertNotIn('recordServerProgress(player,"DAMAGE")',self.g)
  self.assertNotIn('recordServerProgress(player,"KILL")',self.g)
 def test_no_p2w_stat_buffs(self):
  self.assertIn('gameplayStatsIncreased=false',self.xp)
  self.assertIn('requiresPaidPurchase=false',self.xp)
 def test_true_studio_api_not_claimed_verified(self):
  d=json.loads((NEW/"SOURCE_LOCK.json").read_text())
  self.assertFalse(d["actual_Roblox_DataStore_service_executed"])
  self.assertFalse(d["owner_fun_gate_accepted"])
 def test_lobby_classic_five_votes_preserved(self):
  self.assertIn('ModeVote.tally(modeVotes,Players:GetPlayers())',self.g)
  self.assertIn('EXPERIMENTAL_FIVE_EGG_MODE=RunService:IsStudio() and chosenMode==ModeVote.SCORE',self.g)
 def test_mutant_xp_remote_injection_rejected(self):
  with self.assertRaises(AssertionError):
   security_contract(self.g+'data.xp=999999',self.h,self.store,self.xp)
 def test_mutant_no_match_activity_rejected(self):
  with self.assertRaises(AssertionError):
   security_contract(self.g,self.h,self.store,
     self.xp.replace('if round.objectiveEvents<1 then return 0 end','if false then return 0 end'))
 def test_mutant_change_xp_cap_rejected(self):
  with self.assertRaises(AssertionError):
   security_contract(self.g,self.h,self.store,
     self.xp.replace('P.XP_CAP_PER_ROUND = 150','P.XP_CAP_PER_ROUND = 999999'))
 def test_mutant_add_p2w_damage_rejected(self):
  with self.assertRaises(AssertionError):
   security_contract(self.g,self.h,self.store,
     self.xp.replace('gameplayStatsIncreased=false','gameplayStatsIncreased=true'))
 def test_mutant_duplicate_game_authority_rejected(self):
  with self.assertRaises(AssertionError):
   security_contract(self.g+'remote.Name = "TrapRaidersS1Remote"',self.h,self.store,self.xp)
 def test_mutant_progress_wipes_inventory_rejected(self):
  with self.assertRaises(AssertionError):
   security_contract(self.g,self.h,
      self.store.replace('progress=cloneProgress(raw.progress)','progress=nil'),self.xp)
 def test_mutant_change_receipt_identity_rejected(self):
  with self.assertRaises(AssertionError):
   security_contract(self.g.replace('local eventId=tostring(match.serial)..":E"..tostring(progressionEventSerial)',
       'local eventId=tostring(progressionEventSerial)'),self.h,self.store,self.xp)
 def test_mutant_unsafe_client_award_rejected(self):
  with self.assertRaises(AssertionError):
   security_contract(self.g.replace('Progression.recordEvent(round,eventId,kind,true)',
       'Progression.recordEvent(round,eventId,kind,data.confirmed)'),self.h,self.store,self.xp)
 def test_mutant_progress_explicit_unbounded_rejected(self):
  with self.assertRaises(AssertionError):
   security_contract(self.g,self.h,self.store.replace('if profile.settledCount>=Store.MAX_PROGRESS_ROUNDS then',
      'if false then'),self.xp)
 def test_mutant_studio_live_xp_rejected(self):
  with self.assertRaises(AssertionError):
   security_contract(self.g.replace('if not RunService:IsStudio() or match.phase~="ACTIVE" then return end',
     'if match.phase~="ACTIVE" then return end'),self.h,self.store,self.xp)
 def test_mutant_level_hud_secondary_remote_rejected(self):
  with self.assertRaises(AssertionError):
   security_contract(self.g,self.h+'remote:FireServer({action="AWARD_XP"})',self.store,self.xp)
 def test_mutant_unverified_scout_credit_rejected(self):
  with self.assertRaises(AssertionError):
   security_contract(self.g.replace('recordServerProgress(player,"EQUIP_USE")',
     'recordServerProgress(player,"ANY")'),self.h,self.store,self.xp)
 def test_mutant_progress_confirm_before_store_rejected(self):
  with self.assertRaises(AssertionError):
   security_contract(self.g.replace('progressionStatus[player]="SAVED"',
      'progressionStatus[player]="ALWAYS_SAVED"'),self.h,self.store,self.xp)
if __name__=="__main__":unittest.main()
