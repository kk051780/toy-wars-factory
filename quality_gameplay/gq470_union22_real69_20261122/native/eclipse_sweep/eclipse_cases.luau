do
local FLAG="P0D_ENABLE_PRIVATE_NINJA_ECLIPSE"
local LABEL="EGGRUMBLE_LobbyNinjaEclipseLoadoutName"
local STEALTH="EGGRUMBLE_StealthUntil"
local function deck()
 local t={}
 for _,folder in ipairs({player:FindFirstChildOfClass("Backpack"),player.Character}) do
  for _,item in ipairs(folder:GetChildren()) do
   local id=item:GetAttribute("EGGRUMBLE_InternalToolId")
   local slot=type(id)=="string" and id:match("^EGGRUMBLE_SKILL_([ABCD])_")
   if slot then t[slot]=item end
  end
 end
 return t
end
local function original(t)
 check(t.A.Name=="技A・瞬影斬" and t.B.Name=="技B・風走り" and t.C.Name=="技C・千刃旋風" and not t.D,
  "original physical Ninja ABC")
end
local function start(equip,turret)
 local stand=scenes:FindFirstChild("ROLE_NINJA")
 trigger(player,stand,"職業選択")
 if equip then
  check(workspace:GetAttribute(FLAG)==nil,"normal initial host has no diagnostic flag")
  trigger(player,stand,"月蝕を装備")
  check(player:GetAttribute(LABEL)=="月蝕潜航・二影斬・月蝕影舞","real default-on player option")
 end
 if turret then trigger(second,scenes:FindFirstChild("DEFENSE_TURRET"),"装備する") end
 local s=ready("PRIVATE_NINJA_ECLIPSE","NINJA")
 local t=deck()
 if equip then
  check(s.ninjaEclipseLoadouts[player.UserId] and not s.ninjaLoadouts[player.UserId]
   and not s.ninjaFlightLoadouts[player.UserId],"concrete selected one current Eclipse kit")
  check(t.A.Name=="技A・瞬影斬" and t.B:GetAttribute("EGGRUMBLE_FixedAbilityId")=="NINJA-020"
   and t.C:GetAttribute("EGGRUMBLE_FixedAbilityId")=="NINJA-028" and t.D:GetAttribute("EGGRUMBLE_FixedAbilityId")=="COMBO-007",
   "independent real fixed Tools and original A")
 else original(t) end
 return s
