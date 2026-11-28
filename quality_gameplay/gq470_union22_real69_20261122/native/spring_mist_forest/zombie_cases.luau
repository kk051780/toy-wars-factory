local PATH_FLAG="P0D_ENABLE_PRIVATE_ZOMBIE_PATHS"
local function startPath(mist)
 local stand=scenes:FindFirstChild("ROLE_ZOMBIE")
 trigger(player,stand,"職業選択")
 trigger(player,stand,"冥門を装備")
 check(workspace:GetAttribute(PATH_FLAG)==nil and player:GetAttribute(LABEL)=="冥門","actual optional gate selection")
 if mist then
  advanceTo(now+.52);trigger(player,stand,"冥門を装備")
  check(player:GetAttribute(LABEL)=="薄霧・霧印","actual optional alternate mist selection")
 end
 local s=ready("PRIVATE_ZOMBIE_PATHS","ZOMBIE")
 local t=tools()
 check(s.zombieRuneLoadouts[player.UserId]==(if mist then "MIST" else "GATE") and not s.zombieConversionLoadouts[player.UserId],
  "one authorized kit selected before entry")
 check(t.A.Name=="技A・呪印波動" and not t.D,"original A and no added D")
 if mist then
  check(t.B:GetAttribute("EGGRUMBLE_FixedAbilityId")=="ZOMBIE-041" and t.C:GetAttribute("EGGRUMBLE_FixedAbilityId")=="ZOMBIE-044",
   "exact distinct B/C")
 else
  check(t.B:GetAttribute("EGGRUMBLE_FixedAbilityId")=="ZOMBIE-087" and t.C.Name=="技C・不死軍団","gate retains original army C")
 end
 return s,stand
end

local function nearPath(a,b)
 return (a-b).Magnitude<.08
end

function growthCases.path087()
 local s=startPath(false)
 local at,_=setup(s,1)
 local start=player.Character:GetPivot()
 humanoid.Health=81
 local other=secondRoot.CFrame
 local clock=s.rules.endAt
 local score=s.swarm.getTotal()
 local t=now
 activate(player,"B")
 local tell=cue(s,"087","Tell")
 check(energy(s)==60 and tell and not tell.CanCollide and not tell.CanTouch and not tell.CanQuery
  and math.abs(tell.Position.X-at.X-4)<.06,"one E40 and physical planar arrival warning at four studs")
 activate(player,"B")
 check(energy(s)==60 and cue(s,"087","Tell")==tell,"same pending Tool cannot pay or schedule again")
 advanceTo(t+.499)
 check(nearPath(rootPart.Position,at) and cue(s,"087","Tell")==tell and not cue(s,"087","Arrival"),"full .5 seconds before transfer")
 advanceTo(t+.504)
 check(nearPath(rootPart.Position,at+Vector3.new(4,0,0)) and rootPart.CFrame.LookVector:Dot(start.LookVector)>.99
  and not cue(s,"087","Tell") and cue(s,"087","Arrival"),"exact live position moved without rotating the character")
 check(humanoid.Health==81 and nearPath(secondRoot.Position,other.Position) and s.rules.endAt==clock and s.swarm.getTotal()==score,
  "no HP, score, timer or other actor rewrite")
 advanceTo(t+.83)
 check(not cue(s,"087","Arrival"),"closed gate removes its own existing visuals")
 return "087 tells for .5 seconds, moves the same avatar exactly four studs, and changes no other authority"
end

