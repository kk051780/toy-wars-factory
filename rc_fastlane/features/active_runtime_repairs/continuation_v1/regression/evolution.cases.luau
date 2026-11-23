local Store=modules.PersistentHatchStore
local Evolution=modules.EvolutionRules
local uid=8024680123
local receipt="Eindependent20261122_original"
local passed,failed=0,0
local function eq(actual,expected,detail)
 assert(actual==expected,(detail or "mismatch").." actual="..tostring(actual).." expected="..tostring(expected))
end
local function clone(value)
 if type(value)~="table" then return value end
 local out={}
 for key,item in pairs(value)do out[key]=clone(item)end
 return out
end
local function same(a,b)
 if type(a)~=type(b)then return false end
 if type(a)~="table"then return a==b end
 for k,v in pairs(a)do if not same(v,b[k])then return false end end
 for k in pairs(b)do if a[k]==nil then return false end end
 return true
end
local function fresh(item)
 local p=Store.blank()
 p.owned.forest_scout=2;p.owned.star_scout=1;p.equipped=item or "forest_scout"
 p.progress={level=50,xp=0,settledCount=0,claimedRoundIds={},mastery={}}
 for id in pairs(p.owned)do p.progress.mastery[id]={level=10,xp=0}end
 p.evolution=Evolution.newProfile(Store.policyUserId(uid));p.evolution.fragments=60
 assert(Store.validate(p),"FIXTURE_PROFILE_INVALID")
 return p
end
local function evolved(item)
 local input=fresh(item);local frozen=clone(input)
 local p,why=Store.evolveTransition(input,uid,receipt,"NONE")
 assert(p and why=="EVOLVED",tostring(why))
 assert(same(input,frozen),"transition mutated caller input")
 eq(p.revision,1);eq(p.evolution.fragments,58)
 return p
end
local function test(name,callback)
 local ok,detail=pcall(callback)
 if ok then passed+=1 else failed+=1 end
 print("CASE\t"..name.."\t"..(ok and "PASS" or "FAIL").."\t"..tostring(detail or "contract satisfied"))
end
for _,target in ipairs({"starter_scout","forest_scout","star_scout"})do
 for _,equipped in ipairs({"starter_scout","forest_scout","star_scout"})do
  if target==equipped then continue end
  test("replay_"..target.."_after_"..equipped.."_equip",function()
   local p=evolved(target)
   p=assert(Store.equipTransition(p,equipped))
   local frozen=clone(p)
   local replay,reason=Store.evolveTransition(p,uid,receipt,"NONE")
   assert(replay,"saved original receipt rejected: "..tostring(reason))
   eq(reason,"ALREADY_EVOLVED");assert(same(replay,frozen),"replay changed newest profile")
   assert(same(p,frozen),"replay mutated input")
   eq(replay.equipped,equipped);eq(replay.evolution.forms[target].stage,1)
   eq(replay.evolution.forms[equipped],nil);eq(replay.evolution.fragments,58)
  end)
 end
