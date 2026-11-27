do
local names={"火種","霜弾","氷槍","雷針"}
local ids={"MAGE-001","MAGE-011","MAGE-012","MAGE-026"}
local flag="P0D_ENABLE_PRIVATE_MAGE_ELEMENTAL"
local health=96

local function selected(index)
 local stand=scenes:FindFirstChild("ROLE_MAGE")
 trigger(player,stand,"職業選択")
 for _=1,index do
  advanceTo(now+1.01)
  trigger(player,stand,"属性を装備")
 end
 check(player:GetAttribute("EGGRUMBLE_LobbyMageProjectileName")==names[index],"actual element prompt")
 local session=ready("MAGE_ELEMENT_"..index)
 check(session.mageProjectiles[player.UserId]==ids[index],"server snapshots equip choice")
 trigger(player,stand,"属性を装備")
 check(session.mageProjectiles[player.UserId]==ids[index],"queued/deployed element remains fixed")
 return session
end

local function secondNeutral(session,first)
 local horde=session.world:FindFirstChild("NeutralHorde")
 for _=1,25 do
  for _,model in ipairs(horde:GetChildren()) do
   local h=model:FindFirstChildOfClass("Humanoid")
   if model~=first and h and h.Health>0 then return model end
  end
  advanceTo(now+.2)
 end
 error("no second genuine Swarm neutral")
end

local function pose(session,origin,dist,defense,neutral)
 neutral=neutral or spawnCurrentNeutral(session)
 local hum=neutral:FindFirstChildOfClass("Humanoid")
 local aligned=origin+Vector3.new(dist,1,0)
 neutral:SetAttribute("EGGRUMBLE_NeutralSpeed",0)
 neutral:SetAttribute("EGGRUMBLE_NeutralSpecies",defense and "BABY_GOLEM" or "GOBLIN")
 hum.Health=health
 rootPart.CFrame=CFrame.new(origin,origin+Vector3.new(1,0,0))
 advanceTo(now+.39)
 neutral:PivotTo(CFrame.new(aligned))
 return neutral,hum,aligned
end

local function origin(session)
 return session.world:FindFirstChild("TacticalBattlefield").Position+Vector3.new(180,20,80)
end

local function fire()
 local session=selected(1)
 local naturalOrigin=origin(session)
 local neutral,hum=pose(session,naturalOrigin,5,false)
 local t=now
 local E=session.swarm.getRoleGrowthSnapshot(player).energy
 activate(player,"A")
 equal(session.swarm.getRoleGrowthSnapshot(player).energy,E-30,"fire cost E30 once")
 equal(hum.Health,health,"warning and projectile must travel")
 advanceTo(t+.37)
 check(hum.Health<health and hum.Health>health-34,"S0 now has most of hit, with burn reserve")
 check(neutral:FindFirstChild("EGGRUMBLE_Ember")~=nil,"actual neutral receives visible confirmed burn")
 return session,neutral,hum,t
end

function growthCases.element_fire()
 local session,neutral,hum,t=fire()
 local direct=hum.Health
 advanceTo(t+1.68)
 check(hum.Health<direct and hum.Health>=direct-8,"actual delayed damage is capped by one stat budget")
 local final=hum.Health
 advanceTo(t+2.12)
 equal(hum.Health,final,"expired burn cannot deal another hit")
 check(neutral:FindFirstChild("EGGRUMBLE_Ember")==nil,"S0 burn marker expires")
 equal(session.swarm.getTotal(),0,"no fabricated KO")
 return "actual fire projectile reserves some neutral damage for real timed burn"
end

function growthCases.element_fire_rollback()
 local _,neutral,hum,t=fire()
 local direct=hum.Health
 workspace:SetAttribute(flag,false)
 advanceTo(t+1.60)
 equal(hum.Health,direct,"OFF cancels remaining burn")
 check(neutral:FindFirstChild("EGGRUMBLE_Ember")==nil,"OFF retires active burn visual")
 return "OFF cancels in-flight status before delayed damage"
end

