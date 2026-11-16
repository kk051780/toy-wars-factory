-- Native Luau behavioural assertions; appended to EXACT source by build_native_harness.py.
local function kinds(h:number, b:number)
 local r = {}
 for i=1,h do table.insert(r, "HUMAN") end
 for i=1,b do table.insert(r, "BOT") end
 return r
end
local function sample(h:number, b:number, n:number)
 local s={}
 local k=kinds(h,b)
 local human, bot = 0, 0
 local counts={}
 for i=1,n do
  local ix, kind = Fair.chooseIndex(s, "MATCH_A", k)
  assert(type(ix)=="number" and ix>=1 and ix<=#k, "valid in-bounds target index")
  assert(kind==k[ix], "kind must match original aligned target vector")
  counts[ix]=(counts[ix] or 0)+1
  if kind=="HUMAN" then human+=1 else bot+=1 end
 end
 return human,bot,counts,s
end
do
 local h,b,counts=sample(1,15,100)
 assert(h==40 and b==60,"solo human must get >=40% nearby spawn selections")
 assert(counts[1]==40,"solo count is real selections, not fabricated KOs")
 for i=2,16 do assert(counts[i]>=3 and counts[i]<=4,"bots get rotation") end
end
do
 local h,b,counts=sample(8,8,100)
 assert(h==50 and b==50,"normal human/bot parity")
 for i=1,16 do assert(counts[i]>=6 and counts[i]<=7,"no one player/AI starved") end
end
do
 local h,b=sample(16,0,100)
 assert(h==100 and b==0,"all humans receive encounters")
end
do
 local h,b=sample(1,1,100)
 assert(h==50 and b==50,"equal human/bot share stays equal")
end
do
 local s={}
 assert(select(1,Fair.chooseIndex(s,"E",kinds(0,16)))==nil,"bot-only cannot spawn")
 assert(select(1,Fair.chooseIndex(s,"E",{}))==nil,"empty cannot spawn")
 assert(select(1,Fair.chooseIndex(s,"E",{"HUMAN","WRONG"}))==nil,"unknown kind rejected")
 assert(select(1,Fair.chooseIndex(s,nil,{"HUMAN"}))==nil,"missing epoch rejected")
 assert(select(1,Fair.chooseIndex(nil,"E",{"HUMAN"}))==nil,"missing state rejected")
 assert(s.epoch==nil,"invalid calls must not create state")
end
do
 local s={}
 local a=kinds(1,15)
 assert(select(2,Fair.chooseIndex(s,"ROUND_1",a))=="HUMAN","first spawn near human")
 for _=1,7 do Fair.chooseIndex(s,"ROUND_1",a) end
 local ix,kind=Fair.chooseIndex(s,"ROUND_2",a)
 assert(ix==1 and kind=="HUMAN","new round resets quota and cursor")
 Fair.clear(s)
 assert(s.epoch==nil and s.credit==nil,"cleanup must release epoch")
end
print("NEUTRAL_ENCOUNTER_NATIVE: PASS solo 40/100, parity 50/100, 16 humans, bot rotation, invalid input and round reset")