end
test("same_item_replay_never_charges_twice",function()
 local p=evolved("forest_scout")
 for _=1,4 do
  local n,why=Store.evolveTransition(p,uid,receipt,"NONE")
  assert(n and why=="ALREADY_EVOLVED");assert(same(n,p));p=n
 end
 eq(p.revision,1);eq(p.evolution.evoCount,1)
end)
test("old_receipt_after_later_evolution_and_equip",function()
 local p=evolved("forest_scout")
 p=assert(Store.evolveTransition(p,uid,"Eindependent_stage2_guard","GUARD"))
 p=assert(Store.evolveTransition(p,uid,"Eindependent_stage3_none","NONE"))
 p=assert(Store.equipTransition(p,"star_scout"))
 local n,why=Store.evolveTransition(p,uid,receipt,"NONE")
 assert(n,"old receipt rejected: "..tostring(why));assert(same(n,p))
 eq(n.evolution.forms.forest_scout.stage,3);eq(n.evolution.forms.forest_scout.branch,"GUARD")
 eq(n.evolution.fragments,43);eq(n.evolution.evoCount,3);eq(n.equipped,"star_scout")
end)
test("new_request_targets_current_atomic_equipment",function()
 local p=fresh("forest_scout");p=assert(Store.equipTransition(p,"star_scout"))
 local n,why=Store.evolveTransition(p,uid,receipt,"NONE")
 assert(n and why=="EVOLVED");eq(n.evolution.forms.star_scout.stage,1)
 eq(n.evolution.forms.forest_scout,nil);eq(n.evolution.evoReceipts[receipt].itemId,"star_scout")
end)
test("repeated_transform_same_input_is_pure",function()
 local p=fresh();local frozen=clone(p)
 local a=assert(Store.evolveTransition(p,uid,receipt,"NONE"))
 local b=assert(Store.evolveTransition(p,uid,receipt,"NONE"))
 assert(same(a,b));assert(same(p,frozen));a.owned.forest_scout=99
 eq(p.owned.forest_scout,2);eq(b.owned.forest_scout,2)
end)
test("same_id_different_branch_remains_conflict",function()
 local p=evolved("forest_scout");local frozen=clone(p)
 local n,why=Store.evolveTransition(p,uid,receipt,"GUARD")
 eq(n,nil);eq(why,"RECEIPT_CONFLICT");assert(same(p,frozen))
end)
test("same_id_different_action_remains_conflict",function()
 local p=evolved("forest_scout");p.evolution.evoReceipts[receipt].action="SWITCH"
 assert(Store.validate(p));local n,why=Store.evolveTransition(p,uid,receipt,"NONE")
 eq(n,nil);eq(why,"RECEIPT_CONFLICT")
end)
test("wrong_real_user_rejected",function()
 local p=evolved("forest_scout")
 local n,why=Store.evolveTransition(p,uid+1,receipt,"NONE")
 eq(n,nil);eq(why,"INVALID_EVOLUTION_PROFILE")
end)
test("malformed_receipt_item_fails_closed",function()
 local p=evolved("forest_scout");p.evolution.evoReceipts[receipt].itemId={bad=true}
 local n,why=Store.evolveTransition(p,uid,receipt,"NONE")
 eq(n,nil);eq(why,"CORRUPT_RECORD")
end)
test("replay_after_original_item_no_longer_owned",function()
 local p=evolved("forest_scout");p=assert(Store.equipTransition(p,"star_scout"))
 p.owned.forest_scout=0;assert(Store.validate(p))
 local n,why=Store.evolveTransition(p,uid,receipt,"NONE")
 assert(n,"persisted operation must still acknowledge: "..tostring(why));assert(same(n,p))
 eq(n.owned.forest_scout,0);eq(n.evolution.fragments,58)
end)
test("REVISION_V1_real_Store_lost_evolution_ack_equip_then_retry",function()
 local saved=fresh("forest_scout");local failAck=true;local count=0
 local backend={UpdateAsync=function(_,key,callback)
  eq(key,"U_"..uid);count+=1
  local original=clone(saved);local frozen=clone(original)
  local proposed=callback(original);assert(same(original,frozen))
  if proposed then saved=clone(proposed) end
  if failAck then failAck=false;error("FIXTURE_ACK_LOST_AFTER_DURABLE_COMMIT")end
  return proposed and clone(saved)or nil
 end}
 local ok,_,why=Store.evolve(backend,uid,receipt,"NONE")
 eq(ok,false);eq(why,"WRITE_UNCONFIRMED");eq(saved.evolution.fragments,58)
 assert(Store.equip(backend,uid,"star_scout",saved.revision))
 local finalOk,record,reason=Store.evolve(backend,uid,receipt,"NONE")
 assert(finalOk,"saved receipt not acknowledged: "..tostring(reason));assert(same(record,saved))
 eq(saved.equipped,"star_scout");eq(saved.evolution.evoCount,1);eq(saved.revision,2);eq(count,3)
end)
test("uncommitted_callback_discard_uses_new_atomic_equipment",function()
 local initial=fresh("forest_scout");local saved=clone(initial);local calls=0
 local backend={UpdateAsync=function(_,key,callback)
  eq(key,"U_"..uid)
  local abandoned=callback(clone(saved));calls+=1
  eq(abandoned.evolution.evoReceipts[receipt].itemId,"forest_scout")
  saved=assert(Store.equipTransition(saved,"star_scout"))
  local committed=callback(clone(saved));calls+=1
  saved=clone(committed);return clone(saved)
 end}
 local ok,record=Store.evolve(backend,uid,receipt,"NONE")
 assert(ok);eq(calls,2);eq(record.evolution.forms.forest_scout,nil)
 eq(record.evolution.forms.star_scout.stage,1);eq(record.evolution.fragments,58);eq(record.revision,2)
 assert(same(initial,fresh("forest_scout")))
end)
test("missing_backend_does_not_confirm",function()
 local ok,p,why=Store.evolve(nil,uid,receipt,"NONE")
 eq(ok,false);eq(p,nil);eq(why,"INVALID_PLAYER_STORE")
end)
test("new_request_preserves_earned_level_gate",function()
 local p=fresh("forest_scout");p.progress.level=1
 local n,why=Store.evolveTransition(p,uid,receipt,"NONE")
 eq(n,nil);eq(why,"GROWTH_REQUIREMENTS");eq(p.evolution.fragments,60);eq(p.revision,0)
end)
print("TOTAL\t"..passed.."\t"..failed)
if failed>0 then error("independent contracts failed: "..failed)end
