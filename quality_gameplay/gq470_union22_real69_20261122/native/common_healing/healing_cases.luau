do
local SELF,AREA="COMMON-016","COMMON-019"
local FLAG="P0D_ENABLE_PRIVATE_COMMON_HEALING"
local TELL,CONFIRMED="EGGRUMBLE_CommonHealTell","EGGRUMBLE_CommonHealConfirmed"
local function equip(id)
 for _,c in ipairs({player:FindFirstChildOfClass("Backpack"),player.Character}) do
  for _,item in ipairs(c:GetChildren()) do
   if item:IsA("Tool") and item:GetAttribute("EGGRUMBLE_FixedAbilityId")==id then return item end
  end
 end
end
local function cast(id)
 local item=assert(equip(id),id)
 item.Parent=player.Character;item.Activated:Fire()
 return item
end
local function point(s)
 local floor=s.world:FindFirstChild("TacticalBattlefield")
 local at=floor.Position+Vector3.new(170,floor.Size.Y*.5+3,-115)
 humanoid.FloorMaterial=Enum.Material.Grass;humanoid.Sit=false;humanoid.PlatformStand=false
 rootPart.CFrame=CFrame.new(at);rootPart.AssemblyLinearVelocity=Vector3.zero
 advanceTo(now+.40)
 return at
end
local function begin(n,br)
 trigger(player,scenes:FindFirstChild("ROLE_MAGE"),"職業選択")
 local stand=scenes:FindFirstChild("ROLE_FOOTING")
 for _=1,n do trigger(player,stand,"装備する");advanceTo(now+.51) end
 trigger(player,stand,"空中足場を装備")
 local s=if br then growthCases.readySoloBR() else ready("PRIVATE_COMMON_HEALING","MAGE")
 local at=point(s)
 check(equip("COMMON-025"),"existing Footing stays equipped")
 if n==3 then
  check(equip(SELF).Name=="癒し粒" and equip(AREA).Name=="癒光輪","real selected item Tools")
  check(not equip("COMMON-001") and not equip("COMMON-003") and not equip("COMMON-011") and not equip("COMMON-020"),
   "the healing choice occupies exactly the two prior utility slots")
 end
 return s,at
end
local function energy(s) return s.swarm.getRoleGrowthSnapshot(player).energy end
local function count(s,name)
 local n=0
 for _,p in ipairs(s.world:GetChildren()) do if p.Name==name then n+=1 end end
 return n
