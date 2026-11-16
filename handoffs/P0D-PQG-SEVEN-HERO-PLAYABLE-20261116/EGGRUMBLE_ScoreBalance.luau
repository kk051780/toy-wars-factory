--!strict
-- EGGRUMBLE V3: independent pure native match score balance; no screen, UI, lobby or combat ownership.
-- CLAIM: SCORE_BALANCE only. Reuse original EGGRUMBLE_MatchResultService for result presentation.
-- KOs are real Humanoid deaths from SwarmCombat.kills, eggs/castles from the authoritative Rules.events.
-- Scores are deliberately capped PER category to prevent one grind from erasing the egg/castle objectives.
local Results={} -- no Roblox Services: native-Luau executable as real math

local SCORE={
 KO_CAP=1200, KO_RATE=6,
 EGG_STEAL_CAP=7, EGG_STEAL_RATE=170,
 EGG_DEPOSIT_CAP=8, EGG_DEPOSIT_RATE=120,
 CASTLE_CAP=3, CASTLE_RATE=440,
 SURVIVE=200, WIN=500,
}
Results.SCORE=SCORE

local function integer(value:any):number
 if type(value)~="number" or value~=value or value<0 or value==math.huge then return 0 end
 return math.floor(value)
end

local function points(row:any):number
 -- Losing a castle does not erase earlier player accomplishments.
 return math.min(SCORE.KO_CAP,row.ko*SCORE.KO_RATE)
  +math.min(SCORE.EGG_STEAL_CAP,row.stolen)*SCORE.EGG_STEAL_RATE
  +math.min(SCORE.EGG_DEPOSIT_CAP,row.deposited)*SCORE.EGG_DEPOSIT_RATE
  +math.min(SCORE.CASTLE_CAP,row.castlesDestroyed)*SCORE.CASTLE_RATE
  +(if row.alive then SCORE.SURVIVE else 0)
  +(if row.won then SCORE.WIN else 0)
end

function Results.build(state:any,kills:any):any
 assert(type(state)=="table" and type(state.castles)=="table" and type(state.events)=="table","invalid match")
 local rows={};local byId={}
 -- Fixed roster order gives deterministic tie breaks across servers and native tests.
 for _,id in ipairs(state.ids or {}) do
  local c=state.castles[id]
  if c then
   local row={id=tostring(id),team=c.team,alive=c.alive==true,
    isAI=c.isAI==true,ko=integer(kills and kills[id]),
    stolen=0,deposited=0,castlesDestroyed=0,won=false,score=0}
   rows[#rows+1]=row;byId[tostring(id)]=row
  end
 end
 for _,event in ipairs(state.events) do
  local kind=event.type
  if kind=="EGG_TAKEN" then
   local row=byId[tostring(event.thief)]
   if row then row.stolen+=integer(event.quantity) end
  elseif kind=="EGG_DEPOSIT" then
   local row=byId[tostring(event.owner)]
   if row then row.deposited+=integer(event.quantity) end
  elseif kind=="CASTLE_FALL" then
   local row=byId[tostring(event.attacker)]
   if row then row.castlesDestroyed+=1 end
  end
 end
 for _,row in ipairs(rows) do
  row.won=state.phase=="FINISHED" and state.winner~=nil and
   (if state.mode=="TEAM" then row.team==state.winner else row.id==tostring(state.winner))
  row.score=points(row)
 end
 table.sort(rows,function(a,b)
  if a.score~=b.score then return a.score>b.score end
  if a.ko~=b.ko then return a.ko>b.ko end
  return a.id<b.id
 end)
 return {mode=state.mode,phase=state.phase,winner=state.winner,rows=rows}
end


return Results
