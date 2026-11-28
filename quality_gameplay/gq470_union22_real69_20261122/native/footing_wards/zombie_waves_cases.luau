local WAVE_FLAG="P0D_ENABLE_PRIVATE_ZOMBIE_WAVES"
local function startWave()
 local stand=scenes:FindFirstChild("ROLE_ZOMBIE")
 trigger(player,stand,"職業選択")
 trigger(player,stand,"魂術を装備")
 check(workspace:GetAttribute(WAVE_FLAG)==nil and player:GetAttribute(LABEL)=="魂矢・三門呪","optional real J/Zombie role offer")
 local s=ready("PRIVATE_ZOMBIE_WAVES","ZOMBIE")
 local t=tools()
 check(s.zombieRuneLoadouts[player.UserId]=="WAVES" and not s.zombieConversionLoadouts[player.UserId],
  "one real wave kit sampled on entry")
 check(t.A.Name=="技A・呪印波動" and not t.D and
  t.B:GetAttribute("EGGRUMBLE_FixedAbilityId")=="ZOMBIE-093" and
  t.C:GetAttribute("EGGRUMBLE_FixedAbilityId")=="ZOMBIE-098","B/C exact with original A and no extra D")
 return s
end

local function tells(s,id)
 local result={}
 for _,object in ipairs(s.world:GetChildren()) do
  if object.Name=="EGGRUMBLE_ZombieRune_ZOMBIE-"..id.."_Tell" then table.insert(result,object) end
 end
 return result
end

function growthCases.wave093()
 local s=startWave()
 local at,rows=setup(s,2)
 place(rows[1],at+Vector3.new(4,.8,0));place(rows[2],at+Vector3.new(6,.8,0))
 local t=now
 activate(player,"B")
 local indicator=cue(s,"093","Tell")
 check(energy(s)==70 and indicator and indicator.Size.Z==7 and not cue(s,"093","Bolt"),"authored thin trajectory is telegraphed first")
 advanceTo(t+.299)
 check(cue(s,"093","Tell")==indicator and rows[1].h.Health==96 and rows[2].h.Health==96,"no early firing or HP")
 advanceTo(t+.315)
 local bolt=cue(s,"093","Bolt")
 check(bolt and bolt.Size.X==.12 and not bolt.CanQuery and not bolt.CanTouch and not cue(s,"093","Tell"),"physical narrow arrow enters the original moving projectile")
 advanceTo(t+.53)
 check(rows[1].h.Health==86 and rows[2].h.Health==96 and not cue(s,"093","Bolt"),"real single S0 hit through original HP and finite termination")
 return "093 straight warning and narrow real projectile hit one authorized neutral after .30s"
end

function growthCases.wave093_growth()
 local s=startWave()
 local at,rows=setup(s,3)
 local heading=Vector3.new(1,0,0)
 local steps={Vector3.zero,Vector3.new(0,0,1),Vector3.new(1,0,1),heading}
 local horde=s.world:FindFirstChild("NeutralHorde")
 for i=1,590 do
  if player:GetAttribute("EGGRUMBLE_RoleAbilityStage")==2 then break end
  local step=at+steps[(i-1)%4+1]
  rootPart.CFrame=CFrame.lookAt(step,step+heading)
  advanceTo(now+.39)
  for _,unit in ipairs(horde:GetChildren()) do
   if unit:FindFirstChildOfClass("Humanoid") and unit.PrimaryPart then
    unit:SetAttribute("EGGRUMBLE_NeutralSpeed",0)
    unit:PivotTo(CFrame.new(at+Vector3.new(-55,8,25)))
   end
  end
 end
 rootPart.CFrame=CFrame.lookAt(at,at+heading)
 check(s.swarm.getRoleGrowthSnapshot(player).stage==2,"actual match actions naturally unlocked S2")
 place(rows[1],at+Vector3.new(4,.8,0));place(rows[2],at+Vector3.new(8.6,.8,0));place(rows[3],at+Vector3.new(9.85,.8,0))
 local t=now
 activate(player,"B")
 check(energy(s)==70 and cue(s,"093","Tell").Size.Z==11,"authored S2 range and same E30")
 advanceTo(t+.62)
 check(rows[1].h.Health==86 and rows[2].h.Health==86 and rows[3].h.Health==96 and not cue(s,"093","Bolt"),
  "same S2 projectile can hit the two distinct legal contacts, stops before the third")
 return "093 live S2 uses eleven-stud geometry to hit two original neutral targets and exclude the third"
