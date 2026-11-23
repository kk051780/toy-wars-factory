-- Actual full Store modules and literal H0/V3 Game excerpts.
-- Controlled UpdateAsync callback/ack order, not Studio/network observation.
local passed,failed=0,0
local function eq(a,b,message)
 assert(a==b,(message or 'mismatch')..' expected='..tostring(b)..' actual='..tostring(a))
end
local function test(name,fn)
 local ok,detail=pcall(fn)
 if ok then passed+=1 else failed+=1 end
 print('CASE\t'..name..'\t'..(ok and 'PASS' or 'FAIL')..'\t'..tostring(detail or 'contract satisfied'))
end
local function submit(e,p,kind,older)
 local job
 if kind=='evolution' then job=e:evolve(p,if older then 1 else 2)
 elseif kind=='grant' then
  job=e:reward(p,if older then 'Sack_order_older_20261123:1' else 'Sack_order_newer_20261123:2',
   if older then 'star_scout' else 'forest_scout')
 else job=e:equip(p,if older then 'star_scout' else 'forest_scout',if older then 1 else 2) end
 assert(job,'real Game '..kind..' must submit a real Store request')
 return job
end
local function failOperation(e,p,job,kind,commitBeforeError)
 local attempts=if kind=='grant' then 4 elseif kind=='evolution' then 3 else 1
 local expected=e.clone(e:stored(p))
 for i=1,attempts do
  -- If selected, retries replay the SAME immutable receipt; e:commit asserts
  -- the actual callback does not mutate its input. No new request/receipt is
  -- invented by the test or by the pure callback.
  if commitBeforeError and not job.committed then e:commit(job) end
  if commitBeforeError then assert(e.same(e:stored(p),expected),'retry must not duplicate durable award') end
  e:deliver(job,false)
  if i<attempts then job=e:timer() end
 end
 eq(e.status[p],'SAVE_FAILED','newer failed acknowledgement must first be visible')
 eq(e:outstanding(),1,'only the older acknowledgement remains pending')
 assert(e.failures(p),'real Game records a failure episode')
 return e.failures(p)
