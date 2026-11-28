do
local FLAG='P0D_ENABLE_PRIVATE_MAGE_GROUND_TELLS'
local function deck()
 local tools={}
 for _,item in ipairs(player:FindFirstChildOfClass('Backpack'):GetChildren()) do
  local id=item:GetAttribute('EGGRUMBLE_InternalToolId')
  local slot=type(id)=='string' and id:match('^EGGRUMBLE_SKILL_(%u)_')
  if slot then tools[slot]=item end
 end
 return tools
end
local function start()
 local stand=scenes:FindFirstChild('ROLE_MAGE')
 trigger(player,stand,'職業選択')
 trigger(player,stand,'地上技を装備')
 check(player:GetAttribute('EGGRUMBLE_LobbyMageProjectileName')=='地上四術','real new lobby mode')
 local live=ready('PRIVATE_MAGE_GROUND_TELLS')
 check(live.mageProjectiles[player.UserId]=='MAGE_GROUND_TELLS','same Host frozen selection')
 local tools=deck()
 for slot,id in pairs({A='MAGE-006',B='MAGE-022',C='MAGE-058',D='MAGE-069'}) do
  check(tools[slot] and tools[slot]:GetAttribute('EGGRUMBLE_FixedAbilityId')==id,'physical Tool has fixed identity '..id)
 end
 return live
end
local function move(at)
 rootPart.CFrame=CFrame.lookAt(at,at+Vector3.new(1,0,0))
