local NOTICE="⚠ 今の装備を表示中。もう一度選んでね"
local SAVED="✅ 保存サーバー応答あり（再ログイン検証は別）"
local FAILED="⚠️ 保存未確認！再ログインで消失の可能性"
local AMBER="255,207,120"
local GREEN="153,247,177"
local function conflicted()
 local e=environment();local p=e.newPlayer()
 local old=e.equip(p,"forest_scout",1);local latest=e.equip(p,"star_scout",2)
 e.commit(old);e.commit(latest);e.ack(latest)
 eq(e.states[p],"SAVED");eq(e.snapshot(p).hatchEquipNeedsReselect,true)
 return e,p,old,latest
end
local function renderCurrent(e,p)
 local h=makeHud();check(h.accept(e.snapshot(p)),"actual hatch snapshot must pass HUD ordering")
 return h
end

case("UI_LATEST_CONFLICT_SURVIVES_OLD_SUCCESS_ACK",function()
 local e,p,old=conflicted();local current=clone(e.profiles[p]);local token=e.notice(p)
 local h=renderCurrent(e,p);eq(h.label.Text,NOTICE);eq(h.label.TextColor3,AMBER)
 check(h.buttons[2].button.Text:sub(1,4)=="✓ ","actual canonical forest gets the checkmark")
 e.ack(old)
 eq(e.notice(p),token);eq(token.needsReselect,true);check(same(e.profiles[p],current))
 eq(e.snapshot(p).hatchEquipNeedsReselect,true);eq(e.outstanding(),0)
 eq(renderCurrent(e,p).label.Text,NOTICE);eq(#e.operations,2)
 return "older success cannot clear the latest conflict notice or trigger a hidden retry"
end)

case("UI_LATEST_SUCCESS_IGNORES_OLD_CONFLICT_ACK",function()
 local e=environment();local p=e.newPlayer()
 local old=e.equip(p,"forest_scout",1);local latest=e.equip(p,"star_scout",2)
 e.commit(latest);e.ack(latest);local token=e.notice(p);local current=clone(e.profiles[p])
 e.commit(old);e.ack(old)
 eq(e.notice(p),token);eq(token.needsReselect,false);check(same(e.profiles[p],current))
 eq(e.snapshot(p).hatchEquipNeedsReselect,false)
 local h=renderCurrent(e,p);eq(h.label.Text,SAVED);eq(h.label.TextColor3,GREEN)
 check(h.buttons[3].button.Text:sub(1,4)=="✓ ");eq(e.outstanding(),0)
 return "older conflict cannot redisplay a warning after the latest confirmed choice"
end)

case("UI_RESELECTION_WAIT_AND_UNKNOWN_ACK_PRESERVE_TRUTHFUL_STATUS",function()
 local e,p,old=conflicted();e.ack(old);local previous=e.notice(p)
 local retry=e.equip(p,"star_scout",3)
 check(e.notice(p)~=previous);eq(e.notice(p).needsReselect,true)
 eq(renderCurrent(e,p).label.Text,NOTICE,"click alone must not restore green success")
 e.commit(retry);e.ack(retry,false)
 eq(e.states[p],"SAVE_FAILED");eq(e.notice(p).needsReselect,true)
 eq(e.snapshot(p).hatchEquipNeedsReselect,false)
 eq(renderCurrent(e,p).label.Text,FAILED,"unknown ACK keeps the general failure warning")
 local confirmed=e.equip(p,"star_scout",4);e.commit(confirmed);e.ack(confirmed)
 eq(e.states[p],"SAVED");eq(e.notice(p).needsReselect,false)
 eq(renderCurrent(e,p).label.Text,SAVED);eq(e.outstanding(),0)
 return "pending reselect, unknown ACK and acknowledged same-item recovery remain distinct"
end)

case("UI_UNRELATED_ACTUAL_MODE_VOTE_DOES_NOT_RETIRE_EQUIP_NOTICE",function()
 local e=environment();local p=e.newPlayer()
 local old=e.equip(p,"forest_scout",1);local latest=e.equip(p,"star_scout",2)
 local token=e.notice(p);e.commit(old);e.commit(latest)
 e.vote(p,"SCORE_5",99);eq(e.voted(p),"SCORE_5");eq(e.notice(p),token)
 e.ack(latest);eq(e.notice(p).needsReselect,true);e.ack(old)
 eq(renderCurrent(e,p).label.Text,NOTICE);eq(#e.operations,2);eq(e.outstanding(),0)
 return "the actual shared sequence update for mode voting does not suppress equip feedback"
end)

case("UI_NOTICE_USES_MONOTONIC_CACHE_NOT_OLD_ACK_ITEM",function()
 local e=environment();local p=e.newPlayer();local key="U_"..p.UserId
 local latest=e.equip(p,"star_scout",1);e.commit(latest)
 e.backend[key]=assert(PersistentHatch.equipTransition(e.backend[key],"forest_scout"))
 e.profiles[p]=clone(e.backend[key]);local newer=clone(e.profiles[p])
 e.ack(latest)
 check(same(e.profiles[p],newer));eq(e.notice(p).needsReselect,true)
 eq(e.snapshot(p).hatchEquipped,"forest_scout");eq(renderCurrent(e,p).label.Text,NOTICE)
 local other=environment();local q=other.newPlayer();local otherKey="U_"..q.UserId
 local request=other.equip(q,"star_scout",1)
 other.backend[otherKey]=assert(PersistentHatch.equipTransition(other.backend[otherKey],"forest_scout"))
 other.commit(request)
 other.backend[otherKey]=assert(PersistentHatch.equipTransition(other.backend[otherKey],"star_scout"))
 other.profiles[q]=clone(other.backend[otherKey]);newer=clone(other.profiles[q])
 other.ack(request)
 check(same(other.profiles[q],newer));eq(other.notice(q).needsReselect,false)
 eq(renderCurrent(other,q).label.Text,SAVED)
 return "both old-success and old-conflict responses defer to the already newer canonical cache"
end)

case("UI_ACTUAL_LOAD_RETIRES_OLD_FEEDBACK_IDENTITY",function()
 local e=environment();local p=e.newPlayer()
 local old=e.equip(p,"forest_scout",1);local latest=e.equip(p,"star_scout",2)
 e.commit(old);e.commit(latest);check(e.notice(p)~=nil)
 e.load(p);eq(e.notice(p),nil);eq(e.states[p],"SAVED")
 e.ack(latest);e.ack(old)
 eq(e.notice(p),nil);eq(e.snapshot(p).hatchEquipNeedsReselect,false)
 eq(e.outstanding(),0);eq(renderCurrent(e,p).label.Text,SAVED)
 return "real load resets only feedback state; old callbacks cannot recreate it"
end)

case("UI_REMOVAL_AND_CHANGED_ENROLLMENT_ISOLATE_FEEDBACK",function()
 local e,p,old=conflicted();e.remove(p,true);eq(e.notice(p),nil)
 local replacement=e.newPlayer(p.UserId);e.ack(old)
 eq(e.notice(p),nil);eq(e.notice(replacement),nil)
 eq(e.snapshot(replacement).hatchEquipNeedsReselect,false);eq(e.outstanding(),0)
 local other,q,late=conflicted();local token=other.notice(q)
 local newId=other.enroll(q);check(newId~=token.uid)
 eq(other.snapshot(q).hatchEquipNeedsReselect,false)
 other.ack(late);eq(other.notice(q),token)
 eq(other.snapshot(q).hatchEquipNeedsReselect,false);eq(other.outstanding(),0)
 other.remove(q,true);eq(other.notice(q),nil)
 return "removed Player state is released; a live Parent with a different enrollment cannot display an old notice"
end)

case("UI_UNRELATED_REAL_REWARD_FAILURE_KEEPS_GENERAL_WARNING",function()
 local e=environment();local p=e.newPlayer();local failed=e.equip(p,"forest_scout",1)
 e.ack(failed,false);local retry=e.equip(p,"star_scout",2)
 e.rewardAttempt(p,"Sui_unrelated_reward:91","forest_scout")
 local episode=e.failures(p);eq(episode.equipOnly,false)
 e.commit(retry);e.ack(retry)
 eq(e.states[p],"SAVE_FAILED");eq(e.failures(p),episode)
 eq(e.snapshot(p).hatchEquipNeedsReselect,false);eq(renderCurrent(e,p).label.Text,FAILED)
 local count=#e.operations;eq(e.equip(p,"starter_scout",3),nil)
 eq(#e.operations,count);eq(renderCurrent(e,p).label.Text,FAILED);eq(e.outstanding(),0)
 return "UI state cannot clear or hide the actual unrelated failure episode"
end)

case("UI_HUD_STRICT_BOOLEAN_PHASE_AND_FAILURE_PRIORITY",function()
 local e=environment();local p=e.newPlayer();local original=e.snapshot(p)
 local rows={
  {state="SAVED",phase="LOBBY",flag=true,text=NOTICE,color=AMBER,visible=true,active=true},
  {state="SAVED",phase="COUNTDOWN",flag=true,text=SAVED,color=GREEN,visible=true,active=false},
  {state="SAVED",phase="RESULTS",flag=true,text=SAVED,color=GREEN,visible=true,active=false},
  {state="SAVED",phase="ACTIVE",flag=true,text=SAVED,color=GREEN,visible=false,active=false},
  {state="SAVE_FAILED",phase="LOBBY",flag=true,text=FAILED,color=AMBER,visible=true,active=true},
  {state="LOADING",phase="LOBBY",flag=true,text="🔄 以前の魔獣を読み込み中",color=AMBER,visible=true,active=false},
  {state="LOCAL_ONLY",phase="LOBBY",flag=true,text="⚠️ Studioでは一時保存のみ。再ログインで消えます",color=AMBER,visible=true,active=true},
 }
 for _,row in ipairs(rows)do
  local packet=clone(original);packet.hatchSaveStatus=row.state;packet.phase=row.phase
  packet.hatchEquipNeedsReselect=row.flag
  local h=makeHud();check(h.accept(packet));eq(h.label.Text,row.text);eq(h.label.TextColor3,row.color)
  eq(h.label.Visible,row.visible);eq(h.buttons[1].button.Active,row.active)
 end
 for _,row in ipairs({{},{value=false},{value=1},{value="true"},{value={}}})do
  local packet=clone(original);packet.hatchEquipNeedsReselect=row.value
  local h=makeHud();check(h.accept(packet));eq(h.label.Text,SAVED);eq(h.label.TextColor3,GREEN)
 end
 local packet=clone(original);packet.hatchEquipNeedsReselect=true;packet.hatchEnabled=false
 local h=makeHud();check(h.accept(packet));eq(h.label.Visible,false);eq(h.panel.Visible,false)
 eq(h.buttons[1].button.Active,false)
 h=makeHud();h.evolution(true);packet.hatchEnabled=true;check(h.accept(packet))
 eq(h.panel.Visible,false);eq(h.label.Text,NOTICE,"existing evolution panel visibility stays independent")
 return "only strict true plus SAVED and actionable lobby changes the existing label; other state and phase rules remain"
end)

case("UI_EXISTING_SNAPSHOT_ORDER_PREVENTS_OLD_NOTICE_ROLLBACK",function()
 local e=environment();local p=e.newPlayer();local packet=e.snapshot(p);local h=makeHud()
 packet.updateId=10;packet.hatchEquipNeedsReselect=true;check(h.accept(packet));eq(h.label.Text,NOTICE)
 local next=clone(packet);next.updateId=11;next.hatchEquipNeedsReselect=false
 check(h.accept(next));eq(h.label.Text,SAVED)
 eq(h.accept(packet),nil);eq(h.label.Text,SAVED,"old warning cannot return")
 local latest=clone(packet);latest.updateId=12;check(h.accept(latest));eq(h.label.Text,NOTICE)
 eq(h.accept(next),nil);eq(h.label.Text,NOTICE,"old success cannot hide warning")
 for _,row in ipairs({{},{value=-1},{value=1.5},{value=0/0},{value=1000000001}})do
  local bad=clone(next);bad.updateId=row.value
  eq(h.accept(bad),nil);eq(h.label.Text,NOTICE)
 end
 local olderRound=clone(next);olderRound.serial=0;olderRound.updateId=99
 eq(h.accept(olderRound),nil);eq(h.label.Text,NOTICE)
 eq(h.latest(),latest)
 return "the original HUD ordinal and round gate protects both notice directions"
end)