end
local function pair(olderKind,newerKind,commitNewer)
 local e=newEnvironment();local p=e:newPlayer()
 local old=submit(e,p,olderKind,true)
 local newer=submit(e,p,newerKind,false)
 eq(e:outstanding(),2)
 -- A commits first, B commits second, but B's unconfirmed response is
 -- delivered first. A's valid response still carries its own earlier rev1.
 e:commit(old);eq(e:stored(p).revision,1)
 if commitNewer then e:commit(newer);eq(e:stored(p).revision,2) end
 local episode=failOperation(e,p,newer,newerKind,commitNewer)
 e:deliver(old,true)
 eq(e:outstanding(),0,'both actual continuations balance their counters')
 eq(e.profiles[p].revision,1,'old success acknowledgement carries only rev1')
 eq(e:stored(p).revision,if commitNewer then 2 else 1,'durable model is explicit')
 eq(e.failures(p),episode,'failure sidecar identity itself has not changed')
 local last=e.snapshots[#e.snapshots]
 assert(last and last.player==p,'real Game sent its current snapshot through fixture Remote')
 local result={status=e.status[p],cacheRevision=e.profiles[p].revision,
  storedRevision=e:stored(p).revision,cacheEquipped=e.profiles[p].equipped,
  storedEquipped=e:stored(p).equipped,snapshotStatus=last.data.hatchSaveStatus,
  failureEquipOnly=episode.equipOnly,cacheForest=e.profiles[p].owned.forest_scout,
  storedForest=e:stored(p).owned.forest_scout,e=e,p=p}
 print('OBSERVATION\tACK_ORDER\tolder='..olderKind..'\tnewer='..newerKind
  ..'\tbackendNewerCommitted='..tostring(commitNewer)..'\tstatus='..tostring(result.status)
  ..'\tcacheRevision='..result.cacheRevision..'\tstoredRevision='..result.storedRevision
  ..'\tcacheEquipped='..result.cacheEquipped..'\tstoredEquipped='..result.storedEquipped
  ..'\tcacheForest='..result.cacheForest..'\tstoredForest='..result.storedForest
  ..'\tfailureEquipOnly='..tostring(result.failureEquipOnly)..'\tsnapshot='..tostring(result.snapshotStatus))
 return result
end
for _,spec in ipairs({
 {'evolution','equip'}, {'grant','equip'}, {'evolution','grant'}, {'grant','evolution'},
}) do
 test(spec[1]..'_old_success_preserves_newer_'..spec[2]..'_unconfirmed_failure',function()
  local result=pair(spec[1],spec[2],true)
  assert(result.cacheRevision<result.storedRevision,'test must expose a genuinely later durable commit')
  eq(result.status,'SAVE_FAILED','earlier revision confirmation cannot resolve a later unknown durable outcome')
  eq(result.snapshotStatus,'SAVE_FAILED','snapshot must not claim unresolved profile is saved')
 end)
end
test('existing_equipment_success_guard_preserves_failure_episode',function()
 local result=pair('equip','equip',true)
 eq(result.status,'SAVE_FAILED');eq(result.snapshotStatus,'SAVE_FAILED')
end)

-- Matched controls: a false acknowledgement can also mean NO commit. Game
-- receives the same false signal in each model. The harness knows the backend
-- truth; the actual Game/Store caller does not gain that knowledge from ERROR.
-- These are explanatory observations, not two extra passing safety contracts.
for _,older in ipairs({'evolution','grant'}) do
 local result=pair(older,'equip',false)
 eq(result.cacheRevision,result.storedRevision)
 print('OBSERVATION\tUNKNOWN_OUTCOME_CONTROL\tolder='..older
  ..'\tnoCommit=true\tsameCallerFailure=true\tstatus='..tostring(result.status)
  ..'\tNoCommitIsKnownOnlyToFixture=true')
end

-- Six additional bounded contracts. The original five cases stay byte-exact
-- in the combined program except that their unchanged final aggregate moves
-- after these additions. All production functions and engine fixture persist.
for _,olderKind in ipairs({'evolution','grant'}) do
 test(olderKind..'_equip_only_failure_recovers_on_next_explicit_retry',function()
  local r=pair(olderKind,'equip',true);local e,p=r.e,r.p
  eq(r.status,'SAVE_FAILED');eq(r.failureEquipOnly,true)
  local retry=e:equip(p,'star_scout',3)
  assert(retry,'equipment-only failure must allow a NEW explicit real Store retry')
  eq(e.status[p],'SAVE_FAILED','submitting retry alone cannot confirm it')
  eq(e:outstanding(),1)
  e:deliver(retry,true)
  eq(e:outstanding(),0);eq(e.status[p],'SAVED')
  eq(e.profiles[p].revision,3);eq(e:stored(p).revision,3)
  eq(e:stored(p).equipped,'star_scout');eq(e:equipped(p),'star_scout')
  assert(e.same(e.profiles[p],e:stored(p)),'explicit successful retry must cache the actual latest profile')
  eq(e.snapshots[#e.snapshots].data.hatchSaveStatus,'SAVED')
 end)
 test(olderKind..'_non_equipment_failure_is_not_erased_by_equipment',function()
  local failureKind=if olderKind=='evolution' then 'grant' else 'evolution'
  local r=pair(olderKind,failureKind,true);local e,p=r.e,r.p
  eq(r.status,'SAVE_FAILED');eq(r.failureEquipOnly,false)
  local durable=e.clone(e:stored(p));local cached=e.clone(e.profiles[p]);local jobs=#e.jobs
  eq(e:equip(p,'star_scout',3),nil,'equipment must not start a durable recovery for another kind of failed operation')
  eq(#e.jobs,jobs);eq(e:outstanding(),0);eq(e.status[p],'SAVE_FAILED')
  assert(e.same(e:stored(p),durable),'local equipment preview must not change durable data')
  assert(e.same(e.profiles[p],cached),'local equipment preview must not fabricate a saved cache')
  eq(e.snapshots[#e.snapshots].data.hatchSaveStatus,'SAVE_FAILED')
 end)
 test(olderKind..'_two_successes_keep_saved_and_do_not_regress_revision',function()
  local e=newEnvironment();local p=e:newPlayer()
  local older=submit(e,p,olderKind,true);local newer=submit(e,p,'equip',false)
  e:commit(older);eq(e:stored(p).revision,1)
  e:commit(newer);eq(e:stored(p).revision,2)
  -- Revision 2 is acknowledged before the held revision 1 response.
  e:deliver(newer,true)
  eq(e.status[p],'SAVED');eq(e.profiles[p].revision,2)
  local cached=e.clone(e.profiles[p])
  e:deliver(older,true)
  eq(e.status[p],'SAVED');eq(e.profiles[p].revision,2);eq(e:stored(p).revision,2)
  assert(e.same(e.profiles[p],cached),'older acknowledged revision must not replace revision2')
  assert(e.same(e.profiles[p],e:stored(p)))
  eq(e:equipped(p),'forest_scout');eq(e.failures(p),nil);eq(e:outstanding(),0)
  eq(e.snapshots[#e.snapshots].data.hatchSaveStatus,'SAVED')
 end)
end

print('TOTAL\t'..passed..'\t'..failed)
if failed>0 then error('ACK_ORDER_UNCONFIRMED_EPISODE_ERASED:'..failed) end
