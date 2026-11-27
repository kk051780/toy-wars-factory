do
local names={'風切弾','石弾','星弾'}
local ids={'MAGE-033','MAGE-051','MAGE-071'}

local function selectedSession(index)
 local roleStand=scenes:FindFirstChild('ROLE_MAGE')
 trigger(player,roleStand,'職業選択')
 for _=1,index do
  advanceTo(now+1)
  trigger(player,roleStand,'装備する')
 end
 check(player:GetAttribute('EGGRUMBLE_LobbyMageProjectileName')==names[index],'lobby actual equip cycle')
 local session=ready('MAGE_RUNTIME_READY_'..index)
 check(session.mageProjectiles[player.UserId]==ids[index],'actual Host owns frozen selected ID')
 trigger(player,roleStand,'装備する')
 check(session.mageProjectiles[player.UserId]==ids[index],'joined player cannot change selected projectile')
 return session
end

local function pose(session,health)
 local neutral=spawnCurrentNeutral(session)
 local hum=neutral:FindFirstChildOfClass('Humanoid')
 local floor=session.world:FindFirstChild('TacticalBattlefield')
 local origin=floor.Position+Vector3.new(180,20,80)
 local aligned=origin+Vector3.new(5,1,0)
 neutral:SetAttribute('EGGRUMBLE_NeutralSpeed',0)
 neutral:PivotTo(CFrame.new(aligned))
 hum.Health=health or 17
 rootPart.CFrame=CFrame.new(origin,origin+Vector3.new(1,0,0))
 advanceTo(now+.39)
 -- Native player-owned target geometry is a fixture input. The exact
 -- Swarm spawned this neutral and still owns live HP and real KO hooks.
 neutral:PivotTo(CFrame.new(aligned))
 local snapshot=session.swarm.getRoleGrowthSnapshot(player)
 check(snapshot and snapshot.role=='MAGE' and snapshot.stage==0,'same actual match has current S0/E')
 local params=RaycastParams.new()
 params.FilterType=Enum.RaycastFilterType.Exclude
 params.FilterDescendantsInstances={character,second.Character,session.world:FindFirstChild('NeutralHorde')}
 for _,bot in pairs(session.botActors or {}) do table.insert(params.FilterDescendantsInstances,bot) end
 params.RespectCanCollide=true
 local wall=workspace:Raycast(origin+Vector3.new(0,1,0),Vector3.new(8,0,0),params)
 check(not wall,'fixture aim must be clear before intentional walls: '..(if wall then wall.Instance.Name else 'clear'))
 return neutral,hum,origin,aligned, snapshot
end

local function contains(rows,model)
 for _,row in ipairs(rows) do if row.token==model then return true end end
 return false
end

function growthCases.mage_wind_hit()
 local session=selectedSession(1)
 growthCases.expectStart(session,player,'WIND_BEFORE_B1',nil)
 local neutral,hum,origin,_,before=pose(session,17)
 local launch=origin+Vector3.new(0,1,0)
 check(contains(session.swarm.projectileCandidates(launch,8),neutral),'real alive neutral enters candidate query')
 local beforeKo=session.swarm.getTotal()
 local launched=now
 activate(player,'A')
 check(hum.Health==17 and session.swarm.getRoleGrowthSnapshot(player).energy==before.energy-30,
  'actual Tool charges exactly E30 before physical contact')
 local signature=player:GetAttribute('EGGRUMBLE_SkillCastSignature')
 check(type(signature)=='string' and signature:match('^MAGE:A:'),'actual Tool server receipt')
 activate(player,'A')
 check(player:GetAttribute('EGGRUMBLE_SkillCastSignature')==signature,'immediate replay does not start second cast')
 advanceTo(launched+.07)
 equal(hum.Health,17,'Wind has no damage before travel reaches real target')
 advanceTo(launched+.21)
 equal(hum.Health,0,'Wind reached genuine neutral and used real HP authority')
 drainDeferred()
 equal(session.swarm.getTotal(),beforeKo+1,'one real Wind KO')
 check(not contains(session.swarm.projectileCandidates(launch,8),neutral),'dead neutral cannot remain on projectile list')
 growthCases.expectPublic(player,2,10,true,1,'WIND_B2_KO')
 return 'actual Mage equip prompt -> Host Tool A -> private E/CD -> swept real neutral -> one KO and unchanged B2'
end

