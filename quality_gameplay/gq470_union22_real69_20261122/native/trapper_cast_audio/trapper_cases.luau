do
local FLAG="P0D_ENABLE_PRIVATE_TRAPPER_FIELD"
local VERB="念技を装備"
local DIR=Vector3.new(1,0,0)
local DECKS={{A="TRAPPER-001",B="TRAPPER-003",C="TRAPPER-004"},
 {A="TRAPPER-007",B="TRAPPER-008",C="TRAPPER-009"}}

local function tools()
 local deck={}
 for _,parent in ipairs({player:FindFirstChildOfClass("Backpack"),player.Character}) do
  for _,item in ipairs(parent:GetChildren()) do
   local internal=item:GetAttribute("EGGRUMBLE_InternalToolId")
   local slot=type(internal)=="string" and internal:match("^EGGRUMBLE_SKILL_([ABCD])_")
   if slot then check(not deck[slot],"single exact Tool");deck[slot]=item end
  end
 end
 return deck
end

local function stand(live,floor)
 rootPart.CFrame=CFrame.lookAt(floor+Vector3.new(0,3,0),floor+Vector3.new(1,3,0))
 rootPart.AssemblyLinearVelocity=Vector3.zero
 humanoid.FloorMaterial=Enum.Material.Grass;humanoid.Sit=false;humanoid.PlatformStand=false
end

local function start(kit,secondRole)
 local role=scenes:FindFirstChild("ROLE_TRAPPER")
 trigger(player,role,"職業選択")
 for _=1,(kit or 0) do
  advanceTo(now+.51)
  trigger(player,role,VERB)
 end
 local live=ready("PRIVATE_TRAPPER_FIELD_FULL_BODY","TRAPPER",secondRole)
 local ground=live.world:FindFirstChild("TacticalBattlefield")
 local floor=ground.Position+Vector3.new(170,ground.Size.Y*.5,-115)
 stand(live,floor)
 if kit then
  check(live.trapperFieldLoadouts[player.UserId]==kit,"real server selected field kit")
  for slot,id in pairs(DECKS[kit]) do
   check(tools()[slot]:GetAttribute("EGGRUMBLE_FixedAbilityId")==id,"equipped "..id)
  end
 end
 return live,floor
end

local function put(model,floor,x,z,species,speed)
 local at=floor+Vector3.new(x,2*(model.PrimaryPart.Size.Y/2.5),z)
 model:PivotTo(CFrame.new(at))
 model:SetAttribute("EGGRUMBLE_NeutralSpeed",speed or 0)
 model:SetAttribute("EGGRUMBLE_NeutralSpecies",species or "BANNER_KNIGHT")
 local hp=model:FindFirstChildOfClass("Humanoid")
 hp.Health=150
 return {model=model,hp=hp,at=at}
end

local function roster(live,floor,count)
 local collection=live.world:FindFirstChild("NeutralHorde")
 for _=1,48 do
  local actors={}
  for _,mob in ipairs(collection:GetChildren()) do
   if mob.PrimaryPart and mob:FindFirstChildOfClass("Humanoid") and mob:FindFirstChildOfClass("Humanoid").Health>0 then
    put(mob,floor,-38,33)
    table.insert(actors,mob)
   end
  end
  if #actors>=count then return actors end
  advanceTo(now+.35)
 end
 error("expected actual current neutral roster")
end

local function near(a,b) return math.abs(a-b)<.03 end
local function energy(live) return live.swarm.getRoleGrowthSnapshot(player).energy end
local function fx(live,id) return live.world:FindFirstChild("EGGRUMBLE_TrapperField_"..id) end

