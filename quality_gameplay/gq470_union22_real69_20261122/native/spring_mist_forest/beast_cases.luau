-- Runs inside the original Beast maneuvers fixture's lexical scope only.
local ELEMENT_FLAG="P0D_ENABLE_PRIVATE_BEAST_ELEMENTS"
local E_DECK={A="BEAST-061",C="BEAST-062",D="BEAST-067"}
local function elemental()
 local stand=scenes:FindFirstChild("ROLE_BEAST")
 trigger(player,stand,"職業選択")
 trigger(player,stand,"獣技を装備")
 check(player:GetAttribute(LABEL)=="火尾竜・長首竜・雷羽鳥","original J first selection survives")
 advanceTo(now+.55)
 trigger(player,stand,"獣技を装備")
 check(player:GetAttribute(LABEL)=="火狐・氷狸・雷鼬","second physical J selects three fixed element skills")
 local s=ready("PRIVATE_BEAST_ELEMENTS","BEAST")
 check(s.beastManeuverLoadouts[player.UserId]=="ELEMENTS" and tool("B").Name=="技B・巨獣餌","one real frozen deck keeps B")
 for slot,id in pairs(E_DECK) do
  check(tool(slot):GetAttribute("EGGRUMBLE_FixedAbilityId")==id,"exact available "..id)
 end
 spawnCurrentNeutral(s)
 local area=s.world:FindFirstChild("TacticalBattlefield")
 local floor=area.Position+Vector3.new(170,area.Size.Y*.5,-115)
 local p=floor+Vector3.new(-5,3,0)
 rootPart.CFrame=CFrame.lookAt(p,p+DIR)
 secondRoot.CFrame=CFrame.new(floor+Vector3.new(58,3,-26))
 humanoid.Sit=false;humanoid.PlatformStand=false;humanoid.FloorMaterial=Enum.Material.Grass
 return s,floor,p
end
local function cue(s,slot)
 return s.world:FindFirstChild("EGGRUMBLE_BeastManeuver_"..E_DECK[slot])
end
local function startCast(s,slot,fee)
 local start=now
 local before=state(s).energy
 activate(player,slot)
 local sig=player:GetAttribute("EGGRUMBLE_SkillCastSignature")
 check(sig and sig:match("^BEAST:"..slot..":") and cue(s,slot),"real physical ability accepted")
 equal(state(s).energy,before-fee,"one registered Growth debit")
 activate(player,slot)
 check(player:GetAttribute("EGGRUMBLE_SkillCastSignature")==sig,"same pending command never repeats")
 equal(state(s).energy,before-fee,"no duplicate resource loss")
 return start
end

function growthCases.beast_061_ember()
 local s,floor=elemental()
 local rows=roster(s,floor,3)
 local original=summon(s,floor)
 place(rows[1],floor,2.1,0,"BABY_GOLEM")
 place(rows[2],floor,3.55,.25,"ICE_SLIME")
 place(rows[3],floor,4.65,0)
 local t=startCast(s,"A",30)
 advanceTo(t+.269)
 check(not rows[2].model:FindFirstChild("EGGRUMBLE_Ember") and rows[2].h.Health==96,"no effect before whole warning")
 advanceTo(t+.271)
 check(rows[2].model:FindFirstChild("EGGRUMBLE_Ember") and rows[2].h.Health==96,
  "same original neutral status registry, no unrequested direct strike")
 check(not rows[1].model:FindFirstChild("EGGRUMBLE_Ember") and not rows[3].model:FindFirstChild("EGGRUMBLE_Ember"),
  "immune stone skipped; one remaining approved target only")
 advanceTo(t+1.30)
 check(rows[2].h.Health>=89 and rows[2].h.Health<96 and rows[1].h.Health==96 and rows[3].h.Health==96,
  "shared HP owner genuinely burns ice within seven damage and no collateral")
 advanceTo(t+1.55)
 check(witness(s)==original and not rows[2].model:FindFirstChild("EGGRUMBLE_Ember"),
  "finite status disappears without a second escort")
 return "one real existing B fox-tagged effect burns one eligible neutral without direct HP; stone resistance and expiry preserved"
end

function growthCases.beast_062_frost()
 local s,floor=elemental()
 local rows=roster(s,floor,2)
 summon(s,floor)
 place(rows[1],floor,2.3,0,"ICE_SLIME")
 place(rows[2],floor,3.5,0)
 local t=startCast(s,"C",30)
 advanceTo(t+.291)
 local h=rows[2].h
 check(not rows[1].model:FindFirstChild("EGGRUMBLE_Frost") and rows[2].model:FindFirstChild("EGGRUMBLE_Frost")
   and h.Health==96,"one exact eligible neutral receives slow; ice resisted and no HP inflicted")
 local before=rows[2].model.PrimaryPart.Position
 rows[2].model:SetAttribute("EGGRUMBLE_NeutralSpeed",6)
 local step=0
 for _=1,28 do
  advanceTo(now+.015)
  step=(before-rows[2].model.PrimaryPart.Position).Magnitude
  if step>.03 then break end
 end
 check(math.abs(step-(6*.90*.38))<.035,"original Horde patrol step has actual ten per cent slow: "..step)
 advanceTo(t+1.1)
 check(not rows[2].model:FindFirstChild("EGGRUMBLE_Frost"),"fixed .6 S0 pause does not outlive shared status update")
 return "actual neutral patrol displacement reduced from 2.28 to 2.052 studs; ice resistance and no HP preserved"
end

