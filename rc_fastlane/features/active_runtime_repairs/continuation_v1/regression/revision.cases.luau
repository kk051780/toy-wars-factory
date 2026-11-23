local function finishStore(e,call,confirmed)
 if call.operation then e.commit(call.operation);e.ack(call.operation,confirmed)end
 return assert(call.result(),"actual Store call must finish")
end
local function metadataEquals(e,p,expected)
 check(same(e.metadata(p),expected),"UserIds and metadata must preserve the current keyInfo")
end

case("REV_STALE_SESSION",function()
 local e=environment();local old=e.newPlayer();local a=e.equip(old,"forest_scout",1)
 e.remove(old,true);local live=e.newPlayer(old.UserId)
 local b=e.equip(live,"star_scout",1);e.commit(b);e.ack(b)
 local newer=clone(e.stored(live));local info=clone(e.metadata(live))
 e.commit(a);e.ack(a)
 check(same(e.stored(live),newer),"old request cannot change a newer confirmed profile")
 eq(e.rule(live).equipped,"star_scout");eq(e.profiles[old],nil);eq(e.states[old],nil)
 eq(e.outstanding(),0);eq(#e.remotes,1);metadataEquals(e,live,info)
 return "new star stays durable; old session has no cache or remote completion"
end)

case("REV_FRESH_SAME_ITEM",function()
 local e=environment();local old=e.newPlayer();local a=e.equip(old,"forest_scout",1)
 local initial=e.profiles[old].revision;e.remove(old,true);local live=e.newPlayer(old.UserId)
 local b=e.equip(live,"starter_scout",1);e.commit(b);e.ack(b)
 eq(e.stored(live).revision,initial+1,"fresh same-item acceptance must create a revision barrier")
 local saved=clone(e.stored(live));e.commit(a);e.ack(a)
 check(same(e.stored(live),saved));eq(e.rule(live).equipped,"starter_scout")
 return "fresh same-item intent advances once and fences the old request"
end)

case("REV_UNKNOWN_ACK_SAME_ITEM",function()
 local e=environment();local p=e.newPlayer();local a=e.equip(p,"forest_scout",1)
 local initial=e.profiles[p].revision;e.commit(a);e.ack(a,false)
 eq(e.states[p],"SAVE_FAILED");eq(e.profiles[p].revision,initial)
 local committed=clone(e.stored(p));local b=assert(e.equip(p,"forest_scout",2))
 e.commit(b);e.ack(b)
 check(same(e.stored(p),committed),"stale same-item confirmation must not increment again")
 eq(e.states[p],"SAVED");eq(e.rule(p).equipped,"forest_scout");eq(e.outstanding(),0)
 return "existing explicit retry confirms current desired state, not a durable request identity"
end)

case("REV_SAME_SESSION_NEWER_COMMIT",function()
 local e=environment();local p=e.newPlayer();local a=e.equip(p,"forest_scout",1)
 local b=e.equip(p,"star_scout",2);e.commit(b);e.ack(b)
 local newer=clone(e.stored(p));e.commit(a);e.ack(a)
 check(same(e.stored(p),newer));check(same(e.profiles[p],newer))
 eq(e.states[p],"SAVED");eq(e.rule(p).equipped,"star_scout");eq(e.outstanding(),0)
 return "later callback cannot overwrite the revision that already won"
end)

case("REV_ABA",function()
 local e=environment();local p=e.newPlayer();local a=e.equip(p,"forest_scout",1)
 local initial=e.profiles[p].revision
 local b=e.equip(p,"star_scout",2);e.commit(b);e.ack(b)
 local c=e.equip(p,"starter_scout",3);e.commit(c);e.ack(c)
 eq(e.stored(p).revision,initial+2)
 local current=clone(e.stored(p));e.commit(a);e.ack(a)
 check(same(e.stored(p),current));eq(e.rule(p).equipped,"starter_scout")
 return "same item after ABA still has a newer revision"
end)

case("REV_SAFE_INTEGER_BOUNDARY",function()
 local e=environment();local p=e.newPlayer();local key="U_"..p.UserId
 local max=9007199254740991
 e.backend[key].revision=max-1
 local first=finishStore(e,e.storeCall(p.UserId,"forest_scout",max-1))
 eq(first[1],true);eq(first[2].revision,max)
 local frozen=clone(e.stored(p));local next=finishStore(e,e.storeCall(p.UserId,"star_scout",max))
 eq(next[1],false,"fresh write cannot exceed the safe integer range")
 check(same(e.stored(p),frozen))
 e.backend[key].revision=9007199254740992
 frozen=clone(e.stored(p));local unsafe=finishStore(e,e.storeCall(p.UserId,"star_scout",max-1))
 eq(unsafe[1],false);check(same(e.stored(p),frozen))
 return "safe upper boundary works once; unrepresentable or unsafe increments fail closed"
end)

case("REV_METADATA_ALL_RETURN_BRANCHES",function()
 local e=environment();local p=e.newPlayer();local original=clone(e.metadata(p))
 local start=e.stored(p).revision
 local fresh=finishStore(e,e.storeCall(p.UserId,"forest_scout",start));eq(fresh[1],true)
 metadataEquals(e,p,original)
 local freshSame=finishStore(e,e.storeCall(p.UserId,"forest_scout",start+1));eq(freshSame[1],true)
 eq(e.stored(p).revision,start+2);metadataEquals(e,p,original)
 local staleSame=finishStore(e,e.storeCall(p.UserId,"forest_scout",start));eq(staleSame[1],true)
 eq(e.stored(p).revision,start+2);metadataEquals(e,p,original)
 local conflict=finishStore(e,e.storeCall(p.UserId,"star_scout",start))
 eq(conflict[1],false);eq(conflict[3],"REVISION_CONFLICT")
 eq(conflict[2].equipped,"forest_scout");eq(e.stored(p).revision,start+2)
 metadataEquals(e,p,original);eq(e.physicalWrites(),4,"no-op ACKs still use UpdateAsync writes")
 return "fresh/change/same/conflict retain all metadata and UserIds"
end)

case("REV_REPLAY_FOREIGN_GRANT_AND_METADATA",function()
 local e=environment();local p=e.newPlayer();local a=e.equip(p,"forest_scout",1)
 local initial=e.stored(p).revision
 e.commit(a,function(backend,key,info)
  backend[key]=assert(PersistentHatch.grantTransition(backend[key],"Sforeign_revision_fence:71","star_scout"))
  info[key]={userIds={p.UserId,777},metadata={generation=2,foreign="keep-current"}}
 end)
 eq(a.callbacks,2);eq(a.proposals[1].input.revision,initial)
 eq(a.proposals[1].output.value.revision,initial+1)
 eq(a.proposals[2].input.revision,initial+1)
 eq(e.stored(p).revision,initial+1,"replayed old intent must not rebase")
 eq(e.stored(p).equipped,"starter_scout");eq(e.stored(p).owned.star_scout,2)
 e.ack(a)
 eq(e.states[p],"SAVED");eq(e.profiles[p].revision,initial+1)
 eq(e.rule(p).owned.star_scout,2);eq(p.attributes.P0D_V4_SaveStatus,"READY_TO_TRAIN")
 local expected={userIds={p.UserId,777},metadata={generation=2,foreign="keep-current"}}
 metadataEquals(e,p,expected)
 local retry=e.equip(p,"forest_scout",2);e.commit(retry);e.ack(retry)
 eq(e.stored(p).revision,initial+2);eq(e.rule(p).equipped,"forest_scout")
 metadataEquals(e,p,expected)
 return "foreign inventory and latest metadata survive replay; explicit next request succeeds"
end)

case("REV_EXPECTATION_CAPTURED_BEFORE_TASK",function()
 local e=environment();local p=e.newPlayer();local a=e.equip(p,"forest_scout",1)
 local key="U_"..p.UserId
 e.backend[key]=assert(PersistentHatch.grantTransition(e.backend[key],"Scapture_newer_cache:72","star_scout"))
 e.profiles[p]=clone(e.backend[key])
 local current=clone(e.backend[key]);e.commit(a);e.ack(a)
 check(same(e.stored(p),current),"later cache refresh must not replace the captured expected revision")
 eq(e.rule(p).equipped,"starter_scout");eq(e.outstanding(),0)
 return "server scalar expectation remains immutable while the coroutine is pending"
end)

case("REV_UNKNOWN_ACK_NEVER_PUBLISHES_CALLBACK_OBSERVATION",function()
 local e=environment();local p=e.newPlayer();local old=e.equip(p,"forest_scout",1)
 local fresh=e.equip(p,"star_scout",2);e.commit(fresh)
 local before=clone(e.profiles[p]);e.commit(old);e.ack(old,false)
 check(same(e.profiles[p],before),"a failed ACK cannot publish the callback's newer record")
 eq(e.states[p],"SAVE_FAILED")
 local retry=e.equip(p,"star_scout",3);e.commit(retry);e.ack(retry)
 eq(e.states[p],"SAVED");eq(e.rule(p).equipped,"star_scout")
 local saved=clone(e.profiles[p]);e.ack(fresh)
 check(same(e.profiles[p],saved));eq(e.outstanding(),0)
 return "only a later acknowledged same-item state confirms recovery"
end)

case("REV_REQUIRED_EXPECTATION_AND_MISSING_PROFILE",function()
 local e=environment();local p=e.newPlayer();local initial=clone(e.stored(p))
 for _,invalid in ipairs({false,-1,1.5,math.huge,-math.huge,0/0,9007199254740992})do
  local count=#e.operations
  local call=e.storeCall(p.UserId,"forest_scout",invalid)
  local result=finishStore(e,call)
  eq(result[1],false);eq(result[2],nil);eq(result[3],"INVALID_EQUIP_REVISION")
  eq(#e.operations,count,"invalid expectation cannot call UpdateAsync")
 end
 local count=#e.operations
 local missing=finishStore(e,e.storeCall(p.UserId,"forest_scout",nil))
 eq(missing[1],false);eq(#e.operations,count)
 check(same(e.stored(p),initial))
 e.profiles[p]=nil
 eq(e.equip(p,"forest_scout",1),nil,"Game must validate its cache before starting an async write")
 eq(#e.operations,count);eq(e.outstanding(),0);eq(e.states[p],"SAVE_FAILED")
 return "no missing/fractional/unsafe expectation fallback; absent server cache is rejected"
end)

case("REV_NIL_KEYINFO_INITIAL_PROFILE",function()
 local e=environment();local uid=880001
 local call=e.storeCall(uid,"starter_scout",0)
 local result=finishStore(e,call)
 eq(result[1],true);eq(result[2].revision,1)
 eq(result[2].equipped,"starter_scout");eq(call.operation.callbacks,1)
 eq(e.backend["U_"..uid].owned.starter_scout,1)
 return "first profile can be created with nil DataStoreKeyInfo"
end)

case("REV_CORRUPT_UNOWNED_AND_REGRESSED_RECORD",function()
 local e=environment();local p=e.newPlayer();local key="U_"..p.UserId
 local original=clone(e.stored(p));local info=clone(e.metadata(p))
 e.backend[key].owned.forest_scout=0
 local unowned=clone(e.stored(p));local a=finishStore(e,e.storeCall(p.UserId,"forest_scout",original.revision))
 eq(a[1],false);check(same(e.stored(p),unowned));metadataEquals(e,p,info)
 e.backend[key]=clone(original);e.backend[key].revision=-1
 local corrupt=clone(e.stored(p));local b=finishStore(e,e.storeCall(p.UserId,"forest_scout",original.revision))
 eq(b[1],false);check(same(e.stored(p),corrupt));metadataEquals(e,p,info)
 e.backend[key]=clone(original)
 local c=finishStore(e,e.storeCall(p.UserId,"starter_scout",original.revision+1))
 eq(c[1],false,"future expectation cannot claim a lower same-item record")
 check(same(e.stored(p),original));metadataEquals(e,p,info)
 return "invalid ownership/data and revision rollback cannot create a confirmed change"
end)

case("REV_FIRST_COMMIT_WINS_AND_USER_RESELECTS",function()
 local e=environment();local p=e.newPlayer();local first=e.equip(p,"forest_scout",1)
 local later=e.equip(p,"star_scout",2);local start=e.stored(p).revision
 e.commit(first);e.ack(first);e.commit(later);e.ack(later)
 eq(e.stored(p).equipped,"forest_scout");eq(e.stored(p).revision,start+1)
 eq(e.rule(p).equipped,"forest_scout");eq(e.states[p],"SAVED");eq(e.canWrite(p),true)
 eq(#e.operations,2,"conflict has no automatic rebased retry")
 local explicit=e.equip(p,"star_scout",3);e.commit(explicit);e.ack(explicit)
 eq(e.stored(p).equipped,"star_scout");eq(e.stored(p).revision,start+2)
 eq(e.rule(p).equipped,"star_scout");eq(#e.operations,3)
 return "HUD retains forest checkmark; a new explicit star choice is required"
end)

case("REV_CONFLICT_REFRESH_PRESERVES_FAILURE_EPISODE",function()
 local e=environment();local p=e.newPlayer();local failed=e.equip(p,"forest_scout",1)
 local fresh=e.equip(p,"star_scout",2);e.commit(fresh);e.ack(failed,false)
 local episode=e.failures(p)
 local retry=e.equip(p,"forest_scout",3);e.commit(retry);e.ack(retry)
 eq(e.states[p],"SAVE_FAILED");eq(e.failures(p),episode)
 eq(e.profiles[p].revision,e.stored(p).revision);eq(e.profiles[p].equipped,"star_scout")
 eq(p.attributes.P0D_V4_SaveStatus,"LOCAL_ONLY")
 local next=e.equip(p,"forest_scout",4);e.commit(next);e.ack(next)
 eq(e.states[p],"SAVED");eq(e.rule(p).equipped,"forest_scout")
 local current=clone(e.profiles[p]);e.ack(fresh)
 check(same(e.profiles[p],current));eq(e.outstanding(),0)
 return "known conflict refreshes a stale cache but does not confirm the failed equip episode"
end)

case("REV_NEW_FAILURE_CANNOT_BE_CLEARED_BY_OLD_RETRY_ACK",function()
 local e=environment();local p=e.newPlayer();local initial=e.equip(p,"forest_scout",1)
 e.ack(initial,false);local oldEpisode=e.failures(p)
 local retry=e.equip(p,"star_scout",2);local newer=e.equip(p,"forest_scout",3)
 e.commit(retry);e.ack(newer,false);local currentEpisode=e.failures(p)
 check(currentEpisode~=oldEpisode);e.ack(retry)
 eq(e.states[p],"SAVE_FAILED");eq(e.failures(p),currentEpisode)
 local next=e.equip(p,"starter_scout",4);e.commit(next);e.ack(next)
 eq(e.states[p],"SAVED");eq(e.rule(p).equipped,"starter_scout");eq(e.outstanding(),0)
 return "original failure-object identity guard is preserved"
end)

case("REV_REAL_REWARD_FAILURE_REMAINS_NON_EQUIPMENT",function()
 local e=environment();local p=e.newPlayer();local failed=e.equip(p,"forest_scout",1)
 e.ack(failed,false);local retry=e.equip(p,"star_scout",2)
 e.rewardAttempt(p,"Sunrelated_real_reward:88","forest_scout")
 local unrelated=e.failures(p);eq(unrelated.equipOnly,false)
 e.commit(retry);e.ack(retry)
 eq(e.states[p],"SAVE_FAILED");eq(e.failures(p),unrelated)
 eq(p.attributes.P0D_V4_SaveStatus,"LOCAL_ONLY")
 local count=#e.operations;eq(e.equip(p,"starter_scout",3),nil);eq(#e.operations,count)
 eq(e.outstanding(),0)
 return "actual reward failure cannot be reclassified or cleared by equip confirmation"
end)

case("REV_WRONG_ITEM_ACK_IS_NOT_EQUIP_CONFIRMATION",function()
 local e=environment();local p=e.newPlayer();local start=e.stored(p).revision
 local call=e.storeCall(p.UserId,"forest_scout",start);e.commit(call.operation)
 call.operation.response=assert(PersistentHatch.equipTransition(call.operation.response,"star_scout"))
 e.ack(call.operation)
 local result=assert(call.result());eq(result[1],false)
 eq(e.stored(p).equipped,"forest_scout","adversarial response does not mutate fixture backend")
 return "a valid wrong-item record can be a conflict response, never success for the requested item"
end)

case("REV_NONNIL_ENROLLMENT_CHANGE_RETIRES_COMPLETION",function()
 local e=environment();local p=e.newPlayer();local op=e.equip(p,"forest_scout",1)
 local previous=e.ids[p];e.enroll(p);check(e.ids[p]~=previous)
 local replacement=assert(PersistentHatch.equipTransition(e.profiles[p],"star_scout"))
 e.profiles[p]=replacement;e.states[p]="SAVED"
 e.commit(op);e.ack(op)
 eq(e.profiles[p],replacement);eq(e.states[p],"SAVED")
 eq(#e.remotes,0);eq(e.outstanding(),0)
 return "local enrollment fence remains independent of durable revision validation"
end)