function growthCases.element_resistance()
 local session=selected(1)
 local neutral,hum=pose(session,origin(session),5,true)
 local t=now
 activate(player,"A")
 advanceTo(t+.40)
 check(hum.Health<health,"resistant species still takes allowed direct hit")
 local direct=hum.Health
 advanceTo(t+1.50)
 check(neutral:FindFirstChild("EGGRUMBLE_Ember")==nil,"stone species has burn resistance")
 equal(hum.Health,direct,"resistance prevents additional hit")
 return "actual neutral species resists status and preserves direct hit"
end

function growthCases.element_frost()
 local session=selected(2)
 local ground=session.world:FindFirstChild("TacticalBattlefield")
 local at=origin(session)
 local target,hum=pose(session,at,5,false)
 local normal=secondNeutral(session,target)
 local neutralAt=ground.Position+Vector3.new(185,ground.Size.Y/2+2*target.PrimaryPart.Size.Y/2.5,80)
 local offset=at+Vector3.new(5,1,9)
 local shiftedAt=ground.Position+Vector3.new(180,ground.Size.Y/2+3,85)
 for _,mob in ipairs({target,normal}) do
  mob:SetAttribute("EGGRUMBLE_NeutralSpeed",0)
 end
 normal:PivotTo(CFrame.new(offset))
 local t=now
 activate(player,"A")
 advanceTo(t+.30)
 check(hum.Health<health and target:FindFirstChild("EGGRUMBLE_Frost")~=nil,
  "frost only applies after actual swept hit hp="..hum.Health)
 rootPart.CFrame=CFrame.new(shiftedAt,shiftedAt+Vector3.new(1,0,0))
 -- Give both neutrals the same directional path and the same original speed.
 target:PivotTo(CFrame.new(neutralAt))
 local normalAt=Vector3.new(neutralAt.X,ground.Position.Y+ground.Size.Y/2+2*normal.PrimaryPart.Size.Y/2.5,neutralAt.Z)
 normal:PivotTo(CFrame.new(normalAt))
 for _,mob in ipairs({target,normal}) do mob:SetAttribute("EGGRUMBLE_NeutralSpeed",5) end
 advanceTo(t+.74)
 local frostStep=(target:GetPivot().Position-neutralAt).Magnitude
 local normalStep=(normal:GetPivot().Position-normalAt).Magnitude
 check(normalStep>.1 and frostStep<normalStep,"actual Swarm ground movement is slowed "..frostStep.."/"..normalStep)
 advanceTo(t+2.0)
 check(target:FindFirstChild("EGGRUMBLE_Frost")==nil,"frost movement status ends")
 return "actual Frost hit reduces neutral ground movement; marker and slow expire"
end

function growthCases.element_icicle()
 local session=selected(3)
 local at=origin(session)
 local target,first=pose(session,at,5,false)
 local _,second=pose(session,at,7,false,secondNeutral(session,target))
 local t=now
 activate(player,"A")
 check(session.world:FindFirstChild("EGGRUMBLE_MAGE-012_Aim")~=nil,"visible icicle tell")
 advanceTo(t+.19)
 equal(first.Health,health,"tell precedes S0 penetration contact")
 advanceTo(t+.51)
 check(first.Health<health,"first actual neutral hit")
 equal(second.Health,health,"S0 icicle uses exact one neutral limit")
 return "real icicle respects tell, captured direction, and S0 cap"
end

function growthCases.element_needle()
 local session=selected(4)
 local at=origin(session)
 local target,first=pose(session,at,6,false)
 local _,second=pose(session,at,8,false,secondNeutral(session,target))
 local t=now
 activate(player,"A")
 check(session.world:FindFirstChild("EGGRUMBLE_MAGE-026_Aim")~=nil,"real needle tell shown")
 advanceTo(t+.35)
 equal(first.Health,health,"needle has not travelled six studs at 22 studs/s")
 advanceTo(t+.53)
 check(first.Health<health and target:FindFirstChild("EGGRUMBLE_Frost")==nil,"needle actual contact with no frost")
 equal(second.Health,health,"needle stops at first neutral")
 return "fixed needle speed and first-contact stop reach actual HP"
end
end