function growthCases.beast_067_chain_s0()
 local s,floor=elemental()
 local rows=roster(s,floor,2)
 local original=summon(s,floor)
 place(rows[1],floor,1.90,0,"BABY_GOLEM")
 place(rows[2],floor,3.45,0)
 local t=startCast(s,"D",40)
 advanceTo(t+.379)
 check(rows[1].h.Health==96 and rows[2].h.Health==96,"no live chain before fixed warning")
 advanceTo(t+.381)
 check(rows[1].h.Health==86 and rows[2].h.Health==96 and witness(s)==original
  and s.world:FindFirstChild("EGGRUMBLE_BeastChainContact"),"one actual resisted S0 link")
 return "real S0 one distinct link uses existing 10 resisted HP and one visible receipt; another creature untouched"
end

function growthCases.beast_067_chain_s1()
 local s,floor,origin=elemental()
 local deltas={Vector3.zero,Vector3.new(1,0,0),Vector3.new(1,0,1),Vector3.new(0,0,1)}
 for i=1,175 do
  if player:GetAttribute("EGGRUMBLE_RoleAbilityStage")==1 then break end
  local at=origin+deltas[(i-1)%#deltas+1]
  rootPart.CFrame=CFrame.lookAt(at,at+DIR)
  advanceTo(now+.39)
  for _,mob in ipairs(s.world:FindFirstChild("NeutralHorde"):GetChildren()) do
   if mob:FindFirstChildOfClass("Humanoid") and mob.PrimaryPart then
    mob:SetAttribute("EGGRUMBLE_NeutralSpeed",0)
    mob:PivotTo(CFrame.new(floor+Vector3.new(-35,3,29)))
   end
  end
 end
 equal(state(s).stage,1,"actual active time evolves current attack")
 rootPart.CFrame=CFrame.lookAt(origin,origin+DIR)
 local rows=roster(s,floor,4)
 summon(s,floor)
 place(rows[1],floor,2.1,0)
 place(rows[2],floor,4.6,0)
 place(rows[3],floor,4.05,2.55)
 place(rows[4],floor,6.35,2.45)
 local block=wall(s,floor+Vector3.new(3.52,3,0))
 block.Size=Vector3.new(.35,8,1.25)
 local t=startCast(s,"D",40)
 advanceTo(t+.381)
 check(rows[1].h.Health==83 and rows[2].h.Health==96 and rows[3].h.Health==83 and rows[4].h.Health==96,
  "two actual unique links, late blocked previous-target ray skipped, lateral branch accepted, cap two")
 return "live role S1 two legal links from distinct points; shielded closest and excess targets remain unharmed"
end

function growthCases.beast_elements_cancel()
 local s,floor=elemental()
 local rows=roster(s,floor,1)
 activate(player,"A")
 check(state(s).energy==100 and not cue(s,"A"),"no owned B actor denies before E")
 local original=summon(s,floor)
 original:FindFirstChildOfClass("Humanoid").FloorMaterial=Enum.Material.Water
 activate(player,"A")
 check(state(s).energy==100 and not cue(s,"A"),"wrong ground denies before E")
 original:FindFirstChildOfClass("Humanoid").FloorMaterial=Enum.Material.Grass
 place(rows[1],floor,3.6,0)
 local t=startCast(s,"A",30)
 advanceTo(t+.271)
 check(rows[1].model:FindFirstChild("EGGRUMBLE_Ember"),"real status running before source retires")
 original:Destroy()
 advanceTo(t+.66)
 check(not rows[1].model:FindFirstChild("EGGRUMBLE_Ember") and rows[1].h.Health==96,
  "retired owned beast revokes status before real damage tick")
 return "unowned or water-bound escort costs zero; retirement of exact B creature cancels real pending status and HP"
end

function growthCases.beast_elements_live_off()
 local s,floor=elemental()
 local rows=roster(s,floor,1)
 local beast=summon(s,floor)
 -- Placement remains within Fire Fox range and outside the resumed original
 -- four-stud B contact, so an ordinary escort hit cannot mask stale effects.
 place(rows[1],floor,4.65,0)
 workspace:SetAttribute(KEY,false)
 check(tool("A"):GetAttribute("EGGRUMBLE_FixedAbilityId")=="BEAST-061","older own switch is independent")
 local stale=tool("A")
 local t=startCast(s,"A",30)
 workspace:SetAttribute(ELEMENT_FLAG,false)
 check(not cue(s,"A") and not stale.Parent,"own flag cancels pending cue and equipped owner tool")
 standard()
 advanceTo(t+.65)
 check(witness(s)==beast and rows[1].h.Health==96 and not rows[1].model:FindFirstChild("EGGRUMBLE_Ember"),
  "old exact escort survives unchanged and stale cast does nothing")
 return "the original switch cannot revoke element kit; correct OFF clears cue and tool and restores original A/B/C"
end

function growthCases.beast_elements_physical_off()
 local stand=scenes:FindFirstChild("ROLE_BEAST")
 trigger(player,stand,"職業選択")
 trigger(player,stand,"獣技を装備")
 check(player:GetAttribute(LABEL)=="火尾竜・長首竜・雷羽鳥","physical parent has only original selectable attack kit")
 advanceTo(now+.55)
 trigger(player,stand,"獣技を装備")
 check(player:GetAttribute(LABEL)==nil,"original second action clears instead of new kit")
 ready("PRIVATE_BEAST_ELEMENTS_OFF","BEAST")
 standard()
 return "exact ancestor keeps original single optional deck and existing normal skill selection on second interaction"
end