end
local function prep(live,count)
 local field=live.world:FindFirstChild('TacticalBattlefield')
 local floor=field.Position+Vector3.new(170,field.Size.Y*.5,-115)
 local origin=floor+Vector3.new(0,3,0)
 local at=floor+Vector3.new(8,0,0)
 local horde=live.world:FindFirstChild('NeutralHorde')
 local models={}
 move(origin)
 humanoid.Sit=false;humanoid.PlatformStand=false;humanoid.FloorMaterial=Enum.Material.Grass
 for _=1,42 do
  table.clear(models)
  for _,model in ipairs(horde:GetChildren()) do
   local hp=model:FindFirstChildOfClass('Humanoid')
   if hp and hp.Health>0 then
    model:SetAttribute('EGGRUMBLE_NeutralSpeed',0)
    model:PivotTo(CFrame.new(origin+Vector3.new(-51,0,29)))
    table.insert(models,{model=model,hp=hp})
   end
  end
  if #models>=count then break end
  advanceTo(now+.35)
 end
 advanceTo(now+.39)
 check(#models>=count,'actual Swarm spawns enough neutral actors for exact budget')
 local snapshot=live.swarm.getRoleGrowthSnapshot(player)
 check(snapshot and snapshot.stage==0 and snapshot.energy==100,'current authoritative E100')
 return origin,at,models
end
local function aim(row,at,species)
 local h=2*(row.model.PrimaryPart.Size.Y/2.5)
 local root=at+Vector3.new(0,h,0)
 row.model:PivotTo(CFrame.new(root));row.hp.Health=150
 row.model:SetAttribute('EGGRUMBLE_NeutralSpecies',species or 'BANNER_KNIGHT')
 return root
end
local function energy(live) return live.swarm.getRoleGrowthSnapshot(player).energy end
local function effect(live,name) return live.world:FindFirstChild('EGGRUMBLE_'..name) end
local function sig() return player:GetAttribute('EGGRUMBLE_SkillCastSignature') end
local function wall(live,where,size)
 local part=Instance.new('Part')
 part.Anchored=true;part.CanCollide=true;part.CanQuery=true
 part.Size=size;part.CFrame=CFrame.new(where);part.Parent=live.world
 return part
end

function growthCases.ground_fire()
 local live=start()
 local _,at,mobs=prep(live,2)
 aim(mobs[1],at+Vector3.new(0,0,.5),'ICE_SLIME')
 aim(mobs[2],at+Vector3.new(0,0,-1.65))
 local castle=live.rules.castles[tostring(second.UserId)]
 local oldHP,oldHuman=castle.hp,secondHumanoid.Health
 local t=now
 activate(player,'A')
 local accepted=sig()
 local tell=effect(live,'FirePillarTell')
 check(accepted:match('^MAGE:A:') and energy(live)==60 and tell and tell.Size.Y==4,'fire E40 r2')
 check(not tell.CanCollide and not tell.CanTouch and not tell.CanQuery,'warning is visibly inert')
 activate(player,'A')
 check(sig()==accepted and energy(live)==60,'same current work prevents duplicate debit')
 advanceTo(t+.999)
 check(mobs[1].hp.Health==150 and not effect(live,'FirePillarImpact'),'true one-second tell before damage')
 advanceTo(t+1.001)
 check(mobs[1].hp.Health==113 and mobs[2].hp.Health==150 and effect(live,'FirePillarImpact'),
  'nearest neutral takes one FIRE/ICE qualified HP hit and S0 cap1')
 check(castle.hp==oldHP and secondHumanoid.Health==oldHuman and live.swarm.getTotal()==0,'no PvP, castle or ghost KO')
 return 'real Fire Pillar E40, whole 1s warn, exact r2 and actual elemental HP once'
end

function growthCases.ground_lightning()
 local live=start()
 local _,at,mobs=prep(live,1)
 aim(mobs[1],at+Vector3.new(.4,0,.2),'BABY_GOLEM')
 local t=now
 activate(player,'B')
 local tell=effect(live,'LightningMarkerTell')
 check(sig():match('^MAGE:B:') and energy(live)==65 and tell
  and math.abs(tell.Position.X-at.X)<.02,'exact targeted S0 range8 / E35')
 advanceTo(t+.799)
 check(mobs[1].hp.Health==150,'no early lightning')
 advanceTo(t+.801)
 check(mobs[1].hp.Health==126 and effect(live,'LightningMarkerImpact'),'existing LIGHTNING to EARTH resistance applies once')
 advanceTo(t+1.3)
 check(mobs[1].hp.Health==126,'one pulse and no repeat')
 return 'real lightning at legal target after .8s, one resisted exact current Swarm hit'
end

function growthCases.ground_stone()
 local live=start()
 local _,at,mobs=prep(live,2)
 local before=aim(mobs[1],at+Vector3.new(.45,0,1.05))
 local heavy=aim(mobs[2],at+Vector3.new(.15,0,-.25),'BABY_GOLEM')
 local t=now
 activate(player,'C')
 check(sig():match('^MAGE:C:') and energy(live)==60 and effect(live,'StoneArmTell'),'exact real Stone arm starts once')
 advanceTo(t+.799)
 check((mobs[1].model.PrimaryPart.Position-before).Magnitude<.02,'stone cannot move target through the warning')
 advanceTo(t+.801)
 check((mobs[1].model.PrimaryPart.Position-(before+Vector3.new(2.8,0,0))).Magnitude<.1
  and (mobs[2].model.PrimaryPart.Position-heavy).Magnitude<.02 and effect(live,'StoneArmImpact'),
  'existing exact checked movement pushes only one regular neutral and preserves large resistance')
 check(mobs[1].hp.Health==150 and mobs[2].hp.Health==150 and live.swarm.getTotal()==0,'pure force without alternate HP/KO')
 return 'real stone arm uses existing safe neutral sweep, ignores heavy targets and keeps HP'
end

function growthCases.ground_holy()
 local live=start()
 local _,at,mobs=prep(live,3)
 local a=aim(mobs[1],at+Vector3.new(.6,0,-.8))
 local b=aim(mobs[2],at+Vector3.new(.9,0,.8),'BABY_GOLEM')
 local c=aim(mobs[3],at+Vector3.new(-2.4,0,1.1))
 local t=now
 activate(player,'D')
 check(sig():match('^MAGE:D:') and energy(live)==55 and effect(live,'HolyPillarTell').Size.Y==6,'S0 holy cue r3 E45')
 advanceTo(t+.999)
 check((mobs[1].model.PrimaryPart.Position-a).Magnitude<.02,'true full second before repulsion')
 advanceTo(t+1.001)
 local movedA=mobs[1].model.PrimaryPart.Position-a
 local movedB=mobs[2].model.PrimaryPart.Position-b
 check(math.abs(movedA.Magnitude-3.4)<.1 and math.abs(movedB.Magnitude-1.7)<.1 and movedA.Z<0 and movedB.Z>0,
  'ordinary and resistant actual bodies pushed in distinct radial directions')
 check((mobs[3].model.PrimaryPart.Position-c).Magnitude<.02 and effect(live,'HolyPillarImpact'),'total S0 cap2')
 for i=1,3 do check(mobs[i].hp.Health==150,'Holy repels without new HP behavior') end
 return 'real holy radial displacement, bounded heavy resistance and two-target cap'
end

local function negative(kind)
 local live=start()
 local origin,at,mobs=prep(live,1)
 local prior=aim(mobs[1],at+Vector3.new(.45,0,1.25))
 local owner=live.rules.castles[tostring(player.UserId)]
 if kind=='illegal_floor' then
  wall(live,at+Vector3.new(0,.9,0),Vector3.new(1.4,1.8,1.4))
  activate(player,'A')
  check(not effect(live,'FirePillarTell') and energy(live)==100,'not a legal owned arena floor')
  return 'decor and foreign placement never accept or charge'
 elseif kind=='carry' then
  owner.heldEggs=1;activate(player,'A');activate(player,'C');owner.heldEggs=0
  check(not effect(live,'FirePillarTell') and not effect(live,'StoneArmTell') and energy(live)==100,'no carrying bypass')
  return 'held egg blocks all ground casts before debit'
 end
 local t=now
 activate(player,if kind=='push_wall' then 'C' else 'A')
 check(energy(live)==60,'cast genuinely accepted before late interference')
 advanceTo(t+.29)
 if kind=='caster_wall' then wall(live,origin+Vector3.new(4,-1,0),Vector3.new(.2,8,6))
 elseif kind=='push_wall' then wall(live,prior+Vector3.new(mobs[1].model.PrimaryPart.Size.X*.5+.045,0,0),Vector3.new(.10,8,8))
 elseif kind=='avatar' then player.CharacterRemoving:Fire(character);player.Character=Instance.new('Model')
 elseif kind=='off' then
  workspace:SetAttribute(FLAG,false);drainDeferred()
  local tools=deck()
  check(tools.A.Name=='技A・氷弾' and tools.B.Name=='技B・爆炎陣' and tools.C.Name=='技C・雷光治癒' and not tools.D,
   'real old A/B/C restored, stale D removed')
 elseif kind=='phase' then
  live.rules.phase='FINISHED';live.world:SetAttribute('EGGRUMBLE_MatchPhase','FINISHED');drainDeferred()
 end
 advanceTo(t+1.09)
 check(mobs[1].hp.Health==150 and (mobs[1].model.PrimaryPart.Position-prior).Magnitude<.10
  and not effect(live,'FirePillarImpact') and not effect(live,'StoneArmImpact')
  and not effect(live,'FirePillarTell') and not effect(live,'StoneArmTell'),
  'late invalidation cannot fabricate damage, movement or effect hit: '..kind)
 return 'current-life/terrain recheck denies late ground release on '..kind
end
for _,kind in ipairs({'illegal_floor','carry','caster_wall','push_wall','avatar','off','phase'}) do
 growthCases['ground_negative_'..kind]=function() return negative(kind) end
end

function growthCases.ground_parent_off()
 local live=ready('PRIVATE_MAGE_OLD_PHYSICAL')
 local tools=deck()
 check(not live.mageProjectiles[player.UserId] and tools.A.Name=='技A・氷弾' and tools.B.Name=='技B・爆炎陣'
  and tools.C.Name=='技C・雷光治癒' and not tools.D,'actual physical OFF old kit preserved')
 return 'existing Mage default and original physical rollback stay intact'
end

function growthCases.ground_ancestor_zombie_default()
 local flag="P0D_ENABLE_PRIVATE_ZOMBIE_COMBO_019"
 check(workspace:GetAttribute(flag)==nil,"no forced fixture feature attribute")
 local stand=scenes:FindFirstChild("ROLE_ZOMBIE")
 trigger(player,stand,"職業選択")
 trigger(player,stand,"装備する")
 check(player:GetAttribute("EGGRUMBLE_LobbyZombieLoadoutName")=="転向援符・冥軍指揮・冥軍転向令",
  "historical optional kit visible by default under physical PRIVATE profile")
 local session=ready("PRIVATE_ZOMBIE_DEFAULT_LEASE","ZOMBIE")
 local tools=deck()
 check(session.zombieConversionLoadouts[player.UserId]==true and workspace:GetAttribute(flag)==nil,
  "Host retains explicit player opt-in without attribute changes")
 check(tools.A.Name=="技A・呪印波動" and tools.B:GetAttribute("EGGRUMBLE_FixedAbilityId")=="ZOMBIE-035"
  and tools.C:GetAttribute("EGGRUMBLE_FixedAbilityId")=="ZOMBIE-040"
  and tools.D:GetAttribute("EGGRUMBLE_FixedAbilityId")=="COMBO-019","existing opt-in B/C/D identity")
 return "Zombie remains grantable by the local player's explicit opt-in with nil attribute"
end
end
