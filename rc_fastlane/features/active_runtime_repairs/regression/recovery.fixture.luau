local function newEnvironment()
 local PersistentHatch=modules.PersistentHatchStore
 local RewardRules=modules.RewardEquipRules
 local Evolution=modules.EvolutionRules
 local Progression=modules.ProgressionRules
 local Rules=modules.S1Rules
 local function clone(value)
  if type(value)~="table"then return value end
  local result={};for k,v in pairs(value)do result[k]=clone(v)end;return result
 end
 local function same(a,b)
  if type(a)~=type(b)then return false end
  if type(a)~="table"then return a==b end
  for k,v in pairs(a)do if not same(v,b[k])then return false end end
  for k in pairs(b)do if a[k]==nil then return false end end
  return true
 end
 local removing
 local people={}
 local Players={PlayerRemoving={Connect=function(_,f)removing=f end},GetPlayers=function()return table.clone(people)end}
 local studio=true
 local RunService={IsStudio=function()return studio end}
 local Instance={new=function(class)assert(class=="DataStoreGetOptions");return {}end}
 local guid=0
 local HttpService={GenerateGUID=function()guid+=1;return "independent-recovery-guid-"..guid end}
 local h2Ids,lastSeq={},{}
 local rewardState=RewardRules.new()
 local match={phase="LOBBY",serial=1}
 local profileFailure -- Baseline observation only; candidate source declares its real sidecar below.
 --@@FAILURE@@--
 local persistentProfiles,delayedRestore,lastFreeHatch={},{},{}
 local outstandingWrites=0
 local progressionProfile,progressionRound,progressionEvents,progressionStatus,progressionLastAward={},{},{},{},{}
 local evolutionPending,guideProgress,dojoStates,dojoLastTick={},{},{},{}
 local v4WindowStart,v4WindowSkill,v4SavePending,dojoFriends={},{},{},{}
 local earnedPower,modeVotes,lastModeVote,roles,sevenJobs={},{},{},{},{}
 local sevenJobLastChoose,sevenJobLastUse,relayAcceptedSeq,lastAttack,lastRoleChange={},{},{},{},{}
 local lastTrap,lastWind,lastNet,netImmuneUntil,mobCombo,mobComboUntil={},{},{},{},{},{}
 local mobImpactSeq,mobLastHits,mobLastKOs,windUntil,windHighlight,invulnUntil={},{},{},{},{},{}
 local traps={}
 local Power={endRound=function()error("unexpected earnedPower fixture path")end}
 local function dropEgg()end
 local function cleanupScout()end
 local function clearEarnedPowerVisual()end
 local function stopWind()end
 local function restoreSlow()end
 local function stopRound(_,reason)assert(reason=="OPPONENT_LEFT");match.phase="RESULTS"end
 local function getTeamName(p)return p.side end
 local function ownScoutClass()return "WARRIOR"end
 local snapshots={}
 local function snapshotFor(p)return {hatchSaveStatus=persistenceState[p],equipped=RewardRules.export(rewardState,h2Ids[p])}end
 local remote={FireClient=function(_,p,s)table.insert(snapshots,{player=p,data=s})end}
 local warnings={}
 local function warn(...)table.insert(warnings,table.pack(...))end
 local function broadcast()for _,p in ipairs(people)do remote:FireClient(p,snapshotFor(p))end end
 local function publishV4Canonical()end
 local jobs,timers,threads={},{},{}
 local function resume(co,...)
  local ok,kind,arg=coroutine.resume(co,...)
  assert(ok,tostring(kind))
  if coroutine.status(co)=="suspended"then
   if kind=="TIMER"then table.insert(timers,{co=co,seconds=arg})
   else assert(kind=="STORE_REQUEST","unexpected suspension: "..tostring(kind))end
  end
 end
 local task={spawn=function(fn,...)
  local co=coroutine.create(fn);table.insert(threads,co);resume(co,...);return co
 end,wait=function(seconds)return coroutine.yield("TIMER",seconds)end}
 local records={}
 local studioHatchStore={}
 function studioHatchStore:GetAsync(key,options)
  assert(options and options.UseCache==false,"real load must disable cache")
  return clone(records[key])
 end
 function studioHatchStore:UpdateAsync(key,callback)
  local job={key=key,callback=callback,co=coroutine.running(),committed=false,done=false}
  table.insert(jobs,job)
  local outcome=coroutine.yield("STORE_REQUEST",job)
  if outcome=="ERROR"then error("EXPLICIT_BACKEND_UNCONFIRMED_ACK")end
  assert(outcome=="OK")
  return clone(job.result)
 end
 --@@CAN_WRITE@@--
 --@@RESTORE@@--
 --@@REWARD@@--
 --@@LOAD@@--
 --@@EQUIP@@--
 --@@EVOLVE@@--
 --@@REMOVE@@--
 local E={jobs=jobs,timers=timers,records=records,profiles=persistentProfiles,status=persistenceState,
  pending=evolutionPending,ids=h2Ids,rewardState=rewardState,delayed=delayedRestore,snapshots=snapshots,
  failures=function(p)return profileFailure and profileFailure[p]end,
  outstanding=function()return outstandingWrites end,match=match,clone=clone,same=same,warnings=warnings}
 local nextId=0
 function E:newPlayer(realId,ownedCount)
  nextId+=1
  local p={UserId=realId or 7010000001,Parent=Players,side="RED",attrs={}}
  function p:SetAttribute(k,v)self.attrs[k]=v end
  function p:GetAttribute(k)return self.attrs[k]end
  h2Ids[p]=nextId;lastSeq[p]=0;roles[p]="RAIDER";table.insert(people,p)
  assert(RewardRules.enroll(rewardState,nextId))
  local key="U_"..p.UserId
  if not records[key]then
   local raw=PersistentHatch.blank();raw.owned.forest_scout=ownedCount or 1;raw.owned.star_scout=1
   raw.progress={level=50,xp=0,mastery={forest_scout={level=10,xp=0},star_scout={level=10,xp=0},starter_scout={level=10,xp=0}},settledCount=0,claimedRoundIds={}}
   raw.evolution=Evolution.newProfile(PersistentHatch.policyUserId(p.UserId));raw.evolution.fragments=60
   assert(PersistentHatch.validate(raw));records[key]=raw
  end
  loadHatchProfile(p)
  assert(persistenceState[p]=="SAVED","setup load did not save")
  return p
 end
 function E:equip(p,item,seq)
  local count=#jobs;applyEquipScout(p,{action="EQUIP_SCOUT",itemId=item,seq=seq})
  assert(#jobs==count or #jobs==count+1)
  return if #jobs==count+1 then jobs[#jobs]else nil
 end
 function E:evolve(p,seq)
  local count=#jobs;applyEvolveScout(p,{action="EVOLVE_SCOUT",role="NONE",seq=seq})
  return if #jobs==count+1 then jobs[#jobs]else nil
 end
 function E:reward(p,receipt,item)
  local count=#jobs;commitFreeReward(p,receipt,item)
  return if #jobs==count+1 then jobs[#jobs]else nil
 end
 function E:commit(job)
  assert(job and not job.done and not job.committed,"invalid commit step")
  local raw=clone(records[job.key]);local frozen=clone(raw)
  local proposal=job.callback(raw)
  assert(same(raw,frozen),"UpdateAsync callback modified current input")
  if proposal then records[job.key]=clone(proposal)end
  job.result=clone(proposal);job.committed=true
 end
 function E:deliver(job,success)
  assert(job and not job.done,"durable confirmation request missing")
  if success and not job.committed then self:commit(job)end
  job.done=true;resume(job.co,success and "OK"or "ERROR")
 end
 function E:timer()
  local timer=table.remove(timers,1);assert(timer,"retry timer missing");resume(timer.co)
  return jobs[#jobs]
 end
 function E:remove(p,retainParent)
  assert(removing);removing(p)
  for i=#people,1,-1 do if people[i]==p then table.remove(people,i)end end
  if not retainParent then p.Parent=nil end
 end
 function E:load(p)loadHatchProfile(p)end
 function E:stored(p)return records["U_"..p.UserId]end
 function E:equipped(p)return RewardRules.export(rewardState,h2Ids[p]).equipped end
 function E:restore(p)restoreSavedProfile(p)end
 function E:clearCache(p)persistentProfiles[p]=nil end
 function E:startRound()assert(RewardRules.startRound(rewardState,1));match.phase="ACTIVE"end
 function E:finishRound(p)
  assert(RewardRules.finishRound(rewardState,1,{[h2Ids[p]]=true},{}));match.phase="LOBBY";restoreSavedProfile(p)
 end
 function E:externalGrant(p)
  records["U_"..p.UserId]=assert(PersistentHatch.grantTransition(self:stored(p),"Sother_server_20261122:7","forest_scout"))
 end
 return E
end
