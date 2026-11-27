local function pendingRecovery(expectedFixed)
 local e=environment()
 local p=e.newPlayer()
 local initial=e.stored(p).revision
 local failed=e.equip(p,"forest_scout",1)
 e.ack(failed,false)
 assert(e.states[p]=="SAVE_FAILED")
 local old=e.equip(p,"star_scout",2)
 local latest=e.equip(p,"forest_scout",3)
 local latestNotice=e.notice(p)
 e.commit(old)
 e.ack(old)
 assert(e.outstanding()==1 and e.notice(p)==latestNotice)
 assert(e.profiles[p].equipped=="star_scout" and e.profiles[p].revision==initial+1)
 local status=if expectedFixed then "SAVE_FAILED" else "SAVED"
 assert(e.snapshot(p).hatchSaveStatus==status)
 assert(renderCurrent(e,p).label.Text==(if expectedFixed then FAILED else SAVED))
 print("RECOVERY_PENDING",status,e.profiles[p].equipped,e.outstanding())
 e.commit(latest)
 e.ack(latest)
 assert(e.outstanding()==0 and e.states[p]==status)
 assert(e.notice(p).needsReselect==true and e.profiles[p].revision==initial+1)
 assert(e.stored(p).equipped=="star_scout")
 local reselect=e.equip(p,"forest_scout",4)
 e.commit(reselect)
 e.ack(reselect)
 assert(e.outstanding()==0 and e.states[p]=="SAVED")
 assert(e.rule(p).equipped=="forest_scout")
 assert(e.profiles[p].revision==initial+2 and e.stored(p).equipped=="forest_scout")
 assert(not e.snapshot(p).hatchEquipNeedsReselect)
 assert(renderCurrent(e,p).label.Text==SAVED)
 print("RECOVERY_RESELECT",e.states[p],e.profiles[p].revision,e.profiles[p].equipped)

 local control=environment()
 local q=control.newPlayer()
 local controlInitial=control.stored(q).revision
 control.ack(control.equip(q,"forest_scout",1),false)
 local superseded=control.equip(q,"star_scout",2)
 local current=control.equip(q,"forest_scout",3)
 control.commit(current)
 control.ack(current)
 control.commit(superseded)
 control.ack(superseded)
 assert(control.outstanding()==0 and control.states[q]=="SAVED")
 assert(control.profiles[q].equipped=="forest_scout" and control.profiles[q].revision==controlInitial+1)
 print("RECOVERY_LATEST_FIRST",control.states[q],control.profiles[q].revision,control.profiles[q].equipped)
end

local function settledRound(expectedFixed)
 local uid=7010000001
 local summary={id="Solder_round:1",mode="CLASSIC",outcome="LOSS",duration=120,
  itemId="starter_scout",events={{id="A",kind="PICKUP"},{id="B",kind="EQUIP_USE"}}}
 local function seed()
  local record=assert(PersistentHatch.grantTransition(PersistentHatch.blank(),"Sreward_forest:1","forest_scout"))
  record.revision=2
  record.progress={level=2,xp=12,mastery={},claimedRoundIds={},settledCount=0}
  assert(PersistentHatch.validate(record))
  local store={record=record}
  function store:UpdateAsync(_,callback)
   if self.interleave then
    self.interleave=false
    assert(callback(self.record).progress.xp==84)
    assert(PersistentHatch.equip(self,uid,"forest_scout",self.record.revision))
   end
   local nextRecord=callback(self.record)
   if nextRecord then self.record=nextRecord end
   return nextRecord
  end
  return store
 end
 for _,kind in ipairs({"equip_then_settle","callback_replay","settle_first","unowned"}) do
  local store=seed()
  if kind=="equip_then_settle" then assert(PersistentHatch.equip(store,uid,"forest_scout",2)) end
  if kind=="callback_replay" then store.interleave=true end
  if kind=="unowned" then summary.itemId="star_scout" end
  local ok,_,reason=PersistentHatch.settleProgress(store,uid,summary)
  local row=store.record
  local xp=row.progress.xp
  local mastery=row.progress.mastery.starter_scout
  local receipt=row.progress.claimedRoundIds[summary.id]
  print("SETTLEMENT",kind,ok,reason,xp,row.revision,row.equipped,receipt,mastery and mastery.xp)
  if kind=="unowned" then
   assert(not ok and xp==12 and row.revision==2 and receipt==nil and mastery==nil)
  elseif kind=="settle_first" then
   assert(ok and row.equipped=="starter_scout" and xp==84 and mastery.xp==12)
  elseif expectedFixed then
   assert(ok and row.equipped=="forest_scout" and xp==84 and row.revision==4 and receipt==true)
   assert(mastery.xp==12 and row.progress.mastery.forest_scout==nil)
   assert(PersistentHatch.settleProgress(store,uid,summary))
   assert(store.record.revision==4 and store.record.progress.xp==84)
  else
   assert(not ok and reason=="PROGRESS_NOT_CONFIRMED" and xp==12 and row.revision==3)
   assert(receipt==nil and mastery==nil and row.equipped=="forest_scout")
  end
 end
