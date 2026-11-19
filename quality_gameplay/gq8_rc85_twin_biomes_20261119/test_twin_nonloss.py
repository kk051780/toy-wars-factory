#!/usr/bin/env python3
"""Original S1 TwinBiomes+TwinCreatureTraining+TwinBond contract, standalone QA."""
from pathlib import Path
p=Path(__file__).parent
s=(p/"EGGRUMBLE_LegacyTwinBiomes.server.luau").read_text(encoding="utf8")
b=(p/"compose_real68.py").read_text(encoding="utf8")
single=[
 "GQ8_RC85_TWIN_BIOMES_TRAINING_BOND_REAL68_20261119",
 "if not RunService:IsStudio() then return end",
 'world.Name="GQ8_RC85_TwinBiomes"',
 'world:SetAttribute("Species",4);world:SetAttribute("Models",8)',
 'world:SetAttribute("TrainingCapXP",7)',
 'world:SetAttribute("TrainingCooldownSeconds",20)',
 'world:SetAttribute("BondLifetimeSeconds",180)',
 'world:SetAttribute("BondSwitchCooldownSeconds",20)',
 'world:SetAttribute("BondMaxPveBonus",1.2)',
 'world:SetAttribute("SessionOnly",true)',
 'local token=HttpService:GenerateGUID(false)',
 'arena:SetAttribute("EGGRUMBLE_TwinBondSession",token)',
 'if level<2 then return end',
 'p:SetAttribute("EGGRUMBLE_TwinBondServerGranted",true)',
 'p:SetAttribute("EGGRUMBLE_TwinBondExpires",lease.expires)',
 'p:SetAttribute("EGGRUMBLE_TwinBondLevel",level)',
 'p:SetAttribute("EGGRUMBLE_TwinBondSession",token)',
 'p:GetAttribute("EGGRUMBLE_QueuedMode")~=mode',
 'p:GetAttribute("EGGRUMBLE_Eliminated")==true',
 'rayParams.RespectCanCollide=true',
 'state.nextAt=now+20',
 'state.level=if state.xp>=7 then 3 elseif state.xp>=3 then 2 else 1',
 'activateBond(p,sp,state.level)',
 'root.CFrame.RightVector*2.9',
 'Players.PlayerRemoving:Connect',
 'world.Parent=arena',
]
for key in single:assert s.count(key)==1,(key,s.count(key))
for name in ("AWARIN","SANGORU","RAIKO","KUMONON"):
 assert s.count('id="'+name+'"')==1,name
for req in ("TWIN_BIOMES_4NPC_V1","TWIN_CREATURE_TRAINING_V1",
            "TWIN_BOND_PVE_COMPANION_V1"):
 assert req in b,req
assert 'buildOnBank("WEST",west)' in s and 'buildOnBank("EAST",east)' in s
assert 'for _,sp in ipairs(SPECIES) do' in s and 'for _,x in ipairs({-0.73,0.73})' in s
assert 'if old and old.species~=info.id then clearBond(p) end' in s
for dangerous in ("DataStoreService","MarketplaceService","RemoteEvent","RemoteFunction",
                  "Humanoid:TakeDamage","SetAsync(","TeleportService","ProcessReceipt"):
 assert dangerous not in s,dangerous
for term in ("PARENT67","NOT_SOURCE_EXACT65_","NOT_EXACT_CANYON","NONLOSS_ORIGINAL_SOURCE_",
             "ONE_NEW_SCRIPT_ONLY","SOURCE_EXACT","original_rc85_artifact_id",
             "off67_private_place_sha256","existing", "second_game_owners"):
 # EXISTING_COMBAT seen in source's source contract.
 if term=="SOURCE_EXACT":term="NOT_SOURCE_EXACT65"
 if term=="existing":term="EXISTING_HIT_GATE"
 assert term in b,term
assert b.count('{"$path":REL}')==1
assert 'neutralDamage*=math.max(1,bondMult/dojoMult)' in b
assert 'session.world:GetAttribute("EGGRUMBLE_TwinBondSession")' in b
assert 'if stageBasic==true and root.Parent==p.Character' in b
assert 'session.swarm.damageFromPlayer(p,neutralAt,range,neutralDamage,shape)' in b
print("GQ8_TWIN_BIOMES_8_NPC_PRACTICE_BOND_ONE_COMBAT_STUDIO_ONLY_CONTRACT_PASS")
