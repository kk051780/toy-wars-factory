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
    {type="FIELD_EGG_TAKEN",owner="war",eggId="FIELD_1"},
    {type="EGG_DEPOSIT",owner="war",quantity=2},
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
 for _=1,100 do
  table.insert(farm.events,{type="EGG_TAKEN",thief="war",quantity=3})
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

 local ties={mode="BATTLE_ROYALE",phase="FINISHED",winner=nil,
   ids={"Z","A"},castles={Z={alive=false,isAI=true},A={alive=false,isAI=true}},events={}}
 local sorted=Results.build(ties,{})
 equal(sorted.rows[1].id,"A","tie is deterministic")
 equal(sorted.rows[2].id,"Z","tie is deterministic")
 print("EGGRUMBLE_V3_MATCH_RESULTS_NATIVE_PASS assertions="..count)
 return true
end
