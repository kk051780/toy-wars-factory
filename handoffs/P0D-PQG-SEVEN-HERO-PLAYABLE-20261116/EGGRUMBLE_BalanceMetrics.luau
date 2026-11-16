--!strict
-- EGGRUMBLE independent BALANCE lane. Pure Luau: no world mutation or monetization.
-- Authoritative gameplay must opt in only after real Studio/Android balance acceptance.
local B={}
B.TARGET_SECONDS=900
B.MIN_SECONDS=360
B.MAX_SECONDS=1200
B.OVERTIME_START=900
B.OVERTIME_DAMAGE_CAP=1.35
B.MAX_SWARM_PER_HERO=12
B.MIN_SWARM=24
B.MAX_SWARM=144
B.MAX_SIEGE_TOKEN_BONUS=0.10
B.MAX_CASTLE_BONUS=0.05
B.KO_REWARD_CAP_PER_MIN=120
B.TEAM_SWARM_TARGET_PER_HERO=8
B.BR_SWARM_TARGET_PER_HERO=6
B.BR_SIEGE_PRESSURE=1.08

local function integer(v:number,lo:number,hi:number):number
 assert(type(v)=="number" and v==v and v~=math.huge and v~=-math.huge,"finite number required")
 return math.clamp(math.floor(v),lo,hi)
end
function B.neutralBudget(activeHeroes:number,mode:string,quality:number):number
 assert(mode=="TEAM" or mode=="BATTLE_ROYALE","invalid mode")
 local heroes=integer(activeHeroes,1,32)
 local tier=integer(quality,1,3)
 local perHero=if mode=="TEAM" then B.TEAM_SWARM_TARGET_PER_HERO else B.BR_SWARM_TARGET_PER_HERO
 local budget=math.floor(heroes*perHero*(if tier==1 then 0.5 elseif tier==2 then 0.75 else 1))
 return integer(budget,B.MIN_SWARM,B.MAX_SWARM)
end
function B.siegeMultiplier(elapsed:number,mode:string,teamHasToken:boolean):number
 assert(mode=="TEAM" or mode=="BATTLE_ROYALE","invalid mode")
 local t=integer(elapsed,0,3600)
 local overtime=math.clamp((t-B.OVERTIME_START)/300,0,1)
 local pressure=1+0.25*overtime
 local modeFactor=if mode=="BATTLE_ROYALE" then B.BR_SIEGE_PRESSURE else 1
 local tokenFactor=if mode=="TEAM" and teamHasToken then 1+B.MAX_SIEGE_TOKEN_BONUS else 1
 return math.min(B.OVERTIME_DAMAGE_CAP,pressure*modeFactor*tokenFactor)
end
function B.score(kos:number,stolen:number,deposited:number,castleDamage:number,eliminations:number):any
 local k=integer(kos,0,1000000)
 local s=integer(stolen,0,100000)
 local d=integer(deposited,0,100000)
 local damage=integer(castleDamage,0,1000000)
 local e=integer(eliminations,0,32)
 -- KO rewards diminishing returns so horde-farmers cannot trivialize egg raids.
 local koPoints=math.min(k,300)*2+math.max(0,math.min(k-300,700))
 return {ko=koPoints,raid=s*75,delivery=d*100,siege=math.floor(damage/20),elimination=e*250,
 total=koPoints+s*75+d*100+math.floor(damage/20)+e*250}
end
function B.castleParity(baseHp:number,extraDefense:number):boolean
 local hp=integer(baseHp,1,100000)
 local bonus=integer(extraDefense,0,100000)
 return hp==1000 and bonus<=math.floor(hp*B.MAX_CASTLE_BONUS)
end
function B.evaluate(samples:{any}):any
 assert(type(samples)=="table" and #samples>=2,"at least two samples")
 local wins={TEAM=0,BATTLE_ROYALE=0}
 local durations={}
 local maxKo=0
 for _,match in ipairs(samples) do
  assert(match.mode=="TEAM" or match.mode=="BATTLE_ROYALE","invalid mode")
  local seconds=integer(match.seconds,0,3600)
  table.insert(durations,seconds)
  wins[match.mode]+=1
  maxKo=math.max(maxKo,integer(match.maxKo or 0,0,1000000))
 end
 table.sort(durations)
 local n=#durations
 local median=if n%2==1 then durations[(n+1)/2] else (durations[n/2]+durations[n/2+1])/2
 return {matches=n,medianSeconds=median,tooShort=median<B.MIN_SECONDS,
  tooLong=median>B.MAX_SECONDS,modeCoverage=wins.TEAM>0 and wins.BATTLE_ROYALE>0,
  maxKo=maxKo,releaseReady=median>=B.MIN_SECONDS and median<=B.MAX_SECONDS
   and wins.TEAM>0 and wins.BATTLE_ROYALE>0}
end
return B
