--!strict
-- Executes ORIGINAL #482 CastleMatchRules and candidate #515 FieldEggDropBounds.
-- This is pure native Luau: world spawning/collision/Studio has NOT been observed.
local Rules=loadOriginalRules()
local Bounds=loadCandidateBounds()
local checks=0
local function check(condition:any, message:string)
 assert(condition,message)
 checks+=1
end
local function validStock(state:any)
 return Rules.auditEggConservation(state).valid
end
local function roster(mode:string)
 if mode=="TEAM" then
  return {
   {id="red",team="RED",isAI=false},
   {id="blue",team="BLUE",isAI=true},
   {id="other",team="RED",isAI=true},
  }
 end
 return {{id="red"},{id="blue"},{id="other"}}
end
local function exercise(mode:string,quantity:number,fallX:number,fallZ:number)
 local m=Rules.new(mode,roster(mode),24)
 check(validStock(m),"initial egg stock must balance")
 Rules.start(m)
 check(m.phase=="ACTIVE","game must be active")
 check(m.castles.red.heldEggs==0,"carrier begins empty")
 Rules.takeEggs(m,"red",quantity,"blue")
 check(m.castles.red.heldEggs==quantity,"real stolen egg quantity")
 check(m.castles.blue.vaultEggs==3-quantity,"source vault debited exactly")
 check(validStock(m),"original vault and carrying stock remains conserved")
 -- Uses the same numeric arguments as the generated #515 host's ONLY new hook.
 local safe=Bounds.recover(mode,0,4,fallX,fallZ,
  if mode=="TEAM" then -885 else 620,260)
 check(safe.corrected,"out-of-bounds death must be corrected")
 check(safe.x>=safe.minX and safe.x<=safe.maxX,"drop X inside own arena")
 check(safe.z>=safe.minZ and safe.z<=safe.maxZ,"drop Z inside own arena")
 if mode=="TEAM" then
  check(safe.maxX<0,"TEAM egg cannot be placed in BR")
 else
  check(safe.minX>0,"BR egg cannot be placed in TEAM")
 end
 -- The ORIGINAL host then calls Rules.onCarrierEliminated (unchanged) and
 -- creates 1-3 physical egg parts at (safe.x+(i-2)*3,groundY+4,safe.z).
 local n,ids=Rules.onCarrierEliminated(m,"red")
 check(n==quantity and #ids==quantity,"real released egg token count")
 check(m.castles.red.heldEggs==0,"carrier empty after actual original death")
 check(m.fieldEggs==24+quantity,"field token stock increased once")
 check(validStock(m),"real original Rules conserved stock on death")
 for i,eggId in ipairs(ids) do
  check(m.fieldEggTokens[eggId]==true,"generated token is redeemable")
  local x=safe.x+(i-2)*3
  local z=safe.z
  check(x>=safe.minX and x<=safe.maxX,"all three physical positions inside own floor X")
  check(z>=safe.minZ and z<=safe.maxZ,"physical egg remains on same floor Z")
  local picked=Rules.takeFieldEgg(m,"red",eggId)
  check(picked==i,"actual original field-token pickup returns correct carried stock")
  check(m.fieldEggTokens[eggId]==nil,"one-time token removed atomically")
  check(validStock(m),"conservation after each pickup")
 end
 check(m.castles.red.heldEggs==quantity,"carrier successfully regains real eggs")
 local duplicate,duplicateIds=Rules.onCarrierEliminated(m,"red")
 check(duplicate==quantity and #duplicateIds==quantity,
  "a genuinely new death after repickup drops new stock")
 check(validStock(m),"second legitimate death conserves stock")
 local onceMore,onceMoreIds=Rules.onCarrierEliminated(m,"red")
 check(onceMore==0 and #onceMoreIds==0,"duplicate Died callback cannot duplicate drops")
 check(validStock(m),"duplicate callback keeps stock")
 for _,eggId in ipairs(duplicateIds) do
  Rules.takeFieldEgg(m,"red",eggId)
 end
 check(validStock(m),"all repicked tokens conserve stock")
 Rules.depositEggs(m,"red",quantity)
 check(m.castles.red.heldEggs==0,"original deposit removes carry")
 check(m.castles.red.vaultEggs==3+quantity,"original deposit stores all returned eggs")
 check(validStock(m),"post-return deposit conserves stock")
 check(m.phase=="ACTIVE" and m.winner==nil,"neither game mode forced a false winner")
end
for _,mode in ipairs({"TEAM","BATTLE_ROYALE"}) do
 for quantity=1,3 do
  -- Both arenas and both far negative/positive fall coordinates.
  local sign=if quantity%2==1 then 1 else -1
  exercise(mode,quantity,sign*20000,sign*9000)
 end
end
check(checks>=150,"insufficient ORIGINAL Rules + Bounds native checks")
print("EGGRUMBLE_FIELD_EGG_REAL_RULES_CROSS_DOMAIN_NATIVE_PASS checks="..tostring(checks))