function growthCases.mage_stone_wall_and_dodge()
 local session=selectedSession(2)
 local neutral,hum,origin,aligned,before=pose(session,64)
 local wall=Instance.new('Part')
 wall.Name='Native_Authoritative_StoneWall'
 wall.Size=Vector3.new(1,12,12)
 wall.CFrame=CFrame.new(origin+Vector3.new(2,1,0))
 wall.Anchored=true
 wall.CanCollide=true
 wall.CanQuery=true
 wall.Parent=session.world
 local started=now
 activate(player,'A')
 check(session.swarm.getRoleGrowthSnapshot(player).energy==before.energy-30,'blocked flight legal start costs once')
 advanceTo(started+.5)
 equal(hum.Health,64,'real solid wall intercepts moving stone before neutral')
 equal(session.swarm.getTotal(),0,'wall does not fabricate KO')
 check(wall.Parent==session.world and wall.CanCollide,'stone changes no world geometry')
 wall:Destroy()
 advanceTo(started+15.01)
 neutral,hum,origin,aligned=pose(session,64)
 local at=now
 activate(player,'A')
 advanceTo(at+.07)
 neutral:PivotTo(CFrame.new(aligned+Vector3.new(0,0,4)))
 advanceTo(at+.4)
 equal(hum.Health,64,'neutral moved sideways before crossing actual travel segment')
 equal(session.swarm.getTotal(),0,'dodge creates no KO/false receipt')
 return 'actual stone Tool; solid world blocker; next exact CD cast; active sideways dodge; no terrain mutation'
end

function growthCases.mage_star_tell_and_nontracking()
 local session=selectedSession(3)
 local neutral,hum,origin,_,before=pose(session,64)
 local when=now
 activate(player,'A')
 equal(hum.Health,64,'Star no damage at authorized start')
 check(session.swarm.getRoleGrowthSnapshot(player).energy==before.energy-30,'Star legal start pays once')
 check(session.world:FindFirstChild('EGGRUMBLE_StarAim')~=nil,'exact star preview part created before shot')
 advanceTo(when+.21)
 equal(hum.Health,64,'0.22-second tell has no neutral damage')
 check(session.world:FindFirstChild('EGGRUMBLE_MAGE-071')==nil,'visible star held until tell')
 rootPart.CFrame=CFrame.new(origin,origin+Vector3.new(0,0,1))
 advanceTo(when+.40)
 check(hum.Health<64,'Star still flies the exact original warned lane')
 check(session.world:FindFirstChild('EGGRUMBLE_StarAim')==nil,'tell cue cleaned up after release')
 return 'actual Star Tool fixed line, visible 0.22s warning, real HP and no retarget when caster turns'
end

function growthCases.mage_player_restraint_midflight()
 local session=selectedSession(3)
 local _,hum,_,_,before=pose(session,64)
 local cast=now
 activate(player,'A')
 check(session.swarm.getRoleGrowthSnapshot(player).energy==before.energy-30,'legal Star start before custody')
 advanceTo(cast+.1)
 player:SetAttribute('EGGRUMBLE_Restrained',true)
 check(session.swarm.getRoleGrowthSnapshot(player)==nil,'existing server growth sees Player restraint')
 advanceTo(cast+.51)
 equal(hum.Health,64,'RED_PLAYER_RESTRAINT_MIDFLIGHT_DAMAGE')
 return 'server Player restraint after start cancels before the old warned hit, no double spend'
end

function growthCases.mage_crossworld_neutral_reparent()
 local session=selectedSession(1)
 local neutral,hum,origin=pose(session,64)
 local otherArena=Instance.new('Folder')
 otherArena.Name='AnotherPrivateArena';otherArena.Parent=workspace
 neutral.Parent=otherArena
 local launch=origin+Vector3.new(0,1,0)
 local candidate=contains(session.swarm.projectileCandidates(launch,8),neutral)
 local accepted=session.swarm.damageProjectileTarget(player,character,neutral,launch,17)
 check(not candidate and not accepted,
  'RED_FOREIGN_PARENT_IN_PROJECTILE_CANDIDATES'..';candidate='..tostring(candidate)..';hit='..tostring(accepted)..';HP='..hum.Health)
 local cast=now
 activate(player,'A')
 advanceTo(cast+.4)
 equal(hum.Health,64,'OTHER_WORLD_HP_UNCHANGED')
 return 'actual live map token moved to another world fails query, direct damage acceptance and Tool flight'
end

local function cancelFlight(name)
 local session=selectedSession(3)
 local _,hum,origin,_,before=pose(session,64)
 local started=now
 activate(player,'A')
 check(session.swarm.getRoleGrowthSnapshot(player).energy==before.energy-30,'initial server debit')
 advanceTo(started+.1)
 if name=='egg' then session.rules.castles[tostring(player.UserId)].heldEggs=1
 elseif name=='avatar' then player.Character=Instance.new('Model')
 elseif name=='dead' then humanoid:TakeDamage(humanoid.Health)
 elseif name=='role' then player:SetAttribute('EGGRUMBLE_Role','WARRIOR')
 elseif name=='world' then
  local field=session.world:FindFirstChild('TacticalBattlefield')
  rootPart.CFrame=CFrame.new(origin+Vector3.new(field.Size.X,0,0))
 elseif name=='end' then session.rules.phase='FINISHED'
 elseif name=='off' then workspace:SetAttribute('P0D_ENABLE_PRIVATE_MAGE_PROJECTILES',false)
 elseif name=='leave' then Players.PlayerRemoving:Fire(player) end
 advanceTo(started+.55)
 equal(hum.Health,64,'A live round and exact actor fence prevent cancelled Star: '..name)
 check(session.world:FindFirstChild('EGGRUMBLE_StarAim')==nil and session.world:FindFirstChild('EGGRUMBLE_MAGE-071')==nil,
  'no retained warning or projectile')
 return 'actual warned flight cancels at '..name
