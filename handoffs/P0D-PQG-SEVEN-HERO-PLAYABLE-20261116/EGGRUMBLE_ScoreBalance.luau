--!strict
-- EGGRUMBLE V3: independent pure native match score balance; no screen, UI, lobby or combat ownership.
-- CLAIM: SCORE_BALANCE only. Reuse original EGGRUMBLE_MatchResultService for result presentation.
-- KOs are real Humanoid deaths from SwarmCombat.kills, eggs/castles from the authoritative Rules.events.
-- Scores are deliberately capped PER category to prevent one grind from erasing the egg/castle objectives.
-- A stolen egg earns *raid* points only on a subsequent home deposit without a drop.
-- Field eggs are conservatively spent first; no invented per-egg provenance.
-- TEAM castle-support points need a verified match contribution, not idle presence.
-- Actual KO timing is not in source events; no per-siege KO assist is claimed.
local Results={} -- no Roblox Services: native-Luau executable as real math

local SCORE={
 KO_CAP=1200, KO_STAGE1=100, KO_STAGE2=1000, KO_STAGE3=10000, KO_STOP=30000,
 EGG_STEAL_CAP=7, EGG_STEAL_RATE=170,
 EGG_DEPOSIT_CAP=8, EGG_DEPOSIT_RATE=120,
 CASTLE_CAP=3, CASTLE_RATE=440,
 TEAM_CASTLE_SUPPORT_CAP=3, TEAM_CASTLE_SUPPORT_RATE=90,
 TEAM_SUPPORT_KO_MIN=5,
 SURVIVE=200, WIN=500,
}
Results.SCORE=SCORE

local function integer(value:any):number
 if type(value)~="number" or value~=value or value<0 or value==math.huge then return 0 end
 return math.floor(value)
end

-- Reward the first satisfying 100 KOs strongly, then keep real progress up to
-- 30,000 KOs (100 / 1,000 / 10,000 / 30,000 milestones) without displacing eggs.
-- Every KO milestone derives only from server-attributed actual Humanoid deaths.
local function koPoints(realKOs:number):number
 local k=math.min(SCORE.KO_STOP,realKOs)
 local earned=math.min(k,100)*6
  +math.max(0,math.min(k-100,900))*.3
  +math.max(0,math.min(k-1000,9000))*.03
  +math.max(0,k-10000)*.003
 return math.min(SCORE.KO_CAP,math.floor(earned+0.0000001))
end

-- Post-match style is a single truthful, server-derived specialty, never a
-- fabricated best-in-lobby badge or a gameplay advantage. Ranked by actual
-- capped contribution, with deterministic priority when equally valuable.
local function specialty(row:any):string
 local options={
  {name="攻城",value=math.min(SCORE.CASTLE_CAP,row.castlesDestroyed)*SCORE.CASTLE_RATE},
  {name="卵奪取",value=math.min(SCORE.EGG_STEAL_CAP,row.securedSteals)*SCORE.EGG_STEAL_RATE},
  {name="卵運搬",value=math.min(SCORE.EGG_DEPOSIT_CAP,row.deposited)*SCORE.EGG_DEPOSIT_RATE},
  {name="無双",value=koPoints(row.ko)},
  {name="共闘",value=math.min(SCORE.TEAM_CASTLE_SUPPORT_CAP,row.teamCastleSupport)*SCORE.TEAM_CASTLE_SUPPORT_RATE},
 }
 local best="参加";local earned=0
 for _,option in ipairs(options) do
  if option.value>earned then
   earned=option.value;best=option.name
  end
 end
 return best
end

