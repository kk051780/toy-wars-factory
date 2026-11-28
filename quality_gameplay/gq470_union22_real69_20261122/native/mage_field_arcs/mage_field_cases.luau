do
local FLAG="P0D_ENABLE_PRIVATE_MAGE_FIELD_ARCS"
local rows={
 pursuit={id="MAGE-005",deck=1,slot="A",energy=35,tell=.16,kind="track"},
 firebird={id="MAGE-009",deck=1,slot="B",energy=40,tell=.35,kind="vertical"},
 comet={id="MAGE-079",deck=1,slot="C",energy=45,tell=.36,kind="lateral"},
 rain={id="MAGE-078",deck=1,slot="D",energy=45,tell=1,kind="ground",name="StarRain",limit=2},
 ice={id="MAGE-015",deck=2,slot="A",energy=40,tell=.8,kind="ground",name="IceSpire",limit=1},
 water={id="MAGE-047",deck=2,slot="B",energy=40,tell=.8,kind="ground",name="WaterPillar",limit=1},
 ring={id="MAGE-073",deck=2,slot="C",energy=35,tell=.65,kind="ground",name="StarRing",limit=2},
 sand={id="MAGE-083",deck=2,slot="D",energy=35,tell=.8,kind="ground",name="SandDischarge",limit=1},
}
local direction=Vector3.new(1,0,0)
local function tools()
 local result={}
 for _,folder in ipairs({player:FindFirstChildOfClass("Backpack"),player.Character}) do
  for _,item in ipairs(folder:GetChildren()) do
   local internal=item:GetAttribute("EGGRUMBLE_InternalToolId")
   local slot=type(internal)=="string" and internal:match("^EGGRUMBLE_SKILL_([ABCD])_")
   if slot then check(not result[slot],"one current actual Tool");result[slot]=item end
  end
 end
 return result
end
local function standard(deck)
 check(deck.A.Name=="技A・氷弾" and deck.B.Name=="技B・爆炎陣" and deck.C.Name=="技C・雷光治癒" and not deck.D,
  "existing standard Mage Tools returned")
end
local function start(row)
 local stand=scenes:FindFirstChild("ROLE_MAGE")
 trigger(player,stand,"職業選択")
 if row then
  for index=1,row.deck do
   trigger(player,stand,"野外術を装備")
   check(player:GetAttribute("EGGRUMBLE_LobbyMageProjectileName")== (if index==1 then "軌道四術" else "地の四術"),
    "actual server lobby selection")
   advanceTo(now+.51)
  end
 end
 local live=ready("PRIVATE_MAGE_FIELD")
 if row then
  local deck=tools()
  check(deck.D and deck[row.slot]:GetAttribute("EGGRUMBLE_FixedAbilityId")==row.id,"exact current match Tool")
 else standard(tools()) end
 local field=live.world:FindFirstChild("TacticalBattlefield")
 local floor=field.Position+Vector3.new(170,field.Size.Y*.5,-115)
 local origin=floor+Vector3.new(0,3,0)
 rootPart.CFrame=CFrame.lookAt(origin,origin+direction)
 humanoid.FloorMaterial=Enum.Material.Grass
 humanoid.Sit=false;humanoid.PlatformStand=false
 return live,floor