local function cast(live,slot,id,cost)
 check(tools()[slot]:GetAttribute("EGGRUMBLE_FixedAbilityId")==id,"exact authorized Tool")
 local begin=now
 local remaining=energy(live)-cost
 activate(player,slot)
 local cue=fx(live,id)
 check(cue and #cue:GetChildren()>0 and near(energy(live),remaining),"real warning/wind-up and one energy debit")
 activate(player,slot)
 check(fx(live,id)==cue and near(energy(live),remaining),"duplicate creates no work and consumes no energy")
 return begin,cue
end

local function wall(live,at)
 local solid=Instance.new("Part")
 solid.Size=Vector3.new(.4,7,8);solid.CFrame=CFrame.new(at)
 solid.Anchored=true;solid.CanCollide=true;solid.CanQuery=true;solid.Parent=live.world
 return solid
end

function growthCases.trapper_field_push()
 local live,floor=start(1)
 local actors=roster(live,floor,3)
 local target=put(actors[1],floor,2.8,0)
 local side=put(actors[2],floor,2.3,3.3)
 local closeHeavy=put(actors[3],floor,1.5,.1,"BABY_GOLEM")
 local t=cast(live,"A","TRAPPER-001",30)
 advanceTo(t+.23)
 check(target.model.PrimaryPart.Position==target.at,"windup is non damaging")
 advanceTo(t+.245)
 check(target.model.PrimaryPart.Position.X>=target.at.X+.9 and near(target.hp.Health,150)
  and side.model.PrimaryPart.Position==side.at and closeHeavy.model.PrimaryPart.Position==closeHeavy.at,
  "front light neutral moves once, side and heavyweight stay unchanged")
 return "real one-stud neutral push, no HP, circle or heavy-target effect"
end

function growthCases.trapper_field_flight()
 local live,floor=start(1)
 local actors=roster(live,floor,3)
 local target=put(actors[1],floor,4.2,0)
 local behind=put(actors[2],floor,6.7,.05)
 local side=put(actors[3],floor,3.6,2.8)
 local t=cast(live,"B","TRAPPER-003",30)
 advanceTo(t+.24)
 check(target.hp.Health==150 and fx(live,"TRAPPER-003"):FindFirstChild("MovingPebble"),"actual moving pebble without early HP")
 advanceTo(t+.75)
 local damage=dependencies.EGGRUMBLE_CombatBalance.skill("TRAPPER","A").damage
 check(near(target.hp.Health,150-damage) and behind.hp.Health==150 and side.hp.Health==150,
  "exact moving pebble hits only first eligible near center")
 return "swept pebble deals one real neutral HP write, S0 cap one"
end

function growthCases.trapper_field_flight_late_wall()
 local live,floor=start(1)
 local target=put(roster(live,floor,1)[1],floor,5.2,0)
 local t=cast(live,"B","TRAPPER-003",30)
 advanceTo(t+.24)
 wall(live,floor+Vector3.new(2.2,3,0))
 advanceTo(t+.80)
 check(target.hp.Health==150 and not fx(live,"TRAPPER-003"),"late solid blocks moving stone")
 return "a real late wall prevents the in-flight neutral hit"
end

function growthCases.trapper_field_stop()
 local live,floor=start(1)
 local mob=roster(live,floor,1)[1]
 local target=put(mob,floor,4.3,0)
 local t=cast(live,"C","TRAPPER-004",35)
 advanceTo(t+.283)
 local frozen=target.model.PrimaryPart.Position
 target.model:SetAttribute("EGGRUMBLE_NeutralSpeed",5)
 advanceTo(t+.58)
 check((target.model.PrimaryPart.Position-frozen).Magnitude<.03 and target.hp.Health==150,
  "role control stops the actual Swarm mover without HP writes")
 advanceTo(t+1.2)
 check((target.model.PrimaryPart.Position-frozen).Magnitude>.10,"original mover resumes once the bounded hold expires")
 return "bounded stop pauses and releases the same living neutral"
end

function growthCases.trapper_field_ward()
 local live,floor=start(2,"MAGE")
 local door=live.castleModels["43"].door
 for _=1,10 do
  advanceTo(now+3)
  trigger(player,door,"攻城攻撃")
  outsideField(live)
 end
 check(live.castleSiegeStates["43"].gateHP==0,"actual enemy gate collapses")
 local g=live.world:FindFirstChild("Guardian_ICE_MAGE")
 check(g and g:GetAttribute("EGGRUMBLE_GuardianOwner")=="43","actual hostile Ice Mage guardian")
 advanceTo(now+1.8)
 local origin=floor+Vector3.new(0,3,0)
 stand(live,floor)
 g:PivotTo(CFrame.new(origin+DIR*14))
 secondRoot.CFrame=CFrame.new(origin+Vector3.new(70,5,70))
 for _,mob in ipairs(live.world:FindFirstChild("NeutralHorde"):GetChildren()) do
  if mob.PrimaryPart then put(mob,floor,-55,60) end
 end
 humanoid.Health=100
 local bolt
 for _=1,12 do
  bolt=live.world:FindFirstChild("EGGRUMBLE_CastleMageBolt")
  if bolt then break end
  advanceTo(now+.035)
 end
 check(bolt and humanoid.Health==100,"actual in-flight hit begins with no damage")
 local t=cast(live,"A","TRAPPER-007",35)
 local defense=dependencies.EGGRUMBLE_InvulRuntime
 check(near(defense.filterDamage(humanoid,12,"NEUTRAL","SWARM_MELEE",origin+DIR*1),12)
  and fx(live,"TRAPPER-007"),"untagged melee leaves ward intact")
 advanceTo(t+.85)
 check(near(humanoid.Health,100-6*.92) and not fx(live,"TRAPPER-007"),
  "front actual Guardian bolt mitigates once and consumes shield")
 return "real front guardian bolt deals 5.52HP; melee leaves the shield available"
end

function growthCases.trapper_field_pair()
 local live,floor=start(2)
 local actors=roster(live,floor,4)
 local a=put(actors[1],floor,2.15,1.38)
 local b=put(actors[2],floor,2.15,-1.38)
 local inside=put(actors[3],floor,2.15,0)
 local rear=put(actors[4],floor,-1,0)
 local t=cast(live,"B","TRAPPER-008",40)
 advanceTo(t+.39)
 check(a.model.PrimaryPart.Position.Z>a.at.Z+.30 and b.model.PrimaryPart.Position.Z<b.at.Z-.30
  and inside.model.PrimaryPart.Position==inside.at and rear.model.PrimaryPart.Position==rear.at
  and a.hp.Health==150 and b.hp.Health==150,"one neutral per authored side, no repeated target or HP")
 return "two distinct directions share cap two without center or rear effects"
end

function growthCases.trapper_field_ground()
 local live,floor=start(2)
 local actors=roster(live,floor,3)
 local a=put(actors[1],floor,4.6,-1.45)
 local b=put(actors[2],floor,4.6,1.45)
 local wide=put(actors[3],floor,5.5,4.4)
 local t,cue=cast(live,"C","TRAPPER-009",45)
 check(cue:FindFirstChild("PalmRadius"),"visible world-local circle at the floor")
 advanceTo(t+.99)
 check(a.model.PrimaryPart.Position==a.at and b.model.PrimaryPart.Position==b.at,"one second warning before movement")
 advanceTo(t+1.01)
 check(a.model.PrimaryPart.Position.Z<a.at.Z-.7 and b.model.PrimaryPart.Position.Z>b.at.Z+.7
  and wide.model.PrimaryPart.Position==wide.at and a.hp.Health==150 and b.hp.Health==150,
  "real outward move inside the warned floor circle")
 return "real one-second ground warning, two bounded neutral displacements, no HP"
end

function growthCases.trapper_field_live_off()
 local live,floor=start(2)
 local target=put(roster(live,floor,1)[1],floor,4.6,1.4)
 local t=cast(live,"C","TRAPPER-009",45)
 workspace:SetAttribute(FLAG,false)
 drainDeferred()
 local old=tools()
 check(not fx(live,"TRAPPER-009") and old.C:GetAttribute("EGGRUMBLE_FixedAbilityId")~="TRAPPER-009",
  "flag OFF destroys real work and restores original role slots")
 advanceTo(t+1.1)
 check(target.model.PrimaryPart.Position==target.at and target.hp.Health==150,"pending effect cancelled")
 return "live OFF cancels queued move and leaves original Trapper kit"
end

function growthCases.trapper_field_physical_off()
 local live=start()
 local old=tools()
 check(live.trapperFieldLoadouts==nil and old.A and old.B and old.C
  and old.A:GetAttribute("EGGRUMBLE_FixedAbilityId")~="TRAPPER-001","actual previous bitwise source retains original tools")
 return "physical OFF sources keep the original Trapper toolkit"
end
end
