--!strict
-- #509 original author terminal death gate + #515 FIELD egg bounds + original
-- #482 castle Rules executed in ONE pinned native Luau VM. No mock Rules.
local Rules=loadOriginalRules()
local Bounds=loadCandidateBounds()
local n=0
local function check(v:any,label:string)
 assert(v,label)
 n+=1
end
local function roster(mode:string)
 if mode=="TEAM" then
  return {{id="red",team="RED",isAI=false},{id="blue",team="BLUE",isAI=true}}
 end
 return {{id="red"},{id="blue"},{id="green"}}
end
local function test(mode:string,count:number)
 local state=Rules.new(mode,roster(mode),24)
 Rules.start(state)
 check(Rules.auditEggConservation(state).valid,"initial real Rules conservation")
 local got=Rules.takeEggs(state,"red",count,"blue")
 check(got==count,"real Rules steal from opposing fortress")
 local first=state.eggSerial
 local landing=Bounds.recover(mode,0,4,300000,-300000,nil,nil)
 check(landing.corrected,"out-of-map position corrected")
 check(landing.x>=landing.minX and landing.x<=landing.maxX,"X own battlefield")
 check(landing.z>=landing.minZ and landing.z<=landing.maxZ,"Z own battlefield")
 -- Original host only instantiates physical parts when "dropped>0".
 local dropped,ids=Rules.onCarrierEliminated(state,"red")
 check(dropped==count and #ids==count,"active REAL Rules death creates count tokens")
 check(state.eggSerial==first+count,"first death's exact server serial count")
 check(Rules.auditEggConservation(state).valid,"real active death conserved")
 for i,token in ipairs(ids) do
  check(state.fieldEggTokens[token]==true,"live token exists")
  local x=landing.x+(i-2)*3
  check(x>=landing.minX-40 and x<=landing.maxX+40,"live physical X inside field")
  check(landing.z>=landing.minZ-40 and landing.z<=landing.maxZ+40,"live physical Z inside field")
  Rules.takeFieldEgg(state,"red",token)
  check(Rules.auditEggConservation(state).valid,"repickup conserved")
 end
 check(state.castles.red.heldEggs==count,"same carrier recovered physical token ledger")
 -- The original author's castle win may finish while a carrier still has eggs.
 for _=1,4 do Rules.damageCastle(state,"blue","red",250) end
 if mode=="BATTLE_ROYALE" then
  for _=1,4 do Rules.damageCastle(state,"green","red",250) end
 end
 check(state.phase=="FINISHED" and state.winner~=nil,"real original terminal win")
 local oldSerial=state.eggSerial
 local oldField=state.fieldEggs
 local oldEvents=#state.events
 local oldHeld=state.castles.red.heldEggs
 local after,afterIds=Rules.onCarrierEliminated(state,"red")
 check(after==0 and #afterIds==0,"#509 real terminal Rules forbids token mint")
 check(oldSerial==state.eggSerial,"late callback cannot increment serial")
 check(oldField==state.fieldEggs,"late callback cannot change field stock")
 check(oldEvents==#state.events,"late callback cannot emit egg event")
 check(oldHeld==state.castles.red.heldEggs,"late callback cannot destroy held stock")
 check(Rules.auditEggConservation(state).valid,"post-win egg stock remains conserved")
 local twice,twiceIds=Rules.onCarrierEliminated(state,"red")
 check(twice==0 and #twiceIds==0,"duplicate late callback is idempotent")
 check(Rules.auditEggConservation(state).valid,"terminal repeat stock conserved")
end
for _,mode in ipairs({"TEAM","BATTLE_ROYALE"}) do
 for count=1,3 do test(mode,count) end
end
check(n>=120,"undercoverage of integrated real Rules and bounded field")
print("EGGRUMBLE_GQ509_515_FEDERATED_REAL_RULES_NATIVE_PASS checks="..tostring(n))
