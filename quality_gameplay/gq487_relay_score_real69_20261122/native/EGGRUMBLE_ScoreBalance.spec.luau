--!strict
-- Actual native Luau scoring regression; original Results module is required by Runner.
return function(Results:any):boolean
 local count=0
 local function equal(actual:any,expected:any,why:string)
  count+=1
  assert(actual==expected,why.." expected "..tostring(expected).." got "..tostring(actual))
 end
 local function state(mode:string,winner:any,phase:string)
  return {
   mode=mode,phase=phase,winner=winner,ids={"war","mage","assassin","builder"},
   castles={
    war={team=if mode=="TEAM" then "RED" else nil,alive=true,isAI=false},
    mage={team=if mode=="TEAM" then "BLUE" else nil,alive=false,isAI=false},
    assassin={team=if mode=="TEAM" then "RED" else nil,alive=false,isAI=true},
    builder={team=if mode=="TEAM" then "BLUE" else nil,alive=false,isAI=true},
   },
   events={
    {type="EGG_TAKEN",thief="war",quantity=2,source="mage"},
    {type="EGG_DEPOSIT",owner="war",quantity=2},
    {type="FIELD_EGG_TAKEN",owner="war",eggId="FIELD_1"},
    {type="CASTLE_FALL",owner="mage",attacker="war",releasedEggs=1},
    {type="EGG_DROP",owner="war",quantity=1},
    {type="WIN",winner=winner}
   }
  }
 end
 local m=state("TEAM","RED","FINISHED")
 local t=Results.build(m,{war=50,mage=7,assassin=3,builder=0})
 local war=t.rows[1]
 equal(war.id,"war","winner and contributor place first")
 equal(war.ko,50,"actual neutral kills")
 equal(war.stolen,2,"enemy castle eggs count")
 equal(war.deposited,2,"home return counts")
 equal(war.castlesDestroyed,1,"castle final blow")
 equal(war.won,true,"team win reward")
 equal(war.score,300+340+240+440+200+500,"balanced across KO egg and castle")
 equal(t.rows[3].id,"mage","defeated participant still ranked")
 local ally=nil
 for _,row in ipairs(t.rows) do if row.id=="assassin" then ally=row end end
 assert(ally~=nil,"AI ally represented")
 equal(ally.won,true,"living or eliminated teammate receives team victory")
 equal(ally.alive,false,"eliminated player never regains survival points")
 local total=0;for _,row in ipairs(t.rows) do total+=row.ko end
 equal(total,60,"no multiplied kill counts")
 local br=Results.build(state("BATTLE_ROYALE","war","FINISHED"),{war=50,mage=7})
 local mage=nil
 for _,row in ipairs(br.rows) do if row.id=="mage" then mage=row end end
 equal(br.rows[1].won,true,"BR sole castle champion")
 equal(mage.won,false,"BR loser not rewarded")
 local inactive=Results.build(state("TEAM","RED","ACTIVE"),{war=50})
 for _,row in ipairs(inactive.rows) do equal(row.won,false,"no victory reward before finish") end
 local farm=state("TEAM","RED","FINISHED")
 farm.events={}
 -- Actual Rules.takeEggs always emits a non-FIELD enemy source.
 for _=1,100 do
  table.insert(farm.events,{type="EGG_TAKEN",thief="war",source="mage",quantity=3})
  table.insert(farm.events,{type="EGG_DEPOSIT",owner="war",quantity=3})
  table.insert(farm.events,{type="CASTLE_FALL",owner="mage",attacker="war"})
 end
 local capped=Results.build(farm,{war=500000,rogue=1})
 local hero=nil
 for _,row in ipairs(capped.rows) do if row.id=="war" then hero=row end end
 assert(hero~=nil,"capped hero exists")
 equal(hero.ko,500000,"real KO raw total retained")
 equal(hero.score,1200+1190+960+1320+200+500,"every category bounded")
 -- Actual 10k+ mass neutral-KO win condition must keep progressing after 200.
 -- Category point cap stays 1200 so one KO grinder cannot dominate objective play.
 local milestoneState=state("TEAM","RED","ACTIVE")
 milestoneState.events={}
 local function earnedKO(n:number):number
  local result=Results.build(milestoneState,{war=n})
  for _,row in ipairs(result.rows) do
   if row.id=="war" then return row.score-200 end -- living-castle bonus excluded
  end
  error("KO scorer failed to return owner")
 end
 equal(earnedKO(0),0,"zero KO earns no combat points")
 equal(earnedKO(50),300,"early KO pacing preserved")
 equal(earnedKO(100),600,"first hundred worth six points each")
 equal(earnedKO(200),630,"200 KOs no longer caps points")
 equal(earnedKO(1000),870,"one thousand KOs remain rewarding")
 equal(earnedKO(10000),1140,"ten thousand personal KOs still earn more")
 equal(earnedKO(30000),1200,"thirty thousand KOs reach bounded maximum")
 equal(earnedKO(30001),1200,"post milestone cap prevents total domination")
 equal(earnedKO(500000),1200,"extreme grinding cannot dominate eggs and castles")
 equal(Results.SCORE.KO_CAP,1200,"KO maximum unchanged")
 equal(earnedKO(199)<earnedKO(201),true,"KO monotonic across former hard cap")

 local corrupted=Results.build(state("TEAM","RED","FINISHED"),{war=-1,mage=0/0,assassin=math.huge})
 for _,row in ipairs(corrupted.rows) do equal(row.ko,0,"bad kill values rejected") end
 -- A neutral mob farming tie must not outrank identical real castle/egg objective points.
 local contest={
  mode="BATTLE_ROYALE",phase="FINISHED",winner=nil,ids={"KO","OBJECTIVE"},
  castles={KO={alive=false,isAI=false},OBJECTIVE={alive=false,isAI=false}},
  events={{type="EGG_DEPOSIT",owner="OBJECTIVE",quantity=5}}
 }
 local ranked=Results.build(contest,{KO=100,OBJECTIVE=0})
 equal(ranked.rows[1].id,"OBJECTIVE","equal points: egg objective outranks mob farming")
 equal(ranked.rows[1].score,600,"deposited five eggs worth six hundred")
 equal(ranked.rows[2].score,600,"one hundred actual KOs worth six hundred")
 equal(ranked.rows[1].objectiveScore,600,"objective-only tie breaker grounded in events")
 equal(ranked.rows[2].objectiveScore,0,"mob farming is not an objective")
 local originalEvent=contest.events[1]
 equal(originalEvent.owner,"OBJECTIVE","score never changes original authoritative event")
 local withCastle={
  mode="TEAM",phase="ACTIVE",winner=nil,ids={"GOAL","KO"},
  castles={GOAL={alive=false,team="RED"},KO={alive=false,team="BLUE"}},
  events={{type="CASTLE_FALL",attacker="GOAL",owner="other"}}
 }
 local castles=Results.build(withCastle,{KO=74}) -- 74*6=444, castle=440
 equal(castles.rows[1].id,"KO","raw point advantage still beats objective tie breaker")
 equal(castles.rows[2].id,"GOAL","no unconditional castle priority over actual score")

 -- Attack the actual egg-raid exploit: a thief who dies before returning
 -- must keep the raw theft counter, but earns NO completed-raid bonus.
 local function isolated(events:{any}):any
  local m=state("TEAM",nil,"ACTIVE")
  m.events=events
  return m
 end
 local function ownerRow(snapshot:any):any
  for _,row in ipairs(snapshot.rows) do if row.id=="war" then return row end end
  error("war missing from score")
 end
 local raw=ownerRow(Results.build(isolated({
  {type="EGG_TAKEN",thief="war",source="mage",quantity=2},
 }),{}))
 equal(raw.stolen,2,"raw enemy theft count retained for match history")
 equal(raw.securedSteals,0,"steal without return grants no completed raid")
 equal(raw.score,200,"steal-only cannot earn 340 bonus points")
 local death=ownerRow(Results.build(isolated({
  {type="EGG_TAKEN",thief="war",source="mage",quantity=2},
  {type="EGG_DROP",owner="war",quantity=2},
  {type="FIELD_EGG_TAKEN",owner="war",eggId="FIELD_9"},
  {type="EGG_DEPOSIT",owner="war",quantity=1},
 }),{}))
 equal(death.securedSteals,0,"death discards pending raid credit")
 equal(death.deposited,1,"new field egg home deposit still counts")
 equal(death.score,320,"only actual home deposit points after death")
 local mixed=ownerRow(Results.build(isolated({
  {type="EGG_TAKEN",thief="war",source="mage",quantity=2},
  {type="FIELD_EGG_TAKEN",owner="war",eggId="FIELD_8"},
  {type="EGG_DEPOSIT",owner="war",quantity=3},
 }),{}))
 equal(mixed.securedSteals,2,"return three eggs proves two enemy raids")
 equal(mixed.score,200+3*120+2*170,"field-first attribution with full home return")
 local partial=ownerRow(Results.build(isolated({
  {type="EGG_TAKEN",thief="war",source="mage",quantity=2},
  {type="FIELD_EGG_TAKEN",owner="war",eggId="FIELD_6"},
  {type="EGG_DEPOSIT",owner="war",quantity=1},
 }),{}))
 equal(partial.securedSteals,0,"field egg conservatively consumes first deposit")
 equal(partial.pendingSteals,2,"unfinished enemy raid stays unsettled")
 local followup=ownerRow(Results.build(isolated({
  {type="FIELD_EGG_TAKEN",owner="war",eggId="FIELD_4"},
  {type="EGG_DEPOSIT",owner="war",quantity=1},
  {type="EGG_TAKEN",thief="war",source="mage",quantity=1},
  {type="EGG_DEPOSIT",owner="war",quantity=1},
 }),{}))
 equal(followup.securedSteals,1,"later genuine raid deposit is credited")
 equal(followup.deposited,2,"both home deposits remain counted")
 equal(followup.score,670,"FIELD_4 rare60 survives ordinary delivery plus fresh personal raid")
 local fallen=ownerRow(Results.build(isolated({
  {type="EGG_TAKEN",thief="war",source="mage",quantity=2},
  {type="CASTLE_FALL",owner="war",attacker="mage"},
  {type="EGG_DEPOSIT",owner="war",quantity=2},
 }),{}))
 equal(fallen.securedSteals,0,"collapsed home cannot credit pending raid")
 local legacy=ownerRow(Results.build(isolated({
  {type="EGG_TAKEN",thief="war",source="FIELD",quantity=3},
  {type="EGG_DEPOSIT",owner="war",quantity=3},
 }),{}))
 equal(legacy.stolen,0,"legacy field event cannot impersonate enemy vault")
 equal(legacy.securedSteals,0,"field-source events cannot earn raid bonus")
 local redo=ownerRow(Results.build(isolated({
  {type="EGG_TAKEN",thief="war",source="mage",quantity=1},
  {type="EGG_DROP",owner="war",quantity=1},
  {type="EGG_TAKEN",thief="war",source="mage",quantity=1},
  {type="EGG_DEPOSIT",owner="war",quantity=1},
 }),{}))
 equal(redo.stolen,2,"raw theft tracks both actual attempts")
 equal(redo.securedSteals,1,"only successfully returned second theft scores")
 equal(redo.score,200+170+120,"lost and returned raid scored once")
 -- TEAM cooperative castle reward: each personal castle defender who is still
 -- in the match when the team actually captures a rival castle gets 90 points.
 -- The final blow stays 440, BR remains individual, score always bounded.
 local function byId(snapshot:any,key:string):any
  for _,row in ipairs(snapshot.rows) do if row.id==key then return row end end
  error("missing tested participant "..key)
 end
 local coOp=state("TEAM",nil,"ACTIVE")
 coOp.events={{type="CASTLE_FALL",owner="mage",attacker="war"}}
 local coopScore=Results.build(coOp,{assassin=5})
 equal(byId(coopScore,"war").castlesDestroyed,1,"siege final blow remains with actual attacker")
 equal(byId(coopScore,"war").teamCastleSupport,0,"no double-credit for final hitter")
 equal(byId(coopScore,"war").score,200+440,"attacker score unchanged")
 equal(byId(coopScore,"assassin").teamCastleSupport,1,"living same-team defender shares team siege")
 equal(byId(coopScore,"assassin").score,30+90,"eliminated end-state cannot erase earlier team siege")
 equal(byId(coopScore,"assassin").objectiveScore,90,"team objective tie-break includes real siege share")
 equal(byId(coopScore,"builder").teamCastleSupport,0,"enemy team gets no credit")
 -- Anti-AFK: survival/teammate alone is never a server-verified assist.
 local idle=byId(Results.build(coOp,{}),"assassin")
 equal(idle.teamCastleSupport,0,"idle teammate never gets free siege points")
 equal(idle.specialty,"参加","idle teammate cannot claim co-op specialist")
 equal(idle.score,0,"idle teammate keeps zero when castle already eliminated")
 local incidental=byId(Results.build(coOp,{assassin=4}),"assassin")
 equal(incidental.teamCastleSupport,0,"one to four neutral KOs cannot farm ninety support points")
 equal(incidental.score,24,"low KO retains only its real combat points")
 equal(byId(coopScore,"assassin").ko,5,"five actual server KOs make defender active")
 local withDeposit=state("TEAM",nil,"ACTIVE")
 withDeposit.events={
  {type="FIELD_EGG_TAKEN",owner="assassin",eggId="FIELD_1"},
  {type="EGG_DEPOSIT",owner="assassin",quantity=1},
  {type="CASTLE_FALL",owner="mage",attacker="war"},
 }
 local courier=byId(Results.build(withDeposit,{}),"assassin")
 equal(courier.teamCastleSupport,1,"real home-delivery activates team supporter")
 equal(courier.deposited,1,"support uses server egg-delivery event")
 equal(courier.score,120+90,"courier team contribution is bounded and credited")
 local onlySteal=state("TEAM",nil,"ACTIVE")
 onlySteal.events={
  {type="EGG_TAKEN",thief="assassin",source="mage",quantity=1},
  {type="CASTLE_FALL",owner="mage",attacker="war"},
 }
 equal(byId(Results.build(onlySteal,{}),"assassin").teamCastleSupport,0,
  "unreturned stolen egg cannot unlock team siege credit")
 local laterDelivery=state("TEAM",nil,"ACTIVE")
 laterDelivery.events={
  {type="CASTLE_FALL",owner="mage",attacker="war"},
  {type="FIELD_EGG_TAKEN",owner="assassin",eggId="FIELD_3"},
  {type="EGG_DEPOSIT",owner="assassin",quantity=1},
 }
 equal(byId(Results.build(laterDelivery,{}),"assassin").teamCastleSupport,0,
  "later egg delivery never retroactively unlocks a past siege")
 local brSupport=state("BATTLE_ROYALE",nil,"ACTIVE")
 brSupport.events={{type="CASTLE_FALL",owner="mage",attacker="war"}}
 equal(byId(Results.build(brSupport,{}),"assassin").teamCastleSupport,0,"BR has no allied share")
 local ordered=state("TEAM",nil,"ACTIVE")
 ordered.events={
  {type="CASTLE_FALL",owner="assassin",attacker="mage"},
  {type="CASTLE_FALL",owner="builder",attacker="war"},
 }
 local afterDeath=Results.build(ordered,{assassin=5})
 equal(byId(afterDeath,"assassin").teamCastleSupport,0,"already eliminated teammate cannot receive later siege points")
 equal(byId(afterDeath,"mage").teamCastleSupport,0,"enemy final-blow owner never receives extra team assist")
 equal(byId(afterDeath,"war").teamCastleSupport,0,"owner did not receive own final blow twice")
 local supportCap=state("TEAM",nil,"ACTIVE")
 supportCap.events={}
 for _=1,12 do
  table.insert(supportCap.events,{type="CASTLE_FALL",owner="mage",attacker="war"})
 end
 local share=byId(Results.build(supportCap,{assassin=5}),"assassin")
 equal(share.teamCastleSupport,12,"raw team siege captures retained for diagnostics")
 equal(share.score,30+90*3,"team siege bonus capped after real participation")
 equal(share.objectiveScore,90*3,"team objective cap also applies to tie-break")
 -- 6 verified post-game specialties make different roles/rewards feel distinct,
 -- but do NOT alter match score, fake a server event, or imply global MVP.
 local function medal(events:{any},kos:number,mode:string?):any
  local m=state(mode or "TEAM",nil,"ACTIVE")
  m.events=events
  return byId(Results.build(m,{war=kos}),"war")
 end
 local nonContributor=medal({},0)
 equal(nonContributor.specialty,"参加","zero actions never earn fabricated specialist award")
 local trueCastle=medal({
  {type="CASTLE_FALL",owner="mage",attacker="war"}
 },0)
 equal(trueCastle.specialty,"攻城","real castle-final-blow specialty")
 local thiefMedal=medal({
  {type="EGG_TAKEN",thief="war",source="mage",quantity=3},
  {type="EGG_DEPOSIT",owner="war",quantity=3},
 },0)
 equal(thiefMedal.specialty,"卵奪取","returned stolen eggs beat credited deposits")
 local lostEggMedal=medal({
  {type="EGG_TAKEN",thief="war",source="mage",quantity=2},
  {type="EGG_DROP",owner="war",quantity=2},
 },0)
 equal(lostEggMedal.specialty,"参加","unreturned theft cannot earn raid medal")
 local fieldEvents={}
 for i=1,3 do
  table.insert(fieldEvents,{type="FIELD_EGG_TAKEN",owner="war",eggId="FIELD_"..i})
  table.insert(fieldEvents,{type="EGG_DEPOSIT",owner="war",quantity=1})
 end
 equal(medal(fieldEvents,0).specialty,"卵運搬","real field egg returns earn deliverer")
 equal(medal({},100).specialty,"無双","actual neutral KO score earns horde specialist")
 local allyMedal=medal({
  {type="CASTLE_FALL",owner="mage",attacker="assassin"}
 },5)
 equal(allyMedal.specialty,"共闘","real teammate castle capture earns team specialist")
 equal(medal({
  {type="CASTLE_FALL",owner="mage",attacker="assassin"}
 },0,"BATTLE_ROYALE").specialty,"参加","solo royale cannot earn fake teammate medal")
 local tieMedalEvents={}
 -- Five legal non-rare IDs keep KO600 and deposit600 tied; rare is checked below.
 for i=6,10 do
  table.insert(tieMedalEvents,{type="FIELD_EGG_TAKEN",owner="war",eggId="FIELD_"..i})
  table.insert(tieMedalEvents,{type="EGG_DEPOSIT",owner="war",quantity=1})
 end
 local tieMedal=medal(tieMedalEvents,100)
 equal(tieMedal.specialty,"卵運搬","equal score KO and eggs uses objective-first specialty")
 equal(tieMedal.score,600+600+200,"specialty never adds a hidden game score")
 local ties={mode="BATTLE_ROYALE",phase="FINISHED",winner=nil,
   ids={"Z","A"},castles={Z={alive=false,isAI=true},A={alive=false,isAI=true}},events={}}
 local sorted=Results.build(ties,{})
 equal(sorted.rows[1].id,"A","tie is deterministic")
 equal(sorted.rows[2].id,"Z","tie is deterministic")
 -- Current rare-field behavior retained by the exact existing +711 relay branch.
 -- Score-only fixture: both rare pickups are genuine legal FIELD IDs. This
 -- prefix models a valid TEAM relay, without claiming a whole-Rules/Host run.
 local rareRelayEvents={
  {type="FIELD_EGG_TAKEN",owner="a",eggId="FIELD_4"},
  {type="FIELD_EGG_TAKEN",owner="a",eggId="FIELD_5"},
  {type="EGG_RELAY",from="a",to="b",quantity=1,seq=1},
  {type="EGG_DEPOSIT",owner="b",quantity=1},
 }
 local function rareSnapshot(events:{any}):any
  return Results.build({
   mode="TEAM",phase="ACTIVE",winner=nil,ids={"a","b","enemy"},
   castles={a={alive=true,team="RED"},b={alive=true,team="RED"},enemy={alive=true,team="BLUE"}},
   events=events,
  },{})
 end
 local rareRelay=rareSnapshot(rareRelayEvents)
 local rareSender=byId(rareRelay,"a")
 local rareReceiver=byId(rareRelay,"b")
 equal(rareSender.rareEggs,2,"FIELD_4 and FIELD_5 remain credited to their actual picker")
 equal(rareSender.score,320,"picker keeps survival200 plus rare120 after relay")
 equal(rareSender.objectiveScore,120,"rare credit remains an objective after relay")
 equal(rareSender.specialty,"希少卵","picker retains actual rare specialty")
 equal(rareReceiver.rareEggs,0,"relay never creates or transfers rare pickup credit")
 equal(rareReceiver.score,320,"receiver gets survival200 plus genuine delivery120")
 equal(rareReceiver.objectiveScore,120,"receiver objective is ordinary delivery only")
 -- Defensive reducer input only: real Rules rejects duplicate FIELD receipts.
 -- Do not describe this suffix as reachable gameplay or physical egg conservation.
 local duplicateRareEvents=table.clone(rareRelayEvents)
 table.insert(duplicateRareEvents,{type="FIELD_EGG_TAKEN",owner="a",eggId="FIELD_4"})
 table.insert(duplicateRareEvents,{type="FIELD_EGG_TAKEN",owner="b",eggId="FIELD_5"})
 local rareDuplicates=rareSnapshot(duplicateRareEvents)
 equal(byId(rareDuplicates,"a").rareEggs,2,"same-owner duplicate rare ID never adds credit")
 equal(byId(rareDuplicates,"b").rareEggs,0,"cross-owner duplicate rare ID never adds credit")
 print("EGGRUMBLE_V3_MATCH_RESULTS_NATIVE_PASS assertions="..count)
 return true
end
