 function E:progress(p)
  local count=#jobs
  match.serial+=1;match.phase="ACTIVE";match.startedAt=now
  beginProgressRounds("CLASSIC")
  recordServerProgress(p,"PICKUP")
  now+=60
  settleProgressAtRealEnd("RED")
  return if #jobs==count+1 then jobs[#jobs]else nil
 end
 function E:training(p)
  local count=#jobs
  v4SaveOneWindow(p,"BEAST",utc-30,utc)
  return if #jobs==count+1 then jobs[#jobs]else nil
 end
 function E:attributes(p)return clone(p.attrs),#p.attributeWrites end
 function E:localRows(p)
  return {profile=persistentProfiles[p],status=persistenceState[p],failure=profileFailure[p],
   progress=progressionProfile[p],progressStatus=progressionStatus[p],evolvePending=evolutionPending[p],
   trainingPending=v4SavePending[p],id=h2Ids[p]}
 end
