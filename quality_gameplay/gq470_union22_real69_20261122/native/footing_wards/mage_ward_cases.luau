do
local FLAG="P0D_ENABLE_PRIVATE_MAGE_WIND_WARDS"
local DIR=Vector3.new(1,0,0)
local expected={A="MAGE-035",B="MAGE-042",C="MAGE-065",D="COMBO-006"}
local function tools()
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
local function standard()
 local deck=tools()
 check(deck.A.Name=="技A・氷弾" and deck.B.Name=="技B・爆炎陣" and deck.C.Name=="技C・雷光治癒" and not deck.D,
  "original Mage tools")
end
local function start(optIn,secondRole)
 local stand=scenes:FindFirstChild("ROLE_MAGE")
 trigger(player,stand,"職業選択")
 if optIn then trigger(player,stand,"風盾を装備") end
 local live=ready("PRIVATE_MAGE_WIND_WARDS","MAGE",secondRole)
 if optIn then
  check(player:GetAttribute("EGGRUMBLE_LobbyMageProjectileName")=="風壁と光盾","authorized Host slot selection")
  for slot,id in pairs(expected) do check(tools()[slot]:GetAttribute("EGGRUMBLE_FixedAbilityId")==id,"exact Tool "..id) end
 else standard() end
 local field=live.world:FindFirstChild("TacticalBattlefield")
 local floor=field.Position+Vector3.new(170,field.Size.Y*.5,-115)
 local origin=floor+Vector3.new(0,3,0)
 rootPart.CFrame=CFrame.lookAt(origin,origin+DIR)
 humanoid.FloorMaterial=Enum.Material.Grass;humanoid.Sit=false;humanoid.PlatformStand=false
 return live,floor,origin
end
local function energy(live) return live.swarm.getRoleGrowthSnapshot(player).energy end
local function cue(live,kind) return live.world:FindFirstChild("EGGRUMBLE_MageWard_"..kind) end
local function bolt(live) return live.world:FindFirstChild("EGGRUMBLE_CastleMageBolt") end
local function wall(live,where)
 local part=Instance.new("Part");part.Name="WardNativeObstruction"
 part.Size=Vector3.new(.35,7,8);part.CFrame=CFrame.new(where);part.Anchored=true;part.CanCollide=true;part.CanQuery=true;part.Parent=live.world
 return part
end
local function near(a,b) return math.abs(a-b)<.02 end
local function cast(live,slot,cost)
 check(live.swarm.getRoleGrowthSnapshot(player).stage==0,"fresh actual match growth")
 equal(energy(live),100,"full canonical charge before action")
 local start=now
 activate(player,slot)
 local signature=player:GetAttribute("EGGRUMBLE_SkillCastSignature")
 check(signature and signature:match("^MAGE:"..slot..":"),"server accepted exact equipped Tool")
 equal(energy(live),100-cost,"one canonical energy debit")
 activate(player,slot)
 check(player:GetAttribute("EGGRUMBLE_SkillCastSignature")==signature,"immediate duplicate did not accept")
 equal(energy(live),100-cost,"same actor cannot double debit")
 return start,signature
end
local function guardian(live)
 local door=live.castleModels["43"].door
 for _=1,10 do
  advanceTo(now+3)
  trigger(player,door,"攻城攻撃")
  outsideField(live)
 end
 equal(live.castleSiegeStates["43"].gateHP,0,"actual siege gate")
 equal(live.rules.castles["43"].hp,700,"same castle HP/guardian threshold")
 local model=live.world:FindFirstChild("Guardian_ICE_MAGE")
 check(model and model:GetAttribute("EGGRUMBLE_GuardianOwner")=="43","actual hostile Mage-role castle guardian")
 equal(model:FindFirstChildOfClass("Humanoid").Health,70,"unchanged Mage guardian starting HP")
 -- Original nextAttack=spawn+1.6. Let the real tick become ready while both actors are away.
 advanceTo(now+1.8)
 return model
