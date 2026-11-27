-- Virtual Humanoids do not integrate movement. The real companion still owns
-- every MoveTo request, while each scenario supplies deterministic root poses.
function methods:MoveTo(at) self._nativeMoveGoal=at end

do
local FLAG='P0D_ENABLE_PRIVATE_BEAST_THUNDER'
local function start(optIn)
 local stand=scenes:FindFirstChild('ROLE_BEAST')
 trigger(player,stand,'職業選択')
 if optIn then
  trigger(player,stand,'装備する')
  check(player:GetAttribute('EGGRUMBLE_LobbyBeastLoadoutName')=='雷角竜','actual opt-in on existing Beast stand')
 end
 local live=ready('PRIVATE_OWNED_BEAST','BEAST')
 local deck={}
 for _,tool in ipairs(player:FindFirstChildOfClass('Backpack'):GetChildren()) do
  local id=tool:GetAttribute('EGGRUMBLE_InternalToolId')
  local slot=type(id)=='string' and id:match('^EGGRUMBLE_SKILL_(%u)_')
  if slot then deck[slot]=tool end
 end
 check(deck.A and deck.B and deck.C,'original Beast tools remain')
 if optIn then
  check(live.beastThunderLoadouts[player.UserId] and deck.D and deck.D.Name=='技D・雷角竜'
   and deck.D:GetAttribute('EGGRUMBLE_FixedAbilityId')=='BEAST-005','only real grounded D is minted')
 else check(not deck.D,'physical parent never shows a new D') end
 return live,deck
