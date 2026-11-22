-- Independent equipment completion review. Service/backend fixtures only.
-- Complete pinned modules and exact Game excerpts are inserted by run.py.
--@@MODULES@@--
local function clone(value)
 if type(value)~="table"then return value end
 local out={};for k,v in pairs(value)do out[k]=clone(v)end;return out
end
local function same(a,b)
 if type(a)~=type(b)then return false end
 if type(a)~="table"then return a==b end
 for k,v in pairs(a)do if not same(v,b[k])then return false end end
 for k in pairs(b)do if a[k]==nil then return false end end
 return true
end
local function check(ok,message)assert(ok,message)end
local function eq(a,b,message)
 assert(a==b,(message or "equality").." expected="..tostring(b).." actual="..tostring(a))
end
local function environment()
 local now=0
 local os={clock=function()return now end}
 local Players={};local players={};local removeCallback=nil;local closeCallback=nil
 Players.PlayerRemoving={Connect=function(_self,fn)removeCallback=fn end}
 function Players:GetPlayers()return table.clone(players)end
 local game={BindToClose=function(_self,fn)closeCallback=fn end}
 local RunService={IsStudio=function()return true end}
 local tasks,operations,backend,remotes,warnings={},{},{},{},{}
 local trace={}
 local function record(kind,details)table.insert(trace,{at=now,kind=kind,details=details})end
 local function resume(thread,...)
  local ok,yielded=coroutine.resume(thread,...)
  assert(ok,"unexpected async exception: "..tostring(yielded))
  return yielded
 end
 local task={spawn=function(fn)
  local co=coroutine.create(fn);table.insert(tasks,co);resume(co);return co
 end,wait=function(seconds)
  record("WAIT",seconds)
  return coroutine.yield({kind="WAIT",seconds=seconds})
 end}
 local studioHatchStore={}
 function studioHatchStore:UpdateAsync(key,transform)
  local op={index=#operations+1,key=key,transform=transform,
   thread=coroutine.running(),status="REQUESTED",callbacks=0}
  table.insert(operations,op);record("REQUEST",op.index)
  -- Unlike the author's fixture, NO transition or durable commit has occurred.
  local response=coroutine.yield({kind="STORE_REQUEST",operation=op})
  record("ACK",{index=op.index,ok=response.ok})
  if not response.ok then error("bounded backend reports unconfirmed acknowledgement")end
  return clone(response.value)
 end
 function studioHatchStore:GetAsync()error("this review must not silently add a load")end
 function studioHatchStore:SetAsync()error("overwrite persistence API is forbidden")end
 local function transform(op)
  local original=clone(backend[op.key])
  local before=clone(original)
  local co=coroutine.create(op.transform)
  local ok,value=coroutine.resume(co,original)
  assert(ok,"actual Store transition must not throw")
  eq(coroutine.status(co),"dead","UpdateAsync callback cannot yield")
  check(same(original,before),"actual Store callback must not mutate original input")
  op.callbacks+=1;record("TRANSFORM",op.index)
  return value
 end
 local function commit(op,intervene)
  eq(op.status,"REQUESTED","one durable commit per request")
  local value=transform(op)
  if intervene then
   -- A conflicting writer makes the first proposal obsolete. The real Store
   -- callback is rerun against the newly committed record before this commit.
   intervene(backend,op.key)
   value=transform(op)
  end
  if value~=nil then backend[op.key]=clone(value)end
  op.response=clone(value);op.status="COMMITTED"
  record("COMMIT",{index=op.index,revision=value and value.revision})
 end
 local function acknowledge(op,confirmed)
  check(op.status=="REQUESTED"or op.status=="COMMITTED","exactly one acknowledgement")
  if confirmed~=false then eq(op.status,"COMMITTED","success requires actual prior commit")end
  op.status="ACKNOWLEDGED"
  resume(op.thread,{ok=confirmed~=false,value=op.response})
  eq(coroutine.status(op.thread),"dead","equip and successful grant complete without another hidden yield")
 end
 local delayedRestore,dojoFriends,dojoLastTick,dojoStates,earnedPower={},{},{},{},{}
 local evolutionPending,guideProgress,h2Ids,invulnUntil,lastAttack,lastFreeHatch={},{},{},{},{},{}
 local lastModeVote,lastNet,lastRoleChange,lastSeq,lastTrap,lastWind={},{},{},{},{},{}
 local mobCombo,mobComboUntil,mobImpactSeq,mobLastHits,mobLastKOs,modeVotes,netImmuneUntil={},{},{},{},{},{},{}
 local persistenceState,persistentProfiles,progressionEvents,progressionLastAward,progressionProfile={},{},{},{},{}
 local progressionRound,progressionStatus,relayAcceptedSeq,roles,sevenJobLastChoose,sevenJobLastUse={},{},{},{},{},{}
 local sevenJobs,v4SavePending,v4WindowSkill,v4WindowStart,windHighlight,windUntil={},{},{},{},{},{}
 local rewardState=RewardRules.new()
 local match={phase="LOBBY"}
 local traps={}
 local outstandingWrites=0
 local function getTeamName(player)return player.team end
 local function ownScoutClass(_player)return"WARRIOR"end
 local function dropEgg(_player)end
 local function cleanupScout(_player)end
 local function clearEarnedPowerVisual(_player)end
 local function stopWind(_player)end
 local function restoreSlow(_player)end
 local function stopRound(...)error("unrelated settlement not part of isolated review")end
 local function warn(...)table.insert(warnings,table.pack(...))end
 local function snapshotFor(player)
  local inv=RewardRules.export(rewardState,h2Ids[player])
  return {state=persistenceState[player],equipped=inv and inv.equipped}
 end
 local remote={FireClient=function(_self,player,snapshot)
  record("REMOTE",player.UserId)
  table.insert(remotes,{player=player,snapshot=clone(snapshot)})
 end}
