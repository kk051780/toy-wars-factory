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
 local corrupted=Results.build(state("TEAM","RED","FINISHED"),{war=-1,mage=0/0,assassin=math.huge})
 for _,row in ipairs(corrupted.rows) do equal(row.ko,0,"bad kill values rejected") end
 local ties={mode="BATTLE_ROYALE",phase="FINISHED",winner=nil,
   ids={"Z","A"},castles={Z={alive=false,isAI=true},A={alive=false,isAI=true}},events={}}
 local sorted=Results.build(ties,{})
 equal(sorted.rows[1].id,"A","tie is deterministic")
 equal(sorted.rows[2].id,"Z","tie is deterministic")
 print("EGGRUMBLE_V3_MATCH_RESULTS_NATIVE_PASS assertions="..count)
 return true
end
