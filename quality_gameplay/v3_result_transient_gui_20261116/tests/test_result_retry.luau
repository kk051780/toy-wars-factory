--!strict
-- Native Luau: exact owned ResultRetry policy, no fake Roblox runtime acceptance.
local R = require("../EGGRUMBLE_ResultRetry")
local checks=0
local function ok(value:boolean)
 assert(value)
 checks+=1
end
local function harness(initialAvailable:boolean)
 local state={current=true,available=initialAvailable,renders=0}
 local scheduled={}
 local function valid() return state.current end
 local function render()
  state.renders+=1
  return state.available
 end
 local function delay(sec:number,callback:()->())
  assert(sec==.25)
  table.insert(scheduled,callback)
 end
 local function nextTick()
  local cb=table.remove(scheduled,1)
  assert(cb~=nil)
  cb()
 end
 return state,scheduled,valid,render,delay,nextTick
end
do
 local s,q,v,f,delay=harness(true)
 ok(R.deliver(v,f,delay)==true)
 ok(s.renders==1 and #q==0)
end
do
 local s,q,v,f,delay,tick=harness(false)
 ok(R.deliver(v,f,delay)==false and s.renders==1 and #q==1)
 s.available=true
 tick()
 ok(s.renders==2 and #q==0)
end
do
 local s,q,v,f,delay,tick=harness(false)
 R.deliver(v,f,delay)
 s.current=false
 s.available=true
 tick()
 ok(s.renders==1 and #q==0)
end
do
 local s,q,v,f,delay,tick=harness(false)
 R.deliver(v,f,delay)
 for _=1,8 do tick() end
 ok(s.renders==9 and #q==0)
end
do
 local s,q,v,f,delay,tick=harness(false)
 R.deliver(v,f,delay)
 tick()
 tick()
 s.available=true
 tick()
 ok(s.renders==4 and #q==0)
end
do
 local s,q,v,f,delay,tick=harness(false)
 local failure=function() error("transient PlayerGui lookup error") end
 ok(R.deliver(v,failure,delay)==false and #q==1)
 tick()
 ok(#q==1)
end
do
 local s,q,v,f,delay,tick=harness(false)
 local invalid=function() error("session retired") end
 ok(R.deliver(invalid,f,delay)==false)
 ok(s.renders==0 and #q==0)
end
do
 local s,q,v,f,delay,tick=harness(false)
 s.current=false
 ok(R.deliver(v,f,delay)==false and #q==0 and s.renders==0)
end
do
 local a,qa,va,fa,da,ta=harness(false)
 local b,qb,vb,fb,db,tb=harness(true)
 R.deliver(va,fa,da)
 R.deliver(vb,fb,db)
 ok(a.renders==1 and b.renders==1 and #qa==1 and #qb==0)
 a.available=true
 ta()
 ok(a.renders==2 and #qa==0 and b.renders==1)
end
ok(R.MAX_RETRIES==8 and R.INTERVAL_SECONDS==.25)
print("GQ_RESULT_RETRY_NATIVE_PASS", checks)
