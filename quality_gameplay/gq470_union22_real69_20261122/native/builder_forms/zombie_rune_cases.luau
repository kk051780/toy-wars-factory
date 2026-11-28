do
local FLAG="P0D_ENABLE_PRIVATE_ZOMBIE_RUNES"
local LABEL="EGGRUMBLE_LobbyZombieLoadoutName"
local function tools()
 local result={}
 for _,bag in ipairs({player:FindFirstChildOfClass("Backpack"),player.Character}) do
  for _,item in ipairs(bag:GetChildren()) do
   local id=item:GetAttribute("EGGRUMBLE_InternalToolId")
   local slot=type(id)=="string" and id:match("^EGGRUMBLE_SKILL_([ABCD])_")
   if slot then result[slot]=item end
  end
 end
 return result
end
local function old(t)
 check(t.A.Name=="技A・呪印波動" and t.B.Name=="技B・疫病霧" and t.C.Name=="技C・不死軍団" and not t.D,
  "original A/B/C still exact")
end
local function start(kit)
 local stand=scenes:FindFirstChild("ROLE_ZOMBIE")
 trigger(player,stand,"職業選択")
 if kit then
  check(workspace:GetAttribute(FLAG)==nil,"real default private profile")
  trigger(player,stand,"符術を装備")
  check(player:GetAttribute(LABEL)=="印札三技","real MARK prompt")
  if kit=="BOLT" then advanceTo(now+.52);trigger(player,stand,"符術を装備") end
  check(player:GetAttribute(LABEL)==(if kit=="BOLT" then "霊撃三技" else "印札三技"),"right selected deck")
 end
 local s=ready("PRIVATE_ZOMBIE_RUNES","ZOMBIE")
 local t=tools()
 if kit then
  check(s.zombieRuneLoadouts[player.UserId]==kit and not s.zombieConversionLoadouts[player.UserId],"server freezes single chosen deck")
  local names=if kit=="MARK" then {"001","008","009"} else {"072","073","097"}
  for i,slot in ipairs({"B","C","D"}) do
   check(t[slot]:GetAttribute("EGGRUMBLE_FixedAbilityId")=="ZOMBIE-"..names[i],"real fixed Tool "..slot)
  end
  check(t.A.Name=="技A・呪印波動","keep original genuine A hit and conversion path")
 else
  old(t)
 end
 return s
end
local function setup(s,count)
 local one=spawnCurrentNeutral(s)
 check(one,"actual Swarm spawn")
 local floor=s.world:FindFirstChild("TacticalBattlefield")
 local at=floor.Position+Vector3.new(170,floor.Size.Y*.5+3,-115)
 rootPart.CFrame=CFrame.lookAt(at,at+Vector3.new(1,0,0))
 humanoid.Sit=false;humanoid.PlatformStand=false;humanoid.FloorMaterial=Enum.Material.Grass
 secondRoot.CFrame=CFrame.new(at+Vector3.new(-52,0,0))
 local chosen,rows={},{}
 local horde=s.world:FindFirstChild("NeutralHorde")
 for _=1,40 do
  table.clear(rows);table.clear(chosen)
  for _,mob in ipairs(horde:GetChildren()) do
   local h=mob:FindFirstChildOfClass("Humanoid")
   if h and h.Health>0 then
    mob:SetAttribute("EGGRUMBLE_NeutralSpeed",0)
    mob:PivotTo(CFrame.new(at+Vector3.new(-55,8,25)))
    table.insert(rows,{model=mob,h=h});chosen[mob]=true
   end
  end
  if #rows>=count then break end
  advanceTo(now+.31)
 end
 advanceTo(now+.4)
 check(#rows>=count and s.swarm.getRoleGrowthSnapshot(player).energy==100 and s.swarm.getRoleGrowthSnapshot(player).stage==0,
  "real role ledger S0 and current neutral actors")
 for i=count+1,#rows do rows[i]=nil end
 local finish=now+2.8
 task.spawn(function()
  while now<finish do
   for _,mob in ipairs(horde:GetChildren()) do
    if not chosen[mob] and mob.PrimaryPart and (mob.PrimaryPart.Position-at).Magnitude<22 then
     mob:PivotTo(CFrame.new(at+Vector3.new(-55,8,27)))
    end
   end
   task.wait(.025)
  end
 end)
 return at,rows
end
local function place(row,at,hp)
 row.model:PivotTo(CFrame.new(at))
 row.h.MaxHealth=100
 row.h.Health=hp or 96
 row.model:SetAttribute("EGGRUMBLE_NeutralSpecies","BANNER_KNIGHT")
end
local function energy(s)
 return s.swarm.getRoleGrowthSnapshot(player).energy
