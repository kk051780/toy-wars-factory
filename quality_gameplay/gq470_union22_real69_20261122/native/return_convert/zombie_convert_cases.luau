do
local FLAG="P0D_ENABLE_PRIVATE_ZOMBIE_COMBO_019"
local function tools(actor)
 local result={}
 for _,folder in ipairs({actor:FindFirstChildOfClass("Backpack"),actor.Character}) do
  for _,tool in ipairs(folder:GetChildren()) do
   local id=tool:IsA("Tool") and tool:GetAttribute("EGGRUMBLE_InternalToolId")
   local slot=type(id)=="string" and id:match("^EGGRUMBLE_SKILL_([ABCD])_")
   if slot then check(not result[slot],"one server role Tool per slot");result[slot]=tool end
  end
 end
 return result
end
local function legacy(t)
 check(t.A.Name=="技A・呪印波動" and t.B.Name=="技B・疫病霧" and t.C.Name=="技C・不死軍団" and t.D==nil,
  "non-opt-in legacy A/B/C exact")
end
local function begin(equip,secondZombie)
 check(workspace:GetAttribute(FLAG)==nil,"physical candidate starts with no Studio attribute")
 local stand=scenes:FindFirstChild("ROLE_ZOMBIE")
 trigger(player,stand,"職業選択")
 if equip then
  trigger(player,stand,"装備する")
  check(player:GetAttribute("EGGRUMBLE_LobbyZombieLoadoutName")=="転向援符・冥軍指揮・冥軍転向令","real opt-in prompt")
 end
 trigger(second,scenes:FindFirstChild(if secondZombie then "ROLE_ZOMBIE" else "ROLE_WARRIOR"),"職業選択")
 trigger(player,scenes:FindFirstChild("TEAM_PORTAL"),"参加する")
 trigger(second,scenes:FindFirstChild("TEAM_PORTAL"),"参加する")
 advanceTo(now+12.01)
 local s=capturedSessions[#capturedSessions]
 check(s.isCurrentHuman(player) and s.rules.phase=="ACTIVE" and player:GetAttribute("EGGRUMBLE_Role")=="ZOMBIE","actual Host match")
 local t=tools(player)
 if equip then
  check(s.zombieConversionLoadouts[player.UserId] and t.A.Name=="技A・呪印波動","current avatar deck and existing A")
  check(t.B:GetAttribute("EGGRUMBLE_FixedAbilityId")=="ZOMBIE-035" and
   t.C:GetAttribute("EGGRUMBLE_FixedAbilityId")=="ZOMBIE-040" and
   t.D:GetAttribute("EGGRUMBLE_FixedAbilityId")=="COMBO-019","actual B/C/D fixed server Tools")
  check(not tools(second).D,"no other-avatar deck injection")
 else
  legacy(t)
 end
 return s
end
local function settle(s,need)
 local first=spawnCurrentNeutral(s)
 check(first,"existing spawn route")
 local floor=s.world:FindFirstChild("TacticalBattlefield")
 local center=floor.Position+Vector3.new(170,floor.Size.Y*.5+2,-115)
 local function move(actor,at)
  actor.CFrame=CFrame.lookAt(at,at+Vector3.new(1,0,0))
 end
 move(rootPart,center)
 secondRoot.CFrame=CFrame.new(center+Vector3.new(-65,0,0))
 local found={}
 for _=1,48 do
  found={}
  for _,m in ipairs(s.world:FindFirstChild("NeutralHorde"):GetChildren()) do
   local h=m:FindFirstChildOfClass("Humanoid")
   if h and h.Health>0 then
    m:SetAttribute("EGGRUMBLE_NeutralSpeed",0)
    m:PivotTo(CFrame.new(center+Vector3.new(-65,9,40)))
    table.insert(found,{m=m,h=h,accent=m:FindFirstChild("SpeciesAccent")})
   end
  end
  if #found>=need then break end
  advanceTo(now+.25)
 end
 check(#found>=need,"actual Swarm spawn population")
 advanceTo(now+.42)
 local g=s.swarm.getRoleGrowthSnapshot(player)
 check(g and g.stage==0 and g.energy==100,"actual eligible S0 role ledger")
 return found,center
end
local function place(row,center,x,z,health)
 local height=2*(row.m.PrimaryPart.Size.Y/2.5)
 local at=center+Vector3.new(x,height-2,z)
 row.m:PivotTo(CFrame.new(at))
 row.m:SetAttribute("EGGRUMBLE_NeutralSpecies","BANNER_KNIGHT")
 row.h.MaxHealth=80
 row.h.Health=health
 return at
end
local function energy(s)
 local g=s.swarm.getRoleGrowthSnapshot(player)
 return g and g.energy
end
local function mark(row)
 return row.m.PrimaryPart:FindFirstChild("EGGRUMBLE_ConversionCandidate")
end
local function order(row)
 return row.m.PrimaryPart:FindFirstChild("EGGRUMBLE_ConvertedOrder")
end
local function allied(row)
 return row.m:GetAttribute("EGGRUMBLE_NeutralFriendlyOwnerId")
end
local function prepare(s,need)
 local rows,center=settle(s,need)
 local at=place(rows[1],center,5,0,38)
 return rows,center,at
end
local function firstSeal(row)
 activate(player,"A")
 equal(row.h.Health,27,"existing real A reduced neutral HP from 38 to 27")
 equal(row.m:GetAttribute("EGGRUMBLE_NeutralSeals"),1,"exact first legitimate hit receipt")
 check(not allied(row),"one real seal never converts")
end
local function convert(row)
 firstSeal(row)
 advanceTo(now+.91)
 activate(player,"A")
 equal(row.h.Health,16,"second actual A reduces 27 to 16")
 check(allied(row)==tostring(player.UserId),"actual neutral changed owner through existing seal")
end
local function wall(s,at)
 local part=Instance.new("Part")
 part.Name="NativeZombieWall"
 part.Size=Vector3.new(.85,7,12)
 part.CFrame=CFrame.new(at)
 part.Anchored=true;part.CanCollide=true;part.CanQuery=true;part.Parent=s.world
 return part
end

function growthCases.z19_mark()
 local s=begin(true)
 local rows,center=prepare(s,2)
 local first,far=rows[1],rows[2]
 place(far,center,7,0,38)
 local color=first.accent.Color
 activate(player,"B")
 equal(energy(s),70,"actual B debits E30")
 check(mark(first) and not mark(far) and not allied(first) and first.accent.Color==color,"candidate only, original color and team")
 check(mark(first):FindFirstChildOfClass("TextLabel").Text=="転向候補","visible bounded candidate label")
 equal(first.h.Health,38,"cue never changes HP")
 local stamp=player:GetAttribute("EGGRUMBLE_SkillCastSignature")
 activate(player,"B")
 equal(energy(s),70,"repeat cannot spend a second time")
 check(player:GetAttribute("EGGRUMBLE_SkillCastSignature")==stamp,"repeat no valid cast receipt")
 advanceTo(now+2.40)
 check(not mark(first) and not allied(first),"expiry removes marker without creating ally")
 return "B actual Host/Tool -> candidate only, S0 distance 6, E30, CD20, expiry"
end

function growthCases.z19_no_member()
 local s=begin(true)
 local rows=prepare(s,1)
 activate(player,"C")
 equal(energy(s),100,"empty command rejected before debit")
 check(not allied(rows[1]) and not order(rows[1]),"one healthy ordinary neutral is not an owned convert")
 return "C denies unconverted model without energy or extra unit"
end

function growthCases.z19_real_mark_confirmed()
 local s=begin(true)
 local rows=prepare(s,1)
 local first=rows[1]
 firstSeal(first)
 activate(player,"B")
 check(mark(first) and not allied(first),"standalone B marks exact target")
 advanceTo(now+.91)
 activate(player,"A")
 local confirmed=first.m.PrimaryPart:FindFirstChild("EGGRUMBLE_ConversionConfirmed")
 check(not mark(first) and allied(first) and confirmed and not order(first),"actual charm replaces cue with acknowledgement")
 equal(first.h.Health,16,"same old A damage authority")
 advanceTo(now+1.1)
 check(not confirmed.Parent and allied(first),"short acknowledgement expires without releasing original charm")
 return "035 acknowledgement follows the genuine old A conversion and creates no order nor soldier"
end

function growthCases.z19_real_order()
 local s=begin(true)
 local rows,center=prepare(s,2)
 local first,enemy=rows[1],rows[2]
 place(enemy,center,13,0,80)
 convert(first)
 local expiry=first.m:GetAttribute("EGGRUMBLE_NeutralCharmUntil")
 rootPart.CFrame=CFrame.lookAt(center+Vector3.new(0,0,2),center+Vector3.new(-1,0,2))
 activate(player,"C")
 equal(energy(s),55,"one actual C debit E45")
 check(order(first) and not order(enemy) and not allied(enemy),"existing own live convert only")
 advanceTo(now+.80)
 check(first.m.PrimaryPart.Position.X<center.X+3.8 and order(first),"real converted Model moves towards issued order")
 equal(first.m:GetAttribute("EGGRUMBLE_NeutralCharmUntil"),expiry,"same retained charm lifetime")
 advanceTo(now+1.62)
 check(not order(first) and allied(first),"directive expires before unchanged underlying conversion")
 return "C actual S0 order E45, existing Model moves, order expires before original charm"
end

function growthCases.z19_combo()
 local s=begin(true)
 local rows=prepare(s,1)
 local target=rows[1]
 firstSeal(target)
 activate(player,"D")
 equal(energy(s),20,"one E80 combo debit")
 check(mark(target) and not allied(target) and not order(target),"D has candidate but no premature ownership or order")
 local stamp=player:GetAttribute("EGGRUMBLE_SkillCastSignature")
 activate(player,"D")
 check(player:GetAttribute("EGGRUMBLE_SkillCastSignature")==stamp,"D cannot replay")
 advanceTo(now+.91)
 activate(player,"A")
 check(allied(target)==tostring(player.UserId) and order(target) and not mark(target),"same real server seal drives 019 command")
 equal(target.h.Health,16,"only original A hit writes HP")
 local orderBefore=order(target)
 local componentEnergy=energy(s)
 activate(player,"B");activate(player,"C")
 check(order(target)==orderBefore,"D component deadlines fence immediate B/C")
 equal(energy(s),componentEnergy,"neither B nor C debits after D")
 return "D E80 once, A retains HP authority, original CHARM -> owned order"
end

function growthCases.z19_no_seal()
 local s=begin(true)
 local rows=prepare(s,1)
 activate(player,"D")
 equal(energy(s),100,"combo needs an actual already prepared target")
 check(not mark(rows[1]) and not allied(rows[1]),"no off-path mark or convert")
 return "D no server seal record -> no stage progress, cue, ownership or energy spend"
end

function growthCases.z19_wrong_target()
 local s=begin(true,true)
 local rows,center=prepare(s,2)
 local first,other=rows[1],rows[2]
 firstSeal(first)
 activate(player,"D")
 check(mark(first),"real combo mark")
 first.m:PivotTo(CFrame.new(center+Vector3.new(-23,8,21)))
 place(other,center,5,0,38)
 advanceTo(now+.91)
 convert(other)
 check(not order(other) and not allied(first),"different true conversion cannot finish bound combo")
 secondRoot.CFrame=CFrame.lookAt(center,center+Vector3.new(1,0,0))
 check(s.swarm.orderCharmed(second,"GUARD",nil)==false,"no command from a different owner without own conversion record")
 return "bound Model and caster cannot be exchanged"
end

local function invalidCombo(kind)
 local s=begin(true)
 local rows,center=prepare(s,1)
 local first=rows[1]
 firstSeal(first)
 activate(player,"D")
 check(mark(first),"armed receipt before invalidation")
 if kind=="timeout" then
  advanceTo(now+2.41)
 elseif kind=="carry" then
  player:SetAttribute("EGGRUMBLE_CarryingEgg",true)
  advanceTo(now+.41)
 elseif kind=="replacement" then
  local replacement=Instance.new("Model")
  replacement.Name="ZombieNativeReplacement"
  local root=Instance.new("Part")
  root.Name="HumanoidRootPart";root.CFrame=rootPart.CFrame;root.Parent=replacement
  local h=Instance.new("Humanoid");h.Parent=replacement
  replacement.PrimaryPart=root;replacement.Parent=workspace
  player.Character=replacement
  advanceTo(now+.41)
 elseif kind=="finish" then
  s.rules.phase="FINISHED"
  advanceTo(now+.41)
 end
 check(not mark(first) and not order(first) and not allied(first),"pending combo invalidation retires its cue")
 if kind=="timeout" then
  activate(player,"A")
  check(allied(first) and not order(first),"valid late legacy conversion cannot resurrect expired combo")
 elseif kind=="carry" then
  player:SetAttribute("EGGRUMBLE_CarryingEgg",false)
  advanceTo(now+.51)
  activate(player,"A")
  check(allied(first) and not order(first),"exiting carry cannot revive canceled combo")
 end
 return "019 pending " .. kind .. " cleanup and no extra command"
end
function growthCases.z19_combo_timeout() return invalidCombo("timeout") end
function growthCases.z19_combo_carry() return invalidCombo("carry") end
function growthCases.z19_combo_old_avatar() return invalidCombo("replacement") end
function growthCases.z19_finish() return invalidCombo("finish") end

function growthCases.z19_wall_and_immune()
 local s=begin(true)
 local rows,center=prepare(s,2)
 local first,immune=rows[1],rows[2]
 place(immune,center,0,4,38)
 immune.m:SetAttribute("EGGRUMBLE_NeutralSpecies","WARDEN_BOSS")
 local cover=wall(s,center+Vector3.new(2,0,0))
 activate(player,"B")
 equal(energy(s),100,"wall and unsupported boss rejected before debit")
 check(not mark(first) and not mark(immune) and not allied(immune),"actual LOS and original eligible species allowlist")
 cover:Destroy()
 activate(player,"B")
 check(mark(first) and not mark(immune),"same target now legal without wall")
 return "blocked normal and unsupported species fail; real unblocked candidate succeeds"
end

function growthCases.z19_runtime_off()
 local s=begin(true)
 local rows=prepare(s,1)
 local first=rows[1]
 firstSeal(first)
 activate(player,"D")
 check(mark(first),"active D before runtime toggle")
 local stale=tools(player).D
 workspace:SetAttribute(FLAG,false)
 advanceTo(now+.42)
 legacy(tools(player))
 check(not mark(first) and not order(first) and not stale.Parent,"same active Host restores standard Tools, stale D retired")
 stale.Activated:Fire()
 advanceTo(now+.52)
 activate(player,"A")
 check(allied(first) and not order(first),"baseline CurseConversion continues with OFF")
 return "runtime OFF retires new loadout and leaves actual original same-round conversion"
end

function growthCases.z19_physical_off()
 local s=begin(false)
 local rows=prepare(s,1)
 check(not s.swarm.zombieCandidates and not s.zombieConversionLoadouts,"physical parent contains no optional logic")
 convert(rows[1])
 check(not order(rows[1]),"actual parent immutable original conversion")
 return "physical parent 69 sources, original A/B/C and original real two-attack charm"
end

function growthCases.z19_legacy()
 local s=begin(false)
 local rows=prepare(s,1)
 convert(rows[1])
 check(not order(rows[1]),"ON package preserves opt-out original conversion")
 return "ON without opt-in has original actual A/B/C and old two-hit conversion"
end
end