end
local function placeShot(live,model,origin,distance)
 model:PivotTo(CFrame.new(origin+DIR*distance))
 rootPart.CFrame=CFrame.lookAt(origin,origin+DIR)
 secondRoot.CFrame=CFrame.new(origin+Vector3.new(70,5,70))
 local regroup=origin+Vector3.new(-55,0,60)
 for _,neutral in ipairs(live.world:FindFirstChild("NeutralHorde"):GetChildren()) do
  if neutral.PrimaryPart then
   neutral:SetAttribute("EGGRUMBLE_NeutralSpeed",0)
   neutral:PivotTo(CFrame.new(regroup))
  end
 end
 humanoid.Health=100
end
local function waitBolt(live)
 for _=1,12 do
  if bolt(live) then return now end
  advanceTo(now+.035)
 end
 check(false,"actual launched Ice Mage bolt")
end
local function hostile(live,where,side)
 local at=where+DIR*(side and -20 or 20)
 secondRoot.CFrame=CFrame.lookAt(at,where)
 local before=humanoid.Health
 activate(second,"A")
 return before-humanoid.Health
end
local function neutral(live,floor)
 local mob=spawnCurrentNeutral(live)
 for _,model in ipairs(live.world:FindFirstChild("NeutralHorde"):GetChildren()) do
  if model.PrimaryPart then
   model:SetAttribute("EGGRUMBLE_NeutralSpeed",0)
   model:PivotTo(CFrame.new(floor+Vector3.new(-39,2,35)))
  end
 end
 check(mob and mob.PrimaryPart,"actual same-round Swarm actor")
 mob:SetAttribute("EGGRUMBLE_NeutralSpecies","ICE_SLIME")
 mob.PrimaryPart.Size=Vector3.new(.65,2.5,.65)
 mob:PivotTo(CFrame.new(floor+Vector3.new(7.85,2,1.08)))
 local hp=mob:FindFirstChildOfClass("Humanoid")
 hp.Health=150
 return mob,hp
end

function growthCases.ward_membrane()
 local live,_,origin=start(true)
 cast(live,"B",30)
 check(cue(live,"MEMBRANE"),"real front ward preview")
 check(near(hostile(live,origin,false),44*.94),"actual front Player skill mitigated by 6%")
 check(not cue(live,"MEMBRANE"),"one contact consumes ward")
 return "real hostile Warrior skill takes 41.36 HP; one-hit membrane removed"
end

function growthCases.ward_light()
 local live,_,origin=start(true)
 local t=cast(live,"C",35)
 check(near(hostile(live,origin,true),44),"rear hit stays full and leaves ward")
 check(cue(live,"LIGHT"),"rear did not consume stance")
 advanceTo(t+1.001)
 check(not cue(live,"LIGHT"),"exact S0 expiry without eligible contact")
 advanceTo(t+2.71)
 check(near(hostile(live,origin,false),44),"expired light shield no longer mitigates front attack")
 return "actual rear and expired attacks take full HP; S0 Light cleanup at 1.0s"
end

function growthCases.ward_light_hit()
 local live,_,origin=start(true)
 cast(live,"C",35)
 check(near(hostile(live,origin,false),44*.92) and not cue(live,"LIGHT"),"actual Light front takes 40.48 HP once")
 return "actual hostile Warrior skill takes 40.48 HP; one-hit Light shield removed"
end

function growthCases.ward_wind_excludes_melee()
 local live,_,origin=start(true)
 cast(live,"A",40)
 check(near(hostile(live,origin,false),44),"actual immediate melee/skill route is no leap-tagged bolt")
 check(cue(live,"WIND"),"unrelated hostile impact did not consume Wind Ward")
 return "real 44 HP non-flight attack leaves wind active; no category spoofing"
end

