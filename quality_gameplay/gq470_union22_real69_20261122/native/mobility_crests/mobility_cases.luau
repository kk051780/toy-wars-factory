do
local FLAG="P0D_ENABLE_PRIVATE_COMMON_MOBILITY"
local RUN,GLIDE="COMMON-001","COMMON-003"
local MARK,RETURN="COMMON-011","COMMON-020"
local SHOES="EGGRUMBLE_CommonShoes"
local CLOTH="EGGRUMBLE_CommonGlide"
local EAST=Vector3.new(1,0,0)
local function equip(p,id)
 for _,container in ipairs({p:FindFirstChildOfClass("Backpack"),p.Character}) do
  for _,item in ipairs(container:GetChildren()) do
   if item:IsA("Tool") and item:GetAttribute("EGGRUMBLE_FixedAbilityId")==id then return item end
  end
 end
 return nil
end
local function cast(id)
 local tool=assert(equip(player,id),id.." actual approved Tool")
 tool.Parent=player.Character
 tool.Activated:Fire()
 return tool
end
local function change(body,key,value)
 body[key]=value
 body:GetPropertyChangedSignal(key):Fire()
end
local function move(p,velocity)
 rootPart.CFrame=CFrame.lookAt(p,p+EAST)
 rootPart.AssemblyLinearVelocity=velocity or Vector3.zero
end
local function park(s,point)
 for _,m in ipairs(s.world:FindFirstChild("NeutralHorde"):GetChildren()) do
  if m.PrimaryPart then
   m:SetAttribute("EGGRUMBLE_NeutralSpeed",0)
   m:PivotTo(CFrame.new(point+Vector3.new(70,3,60)))
  end
 end
end
local function begin(clicks,footing,role)
 role=role or "MAGE"
 trigger(player,scenes:FindFirstChild("ROLE_"..role),"職業選択")
 local stand=scenes:FindFirstChild("ROLE_FOOTING")
 for _=1,clicks do trigger(player,stand,"装備する");advanceTo(now+.51) end
 if footing then trigger(player,stand,"空中足場を装備") end
 local s=ready("PRIVATE_COMMON_MOBILITY",role)
 local floor=s.world:FindFirstChild("TacticalBattlefield")
 local p=floor.Position+Vector3.new(170,floor.Size.Y*.5+3,-115)
 change(humanoid,"FloorMaterial",Enum.Material.Grass)
 move(p);park(s,p)
 advanceTo(now+.4)
 return s,p,stand
end
local function energy(s) return s.swarm.getRoleGrowthSnapshot(player).energy end
local function prepareDrop(p,y)
 move(p+Vector3.new(0,8,0),Vector3.new(2,y or -9,1))
 change(humanoid,"FloorMaterial",Enum.Material.Air)
 rootPart.AssemblyMass=8;workspace.Gravity=196.2
end
local function force()
 local model=character:FindFirstChild(CLOTH)
 return model and model:FindFirstChild(CLOTH.."Force")
end
local function caseStage(s,p,stage)
 local corners={Vector3.zero,Vector3.new(1,0,0),Vector3.new(1,0,1),Vector3.new(0,0,1)}
 for i=1,600 do
  if player:GetAttribute("EGGRUMBLE_RoleAbilityStage")==stage then break end
  move(p+corners[(i-1)%4+1]);park(s,p);advanceTo(now+.39)
 end
 check(s.swarm.getRoleGrowthSnapshot(player).stage==stage,"actual active movement reaches stage")
end

function growthCases.mobility_menu()
 local s=begin(2,true)
 check(s.commonGuideLoadouts[player.UserId]=="MOBILITY","second existing menu selection is the mobility set")
 check(equip(player,RUN).Name=="疾風靴" and equip(player,GLIDE).Name=="滑空布","two legitimate existing item menu Tools")
 check(not equip(player,MARK) and not equip(player,RETURN) and equip(player,"COMMON-025"),
  "never stack four tools; existing Footing remains distinct")
 local combat=dependencies.EGGRUMBLE_SevenRoleCombat
 check(combat.nextCommonUtility(nil)==true and combat.nextCommonUtility(true)=="MOBILITY"
  and combat.nextCommonUtility("MOBILITY")==nil,"guide, mobility and standard are one cycle")
 workspace:SetAttribute("P0D_ENABLE_PRIVATE_COMMON_ROUTE_GUIDE",false)
 check(equip(player,RUN) and equip(player,GLIDE),"unrelated guide OFF cannot retire mobility")
 return "actual one-stand selection equips two mobility items instead of guide items and keeps Footing"
