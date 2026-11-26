--!strict
local M=require("./EGGRUMBLE_SkillMatchPolicy")
assert(M.MIN_PLAYERS==8 and M.MAX_PLAYERS==16)
local function ticket(id:number,rating:number,part:any,games:number,level:number):any
 return {userId=id,rating=rating,level=level,games=games,mode="TEAM",region="JP",
  queuedAtSeconds=100,partyKey=part,sessionId="s"..id,serverVerified=true,roundEligible=true}
end
local group={}
for i=1,16 do group[i]=ticket(i,1200+i*4,nil,20,40) end
local plan=M.propose(group,130,"TEAM","JP")
assert(plan.status=="MATCH_READY" and plan.size==16 and #plan.teamA==8 and #plan.teamB==8)
assert(plan.teamGapRatio<=0.1 and plan.requiresAuthoritativeQueueClaim and not plan.teleportAuthorizedHere)
local again=M.propose(group,130,"TEAM","JP")
for i,id in ipairs(plan.teamA) do assert(again.teamA[i]==id) end
local short={}
for i=1,8 do short[i]=ticket(i,1400+i,nil,20,50) end
local p=M.propose(short,130,"TEAM","JP")
assert(p.status=="MATCH_READY" and p.size==8 and #p.teamA==4 and #p.teamB==4)
short[1].partyKey="friends"
short[2].partyKey="friends"
p=M.propose(short,130,"TEAM","JP")
assert(p.status=="MATCH_READY")
local a={}
for _,id in ipairs(p.teamA) do a[id]=true end
assert(a[1]==a[2])
-- Sparse servers keep ordinary/AI existing game, never lock players for hours.
local sparse={}
for i=1,7 do sparse[i]=ticket(i,1300,nil,20,20) end
assert(M.propose(sparse,130,"TEAM","JP").status=="FALLBACK_NORMAL_LOBBY")
-- Newcomers cannot be force-merged with veteran cohort.
local mixed={}
for i=1,4 do mixed[#mixed+1]=ticket(i,1000,nil,0,3) end
for i=5,10 do mixed[#mixed+1]=ticket(i,1000,nil,200,100) end
assert(M.propose(mixed,130,"TEAM","JP").status=="WAIT_OR_NORMAL_LOBBY")
-- No 8-person fair rating bracket even when population exceeds min.
local extremes={}
for i=1,7 do extremes[#extremes+1]=ticket(i,450,nil,20,40) end
for i=8,14 do extremes[#extremes+1]=ticket(i,2250,nil,20,40) end
assert(M.propose(extremes,130,"TEAM","JP").status=="WAIT_OR_NORMAL_LOBBY")
local bad={}
for i=1,8 do bad[i]=ticket(i,1300,nil,20,30) end
bad[1].serverVerified=false
assert(M.propose(bad,130,"TEAM","JP").status=="FALLBACK_NORMAL_LOBBY")
bad[1].serverVerified=true;bad[2].userId=bad[1].userId
assert(M.propose(bad,130,"TEAM","JP").status=="FALLBACK_NORMAL_LOBBY")
assert(M.propose({},130,"TEAM","JP").status=="FALLBACK_NORMAL_LOBBY")
assert(M.propose(group,130,"HACK","JP").status=="REJECT_INVALID_INPUT")
assert(M.propose(group,math.huge,"TEAM","JP").status=="REJECT_INVALID_INPUT")
local royale={}
for i=1,8 do
 local t=ticket(i,1200+i*3,nil,20,40)
 t.mode="BR"
 royale[i]=t
end
local battleRoyale=M.propose(royale,130,"BR","JP")
assert(battleRoyale.status=="MATCH_READY" and battleRoyale.freeForAll
 and battleRoyale.teamAssignmentDisabled==true)
assert(plan.teamAssignmentDisabled==false and plan.freeForAll==false)
print("GQ802_SKILL_MATCH_NATIVE_8_16_PARTY_BALANCE_ANTI_DUP_PASS")