--@@CAN_WRITE@@--
--@@RESTORE@@--
--@@COMMIT@@--
--@@EQUIP@@--
--@@REMOVAL@@--
--@@SHUTDOWN@@--
 local serial=0
 local function enroll(player)
  serial+=1;h2Ids[player]=serial
  check(RewardRules.enroll(rewardState,serial),"real RewardRules enrollment")
  return serial
 end
 local function newPlayer(userId)
  local player={UserId=userId or 142857,Parent=Players,team="RED",attributes={}}
  function player:SetAttribute(name,value)self.attributes[name]=value end
  table.insert(players,player);enroll(player)
  local key="U_"..tostring(player.UserId)
  if not backend[key]then
   local raw=PersistentHatch.grantTransition(nil,"Sreviewforest:1","forest_scout")
   raw=PersistentHatch.grantTransition(raw,"Sreviewstarrs:2","star_scout")
   check(PersistentHatch.validate(raw),"initial actual transition result")
   backend[key]=raw
  end
  persistentProfiles[player]=clone(backend[key]);persistenceState[player]="SAVED"
  restoreSavedProfile(player);return player
 end
 local function equip(player,item,seq)
  local count=#operations
  applyEquipScout(player,{action="EQUIP_SCOUT",itemId=item,seq=seq})
  return if #operations==count+1 then operations[#operations]else nil
 end
 local function grant(player,receipt,item)
  local count=#operations
  commitFreeReward(player,receipt,item)
  eq(#operations,count+1,"real free-grant entered actual Store")
  return operations[#operations]
 end
 local function remove(player,keepParent)
  removeCallback(player)
  for i,p in ipairs(players)do if p==player then table.remove(players,i);break end end
  if not keepParent then player.Parent=nil end
  record("REMOVE",player.UserId)
 end
 local function beginShutdown()
  local co=coroutine.create(closeCallback)
  local yielded=resume(co)
  return {thread=co,last=yielded}
 end
 local function stepShutdown(handle)
  eq(coroutine.status(handle.thread),"suspended","shutdown remains pending")
  eq(handle.last.kind,"WAIT","real BindToClose waits on pending count")
  now+=handle.last.seconds
  handle.last=resume(handle.thread,handle.last.seconds)
  return coroutine.status(handle.thread)
 end
 return {newPlayer=newPlayer,enroll=enroll,equip=equip,grant=grant,remove=remove,
  commit=commit,ack=acknowledge,operations=operations,backend=backend,
  profiles=persistentProfiles,states=persistenceState,ids=h2Ids,delayed=delayedRestore,
  remotes=remotes,warnings=warnings,trace=trace,Players=Players,
  outstanding=function()return outstandingWrites end,
  rule=function(player)return RewardRules.export(rewardState,h2Ids[player])end,
  stored=function(player)return backend["U_"..tostring(player.UserId)]end,
  shutdown=beginShutdown,stepShutdown=stepShutdown,
  canWrite=canWriteProfile,
 }
end
local failed=0
local function case(name,body)
 local ok,value=pcall(body)
 print("CASE|"..name.."|"..(if ok then"PASS"else"FAIL").."|"..tostring(value or ""):gsub("\n"," "))
 if not ok then failed+=1 end
end
local function observation(name,body)
 local ok,value=pcall(body)
 print("OBSERVATION|"..name.."|"..(if ok then"CONFIRMED"else"NOT_REPRODUCED").."|"..tostring(value or ""):gsub("\n"," "))
 check(ok,"observation failed unexpectedly: "..name)
end
--@@CASES@@--
if failed>0 then error(tostring(failed).." independent equipment cases failed",0)end