end
local function mark(row,id)
 return row.model.PrimaryPart:FindFirstChild("EGGRUMBLE_ZombieRune_ZOMBIE-"..id.."_Mark")
end
local function cue(s,id,which)
 return s.world:FindFirstChild("EGGRUMBLE_ZombieRune_ZOMBIE-"..id.."_"..which)
end
local function cleanMarks(rows)
 for _,row in ipairs(rows) do
  check(row.h.Health==96 and row.model:GetAttribute("EGGRUMBLE_NeutralFriendlyOwnerId")==nil
   and row.model:GetAttribute("EGGRUMBLE_NeutralSeals")==nil,"information-only marks leave HP, original seal and team exact: "
   ..tostring(row.h.Health).." / "..tostring(row.model:GetAttribute("EGGRUMBLE_NeutralFriendlyOwnerId"))
   .." / "..tostring(row.model:GetAttribute("EGGRUMBLE_NeutralSeals")))
 end
end
local function wall(s,at)
 local p=Instance.new("Part")
 p.Name="NativeRuneWall";p.Size=Vector3.new(.3,9,9);p.CFrame=CFrame.new(at)
 p.Anchored=true;p.CanCollide=true;p.CanQuery=true;p.Parent=s.world
 return p
end

function growthCases.rune001_mark()
 local s=start("MARK")
 local at,rows=setup(s,2)
 place(rows[1],at+Vector3.new(3.4,0,0));place(rows[2],at+Vector3.new(4.6,0,0))
 local ko=s.swarm.getTotal()
 local t=now
 activate(player,"B")
 local b=mark(rows[1],"001")
 check(energy(s)==70 and b and not mark(rows[2],"001") and b:FindFirstChildOfClass("TextLabel").Text=="呪点",
  "real information on one chosen target")
 cleanMarks(rows)
 activate(player,"B")
 check(energy(s)==70 and mark(rows[1],"001")==b,"same deck deadline refuses replay")
 advanceTo(t+1.998)
 check(mark(rows[1],"001")==b,"mark stays for actual 2.0s")
 advanceTo(t+2.002)
 check(not mark(rows[1],"001") and s.swarm.getTotal()==ko,"short marker TTL and no fabricated KO")
 cleanMarks(rows)
 return "001 real E30 single information mark, one existing target, exact expiry and zero HP/seal changes"
end

function growthCases.rune008_dual()
 local s=start("MARK")
 local at,rows=setup(s,3)
 place(rows[1],at+Vector3.new(3.4,0,-.3));place(rows[2],at+Vector3.new(4.1,0,.4))
 place(rows[3],at+Vector3.new(4.5,0,0))
 activate(player,"C")
 check(energy(s)==65 and mark(rows[1],"008") and mark(rows[2],"008")
  and not mark(rows[3],"008"),"two distinct legal neutrals in the same exact cap")
 cleanMarks(rows)
 rows[1].model:SetAttribute("EGGRUMBLE_NeutralFriendlyOwnerId",tostring(second.UserId));drainDeferred()
 check(not mark(rows[1],"008") and mark(rows[2],"008"),"an enlisted neutral loses its original enemy label only")
 return "008 real E35 shows exactly two distinct targets, with independent valid visual removal"
end

function growthCases.rune009_ring()
 local s=start("MARK")
 local at,rows=setup(s,3)
 place(rows[1],at+Vector3.new(5.3,0,.25));place(rows[2],at+Vector3.new(6,0,-.5))
 place(rows[3],at+Vector3.new(7.3,0,0))
 local t=now
 activate(player,"D")
 local tell=cue(s,"009","Tell")
 check(energy(s)==55 and tell and tell.Size.Y==6 and not tell.CanCollide and not tell.CanTouch and not tell.CanQuery,
  "real S0 radius-three nonphysical tell")
 advanceTo(t+.799)
 check(cue(s,"009","Tell")==tell and not mark(rows[1],"009"),"0.8s warning before any mark")
 advanceTo(t+.802)
 check(not cue(s,"009","Tell") and mark(rows[1],"009") and mark(rows[2],"009") and not mark(rows[3],"009"),
  "locked actual ring and 2 target cap")
 cleanMarks(rows)
 return "009 actual 0.8s warning followed by two legal information marks inside radius 3"
end

