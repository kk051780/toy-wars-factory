--!strict
local P = require("./EGGRUMBLE_ZombieOrderPolicy")
local function count(actions, kind)
    local n=0
    for _, a in ipairs(actions) do if a.kind == kind then n += 1 end end
    return n
end
local function snapshot()
    return {
        matchToken="TEAM:7", ownerId="17", phase="ACTIVE", ownerAlive=true,
        ownerPosition={x=0,z=0}, guardPoint={x=25,z=5},
        targets={
            {id="enemy",kind="ENEMY_PLAYER",x=3,z=0,active=true,
             matchToken="TEAM:7",friendly=false},
            {id="ally",kind="ENEMY_PLAYER",x=1,z=0,active=true,
             matchToken="TEAM:7",friendly=true},
            {id="old",kind="ENEMY_BOT",x=1,z=0,active=true,
             matchToken="TEAM:OLD",friendly=false}
        },
        visible=function() return true end
    }
end
local s=P.new("TEAM:7","17",0)
assert(P.enlist(s,"z1",0,{x=0,z=0}))
assert(P.enlist(s,"z2",0,{x=0,z=0}))
assert(P.enlist(s,"z3",0,{x=0,z=0}))
assert(not P.enlist(s,"z4",0,{x=0,z=0}))
assert(not P.enlist(s,"z1",0,{x=0,z=0}))
assert(s.count==3)
assert(not P.issue(s,"FOCUS",""))
assert(not P.issue(s,"INVALID","enemy"))
assert(P.issue(s,"FOCUS","enemy"))
assert(count(P.step(s,0,snapshot()),"ATTACK")==1)
assert(count(P.step(s,0.2,snapshot()),"ATTACK")==0)
assert(count(P.step(s,1.6,snapshot()),"ATTACK")==1)
local wall=snapshot()
wall.visible=function() return false end
assert(count(P.step(s,3.2,wall),"ATTACK")==0)
assert(P.issue(s,"GUARD",nil))
local guard=snapshot()
guard.targets={}
local moves=P.step(s,3.3,guard)
assert(count(moves,"MOVE")==3)
for _, action in ipairs(moves) do
    assert(action.x==25 and action.z==5)
end
local stale=snapshot()
stale.matchToken="TEAM:8"
assert(#P.step(s,4,stale)==0 and not s.active and s.count==0)
assert(not P.issue(s,"FOLLOW",nil))
local s2=P.new("BR:1","17",10)
assert(P.enlist(s2,"unit",10,{x=0,z=0}))
local br=snapshot()
br.matchToken="BR:1"
br.targets={}
assert(#P.step(s2,24,br)==0 and not s2.active)
local s3=P.new("TEAM:7","17",0)
assert(P.enlist(s3,"u",0,{x=0,z=0}))
local enemy=snapshot()
enemy.ownerAlive=false
assert(#P.step(s3,1,enemy)==0 and s3.count==0)
local s4=P.new("TEAM:7","17",0)
assert(P.enlist(s4,"u",0,{x=0,z=0}))
local invalid=snapshot()
invalid.targets={
    {id="friendly",kind="ENEMY_BOT",x=1,z=0,active=true,matchToken="TEAM:7",friendly=true},
    {id="other",kind="NEUTRAL",x=2,z=0,active=true,matchToken="BR:1",friendly=false}
}
assert(count(P.step(s4,0,invalid),"ATTACK")==0)
assert(count(P.step(s4,0,invalid),"MOVE")==1)
print("GQ_ZOMBIE_COMMAND_NATIVE_18_POLICY_CASES_PASS")
