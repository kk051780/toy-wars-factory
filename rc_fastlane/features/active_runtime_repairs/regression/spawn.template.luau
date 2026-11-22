
local function engine()
 local events={}
 local function deferredSignal()
  local listeners={};local event={}
  function event:Connect(fn) table.insert(listeners,fn);return {Disconnect=function()end} end
  function event:Queue(...)
   local args=table.pack(...)
   for _,fn in ipairs(listeners) do table.insert(events,function()fn(table.unpack(args,1,args.n))end) end
  end
  function event:count()return #listeners end
  return event
 end
 local jobs={}
 local task={spawn=function(fn,...)local args=table.pack(...);table.insert(jobs,function()fn(table.unpack(args,1,args.n))end)end}
 local Players={}
 local roles,invulnUntil={},{}
 local effects={}
 local cleanup={}
 local function record(p,kind)
  local state=effects[p]
  if state then state[kind]=false end
  table.insert(cleanup,{player=p,kind=kind})
 end
 local function stopWind(p)record(p,"wind")end
 local function restoreSlow(p)record(p,"slow")end
 local function dropEgg(p)record(p,"egg")end
 local function clearEarnedPowerVisual(p)record(p,"power")end
 local function cleanupScout(p)record(p,"scout")end
 local Config={RoleHealth={RAIDER=100,GUARDIAN=130},RoleWalkSpeed={RAIDER=18,GUARDIAN=15},RespawnInvulnerability=2.5}
 local Vector3={new=function(x,y,z)return {X=x,Y=y,Z=z}end}
 local spawn={}
 setmetatable(spawn,{__add=function(a,b)return {X=a.X+b.X,Y=a.Y+b.Y,Z=a.Z+b.Z}end})
 spawn.X=10;spawn.Y=20;spawn.Z=30
 local map={teams={RED={spawn=spawn},BLUE={spawn=spawn}}}
 local now=100
 local function serverNow()return now end
 local function getTeamName(p)return p.side end
 local function character(label,waitAt)
  local c={Name=label}
  local root={ClassName="BasePart",CFrame=false}
  function root:IsA(class)return self.ClassName==class end
  local hum={ClassName="Humanoid",Health=9,MaxHealth=31,WalkSpeed=5,Died=deferredSignal()}
  function hum:IsA(class)return self.ClassName==class end
  c.root=root;c.hum=hum;c.waitAt=waitAt
  function c:WaitForChild(name,timeout)
   assert(timeout==10)
   if name==self.waitAt then coroutine.yield(name)end
   if name=="HumanoidRootPart" then return self.root else return self.hum end
  end
  return c
 end
 -- Production excerpts below are byte-preserved, no wrapper added inside them.

--@@SPAWN@@--
 local function bind(player)
--@@CHARACTER_ADDED@@--
 end
 local e={Players=Players,roles=roles,effects=effects,invuln=invulnUntil,cleanup=cleanup,character=character,spawn=assignSpawn,bind=bind}
 function e:newPlayer(uid)
  local p={UserId=uid,Parent=Players,side="RED",CharacterAdded=deferredSignal()}
  roles[p]="RAIDER";effects[p]={wind=true,slow=true,egg=true,power=true,scout=true}
  return p
 end
 function e:drainEvents()local list=events;events={};for _,fn in ipairs(list)do fn()end end
 function e:drainJobs()local list=jobs;jobs={};for _,fn in ipairs(list)do fn()end end
 function e:counts()return #events,#jobs end
 return e
