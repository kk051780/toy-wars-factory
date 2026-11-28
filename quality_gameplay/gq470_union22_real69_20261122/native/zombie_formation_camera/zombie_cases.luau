do
local DIR=Vector3.new(1,0,0)
local FLAG="P0D_ENABLE_PRIVATE_ZOMBIE_FORMATION"
local VERB="霊隊を装備"
local NORMAL="ZOMBIE-020"
local COMBO="COMBO-020"
local function place(floor,dx,dz)
 local root=floor+Vector3.new(dx,3,dz)
 rootPart.CFrame=CFrame.lookAt(root,root+DIR)
 humanoid.FloorMaterial=Enum.Material.Grass;humanoid.Sit=false;humanoid.PlatformStand=false
 rootPart.AssemblyLinearVelocity=Vector3.zero
 return root
end
local function deck()
 local result={}
 for _,parent in ipairs({player:FindFirstChildOfClass("Backpack"),player.Character}) do
  for _,item in ipairs(parent:GetChildren()) do
   local internal=item:GetAttribute("EGGRUMBLE_InternalToolId")
   local slot=type(internal)=="string" and internal:match("^EGGRUMBLE_SKILL_([ABCD])_")
   if slot then check(not result[slot],"single exact Tool");result[slot]=item end
  end
 end
 return result
end
local function start(opt)
 local shelf=scenes:FindFirstChild("ROLE_ZOMBIE")
 trigger(player,shelf,"職業選択")
 if opt then
  advanceTo(now+.52)
  trigger(player,shelf,VERB)
  check(player:GetAttribute("EGGRUMBLE_LobbyZombieLoadoutName")=="百影冥列・冥門百影","existing role chose current formation kit")
 end
 local live=ready("PRIVATE_ZOMBIE_FORMATION_FULL_BODY","ZOMBIE")
 local field=live.world:FindFirstChild("TacticalBattlefield")
 local floor=field.Position+Vector3.new(170,field.Size.Y*.5,-115)
 place(floor,0,0)
 if opt then
  local tools=deck()
  check(live.zombieRuneLoadouts[player.UserId]=="FORMATION" and tools.A:GetAttribute("EGGRUMBLE_FixedAbilityId")==NORMAL
   and tools.B:GetAttribute("EGGRUMBLE_FixedAbilityId")=="ZOMBIE-087" and not tools.C:GetAttribute("EGGRUMBLE_FixedAbilityId")
   and tools.D:GetAttribute("EGGRUMBLE_FixedAbilityId")==COMBO,"real exact A/B/D and original C")
 end
 return live,floor
end
local function energy(live) return live.swarm.getRoleGrowthSnapshot(player).energy end
local function near(a,b) return math.abs(a-b)<.03 end
local function fieldCue(live,id,phase)
 return live.world:FindFirstChild("EGGRUMBLE_ZombieRune_"..id.."_"..phase)
end
local function horde(live,floor,targetCount)
 local group=live.world:FindFirstChild("NeutralHorde")
 local roster={}
 for _=1,45 do
  table.clear(roster)
  for _,model in ipairs(group:GetChildren()) do
   local hp=model:FindFirstChildOfClass("Humanoid")
   if model.PrimaryPart and hp and hp.Health>0 then
    model:PivotTo(CFrame.new(floor+Vector3.new(-65,2,30)))
    model:SetAttribute("EGGRUMBLE_NeutralSpeed",0)
    table.insert(roster,model)
   end
  end
  if #roster>=targetCount then return roster end
  advanceTo(now+.35)
 end
 error("actual active neutral roster unavailable")
end
local function at(model,floor,x,z)
 local pos=floor+Vector3.new(x,2,z)
 model:PivotTo(CFrame.new(pos))
 model.PrimaryPart.Size=Vector3.new(.65,2.5,.65)
 model:SetAttribute("EGGRUMBLE_NeutralSpecies","ICE_SLIME")
 local hp=model:FindFirstChildOfClass("Humanoid")
 hp.Health=150
 return hp