function growthCases.rune072_bolt()
 local s=start("BOLT")
 local at,rows=setup(s,2)
 place(rows[1],at+Vector3.new(4,.8,0));place(rows[2],at+Vector3.new(5.7,.8,0))
 local t=now
 activate(player,"B")
 local projectile=cue(s,"072","Bolt")
 check(energy(s)==70 and projectile and not projectile.CanQuery and not projectile.CanCollide,"real single ceramic bolt")
 advanceTo(t+.07)
 check(projectile.Position.X>at.X+.8 and rows[1].h.Health==96 and rows[2].h.Health==96,"observable trajectory before real collision")
 advanceTo(t+.24)
 check(rows[1].h.Health==86 and rows[2].h.Health==96 and not cue(s,"072","Bolt"),
  "first existing hit consumes one nonpenetrating bolt")
 check(rows[1].model:GetAttribute("EGGRUMBLE_NeutralSeals")==1 and not rows[1].model:GetAttribute("EGGRUMBLE_NeutralFriendlyOwnerId"),
  "the original curse engine records one real hit without granting conversion: "
  ..tostring(rows[1].model:GetAttribute("EGGRUMBLE_NeutralSeals")).." / "
  ..tostring(rows[1].model:GetAttribute("EGGRUMBLE_NeutralFriendlyOwnerId")))
 return "072 real moving projectile hits one target once, through existing Swarm HP and seal authority"
end

function growthCases.rune073_line()
 local s=start("BOLT")
 local at,rows=setup(s,3)
 place(rows[1],at+Vector3.new(4,.8,.02));place(rows[2],at+Vector3.new(4,.8,2.2))
 place(rows[3],at+Vector3.new(6.15,.8,0))
 local t=now
 activate(player,"C")
 check(energy(s)==65 and cue(s,"073","Tell").Size.Z==6,"actual fixed S0 line")
 advanceTo(t+.599)
 check(rows[1].h.Health==96 and rows[2].h.Health==96 and rows[3].h.Health==96,"full .60s line warning")
 advanceTo(t+.605)
 check(rows[1].h.Health==86 and rows[2].h.Health==96 and rows[3].h.Health==96 and not cue(s,"073","Tell"),
  "one actual neutral hit, outside range and lateral sidestep both miss")
 return "073 actual 0.60s straight warning and one neutral-only hit inside its six-stud lane"
end

function growthCases.rune073_stage_budget()
 local s=start("BOLT")
 local at,rows=setup(s,3)
 local x=Vector3.new(1,0,0)
 local steps={Vector3.zero,Vector3.new(0,0,1),Vector3.new(1,0,1),x}
 local horde=s.world:FindFirstChild("NeutralHorde")
 for i=1,590 do
  if player:GetAttribute("EGGRUMBLE_RoleAbilityStage")==1 then break end
  local step=at+steps[(i-1)%4+1]
  rootPart.CFrame=CFrame.lookAt(step,step+x)
  advanceTo(now+.39)
  for _,unit in ipairs(horde:GetChildren()) do
   if unit:FindFirstChildOfClass("Humanoid") and unit.PrimaryPart then
    unit:SetAttribute("EGGRUMBLE_NeutralSpeed",0)
    unit:PivotTo(CFrame.new(at+Vector3.new(-55,8,25)))
   end
  end
 end
 rootPart.CFrame=CFrame.lookAt(at,at+x)
 check(s.swarm.getRoleGrowthSnapshot(player).stage==1,"actual match movement unlocked two authorized contacts")
 place(rows[1],at+Vector3.new(3.25,.8,0));place(rows[2],at+Vector3.new(5.2,.8,0))
 place(rows[3],at+Vector3.new(6.3,.8,0))
 local t=now
 activate(player,"C")
 check(energy(s)==65 and cue(s,"073","Tell").Size.Z==8,"one original debit and real S1 warning geometry")
 advanceTo(t+.605)
 check(rows[1].h.Health==91 and rows[2].h.Health==91 and rows[3].h.Health==96,
  "two live HP contacts share exactly 10 in one whole-cast budget, inside the cap: "
  ..rows[1].h.Health.." / "..rows[2].h.Health.." / "..rows[3].h.Health)
 return "073 actual S1 two neutral hits share one 10 HP base budget, with a third unit excluded"
end

function growthCases.rune097_pillar()
 local s=start("BOLT")
 local at,rows=setup(s,3)
 place(rows[1],at+Vector3.new(5.2,0,.2),5)
 place(rows[2],at+Vector3.new(6.2,0,0))
 place(rows[3],at+Vector3.new(7.1,0,0))
 local t=now
 local ko=s.swarm.getTotal()
 activate(player,"D")
 check(energy(s)==60 and cue(s,"097","Tell").Size.Y==4 and not cue(s,"097","Impact"),"real S0 floor impact warning")
 advanceTo(t+.999)
 check(rows[1].h.Health==5 and not cue(s,"097","Impact"),"one second before damage")
 advanceTo(t+1.003)
 check(rows[1].h.Health==0 and rows[2].h.Health==96 and rows[3].h.Health==96 and cue(s,"097","Impact")
  and s.swarm.getTotal()==ko+1,"original one KO and no other target inside/outside cap")
 return "097 actual 1s floor warning, one original neutral KO and no second damage or scoring path"