local function points(row:any):number
 -- Losing a castle does not erase earlier player accomplishments.
 return koPoints(row.ko)
  +math.min(SCORE.EGG_STEAL_CAP,row.securedSteals)*SCORE.EGG_STEAL_RATE
  +math.min(SCORE.EGG_DEPOSIT_CAP,row.deposited)*SCORE.EGG_DEPOSIT_RATE
  +math.min(SCORE.CASTLE_CAP,row.castlesDestroyed)*SCORE.CASTLE_RATE
  +math.min(SCORE.TEAM_CASTLE_SUPPORT_CAP,row.teamCastleSupport)*SCORE.TEAM_CASTLE_SUPPORT_RATE
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
    stolen=0,securedSteals=0,pendingSteals=0,pendingField=0,
    deposited=0,castlesDestroyed=0,teamCastleSupport=0,won=false,score=0}
   rows[#rows+1]=row;byId[tostring(id)]=row
  end
 end
 local fallenSoFar={} -- replay source-true event order; future deaths are not retroactive
 for _,event in ipairs(state.events) do
  local kind=event.type
  if kind=="EGG_TAKEN" then
   local row=byId[tostring(event.thief)]
   -- Only an enemy castle raid counts; unique field-token pickups are not raids.
   if row and event.source~=nil and event.source~="FIELD" then
    local quantity=integer(event.quantity)
    row.stolen+=quantity
    row.pendingSteals+=quantity
   end
  elseif kind=="FIELD_EGG_TAKEN" then
   local row=byId[tostring(event.owner)]
   if row then row.pendingField+=1 end
  elseif kind=="EGG_DEPOSIT" then
   local row=byId[tostring(event.owner)]
   if row then
    local quantity=integer(event.quantity)
    row.deposited+=quantity
    -- Conservative attribution: deposit field eggs first. Without per-egg
    -- provenance, never award more completed raids than could be proven from
    -- same-life server TAKE + DEPOSIT. A death/drop resets unsettled claims.
    local fieldUsed=math.min(row.pendingField,quantity)
    row.pendingField-=fieldUsed
    local secured=math.min(row.pendingSteals,quantity-fieldUsed)
    row.pendingSteals-=secured
    row.securedSteals+=secured
   end
  elseif kind=="EGG_DROP" then
   local row=byId[tostring(event.owner)]
   if row then row.pendingSteals=0;row.pendingField=0 end
  elseif kind=="CASTLE_FALL" then
   local row=byId[tostring(event.attacker)]
   if row then
    row.castlesDestroyed+=1
    -- TEAM cooperative credit requires a real match contribution, not AFK.
    -- KO is server-verified for the match (timing is not recorded); egg
    -- deposits and final blows have precise ordered server event evidence.
    -- No fabricated direct siege hits, heals or per-castle assists.
    if state.mode=="TEAM" and row.team~=nil then
     for _,ally in ipairs(rows) do
      local participated=ally.ko>=SCORE.TEAM_SUPPORT_KO_MIN or
       ally.deposited>0 or ally.securedSteals>0 or ally.castlesDestroyed>0
      if ally.id~=row.id and ally.team==row.team and
       not fallenSoFar[ally.id] and participated then
       ally.teamCastleSupport+=1
      end
     end
    end
   end
   local fallen=byId[tostring(event.owner)]
   if fallen then fallen.pendingSteals=0;fallen.pendingField=0 end
   fallenSoFar[tostring(event.owner)]=true
  end
 end
 for _,row in ipairs(rows) do
  row.won=state.phase=="FINISHED" and state.winner~=nil and
   (if state.mode=="TEAM" then row.team==state.winner else row.id==tostring(state.winner))
  row.score=points(row)
  row.specialty=specialty(row)
  -- Same total score: reward actual egg/castle objectives BEFORE raw KO volume.
  -- The value is derived exclusively from original server-authoritative events.
  row.objectiveScore=
   math.min(SCORE.EGG_STEAL_CAP,row.securedSteals)*SCORE.EGG_STEAL_RATE
   +math.min(SCORE.EGG_DEPOSIT_CAP,row.deposited)*SCORE.EGG_DEPOSIT_RATE
   +math.min(SCORE.CASTLE_CAP,row.castlesDestroyed)*SCORE.CASTLE_RATE
   +math.min(SCORE.TEAM_CASTLE_SUPPORT_CAP,row.teamCastleSupport)*SCORE.TEAM_CASTLE_SUPPORT_RATE
 end
 table.sort(rows,function(a,b)
  if a.score~=b.score then return a.score>b.score end
  if a.objectiveScore~=b.objectiveScore then return a.objectiveScore>b.objectiveScore end
  if a.ko~=b.ko then return a.ko>b.ko end
  return a.id<b.id
 end)
 return {mode=state.mode,phase=state.phase,winner=state.winner,rows=rows}
end


return Results
