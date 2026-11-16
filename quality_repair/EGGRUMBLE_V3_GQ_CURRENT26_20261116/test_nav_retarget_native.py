#!/usr/bin/env python3
"""Native Luau test of the actual asynchronous BotPathRouter path-adoption logic.
No Studio/Android execution or claims of live AI success.
"""
import argparse
import subprocess
import tempfile
from pathlib import Path

ROUTER=Path("handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116/EGGRUMBLE_BotPathRouter.luau")
PREFIX=r'''
local V={}
local vec={}
V.__index=function(self,k)
 if k=="Magnitude" then return math.sqrt(self.X^2+self.Y^2+self.Z^2) end
 return rawget(V,k)
end
function vec.new(x,y,z)return setmetatable({X=x,Y=y,Z=z},V) end
function V.__sub(a,b)return vec.new(a.X-b.X,a.Y-b.Y,a.Z-b.Z) end
local function planar(a,b)return vec.new(b.X-a.X,0,b.Z-a.Z) end
local inFlight=0
local MAX_COMPUTES_IN_FLIGHT=2
local RECOMPUTE_SECONDS=2.8
local GOAL_CHANGE_DISTANCE=12
local PATH_MAX_DISTANCE=2600
local CRAWL_RETRY_DELAY=1.25
local states={}
local delayed={}
local task={spawn=function(fn)table.insert(delayed,fn)end}
local function flush()
 local fn=table.remove(delayed,1)
 assert(fn~=nil,"expected pending path")
 fn()
end
local made={}
local Enum={PathStatus={Success="Success"}}
local failCreate=false
local failCompute=false
local PathfindingService={}
function PathfindingService:CreatePath(_options)
 if failCreate then failCreate=false;error("injected CreatePath failure") end
 local p={Status="Success",destroyed=false}
 function p:ComputeAsync(_at,goal)
  if failCompute then failCompute=false;error("injected ComputeAsync failure") end
  self.destination=goal
 end
 function p:GetWaypoints()return {{Position=self.destination}} end
 function p:Destroy()self.destroyed=true end
 p.Blocked={Connect=function(_,callback)
  return {Disconnect=function()end}
 end}
 table.insert(made,p)
 return p
end
local function surfaceAt(v,_actors)return v end
local function resetPath(s)
 if s.blockedConn then s.blockedConn:Disconnect();s.blockedConn=nil end
 if s.path then s.path:Destroy();s.path=nil end
 s.waypoints=nil;s.index=1
end
'''
SUFFIX=r'''
local actors={}
local model={Parent=true}
local a=vec.new(0,2,100)
local b=vec.new(500,2,100)
local initial=vec.new(0,2,0)
local s={retryAt=0,inFlight=false,index=1,goal=a,latestRequestedGoal=a}
states["bot"]=s
-- Simulate a path request to enemy vault, then the server acquires an egg and
-- immediately switches to home before ComputeAsync finishes.
maybeCompute("bot",model,initial,a,s,actors)
assert(#delayed==1 and inFlight==1 and s.inFlight==true)
s.latestRequestedGoal=b
s.goal=b
flush()
assert(inFlight==0 and not s.inFlight,"stale compute must release flight budget")
assert(made[1].destroyed==true,"stale path must be destroyed")
assert(s.path==nil and s.waypoints==nil,"stale path must not be installed")
assert(s.goal==b,"old result must not overwrite new objective")
assert(s.retryAt<=os.clock()+.05,"stale path must enable new compute without 2.8s wait")
-- Next request to the new home objective must succeed.
maybeCompute("bot",model,initial,b,s,actors)
assert(#delayed==1 and inFlight==1)
flush()
assert(inFlight==0 and not s.inFlight)
assert(s.path==made[2] and s.goal==b)
assert(#s.waypoints==1 and s.waypoints[1].Position==b)
-- Removal/replacement of a bot actor during async search also rejects result.
local s2={retryAt=0,inFlight=false,index=1,goal=a,latestRequestedGoal=a}
states["bot2"]=s2
maybeCompute("bot2",model,initial,a,s2,actors)
states["bot2"]=nil
flush()
assert(made[3].destroyed and inFlight==0,"orphan path must never install")
-- A stable unchanged target should be accepted on the first compute.
local s3={retryAt=0,inFlight=false,index=1,goal=a,latestRequestedGoal=a}
states["bot3"]=s3
maybeCompute("bot3",model,initial,a,s3,actors)
flush()
assert(s3.path==made[4] and s3.goal==a)
-- Broken path allocation must not strand the two global flight slots.
local s4={retryAt=0,inFlight=false,index=1,goal=a,latestRequestedGoal=a}
states["bot4"]=s4
failCreate=true
maybeCompute("bot4",model,initial,a,s4,actors)
flush()
assert(inFlight==0 and not s4.inFlight,"CreatePath failure leaked a compute slot")
assert(s4.failed==1 and s4.retryAt>os.clock(),"CreatePath failure lacked retry")
-- Recovery: next legitimate attempt still reaches the new target.
s4.retryAt=0
maybeCompute("bot4",model,initial,a,s4,actors)
flush()
assert(s4.path==made[5] and inFlight==0,"CreatePath failure prevented recovery")
-- ComputeAsync itself may fail; destroy that allocated path and release slot.
local s5={retryAt=0,inFlight=false,index=1,goal=a,latestRequestedGoal=a}
states["bot5"]=s5
failCompute=true
maybeCompute("bot5",model,initial,a,s5,actors)
flush()
assert(made[6].destroyed and inFlight==0 and not s5.inFlight)
assert(s5.failed==1 and s5.retryAt>os.clock())
print("GQ_NAV_RETARGET_NATIVE_PASS cases=7")
'''