end

function growthCases.mobility_shoes()
 local s,p=begin(2,false)
 local baseline=humanoid.WalkSpeed
 local life=now
 cast(RUN)
 equal(humanoid.WalkSpeed,baseline*1.06,"actual S0 +6 percent")
 equal(energy(s),70,"one E30 debit")
 check(character:FindFirstChild(SHOES) and (rootPart.Position-p).Magnitude<.01,"real plate cue, no teleport")
 cast(RUN);equal(energy(s),70,"no repeat or free refresh")
 advanceTo(life+1.99)
 equal(humanoid.WalkSpeed,baseline*1.06,"same existing speed lease lasts two seconds")
 advanceTo(life+2.01)
 equal(humanoid.WalkSpeed,baseline,"original round movement restored")
 check(not character:FindFirstChild(SHOES),"short ankle visuals are released")
 check(s.swarm.tryRoleGrowthCast(player,"MAGE",1,1,{[RUN]=1})==nil,"existing E ledger has full CD18")
 return "real S0 ground speed +6% for two seconds with one E30/CD18 and exact old baseline restored"
end

function growthCases.mobility_glide()
 local s,p=begin(2,false)
 prepareDrop(p)
 local starting=rootPart.AssemblyLinearVelocity
 local life=now
 cast(GLIDE)
 local f=force()
 check(f and f.Force.Magnitude==0,"original shared VectorForce waits for physics tick")
 RunService.Heartbeat:Fire(1/60)
 equal(f.Force.Y,workspace.Gravity*rootPart.AssemblyMass*.15,"actual 15% downward gravity relief")
 check(f.Force.X==0 and f.Force.Z==0 and f.Force.Y<workspace.Gravity*rootPart.AssemblyMass
  and (rootPart.AssemblyLinearVelocity-starting).Magnitude<.01 and not rootPart.Anchored,"no self lift or illicit velocity/position write")
 equal(energy(s),70,"one E30 through canonical Swarm")
 cast(GLIDE);equal(energy(s),70,"no second descent controller")
 advanceTo(life+.99)
 check(force()==f and rootPart:FindFirstChild(CLOTH.."Point"),"S0 stays until one second")
 advanceTo(life+1.01)
 check(not force() and not rootPart:FindFirstChild(CLOTH.."Point"),"original attachment and counterforce released")
 check(s.swarm.tryRoleGrowthCast(player,"MAGE",1,1,{[GLIDE]=1})==nil,"same authoritative CD20")
 return "real S0 one VectorForce cancels only 15% of gravity during descent for one second, E30/CD20"
end

function growthCases.mobility_denials()
 local s,p=begin(2,false)
 cast(GLIDE);equal(energy(s),100,"cannot glide grounded")
 prepareDrop(p,8)
 cast(GLIDE);cast(RUN)
 equal(energy(s),100,"upward or airborne misuse cannot charge")
 prepareDrop(p,-10)
 change(humanoid,"Sit",true)
 cast(GLIDE);equal(energy(s),100,"seated caster is not accepted")
 change(humanoid,"Sit",false)
 local castle=s.rules.castles[tostring(player.UserId)]
 castle.heldEggs=1
 cast(GLIDE);check(not force(),"canonical held eggs deny actual falling cast")
 castle.heldEggs=0
 change(humanoid,"FloorMaterial",Enum.Material.Grass)
 move(p+Vector3.new(2000,0,0));cast(RUN)
 check(not character:FindFirstChild(SHOES) and not force(),"out of the actual arena rejects")
 move(p);advanceTo(now+.41)
 equal(energy(s),100,"untrusted misuse never charged")
 return "grounded glide, rising glide, airborne speed, seats, custody and leaving the legal field are denied"
end

function growthCases.mobility_real_custody()
 local s,p=begin(2,false)
 local base=humanoid.WalkSpeed
 cast(RUN)
 check(humanoid.WalkSpeed>base and character:FindFirstChild(SHOES),"boost physically active before custody")
 local enemy=s.castleModels[tostring(second.UserId)].model:FindFirstChild("EggVault")
 trigger(player,enemy,"敵の卵を奪取")
 equal(s.rules.castles[tostring(player.UserId)].heldEggs,1,"actual enemy vault accepted exactly one egg")
 equal(humanoid.WalkSpeed,base,"actual custody update cancels before next tick")
 check(not character:FindFirstChild(SHOES),"no lingering plate or speed shortcut")
 return "actual original enemy egg pickup immediately cancels the existing speed token and effects"