end
-- ACTUAL_BOT_ACTOR_FACTORY
local function allies(s,at)
 local team=s.rules.castles[tostring(player.UserId)].team
 local entries={}
 -- The older engine fixture replaces the path scheduler only. Materialize
 -- actual actor factory bodies for the already accepted server AI slots.
 for id,c in pairs(s.rules.castles) do
  if c.isAI and c.team==team and not s.botActors[id] then
   s.botActors[id]=spawnActor(s.world,id,at,c.team)
  end
 end
 for id,model in pairs(s.botActors) do
  local side=s.rules.castles[id]
  local h=model:FindFirstChildOfClass("Humanoid")
  if side and side.team==team and h then table.insert(entries,{id=id,model=model,h=h}) end
 end
 table.sort(entries,function(a,b) return a.id<b.id end)
 for i,e in ipairs(entries) do
  local displacement = if i<=3 then i*.65 else 10+i
  e.model:PivotTo(CFrame.new(at+Vector3.new(displacement,0,0)))
  e.h.MaxHealth=200;e.h.Health=100
 end
 check(#entries>=3,"real current TEAM allied bots, three candidates")
 secondRoot.CFrame=CFrame.new(at+Vector3.new(0,0,1))
 secondHumanoid.Health=50
 return entries
end
local function wall(s,at)
 local p=Instance.new("Part");p.Name="NativeHealingWall";p.CFrame=CFrame.new(at);p.Size=Vector3.new(.25,8,7)
 p.Anchored=true;p.CanCollide=true;p.CanQuery=true;p.Parent=s.world
 return p
end

function growthCases.healing_self()
 local s=begin(3,false)
 cast(SELF);equal(energy(s),100,"no cost on full HP")
 humanoid.MaxHealth=200;humanoid.Health=100
 local t=now
 cast(SELF)
 check(count(s,TELL)==1 and count(s,CONFIRMED)==0 and energy(s)==60,"one valid E40 channel; no early success")
 cast(SELF);equal(energy(s),60,"duplicate denied")
 advanceTo(t+.999)
 equal(humanoid.Health,100,"one-second hold before effect")
 advanceTo(t+1.001)
 equal(humanoid.Health,106,"S0 heals actual 3% maximum HP once")
 check(count(s,TELL)==0 and count(s,CONFIRMED)==1,"visual follows actual HP")
 check(s.swarm.tryRoleGrowthCast(player,"MAGE",1,1,{[SELF]=1})==nil,"same server 28s CD")
 return "016 exact one-second channel, E40/CD28, actual 3% self heal once"
end

function growthCases.healing_area()
 local s,at=begin(3,false)
 local roster=allies(s,at)
 humanoid.Health=60
 local t=now
 cast(AREA)
 check(count(s,TELL)==1 and energy(s)==55,"legitimate squad channels one E45")
 advanceTo(t+.999)
 equal(roster[1].h.Health,100,"no early heal")
 advanceTo(t+1.001)
 equal(roster[1].h.Health,102,"nearest ally 1%");equal(roster[2].h.Health,102,"second nearest ally 1%")
 equal(roster[3].h.Health,100,"third teammate denied");equal(secondHumanoid.Health,50,"near enemy human denied")
 equal(humanoid.Health,60,"caster never targets self with area")
 check(count(s,CONFIRMED)==2 and s.swarm.tryRoleGrowthCast(player,"MAGE",1,1,{[AREA]=1})==nil,
   "two exact HP witnesses and CD32")
 return "019 exact S0 radius3 plus two current allies only, 1% once, E45/CD32"
end

function growthCases.healing_hit()
 local s=begin(3,false)
 humanoid.Health=62;local t=now
 cast(SELF);advanceTo(t+.25)
 humanoid:TakeDamage(4)
 check(count(s,TELL)==0 and count(s,CONFIRMED)==0,"actual HealthChanged cancels tell")
 advanceTo(t+1.05)
 equal(humanoid.Health,58,"receipt cannot heal after damage")
 return "original Humanoid TakeDamage event interrupts channel with no success"
end

function growthCases.healing_candidate_change()
 local s,at=begin(3,false)
 local roster=allies(s,at)
 local t=now;cast(AREA)
 advanceTo(t+.31)
 roster[1].h.Health=0
 local currentlyRegistered=s.botActors[roster[2].id]
 s.botActors[roster[2].id]=nil
 local p=wall(s,at+Vector3.new(1.6,0,0))
 advanceTo(t+1.05)
 equal(roster[1].h.Health,0,"dead ally cannot resurrect")
 equal(roster[2].h.Health,100,"removed squad body cannot heal")
 equal(roster[3].h.Health,100,"new wall blocks remaining target before commit")
 check(count(s,CONFIRMED)==0,"no real target means no success presentation")
 p:Destroy();s.botActors[roster[2].id]=currentlyRegistered
 return "dead, removed squad members and allies newly behind cover are independently rejected at release"
end

function growthCases.healing_br()
 local s=begin(3,true)
 humanoid.Health=50
 cast(AREA)
 check(energy(s)==100 and count(s,TELL)==0,"actual solo BR denies team effect")
 cast(SELF);advanceTo(now+1.001)
 equal(humanoid.Health,53,"true self only remains in BR")
 return "real solo BR denies TEAM heal without debit while exact self-heal still works"
end

function growthCases.healing_custody_off()
 local s=begin(3,false)
 humanoid.Health=60
 local t=now
 local old=cast(SELF)
 local vault=s.castleModels[tostring(second.UserId)].model:FindFirstChild("EggVault")
 trigger(player,vault,"敵の卵を奪取")
 check(s.rules.castles[tostring(player.UserId)].heldEggs==1 and count(s,TELL)==0,"actual original custody cancels immediately")
 advanceTo(t+1.02);equal(humanoid.Health,60,"no HP after custody")
 workspace:SetAttribute(FLAG,false)
 check(not equip(SELF) and not equip(AREA) and equip("COMMON-025"),"live OFF clears only healing menu")
 old.Activated:Fire();check(count(s,TELL)==0,"stale OFF tool cannot resurrect the channel")
 return "real hostile egg acquisition and physical live OFF cancel while Footing remains"
end

function growthCases.healing_tool_phase()
 local s=begin(3,false)
 humanoid.Health=70;local t=now
 local tool=cast(SELF)
 tool.Parent=player:FindFirstChildOfClass("Backpack")
 advanceTo(t+.06)
 check(count(s,TELL)==0,"Tool ownership loss cancels by deferred ancestry")
 advanceTo(t+1.02);equal(humanoid.Health,70,"stale script cannot heal")
 local at=point(s)
 allies(s,at)
 t=now;cast(AREA)
 check(count(s,TELL)==1,"independent TEAM channel")
 s.rules.phase="FINISHED"
 s.world:SetAttribute("EGGRUMBLE_MatchPhase","FINISHED")
 advanceTo(t+1.01)
 check(count(s,TELL)==0 and count(s,CONFIRMED)==0,"stale epoch cannot release")
 return "ownership and phase remove the focused channel before an old delayed callback"
end

function growthCases.healing_physical_off()
 local s=begin(2,false)
 check(s.commonGuideLoadouts[player.UserId]=="MOBILITY" and equip("COMMON-001") and equip("COMMON-003")
  and not equip(SELF) and not equip(AREA),"exact preceding physical deck remains intact")
 return "physical OFF retains mobility and Footing with no healing Tools"
end

function growthCases.healing_legacy_mage()
 local s=ready("PRIVATE_OLD_MAGE_HEAL","MAGE")
 local at=point(s)
 local roster=allies(s,at)
 humanoid.Health=60
 activate(player,"C")
 equal(humanoid.Health,85,"original Mage heals exactly 25")
 equal(roster[1].h.Health,125,"original Mage allied bot heal retained")
 equal(secondHumanoid.Health,8,"original Mage C still deals 42 to the nearby enemy instead of healing")
 return "original Mage C retains its existing +25 heal through the one shared cap writer"
end

function growthCases.healing_stage_four()
 local s,base=begin(3,false)
 local moves={Vector3.zero,Vector3.new(1,0,0),Vector3.new(1,0,1),Vector3.new(0,0,1)}
 for i=1,600 do
  if player:GetAttribute("EGGRUMBLE_RoleAbilityStage")==4 then break end
  rootPart.CFrame=CFrame.new(base+moves[(i-1)%4+1])
  advanceTo(now+.39)
  for _,m in ipairs(s.world:FindFirstChild("NeutralHorde"):GetChildren()) do
   if m.PrimaryPart then
    m:SetAttribute("EGGRUMBLE_NeutralSpeed",0)
    m:PivotTo(CFrame.new(base+Vector3.new(85,3,50)))
   end
  end
 end
 equal(s.swarm.getRoleGrowthSnapshot(player).stage,4,"real active time advances to stage 4")
 local at=rootPart.Position
 local roster=allies(s,at)
 roster[1].model:PivotTo(CFrame.new(at+Vector3.new(6.92,0,0)))
 roster[2].model:PivotTo(CFrame.new(at+Vector3.new(7.08,0,0)))
 roster[3].model:PivotTo(CFrame.new(at+Vector3.new(-5.5,0,0)))
 roster[3].h.Health=198
 humanoid.MaxHealth=200;humanoid.Health=150
 cast(SELF);advanceTo(now+1.001)
 equal(humanoid.Health,164,"S4 7 percent equals 14 authoritative HP")
 cast(AREA);advanceTo(now+1.001)
 equal(roster[1].h.Health,106,"S4 3 percent inside 7-stud radius")
 equal(roster[2].h.Health,100,"S4 just outside 7-stud radius stays outside")
 equal(roster[3].h.Health,200,"S4 cannot overfill MaxHealth")
 check(energy(s)>=15 and energy(s)<30,"shared E40/E45 debits without a second timer")
 return "real active S4: 7% self, 3% inside seven studs only, capped at MaxHealth"
end
end