end
local function squad(live,floor)
 place(floor,-27,-18)
 activate(player,"C")
 local folder=live.world:FindFirstChild("EGGRUMBLE_ZombieServants_"..tostring(player.UserId))
 check(folder and #folder:GetChildren()==3,"original skill C created exactly three existing allowed servants")
 local troops=folder:GetChildren()
 table.sort(troops,function(a,b) return a.Name<b.Name end)
 for i,model in ipairs(troops) do
  model:PivotTo(CFrame.new(floor+Vector3.new(-27,2,-14-i*3)))
 end
 place(floor,0,0)
 return folder,troops
end
local function park(troop,floor,x,z)
 troop:PivotTo(CFrame.new(floor+Vector3.new(x,2,z)))
end
local function block(live,floor,x)
 local part=Instance.new("Part")
 part.Size=Vector3.new(.55,7,10);part.CFrame=CFrame.new(floor+Vector3.new(x,3,0))
 part.Anchored=true;part.CanCollide=true;part.CanQuery=true;part.Parent=live.world
 return part
end

function growthCases.zombie_formation_no_spirit()
 local live,floor=start(true)
 local models=horde(live,floor,1)
 at(models[1],floor,4.0,0)
 activate(player,"A");activate(player,"D")
 check(energy(live)==100 and not fieldCue(live,NORMAL,"FormationTell") and near(rootPart.Position.X,floor.X),
  "no current servant ownership means no energy, cue, or warp")
 return "without the actual current squad no cast or cost is accepted"
end

function growthCases.zombie_formation_single()
 local live,floor=start(true)
 local models=horde(live,floor,2)
 local folder,troops=squad(live,floor)
 local h1=at(models[1],floor,4.1,0)
 local h2=at(models[2],floor,5.2,1.6)
 local t=now
 activate(player,"A")
 local cue=fieldCue(live,NORMAL,"FormationTell")
 check(cue and cue:IsA("BasePart") and not cue.CanCollide and not cue.CanQuery and energy(live)==50,
  "exact server E50 and noninteracting authored warning")
 activate(player,"A")
 check(energy(live)==50 and #folder:GetChildren()==3 and fieldCue(live,NORMAL,"FormationTell")==cue,"no duplicate or new servant")
 advanceTo(t+1.025)
 check(h1.Health==150 and h2.Health==150,"nothing hits before full warning, with all real units still distant")
 park(troops[1],floor,1.0,.35)
 advanceTo(t+1.62)
 RunService.Heartbeat:Fire(.26)
 check(near(h1.Health,144) and h2.Health==150 and #folder:GetChildren()==3 and folder:GetChildren()[1],
  "one existing body writes exactly 6 HP to the single S0 target, not model area around it: "..h1.Health.."/"..h2.Health)
 return "existing squad body spends one S0 hit on one selected neutral after 1s"
end

function growthCases.zombie_formation_combo()
 local live,floor=start(true)
 local models=horde(live,floor,2)
 local folder,troops=squad(live,floor)
 local h1=at(models[1],floor,8.2,0)
 local h2=at(models[2],floor,9.15,1.1)
 humanoid.Health=93
 local t=now
 activate(player,"D")
 check(energy(live)==20 and fieldCue(live,COMBO,"Tell") and near(rootPart.Position.X,floor.X),"one combo spend and .5s gate warning")
 advanceTo(t+.49)
 check(near(rootPart.Position.X,floor.X) and not fieldCue(live,COMBO,"FormationTell"),"no early move or command")
 advanceTo(t+.52)
 check(near(rootPart.Position.X,floor.X+4) and fieldCue(live,COMBO,"FormationTell") and humanoid.Health==93,
  "one 4 stud safe gate followed by a separate command tell")
 advanceTo(t+1.53)
 check(h1.Health==150 and h2.Health==150,"no remote damage while servants are distant")
 park(troops[2],floor,5.3,-.7)
 advanceTo(t+2.12)
 RunService.Heartbeat:Fire(.26)
 check(near(h1.Health,144) and h2.Health==150 and #folder:GetChildren()==3 and humanoid.Health==93,
  "same squad model enters reach after actual travel and phase after warp: "..h1.Health.."/"..h2.Health)
 return "safe 4 stud warp, then full 1s tell, then the same owned spirit legally hits once"
end

function growthCases.zombie_formation_late_wall()
 local live,floor=start(true)
 local models=horde(live,floor,1)
 local _,troops=squad(live,floor)
 local hp=at(models[1],floor,8.2,0)
 local t=now
 activate(player,"D")
 check(energy(live)==20,"legal combo reserved before late obstruction")
 block(live,floor,2.1)
 advanceTo(t+1.8)
 RunService.Heartbeat:Fire(.26)
 check(hp.Health==150 and near(rootPart.Position.X,floor.X) and not fieldCue(live,COMBO,"FormationTell")
  and troops[1].Parent,"late wall cancels warp and command, no artificial owner deletion")
 return "late physical wall aborts both the warp and dependent spirit activity"
end

function growthCases.zombie_formation_stage_four()
 local live,floor=start(true)
 local steps={{0,0},{0,1},{1,1},{1,0}}
 for i=1,590 do
  if player:GetAttribute("EGGRUMBLE_RoleAbilityStage")==4 then break end
  local step=steps[(i-1)%4+1]
  place(floor,step[1],step[2])
  advanceTo(now+.39)
  for _,mob in ipairs(live.world:FindFirstChild("NeutralHorde"):GetChildren()) do
   if mob.PrimaryPart then
    mob:SetAttribute("EGGRUMBLE_NeutralSpeed",0)
    mob:PivotTo(CFrame.new(floor+Vector3.new(-62,2,32)))
   end
  end
 end
 check(live.swarm.getRoleGrowthSnapshot(player).stage==4,"actual retained movement grows this Zombie to S4")
 local models=horde(live,floor,6)
 local folder,troops=squad(live,floor)
 local health={}
 for i,model in ipairs(models) do
  if i>6 then break end
  health[i]=at(model,floor,7.6+i*.92,0)
 end
 local t=now
 activate(player,"A")
 check(energy(live)==50 and fieldCue(live,NORMAL,"FormationShadow5")
  and not fieldCue(live,NORMAL,"FormationShadow6"),"real S4 range admits five indicated neutral targets")
 for i,elapsed in ipairs({1.045,1.47,1.89,2.66,3.08}) do
  local unit=(i-1)%3+1
  advanceTo(t+elapsed)
  for j,troop in ipairs(troops) do
   if j==unit then park(troop,floor,5.55+i*.92,0)
   else park(troop,floor,-28,-17-j*2) end
  end
  RunService.Heartbeat:Fire(.26)
  check(near(health[i].Health,144),"real S4 target "..i.." received one damage write: "..health[i].Health)
 end
 check(health[6].Health==150 and #folder:GetChildren()==3,"five different neutral hits use the same three bodies in separate cooldown windows")
 return "natural S4 expands range and cap to five attacks within the same three-owned-body limit"
end

function growthCases.zombie_formation_egg()
 local live,floor=start(true)
 local models=horde(live,floor,1)
 local folder=squad(live,floor)
 local hp=at(models[1],floor,8.2,0)
 local t=now
 activate(player,"D")
 check(fieldCue(live,COMBO,"Tell") and energy(live)==20,"real pending gate")
 local owner=live.rules.castles[tostring(player.UserId)]
 owner.heldEggs=1;player:SetAttribute("EGGRUMBLE_CarryingEgg",true)
 drainDeferred()
 advanceTo(t+1.8)
 RunService.Heartbeat:Fire(.26)
 check(near(rootPart.Position.X,floor.X) and owner.heldEggs==1 and hp.Health==150
  and #folder:GetChildren()==3 and not fieldCue(live,COMBO,"FormationTell"),"egg custody revokes both dependent actions")
 return "existing egg custody cancels the pending gate and preserves ownership and HP"
end

function growthCases.zombie_formation_custody_off()
 local live,floor=start(true)
 local models=horde(live,floor,1)
 local folder=squad(live,floor)
 local hp=at(models[1],floor,4.15,0)
 local t=now
 activate(player,"A")
 check(fieldCue(live,NORMAL,"FormationTell"),"actual pending command")
 workspace:SetAttribute(FLAG,false);drainDeferred()
 check(not deck().D and not deck().A:GetAttribute("EGGRUMBLE_FixedAbilityId") and not fieldCue(live,NORMAL,"FormationTell"),
  "physical flag switch restores actual standard tools and retires tell")
 advanceTo(t+1.8)
 RunService.Heartbeat:Fire(.26)
 check(hp.Health==150 and #folder:GetChildren()==3,"owned original squad still alive, optional work never issued")
 return "live OFF clears queued command while leaving original servant authority and tools"
end

function growthCases.zombie_formation_physical_off()
 local live=start(false)
 local shelf=scenes:FindFirstChild("ROLE_ZOMBIE")
 for _,offer in ipairs(shelf:GetChildren()) do
  check(not offer:IsA("ProximityPrompt") or offer.ActionText~=VERB,"prior version has no new authority entry")
 end
 local tools=deck()
 check(tools.A and tools.B and tools.C and not tools.D,"all original standard tools")
 return "exact prior physical source and tools remain unchanged"
end
end
