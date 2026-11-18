--!strict
-- GQ822 V2 COUNTER ACTUATOR (only DELEGATES to the original singleton Swarm API).
-- No new Humanoid:TakeDamage, no invented kills, score, Shop, Remote, or player HP write.
-- WARRIOR/NINJA PvP is applied only INSIDE original SevenRoleCombat owner, elsewhere.
local Players=game:GetService("Players")
local Counter={}
local allyBarriers=setmetatable({}, {__mode="k"})
local DAMAGE={
 MAGE={radius=14,amount=20},
 TRAPPER={radius=10,amount=18},
 BEAST={radius=11,amount=28},
 ZOMBIE={radius=7,amount=8},
}
local function activeHuman(session:any,p:Player):boolean
 if not session or not session.world or not session.world.Parent
  or not session.rules or session.rules.phase~="ACTIVE" or not p or p.Parent~=Players then return false end
 local char=p.Character
 local hum=char and char:FindFirstChildOfClass("Humanoid")
 local castle=session.rules.castles and session.rules.castles[tostring(p.UserId)]
 if not char or not hum or hum.Health<=0 or not castle or not castle.alive then return false end
 if session.isCurrentHuman and session.isCurrentHuman(p)~=true then return false end
 return p:GetAttribute("EGGRUMBLE_QueuedMode")==session.mode
end
local function rootOf(p:Player):BasePart?
 local char=p.Character
 local root=char and char:FindFirstChild("HumanoidRootPart")
 return if root and root:IsA("BasePart") then root else nil
end
local function clearLine(a:Vector3,b:Vector3,me:Model,enemy:Model):boolean
 local ray=RaycastParams.new()
 ray.FilterType=Enum.RaycastFilterType.Exclude
 ray.FilterDescendantsInstances={me,enemy}
 ray.RespectCanCollide=true
 return workspace:Raycast(a,b-a,ray)==nil
end
local function findRealNeutral(session:any,p:Player,range:number)
 local folder=session.world:FindFirstChild("NeutralHorde")
 local char=p.Character
 local root=rootOf(p)
 if not folder or not char or not root then return nil end
 local best=nil
 local bestDist=range
 for _,model in ipairs(folder:GetChildren()) do
  if model:IsA("Model") and model:GetAttribute("EGGRUMBLE_Neutral")==true
   and not model:GetAttribute("EGGRUMBLE_NeutralFriendlyOwnerId") then
   local mroot=model.PrimaryPart
   local hum=model:FindFirstChildOfClass("Humanoid")
   if mroot and hum and hum.Health>0 and hum.MaxHealth>0 then
    local delta=mroot.Position-root.Position
    local distance=delta.Magnitude
    if distance<bestDist and clearLine(root.Position+Vector3.new(0,1,0),
      mroot.Position+Vector3.new(0,1,0),char,model) then
     bestDist=distance;best={model=model,hum=hum,position=mroot.Position,distance=distance}
    end
   end
  end
 end
 return best
end
local function findEnemyPlayer(session:any,p:Player,attacker:any)
 local value=tonumber(tostring(attacker))
 if not value then return nil end
 local other=Players:GetPlayerByUserId(value)
 if not other or not activeHuman(session,other) or other==p then return nil end
 local home=session.rules.castles[tostring(p.UserId)]
 local theirs=session.rules.castles[tostring(other.UserId)]
 if session.mode=="TEAM" and home.team==theirs.team then return nil end
 local r1,r2=rootOf(p),rootOf(other)
 if not r1 or not r2 or (r2.Position-r1.Position).Magnitude>18 then return nil end
 if not clearLine(r1.Position+Vector3.new(0,1,0),r2.Position+Vector3.new(0,1,0),
  p.Character,other.Character) then return nil end
 local hum=other.Character:FindFirstChildOfClass("Humanoid")
 if not hum or hum.Health<=0 or hum.MaxHealth<=0 then return nil end
 return {serverVerified=true,alive=true,inRange=true,lineOfSight=true,
  id=tostring(other.UserId),class="PLAYER",hpFraction=hum.Health/hum.MaxHealth}