end
for _,name in ipairs({'egg','avatar','dead','role','world','end','off','leave'}) do
 growthCases['mage_cancel_'..name]=function() return cancelFlight(name) end
end

function growthCases.mage_legacy_tools()
 local session=selectedSession(1)
 workspace:SetAttribute('P0D_ENABLE_PRIVATE_MAGE_PROJECTILES',false)
 local neutral,hum,origin,_,before=pose(session,100)
 local skills={{'A',25,30},{'B',21,52},{'C',14,42}}
 for _,item in ipairs(skills) do
  hum.Health=100
  neutral:PivotTo(CFrame.new(origin+Vector3.new(item[2],1,0)))
  if item[1]=='C' then humanoid.Health=50 end
  activate(player,item[1])
  local signature=player:GetAttribute('EGGRUMBLE_SkillCastSignature')
  check(type(signature)=='string' and signature:match('^MAGE:'..item[1]..':'),'legacy real Tool receipt '..item[1])
  equal(hum.Health,100-item[3],'legacy Mage real damage '..item[1])
  check(session.swarm.getRoleGrowthSnapshot(player).energy==before.energy,'old skill does not debit projectile E')
  if item[1]=='C' then check(humanoid.Health>50,'old Mage C still heals') end
 end
 return 'feature OFF routes old Mage A, B and C damage through exact prior roles; C heals and does not debit new E'
end

function growthCases.mage_cooldown_and_energy()
 local session=selectedSession(1)
 local neutral,hum,_,aligned=pose(session,64)
 neutral:PivotTo(CFrame.new(aligned+Vector3.new(0,0,4)))
 local start=now
 local api=session.swarm
 activate(player,'A')
 local signature=player:GetAttribute('EGGRUMBLE_SkillCastSignature')
 equal(api.getRoleGrowthSnapshot(player).energy,70,'first cast pays exactly once')
 advanceTo(start+15.999)
 activate(player,'A')
 check(player:GetAttribute('EGGRUMBLE_SkillCastSignature')==signature,'before the authorized CD deadline')
 equal(api.getRoleGrowthSnapshot(player).energy,70,'attempt during cooldown does not debit')
 advanceTo(start+16)
 activate(player,'A')
 check(player:GetAttribute('EGGRUMBLE_SkillCastSignature')~=signature,'at the full CD deadline')
 equal(api.getRoleGrowthSnapshot(player).energy,40,'second accepted Tool pays exactly once')
 advanceTo(start+32)
 activate(player,'A')
 equal(api.getRoleGrowthSnapshot(player).energy,10,'third accepted Tool pays exactly once')
 signature=player:GetAttribute('EGGRUMBLE_SkillCastSignature')
 advanceTo(start+48)
 activate(player,'A')
 check(player:GetAttribute('EGGRUMBLE_SkillCastSignature')==signature,'insufficient E creates no cast signature')
 equal(api.getRoleGrowthSnapshot(player).energy,10,'insufficient E does not go negative')
 equal(hum.Health,64,'off-axis target remains unharmed on all casts')
 return 'three real paid Tools at exact CD, no idle charge, no cooldown or insufficient-E receipt'
end

function growthCases.mage_stage_energy_attributes()
 local session=selectedSession(1)
 local model,_,origin,aligned=pose(session,64)
 model:PivotTo(CFrame.new(aligned+Vector3.new(0,0,4)))
 equal(player:GetAttribute('EGGRUMBLE_RoleAbilityStage'),0,'published S0 after actual Native sample')
 equal(player:GetAttribute('EGGRUMBLE_RoleAbilityEnergy'),100,'published E100 after actual Native sample')
 activate(player,'A')
 equal(player:GetAttribute('EGGRUMBLE_RoleAbilityEnergy'),70,'published E70 immediately after actual Tool debit')
 rootPart.CFrame=CFrame.new(origin+Vector3.new(.75,0,0),origin+Vector3.new(1.75,0,0))
 advanceTo(now+.38)
 equal(player:GetAttribute('EGGRUMBLE_RoleAbilityEnergy'),71,'sample refreshes integer E outside the formal Tool debit')
 growthCases.expectPublic(player,1,0,true,0,'MAGE_ATTRIBUTES_KEEP_B1')
 session.rules.phase='FINISHED'
 session.world:SetAttribute('EGGRUMBLE_MatchPhase','FINISHED')
 advanceTo(now+.02)
 check(player:GetAttribute('EGGRUMBLE_RoleAbilityStage')==nil
  and player:GetAttribute('EGGRUMBLE_RoleAbilityEnergy')==nil,'old growth view attributes retired')
 return 'actual S/E debut, immediate Tool debit, existing tick recharge, independent B, phase-driven clear'
end
end