end

local function supersededFailure()
 local e=environment()
 local p=e.newPlayer()
 local initial=e.stored(p).revision
 local old=e.equip(p,"star_scout",1)
 local newest=e.equip(p,"forest_scout",2)
 local notice=e.notice(p)
 e.commit(newest)
 e.ack(newest)
 assert(e.states[p]=="SAVED" and e.profiles[p].revision==initial+1)
 assert(not e.notice(p).needsReselect)
 e.ack(old,false)
 assert(e.outstanding()==0 and e.notice(p)==notice and e.states[p]=="SAVED")
 assert(e.stored(p).equipped=="forest_scout" and e.profiles[p].revision==initial+1)
 assert(renderCurrent(e,p).label.Text==SAVED)
 print("RECOVERY_OBSOLETE_FAILURE_IGNORED",e.states[p],e.profiles[p].revision)

 local active=environment()
 local q=active.newPlayer()
 local first=active.equip(q,"forest_scout",1)
 active.commit(first)
 active.ack(first)
 local current=active.equip(q,"star_scout",2)
 active.ack(current,false)
 assert(active.states[q]=="SAVE_FAILED" and renderCurrent(active,q).label.Text==FAILED)
 assert(active.outstanding()==0 and active.stored(q).equipped=="forest_scout")
 print("RECOVERY_CURRENT_FAILURE_RETAINED",active.states[q])

 local same=environment()
 local r=same.newPlayer()
 local baseRevision=same.stored(r).revision
 local uncertain=same.equip(r,"forest_scout",1)
 local sameChoice=same.equip(r,"starter_scout",2)
 local key="U_"..r.UserId
 same.backend[key]=assert(PersistentHatch.equipTransition(same.backend[key],"star_scout"))
 same.commit(sameChoice)
 same.ack(sameChoice)
 assert(same.states[r]=="SAVED" and same.profiles[r].revision==baseRevision+1)
 assert(same.notice(r).needsReselect==true)
 same.ack(uncertain,false)
 assert(same.states[r]=="SAVE_FAILED" and same.outstanding()==0)
 print("RECOVERY_UNFENCED_FAILURE_RETAINED",same.states[r])

 local early=environment()
 local s=early.newPlayer()
 local stale=early.equip(s,"star_scout",1)
 local pending=early.equip(s,"forest_scout",2)
 early.ack(stale,false)
 assert(early.states[s]=="SAVE_FAILED" and early.outstanding()==1)
 early.commit(pending)
 early.ack(pending)
 assert(early.states[s]=="SAVE_FAILED" and early.outstanding()==0)
 local retry=early.equip(s,"forest_scout",3)
 early.commit(retry)
 early.ack(retry)
 assert(early.states[s]=="SAVED" and early.outstanding()==0)
 assert(early.stored(s).equipped=="forest_scout")
 print("RECOVERY_PENDING_FAILURE_REQUIRES_RETRY",early.states[s])
end
