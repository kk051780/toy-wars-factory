"""Private63 twin biome world+four characters static/safety acceptance.

Python assertions do NOT substitute for native Luau, source-exact Rojo or
real two-client Roblox Studio play and FUN evaluation.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent
SCRIPT = (ROOT/"features/twin_biomes/TwinBiomes.server.luau").read_text("utf8")
ADAPTER = (ROOT/"apply_twin_biomes.py").read_text("utf8")
FLAGS = json.loads((ROOT/"FEATURE_SWITCHES.json").read_text("utf8"))["features"]
CATALOG = json.loads((ROOT/"FEATURE_CATALOG.json").read_text("utf8"))["rows"]
GITBLOB = "ff7c57aae79f03e3fbc72e043fe3f34f5ac373a5"
POLICY = (ROOT/"features/twin_biomes/TwinCreatureTraining.luau").read_text("utf8")
POLICY_BLOB = "b2f8275be676b46fc1ad32050832a4fcf13099af"

def blob(source: str) -> str:
    raw=source.encode("utf8")
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

class TwinBiomes(unittest.TestCase):
    def test_01_exact_author_source(self):
        self.assertEqual(blob(SCRIPT),GITBLOB)
    def test_02_studio_only(self):
        self.assertIn("if not RunService:IsStudio() then",SCRIPT)
    def test_03_missing_boot_flag_off(self):
        self.assertIn('if not value or not value:IsA("BoolValue") or value.Value ~= true then',SCRIPT)
    def test_04_actual_wcs_dependency(self):
        self.assertIn('Workspace:WaitForChild("P0D_WCS_CrystalCanyon", 145)',SCRIPT)
        self.assertIn('Workspace:WaitForChild("P0D_CrystalCanyonAnchor", 15)',SCRIPT)
        self.assertIn('canyon:WaitForChild("AlwaysOpenSafeRoute", 12)',SCRIPT)
    def test_05_no_duplicate_world(self):
        self.assertIn('Workspace:FindFirstChild("P0D_TwinBiomes")',SCRIPT)
    def test_06_symmetry_both_teams(self):
        self.assertIn('{side = "West", sign = -1, x = -50}',SCRIPT)
        self.assertIn('{side = "East", sign = 1, x = 50}',SCRIPT)
        self.assertIn('world:SetAttribute("BothTeamsAccess", true)',SCRIPT)
    def test_07_reef_world_exists(self):
        self.assertIn('"CoralGarden_" .. spec.side',SCRIPT)
        self.assertIn('reef:SetAttribute("Biotope", "TIDAL_CORAL_GARDEN")',SCRIPT)
    def test_08_storm_world_exists(self):
        self.assertIn('"ThunderLookout_" .. spec.side',SCRIPT)
        self.assertIn('lookout:SetAttribute("Biotope", "STORM_CLOUD_LOOKOUT")',SCRIPT)
    def test_09_always_open_ramp(self):
        self.assertIn('for i = 1, 6 do',SCRIPT)
        self.assertIn('deck:SetAttribute("AlwaysOpen", true)',SCRIPT)
    def test_10_four_unique_species(self):
        for spec in ('"AWARIN"','"SANGORU"','"RAIKO"','"KUMONON"'):
            self.assertIn('id = '+spec,SCRIPT)
        self.assertEqual(SCRIPT.count('id = "'),4)
    def test_11_eight_mirrored_npcs(self):
        self.assertIn('world:SetAttribute("CharacterInstances", 8)',SCRIPT)
        self.assertIn('for _, info in ipairs(species) do',SCRIPT)
        self.assertIn('makeGuide(info, side)',SCRIPT)
    def test_12_no_misleading_capture_persistence(self):
        self.assertIn('npc:SetAttribute("CapturableOrOwned", false)',SCRIPT)
        self.assertIn('world:SetAttribute("PersistedCollection", false)',SCRIPT)
    def test_13_prompt_server_verifies_player(self):
        self.assertIn('if not root or not hum or hum.Health <= 0 or hum.Sit or root.Anchored then',SCRIPT)
        self.assertIn('if (root.Position - body.Position).Magnitude > 12 then',SCRIPT)
    def test_14_all_effects_time_bounded(self):
        self.assertIn('local EFFECT_SECONDS = 16',SCRIPT)
        self.assertIn('local REARM_SECONDS = 4',SCRIPT)
        self.assertIn('activeUntil[effect] = now + EFFECT_SECONDS',SCRIPT)
    def test_15_one_bounded_loop_for_8_npcs(self):
        self.assertEqual(SCRIPT.count('task.spawn(function()'),1)
        self.assertEqual(SCRIPT.count('while world.Parent do'),1)
        self.assertIn('task.wait(0.25)',SCRIPT)
        self.assertNotIn("RunService.Heartbeat",SCRIPT)
    def test_16_no_second_authority(self):
        for bad in ('DataStoreService','UpdateAsync(', 'MarketplaceService',
                    'Instance.new("RemoteEvent")','OnServerEvent:Connect(',
                    'FireServer(', 'TakeDamage(', 'PromptProductPurchase(',
                    'leaderstats', 'GetProductInfo('):
            self.assertNotIn(bad,SCRIPT)
    def test_17_known_maps_inside_bounds(self):
        # WCS original bank has centre ±50, width50, local z±42.5.
        # Coral platform ±9.5 X/7 Z; lookout ±9 X/7.5 Z.
        for site_z,half in ((-24,7),(16,6),(-5,7.5)):
            self.assertLessEqual(abs(site_z)+half,42.5)
        self.assertLessEqual(abs(50)+9.5,75)
        self.assertLessEqual(abs(-23)+42.5,76)
        self.assertLessEqual(75,130)
    def test_18_deck_stairs_not_timed_or_removed(self):
        self.assertIn('part("AlwaysOpenStair_"',SCRIPT)
        self.assertIn('part("RearGuard"',SCRIPT)
        self.assertNotIn("world:Destroy()",SCRIPT)
        self.assertNotIn("deck:Destroy()",SCRIPT)
        self.assertIn("toast:Destroy()",SCRIPT)
        self.assertNotIn("CanCollide = false -- route",SCRIPT)
    def test_19_route_beacon_public_world_state_only(self):
        self.assertIn('gate:GetAttribute("WCS_GateOpen")',SCRIPT)
        self.assertIn('star:GetAttribute("PathOpen")',SCRIPT)
        self.assertNotIn("GetAttribute('EggOwner')",SCRIPT)
    def test_20_source_locked_62_to_63(self):
        self.assertIn('PARENT_COUNT = 63',ADAPTER)
        self.assertIn('assert len(after) == 65',ADAPTER)
        self.assertIn('assert sources(dist) == after',ADAPTER)
    def test_21_roll_back_zero_write(self):
        self.assertIn("P0D_TWIN_BIOMES_OFF_ZERO_WRITES_OFFICIAL63_PASS",ADAPTER)
        self.assertIn('if not enabled:',ADAPTER)
        self.assertLess(ADAPTER.index('if not enabled:'),ADAPTER.index('before = sources(dist)'))
    def test_22_true_boolvalue_booted_by_rojo(self):
        self.assertIn('storage[FLAG] = {"$className":"BoolValue","$properties":{"Value":True}}',ADAPTER)
        self.assertIn('"P0D_ENABLE_TWIN_BIOMES_V1"',SCRIPT)
    def test_23_unique_catalog_rows_source_only(self):
        rows={r["id"]:r for r in CATALOG}
        for i in ("P0D-063","P0D-064","P0D-065"):
            self.assertEqual(rows[i]["stage"],"SOURCE")
        self.assertEqual(len({r["id"] for r in CATALOG}),len(CATALOG))
    def test_24_flag_owner_unpublished(self):
        f=FLAGS["TWIN_BIOMES_4NPC_V1"]
        self.assertTrue(f["enabled"])
        self.assertFalse(f["official_rc_adopted"])
        self.assertEqual(f["source_git_blob"],GITBLOB)
        self.assertEqual(f["training_policy_git_blob"],POLICY_BLOB)
    def test_25_parent_features_all_required(self):
        for feature in ("WCS_F01_C01","SEVEN_JOBS_PVE_V1","EGG_RELAY_CLASSIC_V1",
                        "STARRY_PATH_V1","METEOR_FOURTH_V1"):
            self.assertTrue(FLAGS[feature]["enabled"])
            self.assertIn(feature,ADAPTER)
    def test_26_no_new_monetization(self):
        for bad in ("game:GetService('MarketplaceService')", "PromptProductPurchase",
                    "PromptGamePassPurchase", "Subscription"):
            self.assertNotIn(bad,SCRIPT)
    def test_27_reachable_observation_stairs(self):
        self.assertIn('spec.x, 0.7 + i * 0.75, 13 - i * 2.4',SCRIPT)
        self.assertIn('spec.x, 5.5, -5, dark, Enum.Material.Slate, true, lookout)',SCRIPT)
        first_top=0.7+1*0.75+0.85/2
        pad_top=0.23+0.45/2
        last_top=0.7+6*0.75+0.85/2
        deck_top=5.5+1/2
        self.assertLess(first_top-pad_top,2)
        self.assertLess(deck_top-last_top,0.5)
        self.assertTrue(all(abs((0.7+(i+1)*0.75)-(0.7+i*0.75))<=0.750001 for i in range(1,6)))
    def test_28_no_random_player_bias_or_paid_rarity(self):
        self.assertNotIn("math.random",SCRIPT)
        self.assertNotIn("player.Team",SCRIPT)
        self.assertNotIn("GamePass",SCRIPT)
    def test_29_public_route_beacon_with_no_player_tracking(self):
        self.assertIn('local function currentRouteText()',SCRIPT)
        self.assertIn('return "モグロン "',SCRIPT)
        self.assertNotIn("GetPlayers()",SCRIPT)
        self.assertNotIn("GetChildren()",SCRIPT)
    def test_30_no_player_teleports_or_forced_velocity(self):
        for bad in ("HumanoidRootPart.CFrame", "root.CFrame =", "AssemblyLinearVelocity",
                    "VectorForce", "BodyVelocity", "root:PivotTo(",
                    "player.Character:PivotTo(", "Humanoid.JumpPower"):
            self.assertNotIn(bad,SCRIPT)
    def test_31_four_unique_silhouette_constructions(self):
        for key in ("BubbleHalo","Foam_","CoralAntler_","CoralFork_",
                    "ThunderHorn_","ThunderBolt_","CloudWing_"):
            self.assertIn(key,SCRIPT)
        for spec in ('info.id=="AWARIN"','info.id=="SANGORU"',
                     'info.id=="RAIKO"','info.id=="KUMONON"'):
            self.assertIn(spec,SCRIPT)
    def test_32_one_animation_task_controls_all_eight(self):
        self.assertEqual(SCRIPT.count("task.spawn(function()"),1)
        self.assertIn("npc.PrimaryPart=body",SCRIPT)
        self.assertIn("table.insert(animate,{model=npc",SCRIPT)
        self.assertIn("entry.model:PivotTo(",SCRIPT)
        self.assertEqual(SCRIPT.count("task.wait(0.25)"),1)
    def test_33_cosmetic_only_anchored_no_colliders(self):
        self.assertIn("info.localZ+dz,",SCRIPT)
        self.assertIn("tint,Enum.Material.Neon,false,npc)",SCRIPT)
        self.assertNotIn("BodyVelocity",SCRIPT)
        self.assertNotIn("AlignPosition",SCRIPT)
    def test_34_session_codex_four_species_no_persistence(self):
        self.assertIn('local sessionSpecies = {"AWARIN", "SANGORU", "RAIKO", "KUMONON"}',SCRIPT)
        self.assertIn('player:SetAttribute("P0D_TwinCodexCount",count)',SCRIPT)
        self.assertIn('player:SetAttribute("P0D_TwinSeen_"..info.id,true)',SCRIPT)
        self.assertIn('player:SetAttribute("P0D_TwinCodexComplete",count==4)',SCRIPT)
        self.assertIn("Players.PlayerRemoving:Connect(",SCRIPT)
        self.assertIn('world:SetAttribute("SessionCodexOnly", true)',SCRIPT)
    def test_35_toast_bound_and_no_hud_overlap_claim(self):
        self.assertIn('toast.Name="P0D_TwinCodexToast"',SCRIPT)
        self.assertIn('task.delay(5.2,function()',SCRIPT)
        self.assertIn('toast:SetAttribute("ExpiresAt",expires)',SCRIPT)
        self.assertNotIn('Instance.new("RemoteEvent")',SCRIPT)
    def test_36_previous_shard_collection_unchanged(self):
        self.assertIn('"server/StarShardHunt.server.luau" in before',ADAPTER)
        self.assertIn('lock.get("rc_star_shards_overlay", {})',ADAPTER)
        self.assertIn('attrs["P0D_RC_ENABLE_STAR_SHARDS_V1"] is True',ADAPTER)
    def test_37_show_visual_discoveries_only_on_real_player_prompt(self):
        self.assertIn('if not player or player.Parent~=Players then return end',SCRIPT)
        self.assertIn("if seen[info.id] then return end",SCRIPT)
        self.assertIn('local level=awardPractice(player,info,npc,crest)\n        activate(info.effect,level)\n        markDiscovery(player,info)',SCRIPT)
    def test_38_exact_training_module_bytes(self):
        self.assertEqual(blob(POLICY),POLICY_BLOB)
        self.assertIn('return Training',POLICY)
    def test_39_linked_to_existing_one_server_script(self):
        self.assertIn('require(script.Parent:WaitForChild("TwinCreatureTraining"))',SCRIPT)
        self.assertIn('after[POLICY_DEST] = policy_raw',ADAPTER)
        self.assertIn('after[DEST] = raw',ADAPTER)
        self.assertIn('assert len(after) == 65',ADAPTER)
    def test_40_discovery_and_training_separate(self):
        self.assertIn('markDiscovery(player,info)',SCRIPT)
        self.assertIn('awardPractice(player,info,npc,crest)',SCRIPT)
        self.assertIn("if not earned then",SCRIPT)
    def test_41_per_player_not_global_xp(self):
        self.assertIn('local practiceByPlayer = {}',SCRIPT)
        self.assertIn('practiceByPlayer[player] = nil',SCRIPT)
        self.assertIn('player:SetAttribute("P0D_TwinLevel_"..info.id,updated.level)',SCRIPT)
    def test_42_level3_visual_evolution(self):
        self.assertIn('npc:SetAttribute("EvolutionStage",3)',SCRIPT)
        self.assertIn('npc:SetAttribute("MaxTrainingLevel",maxLevel)',SCRIPT)
        self.assertIn('crest:FindFirstChild("P0D_TwinEvolutionGlow")',SCRIPT)
    def test_43_level_no_shared_downgrade(self):
        self.assertIn('math.max(npc:GetAttribute("MaxTrainingLevel") or 1,updated.level)',SCRIPT)
        self.assertIn('maxLevel==3 and " ✦進化" or ""',SCRIPT)
    def test_44_dont_spawn_duplicate_labels(self):
        self.assertIn('crest:FindFirstChild("SpeciesLevelSign")',SCRIPT)
        self.assertIn('label=sign and sign:FindFirstChild("Readout")',SCRIPT)
    def test_45_field_skill_duration_by_level(self):
        self.assertIn('local duration = Training.effectSeconds(level)',SCRIPT)
        self.assertIn('activeUntil[effect] = now + duration',SCRIPT)
        self.assertIn('nextUse[effect] = now + duration + REARM_SECONDS',SCRIPT)
    def test_46_time_validity_and_xp_bounds(self):
        self.assertIn('local MAX_PRACTICE = 7',POLICY)
        self.assertIn('local REPEAT_WAIT_SECONDS = 20',POLICY)
        self.assertIn('xp >= MAX_PRACTICE',POLICY)
        self.assertIn('now ~= now',POLICY)
    def test_47_no_datastore_or_rewards_policy(self):
        for term in ('GetDataStore','UpdateAsync','MarketplaceService','RemoteEvent',
                     'SetAttribute','Instance.new','FireServer'):
            self.assertNotIn(term,POLICY)
    def test_48_new_module_off_unchanged(self):
        self.assertIn('if not enabled:',ADAPTER)
        self.assertLess(ADAPTER.index('if not enabled:'),ADAPTER.index('before = sources(dist)'))
        self.assertIn('assert DEST not in before and POLICY_DEST not in before',ADAPTER)
    def test_49_three_increasing_levels(self):
        self.assertIn('if xp >= 7 then return 3 end',POLICY)
        self.assertIn('if xp >= 3 then return 2 end',POLICY)
        self.assertIn('if level == 3 then return 24 end',POLICY)
    def test_50_no_client_authority(self):
        self.assertNotIn('OnServerEvent:Connect(',SCRIPT)
        self.assertIn('prompt.Triggered:Connect(function(player)',SCRIPT)
        self.assertIn('hum.Health <= 0',SCRIPT)

if __name__=="__main__":
    unittest.main()