end
local passed,failed=0,0
local function eq(a,b)assert(a==b,"expected "..tostring(b)..", got "..tostring(a))end
local function test(name,fn)local ok,err=pcall(fn);if ok then passed+=1;print("PASS\t"..name)else failed+=1;print("FAIL\t"..name.."\t"..tostring(err))end end
local function status(e,p)assert(e.effects[p].egg and e.effects[p].wind and e.effects[p].slow and e.effects[p].power and e.effects[p].scout,"new player effects changed")end
test("deferred_death_after_replacement_does_not_consume_new_effects",function()
 local e=engine();local p=e:newPlayer(10);local a=e.character("a");p.Character=a;e.spawn(p,a)
 a.hum.Health=0;a.hum.Died:Queue()
 local b=e.character("b");p.Character=b;e.spawn(p,b);e.effects[p]={egg=true,wind=true,slow=true,power=true,scout=true}
 e:drainEvents();status(e,p);eq(e.invuln[p],102.5)
end)
test("deferred_current_death_still_cleans",function()
 local e=engine();local p=e:newPlayer(10);local a=e.character("a");p.Character=a;e.spawn(p,a)
 a.hum.Health=0;a.hum.Died:Queue();e:drainEvents();eq(e.effects[p].egg,false);eq(e.effects[p].slow,false);eq(e.invuln[p],0)
end)
test("same_user_new_player_isolated",function()
 local e=engine();local p=e:newPlayer(10);local a=e.character("a");p.Character=a;e.spawn(p,a);a.hum.Health=0;a.hum.Died:Queue()
 e.roles[p]=nil;p.Parent=nil;e.invuln[p]=nil;e.effects[p]=nil
 local q=e:newPlayer(10);q.Character=e.character("q");e.spawn(q,q.Character);e.effects[q]={egg=true,wind=true,slow=true,power=true,scout=true}
 e:drainEvents();status(e,q);eq(e.invuln[p],nil);eq(e.invuln[q],102.5)
end)
test("removed_but_parent_not_updated_is_not_enrolled",function()
 local e=engine();local p=e:newPlayer(10);local a=e.character("a");p.Character=a;e.spawn(p,a);a.hum.Health=0;a.hum.Died:Queue()
 e.roles[p]=nil;e.invuln[p]=nil;e:drainEvents();eq(e.invuln[p],nil)
end)
test("queued_character_added_is_discarded_after_replacement",function()
 local e=engine();local p=e:newPlayer(10);e.bind(p);local a=e.character("a");p.Character=a;p.CharacterAdded:Queue(a)
 p.Character=e.character("b");e:drainEvents();status(e,p);local _,jobs=e:counts();eq(jobs,0)
end)
test("queued_spawn_cannot_outlive_character_added",function()
 local e=engine();local p=e:newPlayer(10);e.bind(p);local a=e.character("a");p.Character=a;p.CharacterAdded:Queue(a);e:drainEvents()
 local b=e.character("b");p.Character=b;e.invuln[p]=222;e:drainJobs();eq(a.hum.Health,9);eq(a.root.CFrame,false);eq(e.invuln[p],222)
end)
test("current_added_and_queued_spawn_remain_operational",function()
 local e=engine();local p=e:newPlayer(10);e.bind(p);local a=e.character("a");p.Character=a;p.CharacterAdded:Queue(a);e:drainEvents();e:drainJobs()
 eq(a.hum.Health,100);eq(a.hum.WalkSpeed,18);eq(a.root.CFrame.Y,22);eq(a.hum.Died:count(),1)
end)
for _,waitAt in ipairs({"HumanoidRootPart","Humanoid"})do
 test("wait_replacement_"..waitAt,function()
  local e=engine();local p=e:newPlayer(10);local a=e.character("a",waitAt);p.Character=a
  local co=coroutine.create(function()e.spawn(p,a)end);local ok,token=coroutine.resume(co);assert(ok);eq(token,waitAt)
  p.Character=e.character("b");local resumed,err=coroutine.resume(co);assert(resumed,err);eq(coroutine.status(co),"dead");eq(a.hum.Health,9);eq(a.hum.Died:count(),0);eq(e.invuln[p],nil)
 end)
end
test("role_change_during_wait_uses_current_enrolled_role",function()
 local e=engine();local p=e:newPlayer(10);local a=e.character("a","Humanoid");p.Character=a
 local co=coroutine.create(function()e.spawn(p,a)end);assert(coroutine.resume(co));e.roles[p]="GUARDIAN";assert(coroutine.resume(co));eq(a.hum.Health,130);eq(a.hum.WalkSpeed,15)
end)
test("missing_root_does_not_install_death_callback",function()
 local e=engine();local p=e:newPlayer(10);local a=e.character("a");p.Character=a;a.root=nil;e.spawn(p,a);eq(a.hum.Health,9);eq(a.hum.Died:count(),0)
end)
test("removed_character_added_no_cleanup_before_parent_change",function()
 local e=engine();local p=e:newPlayer(10);e.bind(p);p.Character=e.character("a");p.CharacterAdded:Queue(p.Character);e.roles[p]=nil;e:drainEvents();status(e,p);local _,jobs=e:counts();eq(jobs,0)
end)
print("TOTAL\t"..passed.."\t"..failed)
if failed>0 then error("INDEPENDENT_BOUNDARY_FAILURES="..failed)end