end

function growthCases.mobility_retire_and_off()
 local s,p=begin(2,true)
 prepareDrop(p)
 local old=cast(GLIDE)
 RunService.Heartbeat:Fire(1/60)
 check(force() and force().Force.Y>0,"legal initial actual descent")
 change(humanoid,"FloorMaterial",Enum.Material.Grass)
 check(not force() and not rootPart:FindFirstChild(CLOTH.."Point"),"floor event synchronously releases force")
 move(p);advanceTo(now+.39)
 cast(RUN)
 check(character:FindFirstChild(SHOES),"new authorized ground lease")
 humanoid.Health=0;humanoid.Died:Fire()
 check(not character:FindFirstChild(SHOES),"death releases active presentation and speed token")
 workspace:SetAttribute(FLAG,false)
 check(not equip(player,RUN) and not equip(player,GLIDE) and equip(player,"COMMON-025"),
  "OFF removes only mobility items while leaving the independent old Footing")
 old.Activated:Fire()
 check(not force(),"stale tool cannot reactivate")
 return "immediate landing and death cleanup; live OFF rejects stale Tool and preserves Footing"
end

function growthCases.mobility_stage_four()
 local s,p=begin(2,false)
 caseStage(s,p,4)
 cast(RUN)
 equal(humanoid.WalkSpeed,22.8,"actual S4 +14 percent from the original 20")
 local t=now
 advanceTo(t+3.99)
 equal(humanoid.WalkSpeed,22.8,"S4 lasts four seconds")
 advanceTo(t+4.01)
 equal(humanoid.WalkSpeed,20,"S4 restores baseline")
 prepareDrop(p);cast(GLIDE)
 local g=now
 local f=force()
 RunService.Heartbeat:Fire(1/60)
 equal(f.Force.Y,workspace.Gravity*rootPart.AssemblyMass*.35,"S4 only 35 percent gravity relief")
 advanceTo(g+2.99)
 check(force()==f,"S4 glide holds for three seconds")
 advanceTo(g+3.01)
 check(not force(),"S4 glide expires at three seconds")
 return "true active-time S4 reaches +14% speed for 4s and 35% descent relief for 3s"
end

function growthCases.mobility_interrupted()
 local s,p=begin(2,false)
 prepareDrop(p)
 cast(GLIDE);RunService.Heartbeat:Fire(1/60)
 check(force() and force().Force.Y>0,"own current descent receives counterforce")
 rootPart.AssemblyLinearVelocity=Vector3.new(0,4,0)
 RunService.Heartbeat:Fire(1/60)
 check(not force() and not rootPart:FindFirstChild(CLOTH.."Point"),"outside upward impulse retires owned force on the same update")
 change(humanoid,"FloorMaterial",Enum.Material.Grass);move(p)
 advanceTo(now+.39)
 cast(RUN)
 check(character:FindFirstChild(SHOES),"legitimate short speed effect after glide is retired")
 player:SetAttribute("EGGRUMBLE_Restrained",true)
 check(not character:FindFirstChild(SHOES) and humanoid.WalkSpeed==20,"existing authoritative restraint cancels immediately")
 return "an outside upward impulse cannot keep descent assist, and current restraint removes the shared walk lease"
end

function growthCases.mobility_cap_override()
 local s,p=begin(2,false)
 s.walkBaseline[tostring(player.UserId)]=26
 humanoid.WalkSpeed=26
 cast(RUN)
 equal(humanoid.WalkSpeed,27,"cannot exceed existing 27-stud fast tool cap")
 local core=dependencies.EGGRUMBLE_BasicMobilityPolicy
 local token,speed=core.walkEffect(player,character,humanoid,s,"SLOW",16,now+3,26,now)
 check(token,"existing status authority applies independent slow")
 change(humanoid,"WalkSpeed",speed)
 check(not character:FindFirstChild(SHOES) and humanoid.WalkSpeed==16,
  "new original status takes precedence over retirement; no overwritten state")
 return "fastest ordinary speed capped at 27 and distinct later slow keeps the sole movement ledger"
end

function growthCases.mobility_physical_off()
 local s=begin(1,true)
 check(equip(player,MARK) and equip(player,RETURN) and equip(player,"COMMON-025"),
  "exact previous route and Footing tools remain")
 check(not equip(player,RUN) and not equip(player,GLIDE),"physical OFF does not equip a new controller")
 return "physical navigation predecessor has both prior guide tools and Footing, no motion kit"
end
end
