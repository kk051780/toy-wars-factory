#!/usr/bin/env python3
"""Execute actual native Luau persistence module with hostile mocked datastore.
This is NOT a real Roblox DataStore API or proof of reconnect persistence.
"""
from pathlib import Path
import hashlib,argparse
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"inputs/PersistentHatchStore.luau"
EXPECTED="47541bdc4f28516d6edcec6624890bcae88bde32"
raw=SOURCE.read_bytes()
gitblob=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
assert gitblob==EXPECTED,(gitblob,EXPECTED)
p=argparse.ArgumentParser();p.add_argument("--write",required=True,type=Path)
args=p.parse_args()
test=r'''
local S=(function()
'''+raw.decode("utf-8")+r'''
end)()
local n=0
local function check(v,expected,label)
 n+=1
 assert(v==expected,label.." expected="..tostring(expected).." got="..tostring(v))
end
local db={}
local ds={values=db,failBefore=false,failAfter=false,twice=false,writes=0,reads=0}
function ds:GetAsync(k,options)
 self.reads+=1
 if self.failBefore then error("disabled_studio_access_403") end
 return self.values[k]
end
function ds:UpdateAsync(k,cb)
 if self.failBefore then error("throttle_before_write") end
 local original=self.values[k]
 local nextValue=cb(original)
 if self.twice then nextValue=cb(original) end
 if nextValue~=nil then
  self.values[k]=nextValue
  self.writes+=1
 end
 if self.failAfter then error("ambiguous_network_error_after_server_commit") end
 return self.values[k]
end
local a=S.makeReceipt("12345678-1234-1234-1234-123456789abc",1)
local b=S.makeReceipt("12345678-1234-1234-1234-123456789abc",2)
local c=S.makeReceipt("different_server_1234567",1)
check(type(a),"string","real_server_token")
check(a~=b,true,"different_round")
check(a~=c,true,"different_server")
check(S.makeReceipt("",1),nil,"no_server_id")
check(S.makeReceipt("not a space id",1),nil,"no_spoof_spaces")
check(S.makeReceipt("validsession_123",-1),nil,"negative_epoch")
check(S.makeReceipt("validsession_123",1.5),nil,"fractional_epoch")
check(S.makeReceipt("validsession_123",0),nil,"zero_epoch")
local blank=S.blank()
check(S.validate(blank),true,"blank_valid")
check(blank.owned.starter_scout,1,"starter_owned")
check(blank.equipped,"starter_scout","starter_eq")
check(S.toRulesRecord(blank).receipts[1],nil,"no_numeric_forgery")
check(S.grantTransition(blank,a,"unknown"),nil,"unknown_reward")
check(S.grantTransition(blank,a,"starter_scout"),nil,"no_extra_starter")
check(S.grantTransition(blank,"short","star_scout"),nil,"no_short_receipt")
check(S.grantTransition(blank,a,"star_scout")[1],nil,"dummy_placeholder_never_use")
local ok,record,status=S.load(ds,10)
check(ok,true,"new_account_load")
check(status,"LOADED","new_account_name")
check(record.equipped,"starter_scout","new_starter")
check(db.U_10,nil,"blank_load_doesnt_write")
local g1,p1,s1=S.grant(ds,10,a,"star_scout")
check(g1,true,"first_grant_success")
check(s1,"PERSISTED_OR_ALREADY_GRANTED","first_grant_ack")
check(p1.owned.star_scout,1,"one_rare")
check(p1.receipts[a],"star_scout","receipt_kept")
check(p1.revision,1,"revision1")
check(ds.writes,1,"one_write")
local g2,p2,s2=S.grant(ds,10,a,"star_scout")
check(g2,true,"first_retry_success")
check(p2.owned.star_scout,1,"retry_not_double_count")
check(ds.writes,2,"double_callback_may_be_called_but_same_value")
local g3,p3,s3=S.grant(ds,10,a,"forest_scout")
check(g3,true,"client_cannot_reroll")
check(s3,"ALREADY_GRANTED_DIFFERENT_ITEM","immutable_item")
check(p3.owned.forest_scout,nil,"no_forged_forest")
check(p3.receipts[a],"star_scout","original_item_stays")
ds.twice=true
local g4,p4=S.grant(ds,10,b,"forest_scout")
check(g4,true,"UpdateAsync_pure_callback_twice")
check(p4.owned.forest_scout,1,"double_callback_never_double_rewards")
check(p4.revision,2,"revision2")
ds.twice=false
local newAccount,copy,statusLoaded=S.load(ds,10)
check(newAccount,true,"reconnect_getasync_mock")
check(copy.owned.star_scout,1,"reconnect_preserved_rare")
check(copy.owned.forest_scout,1,"reconnect_preserved_forest")
check(S.toRulesRecord(copy).equipped,"starter_scout","reconnect_starter")
check(S.toRulesRecord(copy).discovered.star_scout,true,"reconnect_catalog")
check(S.toRulesRecord(copy).receipts[1],nil,"global_receipts_not_misused_as_local_epochs")
local eq,pEq,sEq=S.equip(ds,10,"star_scout")
check(eq,true,"equip_verified_ownership")
check(pEq.equipped,"star_scout","equip_persisted")
check(sEq,"EQUIPPED_PERSISTED","equip_ack")
check(S.equip(ds,10,"admin_dragon"),false,"no_unknown_equip")
check(S.equip(ds,20,"star_scout"),false,"no_unowned_equip")
check(S.equip(ds,10,"forest_scout"),true,"switch_equipped")
check(S.equip(ds,10,"star_scout"),true,"switch_back_equipped")
check(S.load(ds,10),true,"read_after_equip")
check(S.load(ds,10)[1],nil,"dummy_placeholder_never_use")
local otherStore={values=db}
function otherStore:GetAsync(key) return self.values[key] end
function otherStore:UpdateAsync(key,fn)
 local nextValue=fn(self.values[key])
 if nextValue then self.values[key]=nextValue end
 return self.values[key]
end
local cross,after=S.grant(otherStore,10,c,"forest_scout")
check(cross,true,"different_server_is_serialized_by_last_state")
check(after.owned.star_scout,1,"parallel_same_record_no_lost_rare")
check(after.owned.forest_scout,2,"parallel_same_record_adds_second_valid_epoch")
check(after.equipped,"star_scout","parallel_keeps_equip")
check(after.receipts[a],"star_scout","parallel_preserves_receipt")
check(after.receipts[b],"forest_scout","parallel_preserves_other_receipt")
check(after.receipts[c],"forest_scout","parallel_stores_new_receipt")
ds.failBefore=true
check(S.load(ds,10),false,"disabled_Studio_access_load_does_not_claim_saved")
check(S.grant(ds,10,S.makeReceipt("retry_before_1234567",3),"forest_scout"),
      false,"write_throttled_never_ack")
check(S.equip(ds,10,"forest_scout"),false,"equip_throttled_never_ack")
ds.failBefore=false
local beforeReceipt=S.makeReceipt("retry_after_1234567",4)
ds.failAfter=true
local maybeWritten=S.grant(ds,10,beforeReceipt,"star_scout")
check(maybeWritten,false,"ambiguous_error_never_claim_success")
check(db.U_10.receipts[beforeReceipt],"star_scout","server_committed_even_with_network_error")
check(db.U_10.owned.star_scout,2,"one_atomic_backend_commit")
ds.failAfter=false
local replay,confirm=S.grant(ds,10,beforeReceipt,"star_scout")
check(replay,true,"same_key_retry_confirms_real_backend_commit")
check(confirm.owned.star_scout,2,"no_double_count_after_unknown_network_status")
local corrupt={schema=1,revision=0,owned={starter_scout=1,admin_dragon=1},
               receipts={},equipped="starter_scout"}
db.U_30=corrupt
check(S.load(ds,30),false,"fail_closed_corrupt_save")
check(S.grant(ds,30,S.makeReceipt("other_server_123456789",1),"star_scout"),
      false,"no_overwrite_corrupt_save")
check(S.equip(ds,30,"starter_scout"),false,"no_equip_overwrite_corrupt")
check(db.U_30.owned.admin_dragon,1,"corrupt_still_untouched_for_recovery")
check(S.load(ds,0),false,"invalid_negative_user")
check(S.grant(ds,-1,a,"star_scout"),false,"no_negative_data_key")
check(S.equip(ds,-1,"starter_scout"),false,"no_fake_user_equips")
local full=S.blank()
for i=1,S.MAX_RECEIPTS do
 full.receipts[S.makeReceipt("ledger_filled_session_123456789",i)]="forest_scout"
end
check(S.validate(full),true,"full_registry_valid")
local impossible=S.grantTransition(full,S.makeReceipt("ledger_filled_session_123456789",S.MAX_RECEIPTS+1),"star_scout")
check(impossible,nil,"full_registry_fail_closed_no_eviction")
check(S.validate({schema=1,revision=-1,owned={starter_scout=1},receipts={},equipped="starter_scout"}),false,"negative_revision")
check(S.validate({schema=1,revision=1.5,owned={starter_scout=1},receipts={},equipped="starter_scout"}),false,"fractional_revision")
check(S.validate({schema=1,revision=0,owned={starter_scout=0},receipts={},equipped="starter_scout"}),false,"starter_forced")
check(S.validate({schema=1,revision=0,owned={starter_scout=1,star_scout=-1},receipts={},equipped="starter_scout"}),false,"negative_count")
check(S.validate({schema=1,revision=0,owned={starter_scout=1},receipts={},equipped="star_scout"}),false,"unowned_equipped")
for i=1,135 do
 local receipt=S.makeReceipt("session_135_extra_123456789",i)
 local succeed,profile=S.grant(ds,41,receipt,"forest_scout")
 check(succeed,true,"many_distinct_real_grants_"..i)
 check(profile.receipts[receipt],"forest_scout","many_immutable_receipts_"..i)
end
check(db.U_41.owned.forest_scout,135,"100_plus_duplicates_same_item_valid")
check(db.U_41.revision,135,"revision_monotonic_135")
print("EGG_RUMBLE_REAL_NATIVE_DATASTORE_UPDATEASYNC_MOCK_CONFLICTS_PASS_"..tostring(n))
'''
# Remove unreachable Lua pseudo tuple selectors; all tests must compile and execute.
test=test.replace('check(S.grantTransition(blank,a,"star_scout")[1],nil,"dummy_placeholder_never_use")',
                  'local candidate=select(1,S.grantTransition(blank,a,"star_scout"))\ncheck(candidate.owned.star_scout,1,"transition_does_not_mutate_original")')
test=test.replace('check(S.load(ds,10)[1],nil,"dummy_placeholder_never_use")','')
args.write.parent.mkdir(parents=True,exist_ok=True)
args.write.write_text(test,encoding="utf-8")
print("P0D_NATIVE_STORE_ORIGINAL_GIT_BLOB_PIN_PASS",gitblob)
