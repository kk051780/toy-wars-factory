--!strict
-- EGGRUMBLE V3 AI world navigation. Source-only Studio preview, not commercial nav QA.
-- Roblox PathfindingService does real route computation; asynchronous bounded requests
-- avoid 15 bots recalculating expensive city-length routes at the same instant.
local PathfindingService=game:GetService("PathfindingService")
local RunService=game:GetService("RunService")
local Router={}
local MAX_COMPUTES_IN_FLIGHT=2
local RECOMPUTE_SECONDS=2.8
local WAYPOINT_RADIUS=4.2
local GOAL_CHANGE_DISTANCE=12
local PATH_MAX_DISTANCE=2600
local PATH_TRAVEL_SPEED=30
local CRAWL_RETRY_DELAY=1.25
local states:{[string]:any}={}
local inFlight=0

local function planar(a:Vector3,b:Vector3):Vector3
 return Vector3.new(b.X-a.X,0,b.Z-a.Z)
end
local function raycastParams(actors:Instance):RaycastParams
 local params=RaycastParams.new()
 params.FilterType=Enum.RaycastFilterType.Exclude
 params.FilterDescendantsInstances={actors}
 params.RespectCanCollide=true
 return params
end
local function surfaceAt(pos:Vector3,actors:Instance):Vector3
 -- Use the collidable mesh to estimate the foot position of the anchored preview model.
 -- Start near the actor foot, not above a roof: castle ceilings are not walking ground.
 local result=workspace:Raycast(pos+Vector3.new(0,1,0),Vector3.new(0,-70,0),raycastParams(actors))
 if result then return Vector3.new(pos.X,result.Position.Y+2.0,pos.Z) end
 return pos
end
local function routeClear(from:Vector3,to:Vector3,actors:Instance):boolean
 local diff=planar(from,to)
 if diff.Magnitude<.01 then return true end
 local p=raycastParams(actors)
 local at=from+Vector3.new(0,1.2,0)
 local ray=workspace:Raycast(at,diff.Unit*math.min(8,diff.Magnitude),p)
 return ray==nil
end
local function resetPath(state:any)
 if state.blockedConn then
  state.blockedConn:Disconnect()
  state.blockedConn=nil
 end
 if state.path then state.path:Destroy();state.path=nil end
 state.waypoints=nil
 state.index=1
end
local function maybeCompute(id:string,model:Model,at:Vector3,goal:Vector3,state:any,actors:Instance)
 local now=os.clock()
 if state.inFlight or inFlight>=MAX_COMPUTES_IN_FLIGHT or now<state.retryAt then return end
 if planar(at,goal).Magnitude>PATH_MAX_DISTANCE then
  -- Map-level route should be split at sector/bridge waypoints, not a >3000 stud call.
  state.retryAt=now+RECOMPUTE_SECONDS;return
 end
 inFlight+=1;state.inFlight=true;state.retryAt=now+RECOMPUTE_SECONDS
 local expectedTarget=goal
 task.spawn(function()
  local path=PathfindingService:CreatePath({
   AgentRadius=2,AgentHeight=5,AgentCanJump=false,
   WaypointSpacing=8,Costs={Water=15},
  })
  local ok=pcall(function()
   path:ComputeAsync(surfaceAt(at,actors),surfaceAt(expectedTarget,actors))
  end)
  inFlight=math.max(0,inFlight-1)
  if states[id]~=state or not model.Parent then
   path:Destroy();return
  end
  state.inFlight=false
  if ok and path.Status==Enum.PathStatus.Success then
   resetPath(state)
   state.path=path
   state.waypoints=path:GetWaypoints()
   state.index=1
   state.goal=expectedTarget
   state.lastRepath=os.clock()
   state.blocked=false
   state.blockedConn=path.Blocked:Connect(function(blockedAt)
    if blockedAt>=state.index then
     state.blocked=true
     state.retryAt=math.min(state.retryAt,os.clock()+CRAWL_RETRY_DELAY)
    end
   end)
  else
   path:Destroy()
   state.failed=(state.failed or 0)+1
   state.retryAt=os.clock()+RECOMPUTE_SECONDS
  end
 end)
end
local function advanceState(state:any,here:Vector3)
 local points=state.waypoints
 if not points then return end
 while state.index<=#points and planar(here,points[state.index].Position).Magnitude<WAYPOINT_RADIUS do
  state.index+=1
 end
 if state.index>#points then
  resetPath(state)
 end
end
function Router.navigate(id:string,model:Model,goal:Vector3,dt:number,actors:Instance):number
 assert(RunService:IsStudio(),"Preview navigation cannot run in public")
 if not model.Parent or not model.PrimaryPart then return math.huge end
 local here=model:GetPivot().Position
 local remain=planar(here,goal).Magnitude
 if remain<=1.2 then return remain end
 local state=states[id]
 if not state then
  state={retryAt=0,index=1,inFlight=false,blocked=false,goal=nil,lastPos=here,lastProgressAt=os.clock()}
  states[id]=state
 end
 advanceState(state,here)
 local changed=state.goal==nil or planar(state.goal,goal).Magnitude>GOAL_CHANGE_DISTANCE
 if changed or state.blocked or not state.waypoints then
  if changed and not state.inFlight then resetPath(state);state.goal=goal end
  maybeCompute(id,model,here,goal,state,actors)
 end
 local destination=goal
 if state.waypoints and state.index<=#state.waypoints then
  destination=state.waypoints[state.index].Position
 end
 local delta=planar(here,destination)
 if delta.Magnitude<=.05 then return remain end
 local direction=delta.Unit
 local step=math.min(PATH_TRAVEL_SPEED*math.clamp(dt,.05,.3),delta.Magnitude)
 -- A failed path or a stale waypoint MUST NOT enable wall phasing.
 if not routeClear(here,here+direction*step,actors) then
  state.blocked=true
  -- Remain in place until asynchronous PathfindingService provides valid route.
  return remain
 end
 local next=here+direction*step
 local grounded=surfaceAt(next,actors)
 -- Preview skeleton parts are anchored. Follow the navmesh path but avoid fake flight.
 local smoothed=Vector3.new(next.X,math.clamp(grounded.Y,here.Y-2,here.Y+2),next.Z)
 model:PivotTo(CFrame.lookAt(smoothed,smoothed+direction))
 if planar(state.lastPos,smoothed).Magnitude>=2.5 then
  state.lastPos=smoothed;state.lastProgressAt=os.clock()
 elseif os.clock()-state.lastProgressAt>2.8 then
  state.blocked=true;state.retryAt=math.min(state.retryAt,os.clock()+CRAWL_RETRY_DELAY)
  state.lastProgressAt=os.clock()
 end
 return remain
end
function Router.clear(id:string)
 local state=states[id]
 if not state then return end
 resetPath(state);states[id]=nil
end
function Router.close()
 for id,_ in pairs(states) do Router.clear(id) end
end
return Router