def source_function(content: str) -> str:
    start=content.index("local function maybeCompute(")
    end=content.index("local function advanceState(",start)
    code=content[start:end]
    assert "state.latestRequestedGoal" in code
    assert "state.retryAt=os.clock()" in code
    return code

def run(luau: Path, actual: str) -> subprocess.CompletedProcess:
    with tempfile.TemporaryDirectory(prefix="gq-retarget-") as directory:
        file=Path(directory)/"retarget.spec.luau"
        file.write_text(PREFIX+actual+SUFFIX,encoding="utf-8")
        return subprocess.run([str(luau),str(file)],capture_output=True,text=True,check=False)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--luau",required=True,type=Path)
    args=p.parse_args()
    code=source_function(ROUTER.read_text(encoding="utf-8"))
    success=run(args.luau,code)
    assert success.returncode==0,(success.stdout,success.stderr)
    assert "GQ_NAV_RETARGET_NATIVE_PASS cases=7" in success.stdout
    # Removing stale-goal rejection must fail the queued-then-retargeted assertion.
    mutation=code.replace("or planar(state.latestRequestedGoal,expectedTarget).Magnitude>GOAL_CHANGE_DISTANCE",
                          "or false")
    assert mutation!=code
    fail=run(args.luau,mutation)
    assert fail.returncode!=0,(fail.stdout,fail.stderr)
    # A deliberately unguarded allocation now fails when CreatePath raises.
    bad_alloc=code.replace("local ok=pcall(function()","local ok=true\n  do",1)
    bad_alloc=bad_alloc.replace("  end)\n  inFlight=math.max(0,inFlight-1)",
                                "  end\n  inFlight=math.max(0,inFlight-1)",1)
    assert bad_alloc!=code
    fail=run(args.luau,bad_alloc)
    assert fail.returncode!=0,(fail.stdout,fail.stderr)
    print(success.stdout.strip())
    print("GQ_NAV_STALE_GOAL_NEGATIVE_PASS")
    print("GQ_CREATEPATH_EXCEPTION_MUTANT_NEGATIVE_PASS")

if __name__=="__main__":
    main()
