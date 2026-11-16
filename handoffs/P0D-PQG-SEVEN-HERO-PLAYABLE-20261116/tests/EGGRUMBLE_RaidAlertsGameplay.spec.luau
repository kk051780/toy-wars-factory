--!strict
-- Runs original CastleMatchRules and our RaidAlerts module together in Luau VM.
-- Checks actual authoritative game events (not invented event payloads).
return function(Rules:any,Alerts:any)
 local function eq(actual:any,wanted:any,what:string)
  assert(actual==wanted,what..": expected "..tostring(wanted)..", got "..tostring(actual))
 end
 local team=Rules.new(Rules.MODE_TEAM,{
  {id="human",team="RED",isAI=false},
  {id="enemy",team="BLUE",isAI=true}
 },1)
 Rules.start(team)
 local first,cursor=Alerts.collect(team.events,0)
 eq(#first,0,"start is not an attack")
 Rules.takeEggs(team,"human",1,"enemy")
 local theft
 theft,cursor=Alerts.collect(team.events,cursor)
 eq(#theft,1,"real theft creates exactly one alert")
 eq(theft[1].kind,"RAID","theft kind")
 eq(theft[1].castleId,"enemy","threatened owner")
 eq(team.castles.enemy.vaultEggs,2,"authoritative castle stock decreased")
 Rules.depositEggs(team,"human",1)
 local deposit
 deposit,cursor=Alerts.collect(team.events,cursor)
 eq(#deposit,1,"actual deposit creates alert")
 eq(deposit[1].kind,"DELIVER","deposit kind")
 eq(deposit[1].castleId,"human","real depositor's castle")
 eq(team.teamDeposits.RED,1,"server-authoritative deposit score")
 Rules.takeFieldEgg(team,"human","FIELD_1")
 local field
 field,cursor=Alerts.collect(team.events,cursor)
 eq(#field,0,"field collectible must not falsely announce castle raid")
 local last=nil
 for _=1,5 do
  if team.phase~="ACTIVE" then break end
  last=Rules.damageCastle(team,"enemy","human",250)
 end
 assert(last and last.fallen,"real siege collapses enemy castle")
 local fall,after=Alerts.collect(team.events,cursor)
 eq(#fall,1,"winning siege announces one castle fall, not a second WIN event")
 eq(fall[1].kind,"FALL","fall kind")
 eq(fall[1].castleId,"enemy","destroyed castle owner")
 eq(team.winner,"RED","team victory still determined by original rule")
 local noRepeat=Alerts.collect(team.events,after)
 eq(#noRepeat,0,"refresh replay does not reproduce alert")
 assert(Rules.auditEggConservation(team).valid,"alerts do not disturb conserved eggs")

 local br=Rules.new(Rules.MODE_ROYALE,{
  {id="a"},{id="b"},{id="c"}
 },1)
 Rules.start(br)
 local brStart,brCursor=Alerts.collect(br.events,0)
 eq(#brStart,0,"BR start no raid")
 Rules.takeEggs(br,"a",1,"b")
 local brSignal
 brSignal,brCursor=Alerts.collect(br.events,brCursor)
 eq(#brSignal,1,"BR generates own real theft event")
 eq(brSignal[1].castleId,"b","BR owner does not share TEAM cursor")
 eq(br.phase,"ACTIVE","BR keeps game active on first theft")
 Rules.depositEggs(br,"a",1)
 local brDelivered
 brDelivered,brCursor=Alerts.collect(br.events,brCursor)
 eq(#brDelivered,1,"BR real delivery alert")
 eq(brDelivered[1].castleId,"a","BR depositor")
 eq(br.teamDeposits.RED,0,"BR does not write TEAM points")
 assert(Rules.auditEggConservation(br).valid,"BR egg conservation")
 return true
end
