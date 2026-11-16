--!strict
-- Runs against the actual EGGRUMBLE_RaidAlerts.luau in native Luau VM.
-- Native-only rules checks, not Roblox Studio/mobile visual proof.
return function(Alerts:any)
 local function eq(a:any,b:any,label:string)
  assert(a==b,label..": expected "..tostring(b)..", got "..tostring(a))
 end
 eq(Alerts.intent({type="EGG_TAKEN",source="FIELD",quantity=1}),nil,"field pickup is not castle raid")
 eq(Alerts.intent({type="EGG_TAKEN",source="c1",quantity=0}),nil,"zero eggs")
 eq(Alerts.intent({type="EGG_TAKEN",source="c1",quantity=1}).castleId,"c1","real theft identifies victim")
 eq(Alerts.intent({type="EGG_TAKEN",source="c1",quantity=1}).kind,"RAID","theft not deposit")
 eq(Alerts.intent({type="EGG_DEPOSIT",owner="c2",quantity=2}).kind,"DELIVER","delivery")
 eq(Alerts.intent({type="CASTLE_FALL",owner="c1"}).kind,"FALL","castle fall")
 eq(Alerts.intent({type="WIN",winner="RED"}),nil,"winner UI belongs to result owner")
 eq(Alerts.intent({type="EGG_DROP",owner="c2",quantity=2}),nil,"drop not theft")
 eq(Alerts.intent(false),nil,"malformed event ignored")
 local events={
  {type="START",mode="TEAM"},
  {type="EGG_TAKEN",thief="c2",source="c1",quantity=1},
  {type="EGG_DEPOSIT",owner="c2",quantity=1},
  {type="CASTLE_FALL",owner="c1"},
 }
 local first,cursor=Alerts.collect(events,0)
 eq(#first,3,"three objective signals")
 eq(cursor,4,"cursor points to last authoritative event")
 eq(first[1].castleId,"c1","defender sees own threatened castle")
 eq(first[2].castleId,"c2","depositor sees own castle")
 eq(first[3].kind,"FALL","fall recorded")
 local repeatSignals,repeatCursor=Alerts.collect(events,cursor)
 eq(#repeatSignals,0,"same events never alert twice")
 eq(repeatCursor,cursor,"stable refresh cursor")
 table.insert(events,{type="EGG_TAKEN",source="FIELD",quantity=1})
 local newSignals,newCursor=Alerts.collect(events,cursor)
 eq(#newSignals,0,"neutral field eggs never leak into raid alarm")
 eq(newCursor,5,"ignored events still advance cursor")
 table.insert(events,{type="EGG_TAKEN",source="c2",quantity=1})
 local after,afterCursor=Alerts.collect(events,newCursor)
 eq(#after,1,"new theft produces a new signal")
 eq(after[1].castleId,"c2","correct second victim")
 eq(afterCursor,6,"cursor remains monotonic")
 local br,brCursor=Alerts.collect({{type="EGG_TAKEN",source="b1",quantity=1}},0)
 eq(#br,1,"BR independent session emits")
 eq(br[1].castleId,"b1","BR castle isolation")
 eq(brCursor,1,"BR cursor independent of TEAM")
 assert(not pcall(function() Alerts.collect(events,-1) end),"invalid cursor rejected")
 return true
end