function growthCases.path087_oldsquad()
 local s=startPath(false)
 local at,_=setup(s,1)
 activate(player,"C")
 local folder=s.world:FindFirstChild("EGGRUMBLE_ZombieServants_"..tostring(player.UserId))
 local original=folder and folder:GetChildren()
 check(original and #original==3,"real original bounded C forms exactly three original runtime servants")
 for _,model in ipairs(original) do check(model:FindFirstChildOfClass("Humanoid") and model.PrimaryPart,"real server servant") end
 local t=now
 activate(player,"B");advanceTo(t+.504)
 check(nearPath(rootPart.Position,at+Vector3.new(4,0,0)) and #folder:GetChildren()==3,"gate never adds to the old owned army")
 for _,model in ipairs(original) do check(model.Parent==folder,"same actual original owned model preserved") end
 return "087 leaves the original C-created three actual owned servants untouched"
end

function growthCases.path087_castle()
 local s=startPath(false)
 setup(s,1)
 local enemy=s.castleModels[tostring(second.UserId)]
 local floor=enemy and enemy.model:FindFirstChild("StandardFoundation")
 check(floor and enemy.door and not enemy.door.CanCollide,"old hostile castle has its original physical open approach")
 local at=Vector3.new(enemy.door.Position.X,floor.Position.Y+floor.Size.Y*.5+3,enemy.door.Position.Z-1)
 rootPart.CFrame=CFrame.lookAt(at,at+Vector3.new(0,0,1))
 advanceTo(now+.4)
 check(s.swarm.getRoleGrowthSnapshot(player),"actual recent avatar action remains in existing match")
 local hp=s.rules.castles[tostring(second.UserId)].hp
 activate(player,"B")
 check(not cue(s,"087","Tell") and energy(s)==100,"known non-field castle floor is denied before paying")
 advanceTo(now+.51)
 check(nearPath(rootPart.Position,at) and s.rules.castles[tostring(second.UserId)].hp==hp,
  "cannot blink across the actual open hostile gate or alter HP")
 return "087 does not bypass the actual open castle entrance or write enemy castle HP"
end

function growthCases.path087_s4()
 local s=startPath(false)
 local at,_=setup(s,1)
 local heading=Vector3.new(1,0,0)
 local steps={Vector3.zero,Vector3.new(0,0,1),Vector3.new(1,0,1),heading}
 local horde=s.world:FindFirstChild("NeutralHorde")
 for i=1,590 do
  if player:GetAttribute("EGGRUMBLE_RoleAbilityStage")==4 then break end
  local point=at+steps[(i-1)%4+1]
  rootPart.CFrame=CFrame.lookAt(point,point+heading)
  advanceTo(now+.39)
  for _,unit in ipairs(horde:GetChildren()) do
   if unit:FindFirstChildOfClass("Humanoid") and unit.PrimaryPart then
    unit:SetAttribute("EGGRUMBLE_NeutralSpeed",0)
    unit:PivotTo(CFrame.new(at+Vector3.new(-55,8,25)))
   end
  end
 end
 rootPart.CFrame=CFrame.lookAt(at,at+heading)
 check(s.swarm.getRoleGrowthSnapshot(player).stage==4,"real movement unlocks S4")
 local t=now
 activate(player,"B")
 check(math.abs(cue(s,"087","Tell").Position.X-at.X-12)<.06 and energy(s)==60,"fixed maximum range and same E40")
 advanceTo(t+.499);check(nearPath(rootPart.Position,at),"still full original tell at S4")
 advanceTo(t+.504)
 check(nearPath(rootPart.Position,at+heading*12) and cue(s,"087","Arrival"),"one exact S4 displacement")
 return "087 natural S4 moves exactly twelve studs after the same .5 second warning"
end

local function denyPath(kind)
 local s=startPath(false)
 local at,_=setup(s,1)
 local t=now
 if kind=="prewall" then wall(s,at+Vector3.new(2,1,0)) end
 activate(player,"B")
 if kind=="prewall" then
  check(energy(s)==100 and not cue(s,"087","Tell"),"known blocked body rejects before debit")
 else
  check(cue(s,"087","Tell"),"accepted real pending tell")
 end
 if kind=="latewall" then
  advanceTo(t+.215);wall(s,at+Vector3.new(2,1,0))
 elseif kind=="egg" then
  s.rules.castles[tostring(player.UserId)].heldEggs=1
  player:SetAttribute("EGGRUMBLE_CarryingEgg",true);drainDeferred()
 elseif kind=="avatar" then
  local model=Instance.new("Model");local r=Instance.new("Part")
  r.Name="HumanoidRootPart";r.CFrame=rootPart.CFrame;r.Parent=model;model.PrimaryPart=r
  local h=Instance.new("Humanoid");h.Parent=model;model.Parent=workspace
  player.CharacterRemoving:Fire(character);player.Character=model
 elseif kind=="off" then
  local stale=tools().B
  workspace:SetAttribute(PATH_FLAG,false);drainDeferred();old(tools())
  check(not stale.Parent,"old B removed when independent flag is OFF")
  stale.Activated:Fire()
 end
 advanceTo(t+.80)
 check(nearPath(rootPart.Position,at) and not cue(s,"087","Tell") and not cue(s,"087","Arrival"),
  "original and pending gate cannot pass "..kind)
 return "087 rejects "..kind.." without transfer or late appearance"
end
for _,kind in ipairs({"prewall","latewall","egg","avatar","off"}) do
 growthCases["path087_deny_"..kind]=function()return denyPath(kind)end
end

function growthCases.path041()
 local s=startPath(true)
 local at,rows=setup(s,1)
 place(rows[1],at+Vector3.new(4,.9,.24))
 local t=now
 activate(player,"B")
 local tell=cue(s,"041","Tell")
 check(energy(s)==70 and tell and tell.Size.Y==4 and not cue(s,"041","Mist"),"fixed radius-two usable floor cue")
 advanceTo(t+.177)
 check(cue(s,"041","Tell")==tell and not cue(s,"041","Mist"),"auditable short telegraph first")
 advanceTo(t+.183)
 local effect=cue(s,"041","Mist")
 check(not cue(s,"041","Tell") and effect and effect.Size.X==4 and effect.Size.Y<=.45 and effect.Transparency>.8
  and not effect.CanQuery and not effect.CanTouch and not effect.CanCollide
  and rows[1].h.Health==96 and nearPath(rootPart.Position,at),"low, harmless local band, without applying a stealth effect")
 advanceTo(t+1.182)
 check(not cue(s,"041","Mist") and rows[1].h.Health==96,"one exact second and clean expiry")
 return "041 actual safe local floor telegraph produces a low one-second harmless visual band"
end

function growthCases.path044()
 local s=startPath(true)
 local at,rows=setup(s,1)
 place(rows[1],at+Vector3.new(5,.8,0))
 local t=now
 activate(player,"C")
 local flag=cue(s,"044","Marker")
 check(energy(s)==75 and flag and math.abs(flag.Position.X-at.X-6)<.06
  and not flag.CanQuery and not flag.CanCollide and nearPath(rootPart.Position,at) and rows[1].h.Health==96,
  "actual lawful floor marker identifies point, no teleport or damage")
 advanceTo(t+1.999);check(cue(s,"044","Marker")==flag,"two seconds of visible point")
 advanceTo(t+2.002)
 check(not cue(s,"044","Marker"),"exact expiry for both physical decorative pieces")
 return "044 marks one checked floor point six studs away for two seconds and has no movement or HP authority"
end

function growthCases.path_kit_switch()
 local stand=scenes:FindFirstChild("ROLE_ZOMBIE")
 trigger(player,stand,"職業選択")
 local keys={}
 for _,item in ipairs(stand:GetChildren()) do
  if item:IsA("ProximityPrompt") and item.Enabled then keys[item.ActionText]=item end
 end
 local path,oldWave=keys["冥門を装備"],keys["魂術を装備"]
 check(path and path.KeyboardKeyCode==Enum.KeyCode.K and path.GamepadKeyCode==Enum.KeyCode.DPadLeft
  and oldWave.KeyboardKeyCode==Enum.KeyCode.J and keys["符術を装備"].KeyboardKeyCode==Enum.KeyCode.G
  and keys["装備する"].KeyboardKeyCode==Enum.KeyCode.F,"independent physical F/G/J/K inputs")
 trigger(player,stand,"冥門を装備")
 workspace:SetAttribute("P0D_ENABLE_PRIVATE_ZOMBIE_WAVES",false)
 workspace:SetAttribute(FLAG,false);drainDeferred()
 check(player:GetAttribute(LABEL)=="冥門","two old flags never clear the new choice")
 advanceTo(now+.52);trigger(player,stand,"冥門を装備")
 check(player:GetAttribute(LABEL)=="薄霧・霧印","mist deck selection")
 advanceTo(now+.52);trigger(player,stand,"冥門を装備")
 check(player:GetAttribute(LABEL)==nil,"ordinary default remains immediately reachable")
 return "fixed old inputs retain distinct hooks and K reachability is independent"
end

function growthCases.path_physical_off()
 local s=start("BOLT")
 local stand=scenes:FindFirstChild("ROLE_ZOMBIE")
 for _,item in ipairs(stand:GetChildren()) do
  check(not item:IsA("ProximityPrompt") or item.ActionText~="冥門を装備","no new option in exact older root")
 end
 check(tools().B:GetAttribute("EGGRUMBLE_FixedAbilityId")=="ZOMBIE-072","original prior opt-in rune kit")
 return "exact old physical game keeps its old Zombie route and has no gate option"
end