end

function growthCases.rune_late_wall()
 local s=start("BOLT")
 local at,rows=setup(s,1)
 place(rows[1],at+Vector3.new(5.2,0,0))
 activate(player,"D")
 check(cue(s,"097","Tell"),"genuinely admitted floor impact")
 advanceTo(now+.2)
 wall(s,at+Vector3.new(2.1,0,0))
 advanceTo(now+.804)
 check(rows[1].h.Health==96 and not cue(s,"097","Impact") and not cue(s,"097","Tell"),"late solid geometry cancels the reserved impact")
 return "late solid terrain blocks the warned existing HP path"
end

function growthCases.rune_bolt_wall()
 local s=start("BOLT")
 local at,rows=setup(s,1)
 place(rows[1],at+Vector3.new(4.9,.8,0))
 wall(s,at+Vector3.new(2.3,0,0))
 activate(player,"B")
 check(cue(s,"072","Bolt"),"real missile before wall")
 advanceTo(now+.26)
 check(rows[1].h.Health==96 and not cue(s,"072","Bolt"),"solid interception consumes projectile without HP change")
 return "072 authoritative wall collision removes the real projectile and preserves blocked HP"
end

local function retire(kind)
 local s=start("BOLT")
 local at,rows=setup(s,1)
 place(rows[1],at+Vector3.new(5.2,0,0))
 activate(player,"D")
 check(cue(s,"097","Tell"),"genuine pending pillar")
 local stale=tools().D
 if kind=="off" then
  workspace:SetAttribute(FLAG,false);drainDeferred();old(tools())
  check(not stale.Parent,"stale owned D was retired")
  stale.Activated:Fire()
 elseif kind=="avatar" then
  local new=Instance.new("Model")
  local root=Instance.new("Part");root.Name="HumanoidRootPart";root.CFrame=rootPart.CFrame;root.Parent=new
  local h=Instance.new("Humanoid");h.Parent=new;new.PrimaryPart=root;new.Parent=workspace
  player.CharacterRemoving:Fire(character);player.Character=new
 elseif kind=="egg" then
  s.rules.castles[tostring(player.UserId)].heldEggs=1
 elseif kind=="round" then
  s.rules.phase="FINISHED";s.world:SetAttribute("EGGRUMBLE_MatchPhase","FINISHED");drainDeferred()
 end
 advanceTo(now+1.005)
 check(rows[1].h.Health==96 and not cue(s,"097","Impact") and not cue(s,"097","Tell"),"stale or ineligible command never reaches HP")
 return "pending rune cancels for "..kind
end
for _,kind in ipairs({"off","avatar","egg","round"}) do growthCases["rune_retire_"..kind]=function()return retire(kind)end end

function growthCases.rune_switch()
 local stand=scenes:FindFirstChild("ROLE_ZOMBIE")
 trigger(player,stand,"職業選択")
 trigger(player,stand,"符術を装備")
 check(player:GetAttribute(LABEL)=="印札三技","real selected MARK")
 trigger(player,stand,"装備する")
 check(player:GetAttribute(LABEL)=="転向援符・冥軍指揮・冥軍転向令","original selection still useable")
 advanceTo(now+.52)
 trigger(player,stand,"符術を装備")
 check(player:GetAttribute(LABEL)=="印札三技","old choice returns to MARK")
 workspace:SetAttribute("P0D_ENABLE_PRIVATE_ZOMBIE_COMBO_019",false);drainDeferred()
 check(player:GetAttribute(LABEL)=="印札三技","independent old flag preserves current new offer")
 advanceTo(now+.52);trigger(player,stand,"符術を装備")
 check(player:GetAttribute(LABEL)=="霊撃三技","BOLT cycle retained")
 advanceTo(now+.52);trigger(player,stand,"符術を装備")
 check(player:GetAttribute(LABEL)==nil,"standard remains reachable")
 start(nil)
 return "physical G cycles MARK, BOLT and standard while the existing F conversion stays independent"
end

function growthCases.rune_physical_off()
 local s=start(nil)
 check(not s.zombieRuneLoadouts,"physical OFF has no added offer or deck table")
 check(not s.castleModels[tostring(player.UserId)].model:FindFirstChild("EGGRUMBLE_ZombieRune"),"existing authoritative match intact")
 return "exact physical #1059 parent retains existing ZOMBIE A/B/C and existing selection"
end
end
