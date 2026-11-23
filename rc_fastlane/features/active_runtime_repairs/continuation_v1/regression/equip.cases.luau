case("leave_before_transform_preserves_durable_choice_but_retires_local_completion",function()
 local e=environment();local p=e.newPlayer();local op=e.equip(p,"forest_scout",1)
 eq(op.status,"REQUESTED");eq(e.stored(p).equipped,"starter_scout","no pre-yield commit")
 e.remove(p,true);e.commit(op);e.ack(op)
 eq(e.stored(p).equipped,"forest_scout","accepted request may commit after departure")
 eq(e.profiles[p],nil,"departed profile must remain absent")
 eq(e.states[p],nil);eq(e.outstanding(),0);eq(#e.remotes,0);eq(#e.warnings,0)
 return "real callback commits only after actual removal; old in-memory state stays absent"
end)

case("uncommitted_backend_failure_after_departure_releases_once",function()
 local e=environment();local p=e.newPlayer();local op=e.equip(p,"star_scout",1)
 e.remove(p);e.ack(op,false)
 eq(e.stored(p).equipped,"starter_scout","no transform ran")
 eq(op.callbacks,0);eq(e.profiles[p],nil);eq(e.states[p],nil)
 eq(e.outstanding(),0);eq(#e.warnings,0);eq(#e.remotes,0)
 return "pre-commit failure cannot reconstruct SAVE_FAILED for a removed Player"
end)

case("nonnull_reenrollment_preserves_new_epoch_cache_and_remote_silence",function()
 local e=environment();local p=e.newPlayer();local op=e.equip(p,"forest_scout",1)
 local oldId=e.ids[p];local newId=e.enroll(p);check(newId~=oldId)
 local newer=PersistentHatch.equipTransition(e.profiles[p],"star_scout")
 e.profiles[p]=newer;e.states[p]="SAVED"
 e.commit(op);e.ack(op)
 eq(e.profiles[p],newer,"stale old uid cannot replace new cache")
 eq(e.states[p],"SAVED");eq(e.outstanding(),0);eq(#e.remotes,0)
 return "same Player object and live Parent; changed nonnil server enrollment is rejected"
end)

case("Parent_revoked_before_transform_does_not_modify_current_cache",function()
 local e=environment();local p=e.newPlayer();local old=e.profiles[p]
 local op=e.equip(p,"forest_scout",1);p.Parent=nil
 e.commit(op);e.ack(op)
 eq(e.profiles[p],old);eq(e.states[p],"SAVED")
 eq(e.rule(p).equipped,"starter_scout");eq(e.outstanding(),0);eq(#e.remotes,0)
 return "independent Parent fence remains necessary even if enrollment table has not been cleaned"
end)

case("shutdown_waits_for_live_grant_after_departed_equip_finishes",function()
 local e=environment();local old=e.newPlayer(111);local live=e.newPlayer(222)
 local equip=e.equip(old,"forest_scout",1)
 local grant=e.grant(live,"Sreviewmore:3","star_scout")
 eq(e.outstanding(),2)
 local close=e.shutdown();eq(coroutine.status(close.thread),"suspended")
 e.remove(old,true);e.commit(equip);e.ack(equip)
 eq(e.outstanding(),1,"only departed equip retires")
 eq(e.profiles[old],nil,"old cache absent")
 eq(e.stepShutdown(close),"suspended","actual BindToClose must retain live grant")
 e.commit(grant);e.ack(grant)
 eq(e.outstanding(),0)
 eq(e.stepShutdown(close),"dead","actual shutdown resumes only after live grant ack")
 eq(e.stored(live).owned.star_scout,2,"actual free reward delivered")
 eq(e.profiles[live].owned.star_scout,2);eq(#e.remotes,1);eq(#e.warnings,0)
 return "shared global counter validated through actual BindToClose and actual free-grant writer"
end)

case("shutdown_warns_for_unreleased_unrelated_equip_then_accepts_late_ack",function()
 local e=environment();local old=e.newPlayer(111);local live=e.newPlayer(222)
 local a=e.equip(old,"forest_scout",1);local b=e.equip(live,"star_scout",1)
 e.remove(old);e.commit(a);e.ack(a)
 eq(e.outstanding(),1);eq(e.profiles[old],nil)
 local close=e.shutdown()
 for _=1,92 do e.stepShutdown(close)end
 eq(coroutine.status(close.thread),"dead","actual 23-second bound expires")
 eq(#e.warnings,1);eq(e.warnings[1][1],"EGG_RUMBLE_PENDING_HATCH_SAVE_NOT_CONFIRMED")
 eq(e.warnings[1][2],1,"warning reports exact outstanding live write")
 e.commit(b);e.ack(b);eq(e.outstanding(),0)
 return "pending count remains truthful through actual bounded shutdown warning"
end)

case("REVISION_V1_replay_preserves_foreign_grant_and_requires_reselection",function()
 local e=environment();local p=e.newPlayer();local op=e.equip(p,"forest_scout",1)
 local original=e.stored(p)
 e.commit(op,function(backend,key)
  backend[key]=PersistentHatch.grantTransition(backend[key],"Sforeignbonus:4","star_scout")
 end)
 eq(op.callbacks,2,"real callback executed twice with different originals")
 eq(original.revision,2,"first input not mutated")
 eq(original.owned.star_scout,1,"old snapshot not mutated")
 eq(e.stored(p).revision,3,"only the foreign grant advanced the revision")
 eq(e.stored(p).owned.star_scout,2);eq(e.stored(p).equipped,"starter_scout")
 e.ack(op)
 eq(e.profiles[p].revision,3);eq(e.rule(p).owned.star_scout,2)
 eq(e.rule(p).equipped,"starter_scout");eq(e.states[p],"SAVED")
 eq(e.outstanding(),0);eq(#e.warnings,0);eq(#e.operations,1,"no automatic rebase")
 local retry=e.equip(p,"forest_scout",2);e.commit(retry);e.ack(retry)
 eq(e.stored(p).revision,4);eq(e.stored(p).owned.star_scout,2)
 eq(e.rule(p).equipped,"forest_scout");eq(e.outstanding(),0)
 return "discarded proposal cannot consume a newer revision; explicit reselection preserves the grant"
end)

case("REVISION_V1_wrong_item_ack_is_conflict_not_requested_equip_success",function()
 local e=environment();local p=e.newPlayer();local expected=e.profiles[p].revision
 local op=e.equip(p,"forest_scout",1);e.commit(op)
 -- Keep the original deliberately substituted, valid wrong-item response.
 -- First prove the actual wrapper rejects it as the requested equip success.
 op.response=PersistentHatch.equipTransition(op.response,"star_scout")
 local responseStore={UpdateAsync=function(_,key,_callback)
  eq(key,"U_"..p.UserId);return clone(op.response)
 end}
 local confirmed,current,reason=PersistentHatch.equip(responseStore,p.UserId,"forest_scout",expected)
 eq(confirmed,false);eq(reason,"REVISION_CONFLICT");eq(current.equipped,"star_scout")
 e.ack(op)
 eq(e.states[p],"SAVED");eq(e.rule(p).equipped,"star_scout")
 eq(e.profiles[p].revision,op.response.revision)
 eq(e.outstanding(),0);eq(#e.warnings,0)
 return "wrong requested item remains unconfirmed; known current state does not invent an unknown write failure"
end)

case("REVISION_V1_same_userid_old_request_preserves_new_durable_choice",function()
 local e=environment();local old=e.newPlayer();local oldOp=e.equip(old,"forest_scout",1)
 e.remove(old,true)
 local live=e.newPlayer(old.UserId);local fresh=e.equip(live,"star_scout",1)
 e.commit(fresh);e.ack(fresh)
 local current=e.profiles[live]
 e.commit(oldOp);e.ack(oldOp)
 eq(e.profiles[old],nil);eq(e.states[old],nil)
 eq(e.profiles[live],current);eq(e.rule(live).equipped,"star_scout")
 eq(e.outstanding(),0);eq(#e.remotes,1)
 eq(e.stored(live).equipped,"star_scout","older expected revision cannot overwrite the new choice")
 check(same(e.stored(live),current),"whole newer durable record is retained")
 return "new Player and new confirmed durable revision are both protected"
end)

observation("existing_failed_then_successful_equip_keeps_SAVE_FAILED",function()
 local e=environment();local p=e.newPlayer()
 local failed=e.equip(p,"forest_scout",1);local saved=e.equip(p,"star_scout",2)
 e.ack(failed,false);eq(e.states[p],"SAVE_FAILED")
 e.commit(saved);e.ack(saved)
 eq(e.stored(p).equipped,"star_scout");eq(e.profiles[p].equipped,"star_scout")
 eq(e.rule(p).equipped,"star_scout");eq(e.states[p],"SAVE_FAILED")
 eq(e.canWrite(p),false,"success failed to restore subsequent write eligibility")
 local count=#e.operations
 eq(e.equip(p,"forest_scout",3),nil)
 eq(#e.operations,count,"next request silently selects existing local-only branch")
 eq(e.rule(p).equipped,"forest_scout");eq(e.stored(p).equipped,"star_scout")
 eq(e.outstanding(),0)
 return "PREEXISTING: confirmed latest success leaves SAVE_FAILED; next equipment request is local only"
end)

observation("existing_success_then_stale_failure_also_keeps_SAVE_FAILED",function()
 local e=environment();local p=e.newPlayer()
 local old=e.equip(p,"forest_scout",1);local newest=e.equip(p,"star_scout",2)
 e.commit(newest);e.ack(newest);eq(e.states[p],"SAVED")
 e.ack(old,false)
 eq(e.profiles[p].equipped,"star_scout");eq(e.stored(p).equipped,"star_scout")
 eq(e.states[p],"SAVE_FAILED");eq(e.outstanding(),0)
 return "PREEXISTING: older unconfirmed completion overwrites saved status after newer successful equipment"
end)