end
local function gather(live,floor,count)
 local found={}
 for _=1,48 do
  table.clear(found)
  for _,model in ipairs(live.world:FindFirstChild("NeutralHorde"):GetChildren()) do
   local hp=model:FindFirstChildOfClass("Humanoid")
   if hp and hp.Health>0 and model.PrimaryPart then
    model:SetAttribute("EGGRUMBLE_NeutralSpeed",0)
    model:PivotTo(CFrame.new(floor+Vector3.new(-39,2,35)))
    table.insert(found,{model=model,hp=hp})
   end
  end
  if #found>=count then break end
  advanceTo(now+.35)
 end
 check(#found>=count,"actual existing Swarm spawn roster")
 return found
end
local function position(actor,where,species)
 actor.model:PivotTo(CFrame.new(where))
 actor.hp.Health=150
 actor.model:SetAttribute("EGGRUMBLE_NeutralSpecies",species or "BANNER_KNIGHT")
end
local function wall(live,where,size)
 local p=Instance.new("Part")
 p.Name="TestSolidWorldObstruction"
 p.Anchored=true;p.CanCollide=true;p.CanQuery=true
 p.Size=size;p.CFrame=CFrame.new(where);p.Parent=live.world
 return p
end
local function effect(live,id)
 return live.world:FindFirstChild("EGGRUMBLE_"..id)
end
local function cast(live,row)
 local t=now
 activate(player,row.slot)
 local snapshot=live.swarm.getRoleGrowthSnapshot(player)
 check(snapshot and snapshot.energy==100-row.energy,"one canonical E debit per accepted "..row.id)
 local accepted=player:GetAttribute("EGGRUMBLE_SkillCastSignature")
 check(accepted and accepted:match("^MAGE:"..row.slot..":"),"real cast accepted marker")
 activate(player,row.slot)
 check(player:GetAttribute("EGGRUMBLE_SkillCastSignature")==accepted and live.swarm.getRoleGrowthSnapshot(player).energy==100-row.energy,
  "canonical per-ID cooldown rejects immediate duplicate")
 return t
end

local function flying(row)
 local live,floor=start(row)
 local mob=gather(live,floor,2)
 local target=mob[1]
 if row.kind=="track" then
  target.model.PrimaryPart.Size=Vector3.new(.65,2.5,.65)
  position(target,floor+Vector3.new(7.85,2,1.08),"ICE_SLIME")
  position(mob[2],floor+Vector3.new(8.75,2,1.3))
 elseif row.kind=="vertical" then
  position(target,floor+Vector3.new(4.9,2.2,0),"ICE_SLIME")
  position(mob[2],floor+Vector3.new(7.5,2,0))
 else
  position(target,floor+Vector3.new(4.8,2,2.05))
  position(mob[2],floor+Vector3.new(4.8,2,0))
 end
 local t=cast(live,row)
 local preview=effect(live,row.id.."_Preview")
 check(preview and #preview:GetChildren()>0,"real noninteractive path cue")
 if row.kind=="vertical" then
  check(preview:GetChildren()[7].Position.Y>floor.Y+2.9,"real upward arc forecast")
 elseif row.kind=="lateral" then
  check(preview:GetChildren()[7].Position.Z>floor.Z+1.8,"real lateral path forecast")
 end
 advanceTo(t+row.tell-.01)
 check(target.hp.Health==150 and mob[2].hp.Health==150,"no effect before cast warning")
 advanceTo(t+1.4)
 check(target.hp.Health==(if row.kind=="lateral" then 120 else 113) and mob[2].hp.Health==150,
  "live capsule hit follows "..row.kind.." lane, stage cap one and elemental damage")
 check(not preview.Parent and live.swarm.getTotal()==0,"resolved actual HP without fake KO")
 return row.id.." actual "..row.kind.." route to one current neutral"
end

local function ground(row)
 local live,floor=start(row)
 local mob=gather(live,floor,3)
 local center=floor+direction*(if row.name=="StarRing" then 0 else 8)
 local inside=center+Vector3.new(.32,2,.7)
 position(mob[1],inside,if row.name=="SandDischarge" then "BABY_GOLEM" else nil)
 position(mob[2],center+Vector3.new(.55,2,1.45))
 position(mob[3],center+Vector3.new(.9,2,-1.8))
 if row.name=="StarRain" then
  wall(live,inside+Vector3.new(0,6,0),Vector3.new(.5,.35,.5))
 end
 local t=cast(live,row)
 local tell=effect(live,row.name.."Tell")
 check(tell and not tell.CanQuery and not tell.CanCollide,"legal shared ground forecast")
 check((Vector3.new(tell.Position.X,center.Y,tell.Position.Z)-center).Magnitude<.02,"exact self/forward target point")
 advanceTo(t+row.tell-.001)
 check(mob[1].hp.Health==150 and mob[2].hp.Health==150 and mob[3].hp.Health==150,"one timed ground event")
 advanceTo(t+row.tell+.001)
 check(not tell.Parent and effect(live,row.name.."Impact"),"actual effect produces impact once")
 if row.name=="StarRain" then
  check(mob[1].hp.Health==150 and mob[2].hp.Health==120 and mob[3].hp.Health==120,
   "roof rejects its exact target, uncovered two get individual pulses")
 else
  local expected=if row.name=="SandDischarge" then 126 else 120
  check(mob[1].hp.Health==expected and mob[2].hp.Health==(if row.limit==2 then 120 else 150)
   and mob[3].hp.Health==150,"observed fixed target cap and correct element")
 end
 check((mob[1].model.PrimaryPart.Position-inside).Magnitude<.02 and live.swarm.getTotal()==0,
  "no S0 push, displacement or ghost KO")
 return row.id.." genuine settled neutral HP; one timed ground effect with exact S0 cap"
end
for key,row in pairs(rows) do
 growthCases["field_"..key]=function()
  return if row.kind=="ground" then ground(row) else flying(row)
 end
end

function growthCases.field_ice_s4()
 local row=rows.ice
 local live,floor=start(row)
 local base=floor+Vector3.new(0,3,0)
 local turns={Vector3.zero,Vector3.new(0,0,1),Vector3.new(1,0,1),Vector3.new(1,0,0)}
 for tick=1,600 do
  if player:GetAttribute("EGGRUMBLE_RoleAbilityStage")==4 then break end
  local at=base+turns[(tick-1)%4+1]
  rootPart.CFrame=CFrame.lookAt(at,at+direction)
  advanceTo(now+.39)
  for _,mob in ipairs(live.world:FindFirstChild("NeutralHorde"):GetChildren()) do
   if mob:FindFirstChildOfClass("Humanoid") then
    mob:SetAttribute("EGGRUMBLE_NeutralSpeed",0)
    mob:PivotTo(CFrame.new(floor+Vector3.new(-38,2,30)))
   end
  end
 end
 check(live.swarm.getRoleGrowthSnapshot(player).stage==4,"actual existing 180-active-second growth")
 rootPart.CFrame=CFrame.lookAt(base,base+direction)
 local mob=gather(live,floor,1)[1]
 local clearance=2*(mob.model.PrimaryPart.Size.Y/2.5)
 local at=floor+Vector3.new(16,clearance,.6)
 position(mob,at)
 local t=cast(live,row)
 check(effect(live,"IceSpireTell").Size.Y==12,"actual S4 radius6")
 advanceTo(t+.801)
 check(mob.hp.Health==120 and (mob.model.PrimaryPart.Position-at).Magnitude>=1.6
  and mob.model.PrimaryPart.Position.Z>at.Z,"actual S4 ice push through existing safe sweep")
 return "exact S4 by active-time movement gives one genuine pushed neutral"
end

local function denied(kind)
 local row=if kind=="carrier" or kind=="floor" then rows.ice elseif kind=="arc_wall" then rows.comet else rows.firebird
 local live,floor=start(row)
 local mob=gather(live,floor,1)[1]
 position(mob,floor+Vector3.new(4.9,2.2,if kind=="arc_wall" then 2.05 else 0))
 if kind=="carrier" then
  live.rules.castles[tostring(player.UserId)].heldEggs=1
 elseif kind=="floor" then
  humanoid.FloorMaterial=Enum.Material.Air
 end
 if kind=="carrier" or kind=="floor" then
  activate(player,row.slot)
  live.rules.castles[tostring(player.UserId)].heldEggs=0
  check(not effect(live,"IceSpireTell") and not player:GetAttribute("EGGRUMBLE_SkillCastSignature")
   and live.swarm.getRoleGrowthSnapshot(player).energy==100,"reject before Charge")
  return "unqualified old actor/ground carries no cost"
 end
 local t=cast(live,row)
 if kind=="arc_wall" then
  wall(live,floor+Vector3.new(2.5,3,1.3),Vector3.new(.22,7,5))
 elseif kind=="avatar" then
  player.CharacterRemoving:Fire(player.Character);player.Character=Instance.new("Model")
 elseif kind=="off" then
  workspace:SetAttribute(FLAG,false)
  drainDeferred()
  standard(tools())
 end
 advanceTo(t+1.42)
 check(mob.hp.Health==150 and not effect(live,row.id.."_Preview") and not effect(live,row.id),
  "cancellation or first physical obstacle prevents final HP and cleans up")
 return "live arc rechecks "..kind.." before each real contact"
end
for _,kind in ipairs({"arc_wall","carrier","floor","avatar","off"}) do
 growthCases["field_denied_"..kind]=function() return denied(kind) end
end
function growthCases.field_physical_off()
 start(nil)
 local stand=scenes:FindFirstChild("ROLE_MAGE")
 for _,p in ipairs(stand:GetChildren()) do
  check(not p:IsA("ProximityPrompt") or p.ActionText~="野外術を装備","physical ancestor lacks optional mode")
 end
 return "parent standard Mage restored in physically independent OFF"
end
end
