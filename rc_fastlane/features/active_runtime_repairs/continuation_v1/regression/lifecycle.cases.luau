local passed,failed=0,0
local function eq(a,b,why)assert(a==b,(why or "mismatch").." expected="..tostring(b).." actual="..tostring(a))end
local function test(name,fn)
 local ok,detail=pcall(fn)
 if ok then passed+=1 else failed+=1 end
 print("CASE\t"..name.."\t"..(ok and "PASS"or "FAIL").."\t"..tostring(detail or "contract satisfied"))
end
local function start(e,p,kind)
 local job=if kind=="evolution"then e:evolve(p,1)elseif kind=="progress"then e:progress(p)else e:training(p)
 assert(job,"actual Game path must contact actual Store")
 eq(e:outstanding(),1)
 return job
end
local function finishFailure(e,job,kind)
 local attempts=if kind=="progress"then 4 else 3
 for i=1,attempts do
  e:deliver(job,false)
  if i<attempts then job=e:timer()end
 end
 eq(e:outstanding(),0)
end
local function durableAward(e,p,kind)
 local stored=e:stored(p)
 if kind=="evolution"then
  eq(stored.evolution.fragments,58,"one valid stage1 evolution consumes2 fragments")
 elseif kind=="progress"then
  eq(stored.progress.settledCount,1,"one eligible actual objective round is settled")
 else
  eq(stored.trainingV4.receiptCount,1,"one immutable training receipt")
  eq(stored.trainingV4.focusedSeconds,30,"earned30s remain durable after leaving")
 end
end
for _,kind in ipairs({"evolution","progress","training"})do
 test(kind.."_current_member_success_still_publishes",function()
  local e=newEnvironment();local p=e:newPlayer();local job=start(e,p,kind)
  e:deliver(job,true);eq(e:outstanding(),0);durableAward(e,p,kind)
  assert(e.profiles[p]and e.ids[p],"live cached profile must remain")
  if kind=="progress"then eq(e.progressStatus[p],"SAVED")
  elseif kind=="training"then eq(p.attrs.P0D_V4_SaveStatus,"SAVED")
  else eq(e.status[p],"SAVED")end
 end)
 for _,retainParent in ipairs({true,false})do
  local phase=if retainParent then "removing_parent_retained"else "parent_detached"
  test(kind.."_"..phase.."_success_keeps_removed_rows_empty",function()
   local e=newEnvironment();local p=e:newPlayer();local job=start(e,p,kind)
   e:remove(p,retainParent)
   local attributes,writes=e:attributes(p);local snapshots=#e.snapshots
   local q=e:newPlayer(p.UserId);local fresh=e.clone(e.profiles[q]);local qAttributes,qWrites=e:attributes(q)
   local afterJoinSnapshots=#e.snapshots
   e:deliver(job,true);eq(e:outstanding(),0);durableAward(e,p,kind)
   eq(next(e:localRows(p)),nil,"completion must not recreate removed Player cache/status")
   assert(e.same(p.attrs,attributes),"removed Player attributes changed")
   eq(#p.attributeWrites,writes,"removed Player publication happened")
   assert(e.same(e.profiles[q],fresh),"sameUserId replacement cache changed")
   assert(e.same(q.attrs,qAttributes),"sameUserId replacement attributes changed")
   eq(#q.attributeWrites,qWrites);eq(#e.snapshots,afterJoinSnapshots)
   assert(afterJoinSnapshots>=snapshots)
  end)
  test(kind.."_"..phase.."_failure_keeps_removed_rows_empty",function()
   local e=newEnvironment();local p=e:newPlayer();local job=start(e,p,kind)
   e:remove(p,retainParent)
   local attributes,writes=e:attributes(p);local snapshots=#e.snapshots;local warningCount=#e.warnings
   finishFailure(e,job,kind)
   eq(next(e:localRows(p)),nil,"unconfirmed old completion must not recreate removed Player state")
   assert(e.same(p.attrs,attributes),"old failure changed removed attributes")
   eq(#p.attributeWrites,writes);eq(#e.snapshots,snapshots);eq(#e.warnings,warningCount)
  end)
 end
 test(kind.."_lost_ack_retry_keeps_one_earned_award",function()
  local e=newEnvironment();local p=e:newPlayer();local job=start(e,p,kind)
  e:commit(job);local durable=e.clone(e:stored(p));e:deliver(job,false)
  local retry=e:timer();e:remove(p,true);e:deliver(retry,true)
  eq(e:outstanding(),0);durableAward(e,p,kind)
  assert(e.same(e:stored(p),durable),"same receipt retry duplicated or altered durable award")
  eq(next(e:localRows(p)),nil,"retry completion revived departed Player state")
 end)
end
print("TOTAL\t"..passed.."\t"..failed)
if failed>0 then error("completion lifetime cases failed: "..failed)end
