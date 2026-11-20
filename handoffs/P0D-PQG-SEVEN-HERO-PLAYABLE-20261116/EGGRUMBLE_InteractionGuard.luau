--!strict
-- EGGRUMBLE V3 Studio-only prompt server gate.
-- Every human ProximityPrompt action validates position, alive state, LOS and rate-limit.
-- Never treat client-side MaxActivationDistance or HoldDuration as authorization.
local Guard={}
local MAX_DISTANCE=16.0
local VERTICAL_LIMIT=10.0
local EXCESS_RADIUS=1.3
local COOLDOWN={
 ["攻城攻撃"]=1.6,
 ["敵の卵を奪取"]=0.55,
 ["卵を納入"]=0.8,
 ["卵を拾う"]=0.38,
 ["拾う"]=0.38,
 ["旗の装飾変更"]=0.5,
 ["参加する"]=1.0,
 ["装備する"]=0.5,
 ["職業選択"]=0.4,
}
local lastByPlayer:{[number]:{[string]:number}}={}
local function positionValid(actor:Player,part:BasePart):boolean
 if not actor.Parent or not part.Parent then return false end
 local char=actor.Character
 local humanoid=char and char:FindFirstChildOfClass("Humanoid")
 local root=char and char:FindFirstChild("HumanoidRootPart")::BasePart?
 if not char or not humanoid or humanoid.Health<=0 or not root then return false end
 local delta=part.Position-root.Position
 if math.abs(delta.Y)>VERTICAL_LIMIT+part.Size.Y*.5 then return false end
 -- Users can reach the edge of a large interactable; not arbitrary 100-stud walls.
 local near=part:GetClosestPointOnSurface(root.Position)
 if (near-root.Position).Magnitude>MAX_DISTANCE+EXCESS_RADIUS then return false end
 -- A roof, solid wall, or terrain between actor and target is an actual blocker.
 local params=RaycastParams.new()
 params.FilterType=Enum.RaycastFilterType.Exclude
 params.FilterDescendantsInstances={char}
 params.RespectCanCollide=true
 local origin=root.Position+Vector3.new(0,1.2,0)
 local target=part:GetClosestPointOnSurface(origin)
 local cast=target-origin
 if cast.Magnitude>.01 then
  local hit=workspace:Raycast(origin,cast,params)
  if hit and hit.Instance~=part then return false end
 end
 return true
end
function Guard.allow(actor:Player,part:BasePart,verb:string,key:string?):boolean
 if type(verb)~="string" or not COOLDOWN[verb] then return false end
 if not positionValid(actor,part) then return false end
 local clock=os.clock()
 local bucket=lastByPlayer[actor.UserId]
 if not bucket then bucket={};lastByPlayer[actor.UserId]=bucket end
 local id=verb..":"..(key or part.Name)
 local previous=bucket[id]
 if previous and clock-previous<COOLDOWN[verb] then return false end
 bucket[id]=clock
 return true
end
function Guard.clear(actor:Player)
 lastByPlayer[actor.UserId]=nil
end
return Guard