end
local function pose(s,count)
 local one=spawnCurrentNeutral(s)
 check(one,"real world horde populated")
 local floor=s.world:FindFirstChild("TacticalBattlefield")
 local at=floor.Position+Vector3.new(170,floor.Size.Y*.5+3,-115)
 rootPart.CFrame=CFrame.lookAt(at,at+Vector3.new(1,0,0))
 humanoid.Sit=false;humanoid.PlatformStand=false;humanoid.FloorMaterial=Enum.Material.Grass
 local head=character:FindFirstChild("Head")
 if not head then head=Instance.new("Part");head.Name="Head";head.Parent=character end
 head.Transparency=.31;head.CFrame=CFrame.new(at+Vector3.new(0,1.4,0))
 local face=Instance.new("Decal");face.Name="NativeEclipseFace";face.Transparency=.22;face.Parent=head
 humanoid.DisplayDistanceType=Enum.HumanoidDisplayDistanceType.Viewer
 secondRoot.CFrame=CFrame.new(at+Vector3.new(-45,0,0))
 local rows={}
 for _=1,32 do
  table.clear(rows)
  for _,model in ipairs(s.world:FindFirstChild("NeutralHorde"):GetChildren()) do
   local h=model:FindFirstChildOfClass("Humanoid")
   if h and h.Health>0 then
    model:SetAttribute("EGGRUMBLE_NeutralSpeed",0)
    model:PivotTo(CFrame.new(at+Vector3.new(-52,0,29)))
    table.insert(rows,{model=model,h=h})
   end
  end
  if #rows>=count then break end
  advanceTo(now+.3)
 end
 advanceTo(now+.42)
 check(#rows>=count and s.swarm.getRoleGrowthSnapshot(player).energy==100,"real role ledger available")
 return at,head,face,rows
end
local function position(row,at,hp)
 row.model:PivotTo(CFrame.new(at));row.h.Health=hp or 96
end
local function keepTestLane(s,at,rows)
 -- The actual spawn planner keeps running. Move unrelated fixture recruits
 -- out of the chosen lane so an early detection does not mask this timing witness.
 local chosen={}
 for _,row in ipairs(rows) do chosen[row.model]=true end
 local finish=now+2.15
 task.spawn(function()
  while now<finish do
   for _,mob in ipairs(s.world:FindFirstChild("NeutralHorde"):GetChildren()) do
    if not chosen[mob] and mob.PrimaryPart and (mob.PrimaryPart.Position-at).Magnitude<24 then
     mob:PivotTo(CFrame.new(at+Vector3.new(-52,0,29)))
    end
   end
   task.wait(.01)
  end
 end)
end
local function energy(s)
 local state=s.swarm.getRoleGrowthSnapshot(player)
 return state and state.energy
end
local function cue(s,name)
 return s.world:FindFirstChild("EGGRUMBLE_Eclipse"..name)
end
local function hidden()
 return (player:GetAttribute(STEALTH) or 0)>now
end
local function rel(value,expected)
 return math.abs(value-expected)<.0001
end
local function basic()
 local t=nil
 for _,folder in ipairs({player:FindFirstChildOfClass("Backpack"),player.Character}) do
  for _,item in ipairs(folder:GetChildren()) do
   if item:GetAttribute("EGGRUMBLE_InternalToolId")=="EGGRUMBLE_BASIC_ATTACK" then t=item end
  end
 end
 check(t,"actual basic Tool")
 t.Parent=player.Character;t.Activated:Fire()
end
local function wall(s,at)
 local barrier=Instance.new("Part")
 barrier.Name="NativeEclipseWall";barrier.Size=Vector3.new(.4,7,7)
 barrier.CFrame=CFrame.new(at);barrier.Anchored=true;barrier.CanCollide=true;barrier.CanQuery=true;barrier.Parent=s.world
 return barrier
end
local function twoShadows(s)
 for _,name in ipairs({"ShadowLeft","ShadowRight"}) do
  local marker=cue(s,name)
  check(marker and marker:IsA("Part") and marker.Anchored and not marker.CanCollide and not marker.CanTouch
   and not marker.CanQuery,"both visual shadows have no physical/HP authority")
 end
end

function growthCases.eclipse020_standalone()
 local s=start(true)
 local at,head,face,rows=pose(s,1)
 position(rows[1],at+Vector3.new(4.5,0,0))
 keepTestLane(s,at,rows)
 local untilAt=now+1.5
 local t=now
 activate(player,"B")
 check(rel(player:GetAttribute(STEALTH),untilAt) and hidden() and energy(s)==55 and head.Transparency==1
  and face.Transparency==1 and humanoid.DisplayDistanceType==Enum.HumanoidDisplayDistanceType.None,"actual E45 B hides appearance and uses old server attribute")
 local child=Instance.new("Part");child.Name="NativeLateAccessory";child.Transparency=.42;child.Parent=character
 character.DescendantAdded:Fire(child)
 check(child.Transparency==1,"body equipped during stealth follows same avatar")
 advanceTo(t+1.499)
 check(hidden() and not cue(s,"Reappear") and rows[1].h.Health==96,"exact stand-alone S0 window")
 advanceTo(t+1.501)
 check(not hidden() and rel(head.Transparency,.31) and rel(face.Transparency,.22) and rel(child.Transparency,.42)
  and humanoid.DisplayDistanceType==Enum.HumanoidDisplayDistanceType.Viewer and cue(s,"Reappear"),"restore before actual warning")
 advanceTo(t+1.949)
 check(cue(s,"Reappear") and rows[1].h.Health==96,"full 0.45-second reappearance and no attack")
 advanceTo(t+1.952)
 check(not cue(s,"Reappear") and rows[1].h.Health==96,"no standalone hidden attack")
 return "B real 1.5s server stealth, restored concrete avatar, and full 0.45s reappearance without damage"
end

function growthCases.eclipse028_single()
 local s=start(true)
 local at,head,_,rows=pose(s,3)
 position(rows[1],at+Vector3.new(3.9,0,0))
 position(rows[2],at+Vector3.new(4.6,0,0))
 position(rows[3],at+Vector3.new(5.1,0,0))
 local initial=s.swarm.getTotal()
 local t=now
 activate(player,"C")
 check(energy(s)==60 and not hidden() and rel(head.Transparency,.31),"C pays E40 while fully visible")
 twoShadows(s)
 advanceTo(t+.449)
 check(rows[1].h.Health==96,"no early C damage")
 advanceTo(t+.452)
 check(rows[1].h.Health<96 and rows[2].h.Health==96 and rows[3].h.Health==96
  and s.swarm.getTotal()==initial,"exact first target only and no false KO")
 local damage=dependencies.EGGRUMBLE_BasicMobilityPolicy.SPECS.NINJA.basic.damage
 check(rows[1].h.Health==96-damage,"two shadows cause exactly one original damage attempt")
 check(player:GetAttribute("EGGRUMBLE_SkillCastSignature"):match("^NINJA:C:") and not cue(s,"ShadowLeft"),"one actual pulse")
 return "C uses two harmless visuals, one five-stud scan, one real S0 neutral, and one existing damage budget"
end

function growthCases.eclipse028_range()
 local s=start(true)
 local at,_,_,rows=pose(s,2)
 position(rows[1],at+Vector3.new(5.1,0,0))
 position(rows[2],at+Vector3.new(0,0,4.5))
 activate(player,"C")
 twoShadows(s)
 advanceTo(now+.452)
 check(rows[1].h.Health==96 and rows[2].h.Health==96 and not cue(s,"ShadowLeft"),
  "real outside-range and outside-warned-arc neutrals never enter the single hit")
 return "the real 5-stud bound and forward preview reject a target just outside each condition"
end

function growthCases.eclipse028_replaced_visible()
 local s=start(true)
 local at,_,_,rows=pose(s,1)
 position(rows[1],at+Vector3.new(4.0,0,0))
 activate(player,"C")
 twoShadows(s)
 local old=player.Character
 local current=Instance.new("Model")
 local root=Instance.new("Part");root.Name="HumanoidRootPart";root.CFrame=rootPart.CFrame;root.Parent=current
 local human=Instance.new("Humanoid");human.Parent=current;current.PrimaryPart=root;current.Parent=workspace
 player.CharacterRemoving:Fire(old);player.Character=current
 advanceTo(now+.452)
 check(rows[1].h.Health==96 and not cue(s,"ShadowLeft"),"visible old attempt cannot hit after concrete avatar retirement")
 return "a visible old one-shot windup cannot carry over to a new avatar"
end

function growthCases.eclipse007_combo()
 local s=start(true)
 local at,head,_,rows=pose(s,2)
 position(rows[1],at+Vector3.new(4.0,0,0),3)
 position(rows[2],at+Vector3.new(4.7,0,0))
 keepTestLane(s,at,rows)
 local baseKO=s.swarm.getTotal()
 local t=now
 activate(player,"D")
 check(energy(s)==20 and hidden() and head.Transparency==1 and not cue(s,"ShadowLeft"),"one E80 starts D hidden")
 activate(player,"D");activate(player,"B")
 check(energy(s)==20 and hidden(),"repeat cannot break or double charge D")
 advanceTo(t+1.499)
 check(rows[1].h.Health==3 and not cue(s,"ShadowLeft"),"zero damage while hidden")
 advanceTo(t+1.501)
 check(not hidden() and rel(head.Transparency,.31),"actual existing stealth and transparency have ended")
 twoShadows(s)
 advanceTo(t+1.949)
 check(rows[1].h.Health==3 and s.swarm.getTotal()==baseKO,"full visible 0.45-second warning")
 advanceTo(t+1.952)
 check(rows[1].h.Health==0 and rows[2].h.Health==96 and s.swarm.getTotal()==baseKO+1 and not cue(s,"ShadowLeft"),
  "one genuine Swarm KO and no duplicate or sibling target")
 for _,id in ipairs({"NINJA-020","NINJA-028","COMBO-007"}) do
  check(s.swarm.tryRoleGrowthCast(player,"NINJA",1,1,{[id]=1})==nil,"author component deadlines")
 end
 return "D ends real stealth, warns visibly for 0.45s, then deals one authorized S0 hit and one original KO"
end

function growthCases.eclipse_near()
 local s=start(true)
 local at,head,_,rows=pose(s,1)
 position(rows[1],at+Vector3.new(4.4,0,0))
 local t=now
 activate(player,"D")
 check(hidden(),"armed normal D")
 secondRoot.CFrame=CFrame.new(at+Vector3.new(2.8,0,0))
 advanceTo(t+.095)
 check(not hidden() and rel(head.Transparency,.31) and cue(s,"Reappear") and not cue(s,"ShadowLeft"),"near same-match enemy reveals and cancels attack")
 advanceTo(t+1.98)
 check(rows[1].h.Health==96 and not cue(s,"ShadowRight"),"no delayed D after close reveal")
 return "real nearby enemy reveals the same actor and cancels the unspent hit"
end

function growthCases.eclipse_attack()
 local s=start(true)
 local at,head,_,rows=pose(s,1)
 position(rows[1],at+Vector3.new(4.4,0,0))
 local t=now
 activate(player,"D")
 check(hidden(),"actual hidden lease")
 local before=player:GetAttribute("EGGRUMBLE_BasicCastSerial")
 basic()
 check(not hidden() and rel(head.Transparency,.31) and cue(s,"Reappear") and rows[1].h.Health==96
  and player:GetAttribute("EGGRUMBLE_BasicCastSerial")==before,"normal attack intent restores visible pose and cannot hit")
 activate(player,"A")
 check(rows[1].h.Health==96 and not cue(s,"ShadowLeft"),"legacy A cannot hit during reappearance")
 advanceTo(t+.452)
 check(rows[1].h.Health==96,"canceled combo never deals its delayed damage")
 activate(player,"A")
 check(rows[1].h.Health<96,"existing ordinary A still hits once warning has ended")
 return "the real basic and legacy A cannot attack from hidden or during reveal; old A works afterward"
end

function growthCases.eclipse_late_wall()
 local s=start(true)
 local at,_,_,rows=pose(s,1)
 position(rows[1],at+Vector3.new(4.5,0,0))
 keepTestLane(s,at,rows)
 local t=now
 activate(player,"D")
 advanceTo(t+1.55)
 twoShadows(s)
 wall(s,at+Vector3.new(2.1,0,0))
 advanceTo(t+1.96)
 check(rows[1].h.Health==96 and not cue(s,"ShadowLeft"),"late wall rejects actual narrow authorized hit")
 return "a solid late wall blocks the once-only visible strike"
end

function growthCases.eclipse_sensor()
 local s=start(true)
 local at,head,_,rows=pose(s,1)
 position(rows[1],at+Vector3.new(4.5,0,0))
 activate(player,"D")
 local written=now
 player:SetAttribute(STEALTH,written);drainDeferred()
 check(not hidden() and rel(head.Transparency,.31) and cue(s,"Reappear")
  and player:GetAttribute(STEALTH)==written,"existing sensor timestamp is preserved and reveal starts")
 advanceTo(now+2.05)
 check(rows[1].h.Health==96,"external reveal never grants automatic attacks")
 return "the existing detection attribute may end the Eclipse lease without a stale hit"
end

function growthCases.eclipse_actual_defense()
 local s=start(true,true)
 local at,head,_,rows=pose(s,1)
 local id=tostring(second.UserId)
 check(table.find(s.rules.castles[id].modules,"TURRET"),"actual enemy opted into an existing turret")
 local folder=s.world:FindFirstChild("EGGRUMBLE_CastleDefenseLive")
 local target=nil
 local nearest=math.huge
 for _,part in ipairs(folder:GetChildren()) do
  if part.Name=="CastleDefense_TURRET" then
   local distance=(part.Position-s.castleLocations[id]).Magnitude
   if distance<nearest then target,nearest=part,distance end
  end
 end
 check(target and nearest<30,"actual enemy-side turret authored by Host")
 local params=RaycastParams.new()
 params.FilterType=Enum.RaycastFilterType.Exclude;params.FilterDescendantsInstances={character,folder}
 params.RespectCanCollide=true
 local traceSpot=nil
 for _,offset in ipairs({Vector3.new(4,-3,-4),Vector3.new(-5,0,0),Vector3.new(0,0,-5),
  Vector3.new(0,0,5),Vector3.new(5,0,0),Vector3.new(-4,2,-4),Vector3.new(4,2,4),Vector3.new(0,4,0)}) do
  if not workspace:Raycast(target.Position,offset,params) then traceSpot=target.Position+offset;break end
 end
 check(traceSpot,"choose a physically unobstructed existing defender lane")
 keepTestLane(s,at,rows);keepTestLane(s,traceSpot,rows)
 local t=now
 activate(player,"B")
 check(hidden(),"old live enemy acquires via the registered stealth lease")
 rootPart.CFrame=CFrame.lookAt(traceSpot,traceSpot+Vector3.new(1,0,0))
 local hp=humanoid.Health
 advanceTo(t+.70)
 check(hidden() and humanoid.Health==hp and head.Transparency==1,"existing turret rejects the concealed target")
 advanceTo(t+2.30)
 check(not hidden() and rel(head.Transparency,.31) and humanoid.Health<=hp-12,
  "same live turret can acquire the same concrete avatar after it reappears")
 return "actual old enemy turret denies target acquisition while concealed and resumes after visibility returns"
end

function growthCases.eclipse_egg()
 local s=start(true)
 local _,head=pose(s,1)
 activate(player,"D")
 check(hidden(),"armed before touching real vault")
 local victim=s.castleModels[tostring(second.UserId)].model:FindFirstChild("EggVault")
 trigger(player,victim,"敵の卵を奪取")
 local cart=s.rules.castles[tostring(player.UserId)].heldEggs
 check(cart==1 and not hidden() and rel(head.Transparency,.31) and not cue(s,"ShadowLeft"),
  "genuine vault transfer updates authoritative carried egg and restores appearance synchronously")
 advanceTo(now+2.1)
 check(not cue(s,"ShadowRight"),"no delayed strike after actual carry")
 return "the real Host vault transfer reveals immediately and cancels the queued strike"
end

function growthCases.eclipse_siege()
 local s=start(true)
 local _,head=pose(s,1)
 activate(player,"D")
 check(hidden(),"armed before real siege")
 local id=tostring(second.UserId)
 local door=s.castleModels[id].door
 local hp=s.rules.castles[id].hp
 local gate=s.castleSiegeStates[id].gateHP
 trigger(player,door,"攻城攻撃")
 check(s.rules.castles[id].hp==hp and s.castleSiegeStates[id].gateHP==gate
  and not hidden() and rel(head.Transparency,.31) and not cue(s,"ShadowLeft"),
  "genuine siege request revealed before writing castle or gate HP")
 advanceTo(now+1.62)
 trigger(player,door,"攻城攻撃")
 check(s.castleSiegeStates[id].gateHP==gate-36 and s.rules.castles[id].hp==hp,
  "existing gate-first siege is available after reveal")
 return "existing physical castle attack reveals without hidden damage, then normal siege works"
end

local function cancel(kind)
 local s=start(true)
 local at,head,face,rows=pose(s,1)
 position(rows[1],at+Vector3.new(4.5,0,0))
 activate(player,"D")
 local stale=deck().D
 if kind=="off" then
  workspace:SetAttribute(FLAG,false);drainDeferred()
  original(deck());check(not stale.Parent,"runtime OFF retires old actual Tool")
  stale.Activated:Fire()
 elseif kind=="avatar" then
  local new=Instance.new("Model")
  local root=Instance.new("Part");root.Name="HumanoidRootPart";root.CFrame=rootPart.CFrame;root.Parent=new
  local h=Instance.new("Humanoid");h.Parent=new;new.PrimaryPart=root;new.Parent=workspace
  player.Character=new
 elseif kind=="finish" then
  s.rules.phase="FINISHED";s.world:SetAttribute("EGGRUMBLE_MatchPhase","FINISHED");drainDeferred()
 end
 advanceTo(now+.14)
 check(not hidden() and rel(head.Transparency,.31) and rel(face.Transparency,.22),"the old captured avatar appearance is restored")
 advanceTo(now+2.1)
 check(rows[1].h.Health==96 and not cue(s,"ShadowLeft"),"no stale delayed attack from "..kind)
 return "actual Eclipse effect and avatar appearance retire on "..kind
end
for _,kind in ipairs({"off","avatar","finish"}) do
 growthCases["eclipse_cancel_"..kind]=function()return cancel(kind)end
end

function growthCases.eclipse_switch()
 local p=scenes:FindFirstChild("ROLE_NINJA")
 trigger(player,p,"職業選択")
 trigger(player,p,"月蝕を装備")
 check(player:GetAttribute(LABEL)~=nil,"new actual offer")
 trigger(player,p,"宵翼を装備")
 check(player:GetAttribute(LABEL)==nil and player:GetAttribute("EGGRUMBLE_LobbyNinjaFlightLoadoutName")~=nil,"old flight remains")
 advanceTo(now+.52)
 trigger(player,p,"月蝕を装備")
 trigger(player,p,"装備する")
 check(player:GetAttribute(LABEL)==nil and player:GetAttribute("EGGRUMBLE_LobbyNinjaLoadoutName")=="瞬歩・煙玉・霞瞬歩","old blink remains")
 advanceTo(now+.52)
 trigger(player,p,"月蝕を装備")
 advanceTo(now+.52)
 trigger(player,p,"月蝕を装備")
 check(player:GetAttribute(LABEL)==nil,"back to standard")
 start(false)
 return "Eclipse, flight, blink and standard decks remain independently selectable"
end

function growthCases.eclipse_physical_off()
 local s=start(false)
 check(not s.ninjaEclipseLoadouts,"physical OFF retains no new source tables")
 local _,head=pose(s,1)
 activate(player,"B")
 check(hidden() and rel(head.Transparency,.31) and not cue(s,"Reappear"),"old wind remains intentionally unchanged")
 return "exact physical parent keeps original wind stealth and original Ninja Tools"
end
end