end

local function three(s,at,rows)
 place(rows[1],at+Vector3.new(3.8,.8,0))
 place(rows[2],at+Vector3.new(3.25,.8,-1.59))
 place(rows[3],at+Vector3.new(3.69,.8,1.80))
 place(rows[4],at+Vector3.new(5.5,.8,0))
 activate(player,"C")
 local shots=tells(s,"098")
 check(energy(s)==55 and #shots==3,"three visible lanes and one E45")
 local distinct={}
 for _,shot in ipairs(shots) do
  local a=shot.CFrame.LookVector
  distinct[math.floor(a.Z*100)]=true
  check(shot.Size.Z==5 and not shot.CanCollide and not shot.CanQuery and not shot.CanTouch,"each lane shows the authored real S0 range")
 end
 local count=0
 for _ in pairs(distinct) do count+=1 end
 check(count==3,"left, middle and right are distinct physical paths")
end

function growthCases.wave098()
 local s=startWave()
 local at,rows=setup(s,4)
 local t=now
 three(s,at,rows)
 activate(player,"C")
 check(energy(s)==55 and #tells(s,"098")==3,"same pending cast cannot replay or repay")
 advanceTo(t+.999)
 for _,row in ipairs(rows) do check(row.h.Health==96,"one full second before any HP") end
 advanceTo(t+1.003)
 check(#tells(s,"098")==0 and rows[1].h.Health==91 and rows[2].h.Health==91 and rows[3].h.Health==96 and rows[4].h.Health==96,
  "two safe lanes divide one actual 10HP budget, cap and range enforced")
 return "098 warns three actual directions for one second then splits 10 HP across only two distinct live targets"
end

function growthCases.wave098_wall()
 local s=startWave()
 local at,rows=setup(s,4)
 local t=now
 three(s,at,rows)
 local block=Instance.new("Part")
 block.CFrame=CFrame.new(at+Vector3.new(2.4,1,0))
 block.Size=Vector3.new(.24,5,.66);block.Anchored=true;block.CanCollide=true;block.CanQuery=true
 block.Parent=s.world
 advanceTo(t+1.003)
 check(rows[1].h.Health==96 and rows[2].h.Health==91 and rows[3].h.Health==91 and rows[4].h.Health==96,
  "late blocked center stays unharmed while legal side lanes share the same one budget")
 return "098 late wall limits each actual lane while the remaining legal lanes retain the one budget"
end

function growthCases.wave_independent_off()
 local s=startWave()
 workspace:SetAttribute(FLAG,false);drainDeferred()
 check(s.zombieRuneLoadouts[player.UserId]=="WAVES" and tools().C:GetAttribute("EGGRUMBLE_FixedAbilityId")=="ZOMBIE-098",
  "old G rune OFF does not retire another chosen J kit")
 local at,rows=setup(s,1)
 place(rows[1],at+Vector3.new(4,.8,0))
 activate(player,"B")
 check(cue(s,"093","Tell"),"real pending 093")
 local stale=tools().B
 workspace:SetAttribute(WAVE_FLAG,false);drainDeferred();old(tools())
 check(not stale.Parent and not s.zombieRuneLoadouts[player.UserId] and not player:GetAttribute(LABEL),"true runtime OFF restores real standard")
 stale.Activated:Fire()
 advanceTo(now+.55)
 check(rows[1].h.Health==96 and not cue(s,"093","Bolt") and not cue(s,"093","Tell"),"old Tool never recreates delayed shot")
 return "separate J OFF cancels pending damage and restores standard even with old G OFF"
end

function growthCases.wave_physical_off()
 local s=start("BOLT")
 local stand=scenes:FindFirstChild("ROLE_ZOMBIE")
 for _,item in ipairs(stand:GetChildren()) do
  check(not item:IsA("ProximityPrompt") or item.ActionText~="魂術を装備","physical parent has no additional offer")
 end
 check(tools().B:GetAttribute("EGGRUMBLE_FixedAbilityId")=="ZOMBIE-072","original rune bolt remains equipped")
 return "exact physical predecessor keeps G rune loadout and no new J entry"
end
