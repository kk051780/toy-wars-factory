#!/usr/bin/env python3
"""Execute the unchanged real #281 ProgressionRules with ACTUAL modified H1
atomic HatchStore source in native upstream Luau, injecting only a fake isolated
DataStore API. NO Roblox DataStore service call, user session or Studio here.
"""
from pathlib import Path
import argparse,hashlib
OWN=Path(__file__).resolve().parents[1]
SOURCE=OWN/"inputs/PersistentHatchStore.luau"
CORE=OWN/"inputs/ProgressionRules.luau"
def blob(b):return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
original_core=CORE.read_bytes()
assert blob(original_core)=="a72830b039a46ca02d02f6aab7d6a4805bec8860"
store=SOURCE.read_text(encoding="utf-8")
old='local Progression=require(script.Parent:WaitForChild("ProgressionRules"))'
assert store.count(old)==1
store=store.replace(old,"local Progression=ORIGINAL_P281_POLICY",1)
p=argparse.ArgumentParser();p.add_argument("--write",type=Path,required=True)
args=p.parse_args()
source=r'''
local ORIGINAL_P281_POLICY=(function()
'''+original_core.decode("utf-8")+r'''
end)()
local S=(function()
'''+store+r'''
end)()
local tests=0
local function eq(actual,expected,label)
 tests+=1
 assert(actual==expected,label.." expected="..tostring(expected).." actual="..tostring(actual))
end
local U=52345678901 -- actual modern UserId can exceed #281's 100m bound.
eq(ORIGINAL_P281_POLICY.newProfile(U),nil,"original_policy_high_uid_would_fail")
local policyUid=S.policyUserId(U)
eq(type(policyUid),"number","mapped_policy_uid")
eq(policyUid>0 and policyUid<100000000,true,"mapped_original_policy_valid")
eq(S.policyUserId(-1),nil,"negative_uid_not_data_store")
eq(S.policyUserId(0),nil,"zero_uid")
eq(S.policyUserId(1.5),nil,"fraction_uid")
eq(S.policyUserId(9999999999999999),nil,"too_large_uid")
local ds={values={},twice=false,failBefore=false,failAfter=false,writes=0}
function ds:GetAsync(k,options)
 if self.failBefore then error("Studio API disabled") end
 return self.values[k]
end
function ds:UpdateAsync(k,callback)
 if self.failBefore then error("Backend denied before commit") end
 local before=self.values[k]
 local nextData=callback(before)
 if self.twice then nextData=callback(before) end
 if nextData~=nil then self.values[k]=nextData;self.writes+=1 end
 if self.failAfter then error("Caller received network error after COMMITTED") end
 return self.values[k]
end
local function round(id,mode,item,outcome,duration,...)
 return {id=id,mode=mode,itemId=item,outcome=outcome,duration=duration,events={...}}
end
local function ev(id,kind)return {id=id,kind=kind} end
local roundIdA=S.makeReceipt("XP_accountGUID_123456789abc",1)
local roundIdB=S.makeReceipt("XP_accountGUID_123456789abc",2)
local roundIdC=S.makeReceipt("OTHER_job_abc_123456789",1)
eq(type(roundIdA),"string","job_guid_id")
eq(roundIdA~=roundIdB,true,"same_job_two_round_ids")
eq(roundIdA~=roundIdC,true,"two_server_unique_id")
local old=S.blank()
eq(S.validate(old),true,"prior_schema1_no_progress_valid")
eq(old.progress,nil,"migration_without_progress")
eq(S.toProgressProfile(old,U).level,1,"legacy_player_starts_lv1")
eq(S.toProgressProfile(old,U).playerUserId,policyUid,"store_mapped_id_matches")
local loaded,profile,status=S.load(ds,U)
eq(loaded,true,"account_load")
eq(profile.progress,nil,"new_profile_no_progress")
eq(status,"LOADED","load_name")
local first=round(roundIdA,"CLASSIC","starter_scout","LOSS",120,
    ev("PICKUP_auth1","PICKUP"),ev("SCOUT_used1","EQUIP_USE"))
local ok,a,receipt=S.settleProgress(ds,U,first)
eq(ok,true,"legitimate_game_one_egg_source")
eq(receipt,"PROGRESS_PERSISTED_OR_ALREADY_SETTLED","real_update_ack")
eq(S.validate(a),true,"XP_record_valid")
eq(a.progress.level,2,"first_match_reaches_lv2")
eq(a.progress.xp,12,"first_match_72_xp_60_lv2_12_left")
eq(a.progress.mastery.starter_scout.level,1,"starter_lv1")
eq(a.progress.mastery.starter_scout.xp,12,"real_scout_use_12_mastery")
eq(a.progress.settledCount,1,"one_settlement")
eq(a.progress.claimedRoundIds[roundIdA],true,"one_globally_unique_round")
eq(a.owned.starter_scout,1,"original_owned_not_lost")
eq(a.equipped,"starter_scout","original_equip_not_lost")
local again,b,twiceStatus=S.settleProgress(ds,U,first)
eq(again,true,"same_round_idempotent_ack")
eq(b.progress.level,2,"no_duplicate_level")
eq(b.progress.xp,12,"no_duplicate_xp")
eq(b.progress.settledCount,1,"never_double_settle")
local fake=round(roundIdA,"CLASSIC","starter_scout","WIN",320,
    ev("PICKUP_forged","PICKUP"),ev("DEPOSIT_forged","DEPOSIT"))
local same,out=S.settleProgress(ds,U,fake)
eq(same,true,"same_receipt_changing_outcome_not_reroll")
eq(out.progress.xp,12,"original_reward_locked")
local grant,prize=S.grant(ds,U,S.makeReceipt("HATCH_job_same_user_123",1),"star_scout")
eq(grant,true,"free_hatch_with_XP_data")
eq(prize.owned.star_scout,1,"new_rare_owned")
eq(prize.progress.level,2,"free_hatch_does_not_wipe_xp")
eq(prize.progress.mastery.starter_scout.xp,12,"free_hatch_keeps_mastery")
local equipped,pEquipped=S.equip(ds,U,"star_scout")
eq(equipped,true,"equip_owned_rare")
eq(pEquipped.equipped,"star_scout","rare_equip_stored")
eq(pEquipped.progress.level,2,"equip_does_not_reset_level")
eq(pEquipped.progress.claimedRoundIds[roundIdA],true,"equip_does_not_replay_round")
local second=round(roundIdB,"SCORE","star_scout","WIN",220,
    ev("PICKUP_scored2","PICKUP"),ev("DEPOSIT_scored2","DEPOSIT"),
    ev("SCOUT_used2","EQUIP_USE"))
ds.twice=true
local won,pWon=S.settleProgress(ds,U,second)
eq(won,true,"atomic_backend_retries_callback_twice")
eq(pWon.progress.level,3,"first_then_win_reaches_level3")
eq(pWon.progress.xp,24,"lv3_24_remaining")
eq(pWon.progress.mastery.star_scout.xp,12,"rare_equipped_actually_used")
eq(pWon.progress.mastery.starter_scout.xp,12,"starter_mastery_stays")
eq(pWon.owned.star_scout,1,"owned_rare_stays_after_xp")
eq(pWon.progress.settledCount,2,"only_two_valid_rounds")
ds.twice=false
local restored,readBack=S.load(ds,U)
eq(restored,true,"mock_real_reconnect_api_get")
eq(readBack.progress.level,3,"relogin_mock_level3")
eq(readBack.progress.mastery.star_scout.xp,12,"relogin_mock_mastery")
eq(readBack.owned.star_scout,1,"relogin_mock_owned")
eq(readBack.equipped,"star_scout","relogin_mock_equipped")
eq(S.toProgressProfile(readBack,U).level,3,"restored_authoritative_progress")
eq(S.toRulesRecord(readBack).owned.star_scout,1,"unmodified_original_hatch_adapter_compatible")
local afterError=round(roundIdC,"CLASSIC","star_scout","DRAW",160,
    ev("PICKUP_s3","PICKUP"),ev("GUARD_def3","DEFEND"))
ds.failAfter=true
local unknownResult=S.settleProgress(ds,U,afterError)
eq(unknownResult,false,"ambiguous_network_error_never_falsely_saved")
eq(ds.values["U_"..tostring(U)].progress.claimedRoundIds[roundIdC],
   true,"backend_committed_despite_caller_error")
local prevProgress=ds.values["U_"..tostring(U)].progress.level
local prevCount=ds.values["U_"..tostring(U)].progress.settledCount
ds.failAfter=false
local retry,r=S.settleProgress(ds,U,afterError)
eq(retry,true,"retry_same_guid_receipt_confirms")
eq(r.progress.claimedRoundIds[roundIdC],true,"retry_sees_same_receipt")
eq(r.progress.level,prevProgress,"after_commit_error_no_double_level")
eq(r.progress.settledCount,prevCount,"after_commit_error_no_duplicate_count")
local interleaved=S.makeReceipt("second_server_XP_run_99887766",5)
local d=round(interleaved,"SCORE","star_scout","LOSS",150,ev("D4","DEPOSIT"))
local cross,merged=S.settleProgress(ds,U,d)
eq(cross,true,"second_server_atomic_merge")
eq(merged.progress.claimedRoundIds[roundIdA],true,"preserve_server_a_round")
eq(merged.progress.claimedRoundIds[roundIdB],true,"preserve_server_a_other_round")
eq(merged.progress.claimedRoundIds[roundIdC],true,"preserve_server_a_retry")
eq(merged.progress.claimedRoundIds[interleaved],true,"persist_server_b_round")
eq(merged.owned.star_scout,1,"second_server_doesnt_wipe_rare")
local previousXP=merged.progress.xp
local noObj=round(S.makeReceipt("no_impact_run_123456789",6),
    "CLASSIC","star_scout","WIN",120,ev("only_scout","EQUIP_USE"))
eq(S.settleProgress(ds,U,noObj),false,"equip_only_no_afk_xp")
eq(ds.values["U_"..tostring(U)].progress.xp,previousXP,"no_obj_no_change")
local tooSoon=round(S.makeReceipt("too_short_run_12345678",7),
    "CLASSIC","star_scout","WIN",30,ev("PICKUP_short","PICKUP"))
eq(S.settleProgress(ds,U,tooSoon),false,"less_than_60_no_xp")
local tooLong=round(S.makeReceipt("too_long_run_12345678",8),
    "CLASSIC","star_scout","WIN",361,ev("PICKUP_long","PICKUP"))
eq(S.settleProgress(ds,U,tooLong),false,"duration_over360_rejected")
local duplicate=round(S.makeReceipt("repeated_event_ids_12345678",9),
    "SCORE","star_scout","LOSS",120,ev("duplicate_same","PICKUP"),
    ev("duplicate_same","DEPOSIT"))
eq(S.settleProgress(ds,U,duplicate),false,"duplicate_event_no_xp")
local unknown=round(S.makeReceipt("unknown_event_123456789",10),
    "SCORE","star_scout","LOSS",120,ev("dangerous","ADMIN_XP"))
eq(S.settleProgress(ds,U,unknown),false,"unknown_event_no_xp")
local tampered=round(S.makeReceipt("unowned_use_123456789",11),
    "CLASSIC","admin_dragon","LOSS",120,
    ev("picked_up","PICKUP"),ev("use_item","EQUIP_USE"))
local noCheat,derived=S.settleProgress(ds,U,tampered)
eq(noCheat,true,"allow_objective_xp_but_ignore_fake_mastery_item")
eq(derived.progress.mastery.admin_dragon,nil,"no_unowned_mastery")
eq(derived.progress.mastery.star_scout.xp,12,"real_mastery_unchanged")
ds.failBefore=true
eq(S.load(ds,U),false,"Studio_disabled_doesnt_claim_read")
eq(S.settleProgress(ds,U,round(S.makeReceipt("write_denied_123456789",12),
   "CLASSIC","star_scout","LOSS",120,ev("p12","PICKUP"))),
   false,"Studio_disabled_doesnt_claim_write")
ds.failBefore=false
local badOwned=S.blank()
badOwned.owned.admin_dragon=999
eq(S.validate(badOwned),false,"old_item_validation_still_working")
local badProgress=S.blank()
badProgress.progress={level=1,xp=60,mastery={},claimedRoundIds={},settledCount=0}
eq(S.validate(badProgress),false,"unapplied_level_threshold_bad")
local badMastery=S.blank()
badMastery.progress={level=1,xp=0,mastery={admin_dragon={level=3,xp=0}},
   claimedRoundIds={},settledCount=0}
eq(S.validate(badMastery),false,"unowned_unknown_mastery_bad")
local badRounds=S.blank()
badRounds.progress={level=1,xp=0,mastery={},
    claimedRoundIds={[roundIdA]=true},settledCount=0}
eq(S.validate(badRounds),false,"mismatched_claimed_round_count")
local negative=S.blank()
negative.progress={level=-1,xp=0,mastery={},claimedRoundIds={},settledCount=0}
eq(S.validate(negative),false,"negative_level_bad")
local invalid=S.blank()
invalid.progress={level=1,xp=0,mastery={},claimedRoundIds={},settledCount=0}
invalid.owned.admin_dragon=1
ds.values["U_41"]=invalid
eq(S.settleProgress(ds,41,round(S.makeReceipt("other_corrupt_server_123",13),
    "CLASSIC","starter_scout","LOSS",150,ev("x","PICKUP"))),
    false,"invalid_old_saves_fail_closed")
eq(ds.values["U_41"].owned.admin_dragon,1,"invalid_item_not_deleted_silently")
local limited=S.blank()
limited.progress={level=1,xp=0,mastery={},claimedRoundIds={},settledCount=S.MAX_PROGRESS_ROUNDS}
for i=1,S.MAX_PROGRESS_ROUNDS do
 limited.progress.claimedRoundIds[S.makeReceipt("bounded_roundledger_session_998",i)]=true
end
eq(S.validate(limited),true,"full4096_roundledger_valid")
local last=S.makeReceipt("bounded_roundledger_session_998",S.MAX_PROGRESS_ROUNDS+1)
local nothing=S.settleProgressTransition(limited,2,
    round(last,"CLASSIC","starter_scout","LOSS",150,ev("full","PICKUP")))
eq(nothing,nil,"4096_full_fails_closed_not_silent_eviction")
local many=S.blank()
ds.values["U_80"]=many
for i=1,90 do
 local rid=S.makeReceipt("ninety_true_matches_88888",i)
 local summary=round(rid,if i%2==0 then "CLASSIC" else "SCORE",
     "starter_scout","LOSS",120,ev("valid_egg_"..tostring(i),"PICKUP"))
 local good,record=S.settleProgress(ds,80,summary)
 eq(good,true,"many_distinct_genuine_rounds_"..tostring(i))
 eq(record.progress.settledCount,i,"many_round_ids_not_duplicate_"..tostring(i))
end
local final=ds.values["U_80"]
eq(final.progress.level>2,true,"many_real_rounds_progress")
eq(final.owned.starter_scout,1,"many_rounds_never_wipe_own_item")
eq(final.equipped,"starter_scout","many_rounds_never_wipe_equip")
print("EGG_RUMBLE_NATIVE_ORIGINAL_PROGRESS_AND_INVENTORY_UPDATEASYNC_ATOMIC_PASS_"..tostring(tests))
'''
args.write.parent.mkdir(parents=True,exist_ok=True)
args.write.write_text(source,encoding="utf-8")
print("P0D_GENUINE_NATIVE_IMPORTED_ORIGINAL_281_WITH_REAL_H1_STORE_LUAU_TEST_GENERATED",len(source))