function growthCases.ward_guardian_hit()
 local live,_,origin=start(true,"MAGE")
 local g=guardian(live)
 placeShot(live,g,origin,14)
 local t=waitBolt(live)
 check(near(humanoid.Health,100),"no instantaneous damage on launch "..humanoid.Health)
 cast(live,"A",40)
 advanceTo(t+.26)
 check(bolt(live) and near(humanoid.Health,100),"flight across actual time")
 advanceTo(t+.69)
 check(near(humanoid.Health,100-6*.94) and not bolt(live) and not cue(live,"WIND"),
  "actual Guardian bolt consumes front Wind ward")
 advanceTo(t+1)
 check(near(humanoid.Health,100-6*.94),"at most one HP write before old period")
 return "10 siege prompts create actual Ice Mage guardian; one swept front bolt deals 5.64 HP, old period holds"
end

function growthCases.ward_guardian_dodge()
 local live,_,origin=start(false,"MAGE")
 local g=guardian(live)
 placeShot(live,g,origin,14)
 local t=waitBolt(live)
 local at=origin+Vector3.new(0,0,3.5)
 rootPart.CFrame=CFrame.lookAt(at,at+DIR)
 advanceTo(t+1)
 check(near(humanoid.Health,100) and not bolt(live),"lateral dodge avoids non-homing bolt "..humanoid.Health.." "..tostring(bolt(live)))
 return "same real targeted flight deals zero after lateral dodge and retires at the range bound"
end

function growthCases.ward_guardian_wall()
 local live,_,origin=start(false,"MAGE")
 local g=guardian(live)
 placeShot(live,g,origin,14)
 local t=waitBolt(live)
 wall(live,origin+DIR*.7)
 advanceTo(t+1)
 check(near(humanoid.Health,100) and not bolt(live),"late wall ahead of the true target wins before projected radius "..humanoid.Health.." "..tostring(bolt(live)))
 return "late wall added after actual Ice Mage launch cancels impact without HP writes"
end

function growthCases.ward_guardian_ally()
 local live,_,origin=start(false,"MAGE")
 local g=guardian(live)
 placeShot(live,g,origin,14)
 local t=waitBolt(live)
 local oldTeam=live.rules.castles["42"].team
 -- Simulate a changed real Rules allegiance between flight and contact.
 live.rules.castles["42"].team=live.rules.castles["43"].team
 advanceTo(t+.74)
 check(near(humanoid.Health,100) and not bolt(live),"same real ally predicate applies to in-flight impact "..humanoid.Health.." "..tostring(bolt(live)))
 live.rules.castles["42"].team=oldTeam
 return "actual enemy on launch and ally before contact does not receive damage"
end

function growthCases.ward_guardian_range()
 local live,_,origin=start(false,"MAGE")
 local g=guardian(live)
 placeShot(live,g,origin,19)
 advanceTo(now+.35)
 check(near(humanoid.Health,100) and not bolt(live),"original 17-stud acquisition bound")
 placeShot(live,g,origin,14)
 local t=waitBolt(live)
 local distant=origin-DIR*4.5
 rootPart.CFrame=CFrame.lookAt(distant,distant+DIR)
 advanceTo(t+1)
 check(near(humanoid.Health,100) and not bolt(live),"launched bolt stays in original range; no chasing")
 return "out-of-range target would not launch guardian bolt; in-flight target cannot be pursued beyond original 17 studs"
end

function growthCases.ward_combo()
 local live,floor,origin=start(true)
 local _,h=neutral(live,floor)
 rootPart.CFrame=CFrame.lookAt(origin,origin+DIR)
 local got
 local old=live.swarm.tryRoleGrowthCast
 live.swarm.tryRoleGrowthCast=function(p,role,cd,e,deadlines)
  got={role,cd,e,deadlines}
  return old(p,role,cd,e,deadlines)
 end
 local t=cast(live,"D",80)
 check(got[1]=="MAGE" and got[2]==40 and got[3]==80 and got[4]["MAGE-005"]==22
   and got[4]["MAGE-035"]==24 and got[4]["COMBO-006"]==40,"canonical component+combo deadlines")
 check(cue(live,"WIND") and h.Health==150,"actual guard established before flight")
 advanceTo(t+.17)
 check(not live.world:FindFirstChild("EGGRUMBLE_MAGE-005_Preview") and h.Health==150,"no premature offense")
 advanceTo(t+.21)
 check(live.world:FindFirstChild("EGGRUMBLE_MAGE-005_Preview") and h.Health==150,"existing pursuit preview precedes hit")
 advanceTo(t+.82)
 check(h.Health<150 and h.Health>0 and not live.world:FindFirstChild("EGGRUMBLE_MAGE-005_Preview"),"true pursued target HP write")
 local remaining=h.Health
 advanceTo(t+1)
 check(h.Health==remaining,"one actual existing projectile hit")
 return "one E80, all three shared deadlines; Wind arms, then actual same-world Swarm pursuit damages one tracked neutral"
