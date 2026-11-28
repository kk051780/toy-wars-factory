do
local KEY="P0D_ENABLE_PRIVATE_BEAST_MANEUVERS"
local LABEL="EGGRUMBLE_LobbyBeastLoadoutName"
local ACTION="獣技を装備"
local DIR=Vector3.new(1,0,0)
local deck={A="BEAST-001",C="BEAST-007",D="BEAST-028"}
local function tool(slot)
 local result=nil
 for _,container in ipairs({player:FindFirstChildOfClass("Backpack"),player.Character}) do
  for _,item in ipairs(container:GetChildren()) do
   local internal=item:GetAttribute("EGGRUMBLE_InternalToolId")
   if type(internal)=="string" and internal:match("^EGGRUMBLE_SKILL_"..slot.."_") then
    check(not result,"one exact physical Tool");result=item
   end
  end
 end
 return result
end
local function standard()
 check(tool("A").Name=="技A・獣牙撃" and tool("B").Name=="技B・巨獣餌"
  and tool("C").Name=="技C・分裂餌" and not tool("D"),"original Beast deck")
end
local function begin(optIn)
 local stand=scenes:FindFirstChild("ROLE_BEAST")
 trigger(player,stand,"職業選択")
 if optIn then trigger(player,stand,ACTION) end
 local s=ready("PRIVATE_BEAST_MANEUVERS","BEAST")
 if optIn then
  check(player:GetAttribute(LABEL)=="火尾竜・長首竜・雷羽鳥","actual Host selection")
  for slot,id in pairs(deck) do check(tool(slot):GetAttribute("EGGRUMBLE_FixedAbilityId")==id,"exact "..slot.." Tool") end
  check(tool("B").Name=="技B・巨獣餌","original B summon preserved")
 else standard() end
 spawnCurrentNeutral(s)
 local area=s.world:FindFirstChild("TacticalBattlefield")
 local floor=area.Position+Vector3.new(170,area.Size.Y*.5,-115)
 local ownerAt=floor+Vector3.new(-5,3,0)
 rootPart.CFrame=CFrame.lookAt(ownerAt,ownerAt+DIR)
 secondRoot.CFrame=CFrame.new(floor+Vector3.new(55,3,-25))
 humanoid.Sit=false;humanoid.PlatformStand=false;humanoid.FloorMaterial=Enum.Material.Grass
 return s,floor,ownerAt