end
local function parkAndPrepare(live,count)
 local floor=live.world:FindFirstChild('TacticalBattlefield')
 local center=floor.Position+Vector3.new(170,floor.Size.Y*.5,-115)
 rootPart.CFrame=CFrame.lookAt(center+Vector3.new(-3,3,0),center+Vector3.new(-2,3,0))
 humanoid.Sit=false;humanoid.PlatformStand=false
 humanoid.FloorMaterial=Enum.Material.Grass
 local horde=live.world:FindFirstChild('NeutralHorde')
 local mobs={}
 for _=1,40 do
  table.clear(mobs)
  for _,model in ipairs(horde:GetChildren()) do
   local hp=model:FindFirstChildOfClass('Humanoid')
   if hp and hp.Health>0 then
    model:SetAttribute('EGGRUMBLE_NeutralSpeed',0)
    model:PivotTo(CFrame.new(center+Vector3.new(-60,3,30)))
    table.insert(mobs,{model=model,hp=hp})
   end
  end
  if #mobs>=count then break end
  advanceTo(now+.35)
 end
 advanceTo(now+.39)
 check(#mobs>=count and live.swarm.getRoleGrowthSnapshot(player).energy==100,'actual horde contains required live neutral models')
 return center,mobs
end
local function witness(live)
 for _,model in ipairs(live.world:GetChildren()) do
  if model:GetAttribute('EGGRUMBLE_BeastCompanion')==true then return model end
 end
 return nil
end
local function summon(live,point)
 activate(player,'B')
 local pet=witness(live)
 check(pet and pet.Parent==live.world and pet:GetAttribute('EGGRUMBLE_OwnerId')==player.UserId,'original B spawned its real owned escort')
 pet:PivotTo(CFrame.lookAt(point+Vector3.new(0,1.5,0),point+Vector3.new(1,1.5,0)))
 local h=pet:FindFirstChildOfClass('Humanoid')
 h.FloorMaterial=Enum.Material.Grass
 advanceTo(now+.075)
 return pet,h
end
local function aim(target,at,health)
 target.model:PivotTo(CFrame.new(at))
 target.hp.Health=health or 96
end
local function energy(live) return live.swarm.getRoleGrowthSnapshot(player).energy end
local function tell(live) return live.world:FindFirstChild('EGGRUMBLE_BeastThunderTell') end
local function sig() return player:GetAttribute('EGGRUMBLE_SkillCastSignature') end

function growthCases.beast_grounded_discharge()
 local live=start(true)
 local point,mobs=parkAndPrepare(live,3)
 activate(player,'D')
 check(not witness(live) and not tell(live) and energy(live)==100,'D never manufactures its own companion')
 local pet=summon(live,point)
 local head=pet:FindFirstChild('Head')
 local original=head.Color
 local first,near,far=mobs[1],mobs[2],mobs[3]
 aim(first,point+Vector3.new(2,2.15,0))
 aim(near,point+Vector3.new(3.8,2.15,0))
 aim(far,point+Vector3.new(4.25,2.15,0))
 local castle=live.rules.castles[tostring(second.UserId)]
 local castleHP,otherHP=castle.hp,secondHumanoid.Health
 local t=now
 activate(player,'D')
 local accepted=sig()
 check(accepted and accepted:match('^BEAST:D:') and energy(live)==60 and tell(live).Size.Y==8,'actual E40 and stage-0 radius4 tell')
 check(witness(live)==pet and head.Color~=original,'one existing owned model receives the horn cue')
 check(live.swarm.tryRoleGrowthCast(player,'BEAST',1,1,{['BEAST-005']=1})==nil,'22-second deadline uses the existing state')
 activate(player,'D')
 check(sig()==accepted and energy(live)==60,'replay cannot double debit while warned')
 advanceTo(t+.339)
 check(first.hp.Health==96 and near.hp.Health==96,'no damage before the ring warning ends')
 advanceTo(t+.341)
 check(first.hp.Health==83 and near.hp.Health==96 and far.hp.Health==96,'real nearest valid neutral gets -13 within stage cap1')
 check(not tell(live) and witness(live)==pet and head.Color==original,'original model survives and its appearance reverts')
 check(castle.hp==castleHP and secondHumanoid.Health==otherHP,'ground discharge has no human or castle damage')
 return 'original summon and single owned escort issue one exact server neutral discharge after warning'
end

function growthCases.beast_los_ko()
 local live=start(true)
 local point,mobs=parkAndPrepare(live,2)
 local pet=summon(live,point)
 local blocked,legal=mobs[1],mobs[2]
 aim(blocked,point+Vector3.new(2.0,2.15,0),10)
 aim(legal,point+Vector3.new(0,2.15,3.4),10)
 local wall=Instance.new('Part')
 wall.CFrame=CFrame.new(point+Vector3.new(1.23,3,0));wall.Size=Vector3.new(.16,6,1.2)
 wall.Anchored=true;wall.CanCollide=true;wall.CanQuery=true;wall.Parent=live.world
 local t=now
 activate(player,'D')
 check(tell(live) and energy(live)==60,'current companion authorizes actual cast')
 advanceTo(t+.341)
 check(blocked.hp.Health==10 and legal.hp.Health==0 and live.swarm.getTotal()==1 and witness(live)==pet,
  'obstruction cannot consume cap, one grounded legal target credits one real KO')
 return 'same Swarm verifies cover and credits one actual neutral Humanoid death'
end

local function negative(kind)
 local live,deck=start(true)
 local point,mobs=parkAndPrepare(live,1)
 local mob=mobs[1]
 if kind=='unregistered' then
  local actor=Instance.new('Model');actor.Name='BEAST_SKY_BEAST_'..tostring(player.UserId)
  actor:SetAttribute('EGGRUMBLE_BeastCompanion',true);actor:SetAttribute('EGGRUMBLE_OwnerId',player.UserId)
  actor.Parent=live.world
  activate(player,'D')
  check(not tell(live) and energy(live)==100,'name and attributes cannot spoof a BeastEscort owned lease')
  return 'unregistered craft and replicated owner tag do not admit a discharge'
 end
 local pet,h=summon(live,point)
 aim(mob,point+Vector3.new(2,2.15,0))
 if kind=='air' then
  h.FloorMaterial=Enum.Material.Air
  activate(player,'D')
  check(not tell(live) and energy(live)==100,'airborne companion rejected before debit')
  return 'unsettled or airborne companion never admits ground lightning'
 end
 if kind=='seat' then
  local seat=Instance.new('VehicleSeat');seat.Name='PilotSeat';seat.Parent=live.world
  humanoid.SeatPart=seat
  activate(player,'D')
  check(not tell(live) and energy(live)==100,'existing or spoofed seated state cannot stand in for same-body Beast flight')
  return 'seated rider cannot bypass the grounded-only candidate'
 end
 local t=now
 activate(player,'D')
 check(tell(live) and energy(live)==60,'legal D queued before invalidation')
 advanceTo(t+.10)
 if kind=='death' then h:TakeDamage(h.Health)
 elseif kind=='avatar' then player.CharacterRemoving:Fire(character);player.Character=Instance.new('Model')
 elseif kind=='off' then workspace:SetAttribute(FLAG,false);drainDeferred();check(deck.D.Parent==nil,'actual rollback removes D')
 elseif kind=='carry' then live.rules.castles[tostring(player.UserId)].heldEggs=1
 elseif kind=='round' then live.rules.phase='FINISHED' end
 -- The original AI remains authorized after a rejected special. Retire the
 -- test neutral beyond its normal reach so only a stale special would see it.
 if kind=='off' then aim(mob,point+Vector3.new(0,2.7,3.97)) end
 advanceTo(t+.341)
 check(not tell(live) and mob.hp.Health==96,'stale request cannot release a late horn hit: '..kind)
 return 'pending ground discharge cancels on '..kind
end
for _,kind in ipairs({'unregistered','air','seat','death','avatar','off','carry','round'}) do
 growthCases['beast_negative_'..kind]=function() return negative(kind) end
end

function growthCases.beast_physical_parent_off()
 local live=start(false)
 local point=parkAndPrepare(live,1)
 local pet=summon(live,point)
 check(witness(live)==pet and not tell(live),'parent standard Beast summon remains actual')
 return 'original Beast A/B/C and one live companion remain on unchanged physical rollback'
end
end