end

function growthCases.ward_combo_wall()
 local live,floor,origin=start(true)
 local _,h=neutral(live,floor)
 rootPart.CFrame=CFrame.lookAt(origin,origin+DIR)
 local t=cast(live,"D",80)
 advanceTo(t+.215)
 wall(live,origin+DIR*3)
 advanceTo(t+.89)
 check(h.Health==150 and not cue(live,"WIND"),"occluded pursuit never records success; its pending ward retires")
 return "late solid blocker on actual pursuit leaves neutral HP intact and clears owned ward"
end

function growthCases.ward_combo_avatar()
 local live,floor,origin=start(true)
 local _,h=neutral(live,floor)
 rootPart.CFrame=CFrame.lookAt(origin,origin+DIR)
 local t=cast(live,"D",80)
 advanceTo(t+.21)
 check(live.world:FindFirstChild("EGGRUMBLE_MAGE-005_Preview"),"actual delayed flight began")
 player.CharacterRemoving:Fire(character)
 player.Character=Instance.new("Model")
 advanceTo(t+.9)
 check(h.Health==150 and not cue(live,"WIND") and not live.world:FindFirstChild("EGGRUMBLE_MAGE-005_Preview"),
  "replaced avatar owns no running guard or flight")
 return "old avatar ownership revoked after real flight starts; ward and projectile retire without HP"
end

function growthCases.ward_invalid_or_off()
 local live,_,origin=start(true)
 local original=tools().D
 player:SetAttribute("EGGRUMBLE_CarryingEgg",true)
 activate(player,"D")
 check(not cue(live,"WIND") and energy(live)==100,"carrying cannot authorize guard or debit")
 player:SetAttribute("EGGRUMBLE_CarryingEgg",nil)
 humanoid.FloorMaterial=Enum.Material.Air
 activate(player,"D")
 check(not cue(live,"WIND") and energy(live)==100,"air cannot authorize guard or debit")
 humanoid.FloorMaterial=Enum.Material.Grass
 rootPart.CFrame=CFrame.lookAt(origin,origin+DIR)
 local t=cast(live,"D",80)
 workspace:SetAttribute(FLAG,false)
 check(not cue(live,"WIND") and not original.Parent,"live OFF instantly retires guard and equipped Tool")
 standard()
 advanceTo(t+.82)
 check(not live.world:FindFirstChild("EGGRUMBLE_MAGE-005_Preview"),"live OFF cannot launch queued attack")
 return "no debit while carrying/airborne; observed physical live OFF removes queued combo, stance, and old Tool"
end

function growthCases.ward_physical_off()
 local stand=scenes:FindFirstChild("ROLE_MAGE")
 for _,item in ipairs(stand:GetChildren()) do
  check(not item:IsA("ProximityPrompt") or item.ActionText~="風盾を装備","base does not offer new loadout")
 end
 local live,_,origin=start(false,"MAGE")
 local g=guardian(live)
 placeShot(live,g,origin,14)
 advanceTo(now+.40)
 check(near(humanoid.Health,94) and not bolt(live),"actual physical OFF has old instantaneous 6 HP Guardian owner")
 return "ancestor 69 sources: original Mage tools, no ward or true-flight conversion; old 6 HP Guardian hit"
end
end