end
local function roster(s,floor,count)
 local rows={}
 for _=1,44 do
  table.clear(rows)
  for _,model in ipairs(s.world:FindFirstChild("NeutralHorde"):GetChildren()) do
   local h=model:FindFirstChildOfClass("Humanoid")
   if h and h.Health>0 and model.PrimaryPart then
    model:SetAttribute("EGGRUMBLE_NeutralSpeed",0)
    model:PivotTo(CFrame.new(floor+Vector3.new(-35,3,29)))
    table.insert(rows,{model=model,h=h})
   end
  end
  if #rows>=count then break end
  advanceTo(now+.27)
 end
 check(#rows>=count,"current alive authoritative Horde actors")
 return rows
end
local function witness(s)
 local beast=nil
 for _,m in ipairs(s.world:GetChildren()) do
  if m:GetAttribute("EGGRUMBLE_BeastCompanion")==true then
   check(not beast,"single permitted physical AI");beast=m
  end
 end
 return beast
end
local function summon(s,floor)
 activate(player,"B")
 local beast=witness(s)
 check(beast and beast:GetAttribute("EGGRUMBLE_OwnerId")==player.UserId,"existing B made exact owned real creature")
 local at=floor+Vector3.new(0,1.55,0)
 beast:PivotTo(CFrame.lookAt(at,at+DIR))
 beast:FindFirstChildOfClass("Humanoid").FloorMaterial=Enum.Material.Grass
 return beast
end
local function place(row,floor,x,z,species)
 row.model:PivotTo(CFrame.new(floor+Vector3.new(x,2.4,z)))
 row.model:SetAttribute("EGGRUMBLE_NeutralSpecies",species or "BANNER_KNIGHT")
 row.h.Health=96
end
local function prep(s,slot)
 return s.world:FindFirstChild("EGGRUMBLE_BeastManeuver_"..deck[slot])
end
local function state(s) return s.swarm.getRoleGrowthSnapshot(player) end
local function cast(s,slot,cost)
 local before=state(s).energy
 local t=now
 activate(player,slot)
 local sig=player:GetAttribute("EGGRUMBLE_SkillCastSignature")
 check(sig and sig:match("^BEAST:"..slot..":") and prep(s,slot),"real Tool accepted and visible attack shape")
 equal(state(s).energy,before-cost,"single canonical E debit")
 activate(player,slot)
 check(player:GetAttribute("EGGRUMBLE_SkillCastSignature")==sig,"no duplicate/id bypass at same time")
 equal(state(s).energy,before-cost,"same valid request yielded one charge")
 return t
end
local function wall(s,at)
 local p=Instance.new("Part");p.Name="ManeuverNativeWall";p.Anchored=true;p.CanQuery=true;p.CanCollide=true
 p.Size=Vector3.new(.35,8,7);p.CFrame=CFrame.new(at);p.Parent=s.world
 return p
end

function growthCases.beast001_maneuver()
 local s,floor=begin(true)
 local rows=roster(s,floor,4)
 local m=summon(s,floor)
 place(rows[1],floor,1.15,1.2,"ICE_SLIME")
 place(rows[2],floor,2.65,.15)
 place(rows[3],floor,-1.7,0)
 place(rows[4],floor,3.35,0)
 local t=cast(s,"A",35)
 advanceTo(t+.259)
 check(rows[1].h.Health==96 and #prep(s,"A"):GetChildren()==6,"actual tail fan holds before release")
 advanceTo(t+.261)
 check(rows[1].h.Health==80 and rows[2].h.Health==96 and rows[3].h.Health==96 and rows[4].h.Health==96,
  "one Fire/ICE real 16 HP; extra target, rear and exceeds radius stay unchanged")
 check(witness(s)==m and not prep(s,"A"),"one original AI and old follow returns")
 return "B original pet; fixed radius3 tail fan hits one eligible neutral for 16 HP after warning; extra/rear/far untouched"
end

function growthCases.beast007_maneuver()
 local s,floor=begin(true)
 local rows=roster(s,floor,3)
 local m=summon(s,floor)
 place(rows[1],floor,4.25,.12)
 place(rows[2],floor,2.35,1.2)
 place(rows[3],floor,5.4,0)
 local t=cast(s,"C",35)
 advanceTo(t+.299)
 check(rows[1].h.Health==96,"actual neck thrust has no early damage")
 advanceTo(t+.301)
 check(rows[1].h.Health==83 and rows[2].h.Health==96 and rows[3].h.Health==96,"one actual 13 HP in narrow 5-stud lane")
 check(witness(s)==m and not prep(s,"C"),"no second body or lingering pose")
 return "same grounded beast hits one exact neutral in 5-stud lance; lateral near target and outside range safe"
end

function growthCases.beast028_maneuver()
 local s,floor=begin(true)
 local rows=roster(s,floor,3)
 local m=summon(s,floor)
 place(rows[1],floor,5.75,.6,"BABY_GOLEM")
 place(rows[2],floor,6.8,.1)
 place(rows[3],floor,7.2,0)
 local t=cast(s,"D",40)
 advanceTo(t+.419)
 check(rows[1].h.Health==96 and prep(s,"D")~=nil,"warning before actual bolt")
 advanceTo(t+.421)
 check(rows[1].h.Health==86 and rows[2].h.Health==96 and rows[3].h.Health==96,
  "Lightning Earth's 20% resistance; one target limit and original x7 extent")
 check(witness(s)==m and not prep(s,"D"),"same original beast")
 return "Earth target takes authoritative resisted 10 HP after .42s; in-lane second and beyond 7stud remain safe"
end

function growthCases.beast028_maneuver_s4()
 local s,floor,origin=begin(true)
 local deltas={Vector3.zero,Vector3.new(1,0,0),Vector3.new(1,0,1),Vector3.new(0,0,1)}
 for frame=1,590 do
  if player:GetAttribute("EGGRUMBLE_RoleAbilityStage")==4 then break end
  local at=origin+deltas[(frame-1)%#deltas+1]
  rootPart.CFrame=CFrame.lookAt(at,at+DIR)
  advanceTo(now+.39)
  for _,model in ipairs(s.world:FindFirstChild("NeutralHorde"):GetChildren()) do
   if model:FindFirstChildOfClass("Humanoid") and model.PrimaryPart then
    model:SetAttribute("EGGRUMBLE_NeutralSpeed",0)
    model:PivotTo(CFrame.new(floor+Vector3.new(-35,3,29)))
   end
  end
 end
 equal(state(s).stage,4,"normal active progression reached exact S4")
 rootPart.CFrame=CFrame.lookAt(origin,origin+DIR)
 local rows=roster(s,floor,7)
 local m=summon(s,floor)
 for i=1,6 do place(rows[i],floor,8.2+i*.94,0) end
 place(rows[7],floor,15.35,0)
 local t=cast(s,"D",40)
 advanceTo(t+.421)
 for i=1,7 do equal(rows[i].h.Health,i<=5 and 83 or 96,"S4 five unique in-bound real HP targets "..i) end
 check(witness(s)==m,"high stage did not increase summon count")
 return "true active S4: five distinct old neutral HP writes inside 15 stud; sixth and farther excluded"
end

function growthCases.beast_maneuver_wall()
 local s,floor=begin(true)
 local rows=roster(s,floor,1)
 local m=summon(s,floor)
 place(rows[1],floor,4.3,0)
 local t=cast(s,"C",35)
 advanceTo(t+.23)
 wall(s,floor+Vector3.new(2.7,3,0))
 advanceTo(t+.301)
 check(rows[1].h.Health==96 and witness(s)==m and not prep(s,"C"),"solid wall added after cue wins")
 return "actual late world wall defeats unchanged canonical neutral HP"
end

function growthCases.beast_maneuver_denials()
 local s,floor=begin(true)
 local rows=roster(s,floor,1)
 activate(player,"D")
 check(not prep(s,"D") and state(s).energy==100,"no approved owned beast, no E")
 local pet=summon(s,floor)
 local h=pet:FindFirstChildOfClass("Humanoid")
 h.FloorMaterial=Enum.Material.Air
 activate(player,"D")
 check(not prep(s,"D") and state(s).energy==100,"airborne actual pet denied")
 h.FloorMaterial=Enum.Material.Grass
 player:SetAttribute("EGGRUMBLE_CarryingEgg",true)
 activate(player,"D")
 check(not prep(s,"D") and state(s).energy==100,"carrying egg denied")
 player:SetAttribute("EGGRUMBLE_CarryingEgg",nil)
 place(rows[1],floor,5.8,0)
 local t=cast(s,"D",40)
 player.CharacterRemoving:Fire(character)
 player.Character=Instance.new("Model")
 advanceTo(t+.63)
 check(not prep(s,"D") and rows[1].h.Health==96,"old avatar releases real cue and cannot apply delayed HP")
 return "no pet, air and egg leave energy unchanged; actual stale avatar after accepted warning produces no impact"
end

function growthCases.beast_maneuver_off()
 local s,floor=begin(true)
 local rows=roster(s,floor,1)
 local m=summon(s,floor)
 place(rows[1],floor,5.8,0)
 local stale=tool("D")
 local t=cast(s,"D",40)
 workspace:SetAttribute(KEY,false)
 check(not prep(s,"D") and not stale.Parent,"dynamic OFF cancels alert and obsolete tool")
 standard()
 advanceTo(t+.421)
 check(rows[1].h.Health==96 and m.Parent==s.world and witness(s)==m,"OFF does not replace the legacy escort or deal queued damage")
 return "rollback removes only new deck and its pending effect; old owned beast and original A/B/C retained"
end

function growthCases.beast_maneuver_switches()
 local stand=scenes:FindFirstChild("ROLE_BEAST")
 trigger(player,stand,"職業選択")
 trigger(player,stand,ACTION)
 trigger(player,stand,"月狼を装備")
 check(player:GetAttribute(LABEL)==nil and player:GetAttribute("EGGRUMBLE_LobbyBeastMoonLoadoutName")~=nil,"Moon replaces new deck")
 advanceTo(now+.55)
 trigger(player,stand,ACTION)
 workspace:SetAttribute("P0D_ENABLE_PRIVATE_BEAST_THUNDER",false)
 check(player:GetAttribute(LABEL)=="火尾竜・長首竜・雷羽鳥","legacy thunder OFF cannot erase current other deck")
 trigger(player,stand,"指令笛を装備")
 local s=ready("PRIVATE_BEAST_MANEUVERS_ORDERS","BEAST")
 check(not s.beastManeuverLoadouts[player.UserId] and s.beastOrderLoadouts[player.UserId]
  and tool("A"):GetAttribute("EGGRUMBLE_FixedAbilityId")=="BEAST-091",
  "same server freezes exactly one legal current deck")
 return "live offer changes preserve older Moon and Orders and one authoritative frozen deck"
end

function growthCases.beast_maneuver_physical_off()
 local stand=scenes:FindFirstChild("ROLE_BEAST")
 for _,p in ipairs(stand:GetChildren()) do check(not p:IsA("ProximityPrompt") or p.ActionText~=ACTION,"prior physical source has no new selection") end
 local s,floor=begin(false)
 check(summon(s,floor)~=nil,"real original B remains")
 return "actual ancestor: no new prompt, standard tools and same original B physical pet"
end
end