end
local function validate(p:Player,session:any,c:any):boolean
 return activeHuman(session,p) and c and c.serverCurrent==true
  and c.characterAlive==true and c.roleVerified==true
  and c.castleAlive==true and c.downed==false and c.eliminated==false
  and c.carryingEgg==false and c.shieldActive==false
end
function Counter.react(session:any,p:Player,role:string,policy:any,ledger:any,c:any,attackerId:any)
 if not validate(p,session,c) then return nil end
 if role=="WARRIOR" or role=="NINJA" then
  -- Deliberately do NOT "execute" a generic Swarm attacker or an arbitrary
  -- nearest neutral as though it were the first marked attacker. PvP is only
  -- accepted by the original SevenRoleCombat method with an exact UserId.
  return nil
 end
 local cfg=DAMAGE[role]
 local near=findRealNeutral(session,p,if cfg then cfg.radius else 10)
 local proof=if near then {serverVerified=true,alive=true,inRange=true,lineOfSight=true,
  id=tostring(near.model:GetAttribute("EGGRUMBLE_NeutralInstanceId") or near.model),
  class="MINION",hpFraction=near.hum.Health/near.hum.MaxHealth}
  else findEnemyPlayer(session,p,attackerId)
 if not proof then return nil end
 local command=policy.claimCounter(ledger,c,proof)
 if not command then return nil end
 if role=="BUILDER" then
  if command.effect~="ALLY_BARRIER_50PCT_3S" then return nil end
  local owner=session.rules.castles[tostring(p.UserId)]
  local root=rootOf(p)
  if not root then return nil end
  local protected=0
  if session.mode=="TEAM" then
   for _,other in ipairs(Players:GetPlayers()) do
    if other~=p and activeHuman(session,other) then
     local theirs=session.rules.castles[tostring(other.UserId)]
     local oroot=rootOf(other)
     if theirs and theirs.team==owner.team and oroot
      and (oroot.Position-root.Position).Magnitude<=command.radius then
      allyBarriers[other]={session=session,character=other.Character,
       expires=c.now+command.allyDuration,owner=p}
      protected+=1
     end
    end
   end
  end
  p:SetAttribute("EGGRUMBLE_AwakenCounterKind","ALLY_BARRIER_50PCT_3S")
  p:SetAttribute("EGGRUMBLE_AwakenCounterHits",protected)
  return command
 end
 if not cfg or not near or not session.swarm
  or type(session.swarm.damageFromPlayer)~="function" then return nil end
 -- Delegates damage/KO to the SAME original neutral Swarm singleton and its
 -- established wall/range/24-hit/ray budgets; doesn't apply any new HP write.
 local before=near.hum.Health
 local hits=session.swarm.damageFromPlayer(p,near.position,cfg.radius,cfg.amount,"CIRCLE")
 local actuallyHurt=(near.hum.Health<before)
 p:SetAttribute("EGGRUMBLE_AwakenCounterKind",command.effect)
 p:SetAttribute("EGGRUMBLE_AwakenCounterHits",hits)
 if hits>0 and actuallyHurt then
  -- Verified real neutral HP loss, not a client score claim.
  policy.rewardConfirmedCounter(ledger,c,{
   serverVerified=true,hitConfirmed=true,kind="NEUTRAL"})
 end
 return command
end
-- Existing original recipient's pre-damage gate calls this BEFORE its own
-- :TakeDamage. Legitimately protected allies lose half HP, not full immunity.
function Counter.allyMultiplier(session:any,victim:Player,now:number):number
 local rec=allyBarriers[victim]
 if not rec then return 1 end
 if rec.session~=session or rec.character~=victim.Character or rec.expires<=now
  or not activeHuman(session,victim) or not activeHuman(session,rec.owner) then
  allyBarriers[victim]=nil
  return 1
 end
 local their=session.rules.castles[tostring(victim.UserId)]
 local owner=session.rules.castles[tostring(rec.owner.UserId)]
 if session.mode~="TEAM" or not their or not owner or their.team~=owner.team then
  allyBarriers[victim]=nil;return 1
 end
 local r1,r2=rootOf(victim),rootOf(rec.owner)
 if not r1 or not r2 or (r1.Position-r2.Position).Magnitude>10 then
  allyBarriers[victim]=nil;return 1
 end
 return .5
end
return Counter
