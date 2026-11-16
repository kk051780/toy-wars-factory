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

 -- Real AI/player siege damage comes from original castle rules, not fake
 -- event fixtures. First snapshot at spawn must be quiet.
 local siege=Rules.new(Rules.MODE_TEAM,{
  {id="red",team="RED",isAI=false},{id="blue",team="BLUE",isAI=true}
 },1)
 Rules.start(siege)
 local priorHP:{[string]:number}={}
 local lastShown:{[string]:number}={}
 eq(#Alerts.siegeSignals(siege.castles,priorHP,lastShown,100),0,"spawn never triggers siege warning")
 Rules.damageCastle(siege,"blue","red",100)
 local firstSiege=Alerts.siegeSignals(siege.castles,priorHP,lastShown,101)
 eq(#firstSiege,1,"real castle damage raises siege warning")
 eq(firstSiege[1].kind,"SIEGE","siege signal kind")
 eq(firstSiege[1].castleId,"blue","only the attacked castle")
 eq(#Alerts.siegeSignals(siege.castles,priorHP,lastShown,102),0,"refresh unchanged HP is quiet")
 Rules.damageCastle(siege,"blue","red",100)
 eq(#Alerts.siegeSignals(siege.castles,priorHP,lastShown,103),0,"AI rapid attack is throttled")
 Rules.damageCastle(siege,"blue","red",100)
 local again=Alerts.siegeSignals(siege.castles,priorHP,lastShown,109)
 eq(#again,1,"siege warning allowed after seven-second cooldown")
 eq(again[1].castleId,"blue","throttled warning still identifies target")
 eq(#Alerts.siegeSignals(br.castles,{}, {},120),0,"BR new session has no stale siege warning")
 local endSiege
 for _=1,4 do
  if siege.phase~="ACTIVE" then break end
  endSiege=Rules.damageCastle(siege,"blue","red",250)
  Alerts.siegeSignals(siege.castles,priorHP,lastShown,111)
 end
 assert(endSiege and endSiege.fallen,"real siege eventually destroys castle")
 eq(#Alerts.siegeSignals(siege.castles,priorHP,lastShown,120),0,"dead castle never raises siege warning")
 assert(Rules.auditEggConservation(siege).valid,"siege warnings never change egg ledger")

 -- Native VM lightweight Roblox visual-state mock. Tests actual render function
 -- without making claims about fonts, performance, Studio cameras or Android.
 local instances={}
 local pending={}
 local function mockInstance(className:string):any
  local node:any={ClassName=className,Name="",_attributes={}}
  function node:FindFirstChild(name:string):any
   for _,item in ipairs(instances) do
    if item.Parent==self and item.Name==name then return item end
   end
   return nil
  end
  function node:GetAttribute(name:string):any return self._attributes[name] end
  function node:SetAttribute(name:string,value:any) self._attributes[name]=value end
  table.insert(instances,node)
  return node
 end
 Instance={new=mockInstance}
 Enum={Font={GothamBold="GothamBold"}}
 Color3={fromRGB=function(r:number,g:number,b:number)
  return {_type="Color3",r=r,g=g,b=b}
 end}
 UDim2={fromOffset=function(...) return {...} end,fromScale=function(...) return {...} end}
 Vector3={new=function(x:number,y:number,z:number) return {x=x,y=y,z=z} end}
 task={delay=function(_:number,callback:any) table.insert(pending,callback) end}
 typeof=function(value:any)
  if type(value)=="table" and value._type=="Color3" then return "Color3" end
  return type(value)
 end
 local visuals=Rules.new(Rules.MODE_TEAM,{
  {id="A",team="RED",isAI=false},{id="B",team="BLUE",isAI=true}
 },1)
 Rules.start(visuals)
 local banner=mockInstance("Part")
 banner.Name="OwnerFlag"
 banner.Parent={Name="VisualScene"}
 banner.Color=Color3.fromRGB(10,20,30)
 local session:any={rules=visuals,castleModels={
  B={banner=banner},
 }}
 Alerts.process(session) -- initial source event and HP baseline
 eq(#pending,0,"initial castle spawn must not create visual warning")
 Rules.damageCastle(visuals,"B","A",120)
 Alerts.process(session)
 local notice=banner:FindFirstChild("EGGRUMBLE_RaidNotice")
 assert(notice and notice.Enabled,"actual castle damage creates visible BillboardGui")
 local title=notice:FindFirstChild("Text")
 eq(title.Text,"城が攻撃中！","visible native mock siege copy")
 eq(#pending,1,"one pending expiration for initial siege alert")
 -- Theft has higher priority than same-round siege, and must extend the timer.
 Rules.takeEggs(visuals,"A",1,"B")
 Alerts.process(session)
 eq(title.Text,"卵強奪！防衛せよ","real egg theft supersedes siege warning")
 eq(#pending,2,"second alert schedules one new timeout")
 pending[1]()
 assert(notice.Enabled,"stale timer cannot hide a more recent objective alert")
 pending[2]()
 assert(not notice.Enabled,"latest timer hides the alert")
 eq(banner.Color.r,10,"timer restores original castle flag color")
 Rules.depositEggs(visuals,"A",1)
 Alerts.process(session)
 eq(#instances,3,"repeated events reuse one banner and one label")
 eq(title.Text,"卵強奪！防衛せよ","enemy flag never shows another player's delivery")
 return true
end
