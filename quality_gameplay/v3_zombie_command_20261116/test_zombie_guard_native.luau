--!strict
-- Non-overlap GQ582 guard-perimeter regression: real original author Policy Luau.
-- Castle-defense orders may not be stalled by roadside attackers or chase beyond base.
local P = require("./EGGRUMBLE_ZombieOrderPolicy")
assert(P.GUARD_LEASH_STUDS==12)
local function target(x:number,z:number, id:string):any
 return {id=id,kind="ENEMY_PLAYER",x=x,z=z,active=true,
         matchToken="TEAM:castle",friendly=false}
end
local function snap(t:any):any
 return {matchToken="TEAM:castle",ownerId="91",phase="ACTIVE",ownerAlive=true,
 ownerPosition={x=0,z=0},guardPoint={x=0,z=0},targets={t},
 visible=function() return true end}
end
local function only(actions:any,kind:string):any
 assert(#actions==1, "expected one squad action")
 assert(actions[1].kind==kind, "unexpected command "..actions[1].kind)
 return actions[1]
end
local state=P.new("TEAM:castle","91",0)
assert(P.enlist(state,"z",0,{x=39,z=0}))
assert(P.issue(state,"GUARD",nil))
-- 1: Roadside minion must RETURN even with touching enemy (old logic ATTACK).
local a=only(P.step(state,0,snap(target(40,0,"road"))),"MOVE")
assert(a.x==0 and a.z==0)
-- 2: no attacks by a defender who drifted out of leash.
a=only(P.step(state,0.5,snap(target(39,0,"road"))),"MOVE")
assert(a.x==0 and a.z==0)
-- 3: minion inside ring, adversary outside ring is ignored, even at melee reach.
assert(P.locate(state,"z",{x=11,z=0}))
a=only(P.step(state,1,snap(target(14,0,"far"))),"MOVE")
assert(a.x==0 and a.z==0)
-- 4: enemy at exact defense ring edge is attackable from inside (no false dead-zone).
a=only(P.step(state,2,snap(target(12,0,"edge"))),"ATTACK")
assert(a.targetId=="edge")
-- 5: outside player close to castle defender still cannot be attacked.
a=only(P.step(state,4,snap(target(13,0,"out"))),"MOVE")
assert(a.x==0)
-- 6: while inside ring, close valid enemy remains attackable.
assert(P.locate(state,"z",{x=0,z=0}))
a=only(P.step(state,5.6,snap(target(4,0,"inside"))),"ATTACK")
assert(a.targetId=="inside")
-- 7: without castle anchor, current owner is a strict safe fallback.
local missing=snap(target(50,0,"remote"))
missing.guardPoint=nil
assert(P.locate(state,"z",{x=40,z=0}))
a=only(P.step(state,7,missing),"MOVE")
assert(a.x==0 and a.z==0)
-- 8: FOLLOW order is not made GUARD-only; chase distant target remains possible.
assert(P.issue(state,"FOLLOW",nil))
a=only(P.step(state,8,snap(target(46,0,"follow"))),"MOVE")
assert(a.x==46)
-- 9: FOCUS can still lock its intended target while outside guard perimeter.
assert(P.issue(state,"FOCUS","chosen"))
local f=snap(target(43,0,"chosen"))
a=only(P.step(state,9,f),"ATTACK")
assert(a.targetId=="chosen")
-- 10: wrong match token is still terminal; no harmful afterlife.
local wrong=snap(target(43,0,"chosen"))
wrong.matchToken="BR:stale"
assert(#P.step(state,10,wrong)==0 and not state.active)
-- 11: no orders after retirement
assert(not P.issue(state,"GUARD",nil))
-- 12: no fake fourth servant; cap unchanged.
local cap=P.new("TEAM:castle","91",0)
for i=1,3 do assert(P.enlist(cap,"servant"..i,0,{x=0,z=0})) end
assert(not P.enlist(cap,"servant4",0,{x=0,z=0}))
print("GQ_ZOMBIE_GUARD_CASTLE_LEASH_NATIVE_12_CASES_PASS")
